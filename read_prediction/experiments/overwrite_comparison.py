"""Compare frozen prediction errors with next writes at the same starting offset."""

import argparse
import gc
import json
from pathlib import Path
import resource
import time

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.checks.mae_improvement import verify_hashes
from read_prediction.extended import load_duration
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import TICKS_PER_SECOND

OUTPUT = PROJECT_ROOT / "results/overwrite-comparison"
DAYS = (5, 6, 7)
METHODS = ("current", "address_median", "selected")


def dump(path, record):
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def hashes(paths):
    return {path.relative_to(PROJECT_ROOT).as_posix(): fingerprint(path)["sha256"]
            for path in sorted(set(paths))}


def next_write_table(events):
    """Adjacent writes within a stable offset group; reads do not reset the group."""
    writes = np.flatnonzero(events["is_read"] == 0)
    next_writes = np.full(len(writes), -1, dtype=np.int64)
    if len(writes) < 2:
        return writes, next_writes
    offsets = events["offset"][writes]
    order = np.argsort(offsets, kind="stable")
    grouped_offsets = offsets[order]
    same_address = grouped_offsets[:-1] == grouped_offsets[1:]
    next_writes[order[:-1][same_address]] = writes[order[1:][same_address]]
    return writes, next_writes


def next_overwrite(events, write_indices):
    writes, next_writes = next_write_table(events)
    indices = np.asarray(write_indices, dtype=np.int64)
    if not len(indices):
        return np.empty(0, dtype=np.int64)
    positions = np.searchsorted(writes, indices)
    if np.any(positions >= len(writes)) or not np.array_equal(writes[positions], indices):
        raise ValueError("Requested indices must refer to Write events")
    return next_writes[positions]


def distribution(values):
    if not len(values):
        return None
    p10, median, p90 = np.quantile(values, [.1, .5, .9])
    return {"n": len(values), "mean_seconds": float(values.mean()),
            "median_seconds": float(median), "p10_seconds": float(p10),
            "p90_seconds": float(p90), "max_seconds": float(values.max())}


def paired(errors, durations):
    if not len(errors):
        return None
    mae = float(errors.mean())
    positive = durations > 0
    ratios = errors[positive] / durations[positive]
    return {"n": len(errors), "mae_seconds": mae,
            "fraction_error_lt_overwrite": float(np.mean(errors < durations)),
            "mae_lt_mean_overwrite": bool(mae < durations.mean()),
            "mae_lt_median_overwrite": bool(mae < np.median(durations)),
            "median_error_to_overwrite_ratio": float(np.median(ratios)) if len(ratios) else None,
            "p90_error_to_overwrite_ratio": float(np.quantile(ratios, .9)) if len(ratios) else None}


def summarize(data, annotation):
    overwrite = annotation["overwrite_seconds"]
    lower_bound = annotation["overwrite_censor_lower_bound_seconds"]
    read_first = annotation["read_before_overwrite"]
    known = np.isfinite(overwrite)
    unknown = ~known
    read_first_known = read_first & known
    n = len(overwrite)
    result = {"n": n, "overwrite_observed_n": int(known.sum()),
              "overwrite_censored_n": int(unknown.sum()),
              "zero_overwrite_n": int(np.count_nonzero(known & (overwrite == 0))),
              "read_before_overwrite_n": int(read_first.sum()),
              "overwrite_before_read_n": int(np.count_nonzero(known & ~read_first)),
              "fraction_read_before_overwrite": float(read_first.mean()) if n else None,
              "overwrite_distribution": distribution(overwrite[known]),
              "read_first_overwrite_distribution": distribution(overwrite[read_first_known]),
              "methods": {}}
    for method in METHODS:
        errors = np.abs(data["target_seconds"] - data[method])
        known_passes = int(np.count_nonzero(errors[known] < overwrite[known]))
        censored_passes = int(np.count_nonzero(errors[unknown] < lower_bound[unknown]))
        result["methods"][method] = {
            "all_mae_seconds": float(errors.mean()) if n else None,
            "paired": paired(errors[known], overwrite[known]),
            "read_first_mae_seconds": float(errors[read_first].mean()) if read_first.any() else None,
            "read_first_paired": paired(errors[read_first_known], overwrite[read_first_known]),
            "censored_definitely_error_lt_overwrite_n": censored_passes,
            "fraction_error_lt_overwrite_lower_bound": (known_passes + censored_passes) / n if n else None,
            "fraction_error_lt_overwrite_upper_bound": (known_passes + int(unknown.sum())) / n if n else None,
        }
    return result


