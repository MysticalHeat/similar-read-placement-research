"""Compare full-Write selectors, finite-window outcomes and unchanged timing."""

import json

import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT


def pct(value):
    return "—" if value is None else f"{value:.2%}"


def main():
    lines = ["# Все Write и вероятность Read-first до заданного окна", "",
             "Два диагностических этапа: cause-gate на разрешённых исходах и дополнительный трёхклассовый gate на полных обучающих окнах. Все дни уже просмотрены: независимого holdout нет. Обучение день 5, выбор день 6, замороженная повторная диагностика день 7.", "",
             "Новые признаки строятся из **всего** прошлого I/O, включая Write без наблюдённого Read: pending Write после последнего Read, интервалы между Write, предыдущий size, глобальная интенсивность за завершённые 1/60 секунд, расстояние до предыдущей Write. Признаки не зависят от будущего попадания записи в завершённый набор.", "",
             "## Результаты на всех Write дня 7", "",
             "Все selected, включая цензурированные и не имеющие наблюдённого Read, входят в знаменатель. В таблице нижние, а не оптимистические границы. Coverage — число операций, не уникальные физические данные.", "",
             "| Нагрузка | Этап | Выбрано / все Write | Coverage | Подтверждённые Read-first | Подтверждённая ошибка < overwrite | MAE selected с наблюдённым Read, с | Проходит диагностическое условие |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    records = {}
    extras = []
    for workload in ("usr_1", "prxy_1"):
        for study, label in (("all-write", "cause-gate"), ("window-outcome", "исход до окна")):
            folder = PROJECT_ROOT / "results" / study / workload
            if not (folder / "verification.json").exists():
                raise ValueError(f"Verify {study}/{workload} first")
            result = json.loads((folder / "diagnostic.json").read_text())
            records[study, workload] = result
            metric = result["all_write_selective"]
            mae = metric["observed_selected_mae_seconds"]
            lines.append(f"| {workload} | {label} | {metric['selected_n']:,}/{metric['all_writes']:,} | {pct(metric['coverage'])} | {pct(metric['read_first_lower'])} | {pct(metric['confirmed_error_lt_overwrite_lower'])} | {mae:.3f} | {'да' if metric['qualifies'] else 'нет'} |")
    lines += ["", "Диагностическое условие: обе нижние доли >=90%, coverage >=10% всех Write. Это не заменяет первоначальную цель 90% на всём прежнем оцениваемом наборе.", "",
              "## Состав исходов дня 7", "",
              "| Нагрузка | Все Write | Read-first | Write-first | Первый исход не наблюдался | Есть Read до конца окна |",
              "|---|---:|---:|---:|---:|---:|"]
    for workload in ("usr_1", "prxy_1"):
        outcome = records["all-write", workload]["outcomes"]
        n = outcome["all_writes"]
        lines.append(f"| {workload} | {n:,} | {outcome['read_first']:,} ({outcome['read_first']/n:.2%}) | {outcome['write_first']:,} ({outcome['write_first']/n:.2%}) | {outcome['censored']:,} ({outcome['censored']/n:.2%}) | {outcome['observed_reads']:,} ({outcome['observed_reads']/n:.2%}) |")
        parent = PROJECT_ROOT / "results/all-write" / workload
        source = json.loads((parent / "source.json").read_text())
        parent_selection = json.loads((parent / "selection.json").read_text())
        meta = np.load(parent / "meta.npy", mmap_mode="r")
        cut = {int(k): v for k, v in parent_selection["cutoffs"].items()}
        begin, end = np.searchsorted(meta["write"], cut[6]), np.searchsorted(meta["write"], cut[7])
        test = meta[begin:end]
        window = PROJECT_ROOT / "results/window-outcome" / workload
        selection = json.loads((window / "selection.json").read_text())
        with np.load(window / "day7.predictions.npz") as saved:
            mask = saved["probability"] >= float(selection["chosen"].split("/")[-1])
        metric = records["window-outcome", workload]["all_write_selective"]
        assert int(mask.sum()) == metric["selected_n"]
        positive = int(round(metric["read_first_lower"]*metric["selected_n"]))
        recall = positive/outcome["read_first"]
        events = np.memmap(parent / "events.bin", mode="r", dtype=EVENT_DTYPE, shape=(source["loaded_events"],))
        sizes = events["size"][test["write"]]
        byte_coverage = float(sizes[mask].sum()/sizes.sum())
        observed = (test["read"] >= 0) & (test["read"] < cut[7])
        known_write = (test["overwrite"] >= 0) & (test["overwrite"] < cut[7])
        observation_end = min(source["last_timestamp"], source["first_timestamp"]+168*3600*10_000_000)
        budget = np.where(known_write, test["lifetime"], (observation_end-test["timestamp"])/10_000_000)
        observed_selected = mask & observed
        zero_mae = float(test["target"][observed_selected].mean()) if observed_selected.any() else None
        zero_lower = int(np.count_nonzero(observed_selected & (test["target"] < budget))) / int(mask.sum()) if mask.any() else None
        detail = {"workload": workload, "known_read_first_selected": positive, "known_read_first_recall": recall,
                  "selected_write_request_bytes_fraction": byte_coverage, "zero_prediction_observed_mae_seconds": zero_mae,
                  "zero_prediction_certified_pass_lower": zero_lower}
        (window / "report-metrics.json").write_text(json.dumps(detail, indent=2)+"\n")
        extras += [f"### {workload}: трёхклассовый gate", "",
                   f"Распознано {positive:,}/{outcome['read_first']:,} известных Read-first ({recall:.2%}). Coverage по сумме размеров Write-запросов {byte_coverage:.2%}; повторные записи считаются повторно, это не объём уникальных данных.", "",
                   f"Выбран `{selection['chosen']}`. Цензурированных selected: {metric['selected_censored']:,}/{metric['selected_n']:,}. Нижняя–верхняя границы Read-first: {pct(metric['read_first_lower'])}–{pct(metric['read_first_upper'])}.", "",
                   f"Диагностический нулевой прогноз на том же selected наборе: подтверждённо проходит {pct(zero_lower)}, MAE наблюдаемых Read {zero_mae:.3f} с. Это не новый выбор рецепта и не улучшение модели.", ""]
        del events, sizes
    lines += ["", "## Исходный критерий: все прежние наблюдённые Read", "",
              "| Нагрузка | Прежний current | Routed cause-gate | Routed window-gate | Общие 90% |",
              "|---|---:|---:|---:|---|"]
    for workload in ("usr_1", "prxy_1"):
        base = records["all-write", workload]
        window = records["window-outcome", workload]
        lines.append(f"| {workload} | {pct(base['original_observed_current']['pass_lower_bound'])} | {pct(base['original_observed_routed']['pass_lower_bound'])} | {pct(window['original_observed_routed']['pass_lower_bound'])} | {'да' if window['original_observed_routed']['meets_90_percent'] else 'нет'} |")
    lines += ["", "Во всех новых комбинациях для времени выбран current, поэтому исходный routed-прогноз не изменился. Старый отдельный overwrite90-кандидат usr_1 имел на том же дне 50.18%; эти gates не являются его улучшенной заменой.", "",
              "## Интерпретация", "", *extras,
              "На prxy_1 полный ввод Write и признаки серий позволили охватить почти все известные Read-first, а finite-window head уменьшил число неопределённых selected. Старый read-first этап отбирал 716,912 из 4,548,153 завершённых примеров (15.76% условного набора); его процент нельзя напрямую сравнивать с новым процентом всех 8,458,026 Write. Новый count selected — 1,955,499, около 2.73 раза прежнего.", "",
              "На usr_1 finite-window head уменьшил долю неопределённых selected, но точности и покрытия недостаточно. Нижняя доля подтверждённых проходящих не равна доле истинных ошибок: для ненаблюдаемых Read точной ошибки нет.", "",
              "Важно: в Read-first группе нулевой прогноз почти автоматически удовлетворяет error<overwrite, потому что само чтение раньше перезаписи. Поэтому высокое значение этого критерия само по себе не доказывает полезный прогноз времени или хорошую группировку. Нулевая baseline-диагностика выше помогает отделить точность отбора от точности времени. Нужны также MAE/P90 и качество временных групп.", "",
              "## Ограничения и следующий шаг", "",
              "- Полная выборка all-write включает незавершённые Write и хранит unknown отдельным состоянием. Binary cause-gate обучается только на разрешённых исходах и не моделирует вероятность наступления события до границы.",
              "- Дополнительный gate моделирует события до планового конца собственного 24h-окна рождения. В полных обучающих окнах класс 2 означает отсутствие первого события до этой границы, а не отсутствие Read навсегда. На частичном дне 7 отсутствующие события остаются цензурированными для оценки.",
              "- Planned deadline доступен в момент Write; будущий EOF не используется в признаках. При refit сохраняется deadline своего дня, а не общий новый конец дня 6.",
              "- Все дни использованы ранее; результаты требуют новой независимой проверки. Нет оценки SSD throughput, физического wear или эффективности размещения.",
              "- Перезапись и чтение пока определены по одинаковому начальному Offset и времени события. Перед выводами о записанных версиях нужна согласованная блочная гранулярность и разметка пересечений диапазонов/порядка завершения I/O.",
              "- Дальнейшая работа для usr_1: модели конкурирующих событий/времени с цензурированием и проверка на более длинной истории. Для общей цели 90% надо отдельно оценивать случаи Write-first, где последующий Read адреса не является гарантированным чтением исходной версии.", "",
              "## Проверка и воспроизведение", "",
              "У каждой нагрузки проверены 42 cause-gate и 42 finite-window validation-комбинации; все Write дня 7 входят в метрики. Raw-признаки и next events восстановлены независимой reference-функцией из источника для 64 Write, отдельный replay frozen моделей — 64 точки. Старый наблюдаемый набор полностью совпадает по Write/Read индексам, target и current. Fingerprints данных, кода и моделей сверены; checker не обучает модели.", "",
              "```bash", "uv run python -m read_prediction.experiments.all_write usr_1",
              "uv run python -m read_prediction.experiments.all_write prxy_1",
              "uv run python -m read_prediction.checks.all_write usr_1",
              "uv run python -m read_prediction.checks.all_write prxy_1",
              "uv run python -m read_prediction.experiments.window_outcome usr_1",
              "uv run python -m read_prediction.experiments.window_outcome prxy_1",
              "uv run python -m read_prediction.checks.window_outcome usr_1",
              "uv run python -m read_prediction.checks.window_outcome prxy_1",
              "uv run python -m read_prediction.all_write_reporting", "```", "",
              "Эксперименты отказываются перезаписывать готовые папки. Протоколы: `docs/protocols/all-write-protocol.md`, `docs/protocols/window-outcome-protocol.md`.", ""]
    path = PROJECT_ROOT / "reports/all-write.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
