"""Select saved predictions by validation MAE and compare with mean overwrite."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.experiments.long_history import CANDIDATES, METHODS
from read_prediction.experiments.mixture import WEIGHTS
from read_prediction.experiments.prxy0_check import dump
from read_prediction.overwrite_reporting import lifetime_bounds
from read_prediction.paths import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "results/mean-overwrite"
WINDOWS = ("validation", "day5", "day6", "day7")


def mean_comparison(mae, mean):
    return {"mae_seconds": mae, "mean_overwrite_seconds": mean,
            "ratio": mae / mean if mean > 0 else None,
            "margin_seconds": mean - mae, "passed": mae < mean}


def summarize(data, methods):
    seen = data["read"] >= 0
    known = np.isfinite(data["lifetime"][seen])
    target = data["target"][seen]
    lifetime, remaining = data["lifetime"][seen], data["remaining"][seen]
    bounds = lifetime_bounds(lifetime, remaining)
    result = {"all_writes": len(seen), "observed_reads": int(seen.sum()),
              "paired_n": int(known.sum()), "censored_n": int((~known).sum()),
              "coverage": float(seen.mean()), "bounds": bounds, "methods": {}}
    for method in methods:
        error = np.abs(target - data[method][seen])
        mae = float(error.mean())
        lower = bounds["mean_lower_bound_seconds"]
        if mae < lower:
            status = "passed"
        elif known.all():
            status = "failed"
        else:
            status = "undetermined"
        result["methods"][method] = {
            "paired": mean_comparison(float(error[known].mean()), float(lifetime[known].mean())) if known.any() else None,
            "observed_read": {"mae_seconds": mae, "mean_overwrite_lower_seconds": lower,
                              "ratio_upper_bound": mae / lower if lower > 0 else None,
                              "margin_lower_seconds": lower - mae, "status": status}}
    return result


def load_window(workload, rule, window):
    folder = PROJECT_ROOT / "results/long-history" / workload
    with np.load(folder / f"{rule}.{window}.npz") as saved:
        data = {key: saved[key].copy() for key in ("write_rows", "read", "overwrite", "target", "lifetime", "remaining", *METHODS)}
    if workload == "prn_1":
        with np.load(PROJECT_ROOT / f"results/mixture/prn_1/{rule}.{window}.npz") as saved:
            for key in data:
                if key in saved:
                    np.testing.assert_array_equal(data[key], saved[key])
            data.update({method: saved[method].copy() for method in WEIGHTS})
    return data


def report(records):
    lines = ["# MAE относительно среднего времени до перезаписи", "",
             "Выбор по минимальной MAE на всех observed-Read записях validation дня 4, без ограничения pass count. Нового обучения нет. Дни 5–7 — development, не новый holdout.", "",
             "## Дни 5–7: одинаковые записи с известными Read и overwrite", "",
             "R = MAE / среднее overwrite; успех строго R < 1. Запас = среднее overwrite − MAE. ★ — выбор по validation, остальные методы — сравнение.", "",
             "| Нагрузка / правило | Метод | N paired | MAE, с | Среднее overwrite, с | R | Запас, с | Успех |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    for workload, rules in records.items():
        for rule, record in rules.items():
            for method, metric in record["windows"]["pooled"]["methods"].items():
                paired = metric["paired"]
                if paired is None:
                    continue
                ratio = f"{paired['ratio']:.4f}" if paired["ratio"] is not None else "—"
                marker = " ★" if method == record["selected"] else ""
                lines.append(f"| {workload} / {rule} | {method}{marker} | {record['windows']['pooled']['paired_n']:,} | {paired['mae_seconds']:.2f} | {paired['mean_overwrite_seconds']:.2f} | {ratio} | {paired['margin_seconds']:.2f} | {'да' if paired['passed'] else 'нет'} |")
    lines += ["", "## Выбранные модели: все записи с наблюдаемым Read", "",
              "Неизвестные overwrite не исключены. Remaining — только нижняя граница интервала. «Доказано» означает MAE ниже даже нижней границы среднего; «не определено» не означает неуспех.", "",
              "| Нагрузка / правило | Окно | Метод | N Read / все Write | Неизвестных overwrite | MAE, с | Среднее overwrite ≥, с | Статус |",
              "|---|---|---|---:|---:|---:|---:|---|"]
    statuses = {"passed": "доказано", "failed": "не выполнено", "undetermined": "не определено"}
    for workload, rules in records.items():
        for rule, record in rules.items():
            method = record["selected"]
            for window, values in record["windows"].items():
                metric = values["methods"][method]["observed_read"]
                lines.append(f"| {workload} / {rule} | {window} | {method} | {values['observed_reads']:,} / {values['all_writes']:,} | {values['censored_n']:,} | {metric['mae_seconds']:.2f} | {metric['mean_overwrite_lower_seconds']:.2f} | {statuses[metric['status']]} |")
    lines += ["", "Среднее чувствительно к длинным интервалам. Условие на средние не означает малую ошибку у большинства записей. Для Write без наблюдаемого Read MAE здесь не определена.", "",
              "Все методы, дневные и validation показатели, отношения и запасы сохранены в `results/mean-overwrite/metrics.json`; выбор — `frozen.json`. Протокол: `docs/protocols/mean-overwrite-protocol.md`.", "",
              "```bash", ".venv/bin/python -m read_prediction.experiments.mean_overwrite",
              ".venv/bin/python -m read_prediction.checks.mean_overwrite", "```", ""]
    (PROJECT_ROOT / "reports/mean-overwrite.ru.md").write_text("\n".join(lines))


def main():
    paths = [PROJECT_ROOT / "read_prediction/experiments/mean_overwrite.py",
             PROJECT_ROOT / "read_prediction/overwrite_reporting.py",
             PROJECT_ROOT / "docs/protocols/mean-overwrite-protocol.md"]
    for relative in ("long-history/proj_1", "long-history/prn_1", "mixture/prn_1"):
        parent = PROJECT_ROOT / "results" / relative
        verification = json.loads((parent / "verification.json").read_text())
        assert verification["passed"] and verification["metrics_fingerprint"] == fingerprint(parent / "metrics.json")
        provenance = json.loads((parent / "provenance.json").read_text())
        for path, expected in provenance["hashes"].items():
            assert fingerprint(PROJECT_ROOT / path) == expected, path
        paths.extend([parent / "provenance.json", parent / "verification.json"])
        paths.extend(parent / f"{rule}.{window}.npz" for rule in ("same_start", "range") for window in WINDOWS)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    records, frozen = {}, {}
    for workload in ("proj_1", "prn_1"):
        records[workload], frozen[workload] = {}, {}
        methods = (*METHODS, *WEIGHTS) if workload == "prn_1" else METHODS
        candidates = (*CANDIDATES, *WEIGHTS) if workload == "prn_1" else CANDIDATES
        for rule in ("same_start", "range"):
            data = load_window(workload, rule, "validation")
            validation = summarize(data, methods)
            selected = min(candidates, key=lambda name: (validation["methods"][name]["observed_read"]["mae_seconds"], name))
            frozen[workload][rule] = {"selected": selected, "candidates": candidates,
                                      "selection_metric": "validation observed_read MAE"}
            windows = {"validation": validation}
            parts = []
            for window in WINDOWS[1:]:
                saved = load_window(workload, rule, window)
                windows[window] = summarize(saved, methods)
                parts.append(saved)
            windows["pooled"] = summarize({key: np.concatenate([part[key] for part in parts]) for key in parts[0]}, methods)
            records[workload][rule] = {"selected": selected, "windows": windows}
            print(workload, rule, selected, windows["pooled"]["methods"][selected], flush=True)
    dump(OUTPUT / "frozen.json", frozen)
    dump(OUTPUT / "metrics.json", records)
    report(records)
    paths.extend([OUTPUT / "frozen.json", OUTPUT / "metrics.json", PROJECT_ROOT / "reports/mean-overwrite.ru.md"])
    dump(OUTPUT / "provenance.json", {"hashes": {str(path.relative_to(PROJECT_ROOT)): fingerprint(path) for path in paths}})


if __name__ == "__main__":
    main()