def verify_source_samples(events, writes, examples):
    """Independent forward walk over ungrouped writes for sampled next-write truth."""
    if not examples:
        return 0
    wanted = np.asarray(sorted({int(events["offset"][index]) for index in examples}), dtype=np.int64)
    pending = {}
    verified = 0
    for start in range(0, len(writes), 250_000):
        block = writes[start:start + 250_000]
        offsets = events["offset"][block]
        positions = np.minimum(np.searchsorted(wanted, offsets), len(wanted) - 1)
        matching = wanted[positions] == offsets
        for index, offset in zip(block[matching], offsets[matching]):
            previous = pending.pop(int(offset), None)
            if previous is not None:
                expected_index, expected_seconds = examples[previous]
                assert int(index) == expected_index
                elapsed = (int(events["timestamp"][index]) - int(events["timestamp"][previous])) / TICKS_PER_SECOND
                assert elapsed == expected_seconds
                verified += 1
            if int(index) in examples:
                pending[int(offset)] = int(index)
    for index in pending.values():
        assert examples[index][0] == -1 and np.isnan(examples[index][1])
        verified += 1
    assert verified == len(examples)
    return verified


def analyze(workload):
    output = OUTPUT / workload
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    original = PROJECT_ROOT / "results/mae-improvement" / workload
    holdout = json.loads((original / "holdout.json").read_text())
    frozen = json.loads((original / "frozen.json").read_text())
    verify_hashes(PROJECT_ROOT, frozen["hashes"])
    input_paths = [original / "holdout.json", original / "frozen.json", original / "selection.json"]
    input_paths += [original / f"holdout-day{day}.predictions.npz" for day in DAYS]
    selection = json.loads((original / "selection.json").read_text())
    input_paths += [PROJECT_ROOT / definition["model_path"] for definition in
                    (selection["definitions"]["current"], frozen["selection"]) if definition.get("model_path")]
    input_hashes = hashes(input_paths)
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 168, 200_000_000, output / "events.bin")
    assert json.loads(json.dumps(source)) == holdout["source"], "Source differs from the saved holdout"
    writes, next_writes = next_write_table(events)
    days, parts, examples = {}, [], {}
    for day in DAYS:
        with np.load(original / f"holdout-day{day}.predictions.npz") as saved:
            data = {key: saved[key] for key in ("write_event_index", "next_read_event_index", "target_seconds", *METHODS)}
        indices = data["write_event_index"]
        positions = np.searchsorted(writes, indices)
        np.testing.assert_array_equal(writes[positions], indices)
        following = next_writes[positions]
        observed = following >= 0
        duration = np.full(len(indices), np.nan)
        duration[observed] = (events["timestamp"][following[observed]] - events["timestamp"][indices[observed]]) / TICKS_PER_SECOND
        assert np.all(events["offset"][following[observed]] == events["offset"][indices[observed]])
        assert np.all(events["is_read"][following[observed]] == 0)
        annotation = {"write_event_index": indices, "next_write_event_index": following,
                      "overwrite_seconds": duration,
                      "overwrite_censor_lower_bound_seconds": (source["last_timestamp"] - events["timestamp"][indices]) / TICKS_PER_SECOND,
                      "read_before_overwrite": ~observed | (data["next_read_event_index"] < following)}
        day_summary = summarize(data, annotation)
        for method in METHODS:
            np.testing.assert_allclose(day_summary["methods"][method]["all_mae_seconds"],
                                       holdout["days"][str(day)]["metrics"][method]["mae_seconds"], rtol=1e-12)
        days[str(day)] = {**day_summary, "coverage": holdout["days"][str(day)]["coverage"]}
        np.savez(output / f"day{day}.comparison.npz", **annotation)
        for row in np.unique(np.linspace(0, len(indices) - 1, min(64, len(indices)), dtype=int)):
            examples[int(indices[row])] = (int(following[row]), float(duration[row]))
        parts.append((data, annotation))
        print(f"{workload} day {day}: known overwrite {int(observed.sum()):,}/{len(indices):,}; read-first={day_summary['fraction_read_before_overwrite']:.2%}", flush=True)
    verified = verify_source_samples(events, writes, examples)
    del events, writes, next_writes
    gc.collect()
    (output / "events.bin").unlink()
    pooled_data = {key: np.concatenate([part[0][key] for part in parts]) for key in ("target_seconds", *METHODS)}
    pooled_annotation = {key: np.concatenate([part[1][key] for part in parts]) for key in
                         ("overwrite_seconds", "overwrite_censor_lower_bound_seconds", "read_before_overwrite")}
    del parts
    gc.collect()
    pooled = summarize(pooled_data, pooled_annotation)
    code_paths = [Path(__file__), PROJECT_ROOT / "read_prediction/checks/overwrite_comparison.py",
                  PROJECT_ROOT / "docs/protocols/overwrite-comparison-protocol.md",
                  PROJECT_ROOT / "docs/protocols/mae-improvement-protocol.md"]
    dump(output / "summary.json", {"workload": workload, "source": source,
                                   "input_hashes": input_hashes, "code_hashes": hashes(code_paths),
                                   "days": days, "pooled": pooled, "new_fits": 0,
                                   "source_samples_verified": verified,
                                   "elapsed_seconds": time.monotonic() - started,
                                   "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
    print(f"Completed {workload}: {pooled['overwrite_observed_n']:,} paired examples, {verified} next-write histories checked", flush=True)


def report():
    records = {workload: json.loads((OUTPUT / workload / "summary.json").read_text())
               for workload in ("usr_1", "prxy_1")}
    for workload in records:
        if not (OUTPUT / workload / "verification.json").exists():
            raise ValueError("Verify both comparisons before generating the report")
    lines = ["# MAE и время до следующей перезаписи", "",
             "Проверка сохранённых прогнозов дней 5–7; новых обучений нет. Перезапись означает следующую Write с тем же начальным Offset, не пересечение диапазонов или полную замену физического блока.", "",
             "## Основное сравнение", "",
             "Для usr_1 показан ранее выбранный смешанный прогноз (selected), для prxy_1 — ранее рекомендованная прежняя модель (current). Сравнение MAE с интервалом выполняется на одинаковых записях, у которых наблюдалась следующая Write. Среднее и медиана интервала — разные ориентиры; основной пообъектный показатель — доля error < overwrite.", "",
             "| Нагрузка / метод | Все оценённые N | Известна перезапись | MAE всей выборки, с | MAE совпадающей выборки, с | Среднее до перезаписи, с | Медиана до перезаписи, с | Ошибка меньше перезаписи | Чтение раньше повторной записи (вся выборка) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for workload, record in records.items():
        pooled = record["pooled"]
        method = "selected" if workload == "usr_1" else "current"
        metric = pooled["methods"][method]
        pair, dist = metric["paired"], pooled["overwrite_distribution"]
        lines.append(f"| {workload} / {method} | {pooled['n']:,} | {pooled['overwrite_observed_n']:,} | {metric['all_mae_seconds']:.3f} | {pair['mae_seconds']:.3f} | {dist['mean_seconds']:.3f} | {dist['median_seconds']:.3f} | {pair['fraction_error_lt_overwrite']:.2%} | {pooled['fraction_read_before_overwrite']:.2%} |")
        lines += ["", f"**{workload}:** MAE меньше среднего интервала: {'да' if pair['mae_lt_mean_overwrite'] else 'нет'}; меньше медианного интервала: {'да' if pair['mae_lt_median_overwrite'] else 'нет'}. С учётом неизвестных перезаписей общая доля error < overwrite находится в пределах {metric['fraction_error_lt_overwrite_lower_bound']:.2%}–{metric['fraction_error_lt_overwrite_upper_bound']:.2%}. Нулевых интервалов: {pooled['zero_overwrite_n']:,}.", ""]
    lines += ["## Дневные показатели и все методы", "",
              "| Нагрузка | День | Метод | MAE при известной перезаписи, с | Среднее / медиана перезаписи, с | error < overwrite | MAE только чтений до повторной записи, с |",
              "|---|---:|---|---:|---|---:|---:|"]
    for workload, record in records.items():
        for day, entry in record["days"].items():
            dist = entry["overwrite_distribution"]
            for method, metric in entry["methods"].items():
                pair = metric["paired"]
                read_mae = metric["read_first_mae_seconds"]
                lines.append(f"| {workload} | {day} | {method} | {pair['mae_seconds']:.3f} | {dist['mean_seconds']:.3f} / {dist['median_seconds']:.3f} | {pair['fraction_error_lt_overwrite']:.2%} | {read_mae:.3f} |")
    lines += ["", "## Только записи, прочитанные до следующей Write", "",
              "Это отдельная диагностическая подвыборка, а не улучшение исходной MAE отбором примеров. Здесь отдельно ограничиваем сравнение известной следующей Write.", "",
              "| Нагрузка / метод | Чтений раньше Write, N | Известных перезаписей в этой группе, N | MAE, с | Среднее / медиана до Write, с | error < overwrite |",
              "|---|---:|---:|---:|---|---:|"]
    for workload, record in records.items():
        entry = record["pooled"]
        method = "selected" if workload == "usr_1" else "current"
        pair = entry["methods"][method]["read_first_paired"]
        dist = entry["read_first_overwrite_distribution"]
        lines.append(f"| {workload} / {method} | {entry['read_before_overwrite_n']:,} | {pair['n']:,} | {pair['mae_seconds']:.3f} | {dist['mean_seconds']:.3f} / {dist['median_seconds']:.3f} | {pair['fraction_error_lt_overwrite']:.2%} |")
    lines += ["", "## Ограничения и проверка", "",
              "- Все записи здесь уже имели чтение до конца своего дневного окна; вывод не относится ко всем Write. Доли неизвестных перезаписей относятся к этому же набору.",
              "- Следующая Write может находиться за границей дня; поиск ограничен всем наблюдённым префиксом. Отсутствие Write после Read подтверждает чтение раньше повторной записи в доступной истории, но время до будущей Write остаётся неизвестным.",
              "- Цензурированные интервалы не заменены бесконечностью. Нижняя граница проходящих учитывает только заведомо проходящие случаи; верхняя допускает прохождение всех неизвестных.",
              "- Равные timestamps различаются порядком строк. При нулевом интервале строгий критерий error < overwrite не выполняется даже при нулевой ошибке; отношения error/overwrite для нулей не вычисляются.",
              "- MAE меньше среднего/медианы не гарантирует правильную группировку данных. Не задана ширина групп; корректность группировки и реальные версии блоков здесь не проверялись.",
              "- Сохранены независимые пересчёты метрик, hashes источника/прогнозов/моделей и прямой хронологический аудит следующих Write для 64 примеров каждого дня.", "",
              "```bash", "uv run python -m read_prediction.experiments.overwrite_comparison analyze usr_1",
              "uv run python -m read_prediction.experiments.overwrite_comparison analyze prxy_1",
              "uv run python -m read_prediction.checks.overwrite_comparison --workload usr_1",
              "uv run python -m read_prediction.checks.overwrite_comparison --workload prxy_1",
              "uv run python -m read_prediction.experiments.overwrite_comparison report", "```", ""]
    path = PROJECT_ROOT / "reports/overwrite-comparison.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("analyze", "report"))
    parser.add_argument("workload", nargs="?", choices=("usr_1", "prxy_1"))
    args = parser.parse_args()
    if args.stage == "report":
        report()
    elif args.workload:
        analyze(args.workload)
    else:
        parser.error("analyze requires workload")


if __name__ == "__main__":
    main()
