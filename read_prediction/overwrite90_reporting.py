"""Report the fixed 90% criterion and measured failure regimes."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT


def breakdown(target, prediction, annotation):
    duration = annotation["overwrite_seconds"]
    known = np.isfinite(duration)
    errors = np.abs(target - prediction)
    passes = known & (errors < duration)
    failures = int(np.count_nonzero(known & ~passes))
    groups = {
        "zero": known & (duration == 0),
        "0_to_1ms": known & (duration > 0) & (duration <= .001),
        "1ms_to_1s": known & (duration > .001) & (duration <= 1),
        "1s_to_1min": known & (duration > 1) & (duration <= 60),
        "1min_to_1h": known & (duration > 60) & (duration <= 3600),
        "over_1h": known & (duration > 3600),
        "read_before_overwrite": known & annotation["read_before_overwrite"],
        "overwrite_before_read": known & ~annotation["read_before_overwrite"],
    }
    result = {"n": len(target), "known_failures": failures, "groups": {}}
    for name, mask in groups.items():
        n = int(mask.sum())
        passed = int(np.count_nonzero(passes & mask))
        result["groups"][name] = {
            "n": n, "share_of_all_examples": n / len(target),
            "pass_fraction": passed / n if n else None,
            "mae_seconds": float(errors[mask].mean()) if n else None,
            "failures": n - passed,
            "share_of_known_failures": (n - passed) / failures if failures else None,
        }
    return result


def percentage(value):
    return "—" if value is None else f"{value:.2%}"


def main():
    lines = ["# Эксперимент: не менее 90% ошибок меньше интервала до перезаписи", "",
             "**Критерий:** `abs(prediction - target) < time_to_next_write` минимум для 90% оценённых записей. При неизвестной будущей Write для принятия результата требуется нижняя, а не верхняя граница доли проходящих. Нулевые интервалы входят в знаменатель. Отказов от прогноза нет.", "",
             "Перезапись означает следующую Write с тем же точным начальным Offset. Физическое перекрытие диапазонов и время завершения I/O вместо времени события здесь не моделируются.", "",
             "**Статус данных:** все дни уже просмотрены. День 5 обучает, день 6 выбирает рецепт и число деревьев, после фиксации выбора день 7 даёт повторную диагностику. Это не новый независимый holdout. Числа ниже относятся только к дню 7, не к pooled дням 5–7.", "",
             "## Результат на одинаковых записях дня 7", "",
             "| Нагрузка | Прогноз | N | Нижняя–верхняя граница проходящих | MAE, с | Порог 90% |",
             "|---|---|---:|---|---:|---|"]
    details = []
    for workload in ("usr_1", "prxy_1"):
        folder = PROJECT_ROOT / "results/overwrite90" / workload
        if not (folder / "verification.json").exists():
            raise ValueError(f"Verify {workload} first")
        result = json.loads((folder / "diagnostic.json").read_text())
        selection = json.loads((folder / "selection.json").read_text())
        original = PROJECT_ROOT / "results/mae-improvement" / workload
        with np.load(original / "holdout-day7.predictions.npz") as saved:
            target = saved["target_seconds"]
            previous_selected = saved["selected"]
        with np.load(folder / "day7.predictions.npz") as saved:
            prediction = saved["prediction"]
        with np.load(PROJECT_ROOT / "results/overwrite-comparison" / workload / "day7.comparison.npz") as saved:
            annotation = {key: saved[key] for key in saved.files}
        for label, metric in (("прежняя модель", result["current"]),
                              (f"выбранный рецепт: {result['chosen']}", result["selected"])):
            lines.append(f"| {workload} | {label} | {metric['n']:,} | {metric['pass_lower_bound']:.2%}–{metric['pass_upper_bound']:.2%} | {metric['mae_seconds']:.3f} | {'достигнут' if metric['meets_90_percent'] else 'не достигнут'} |")
        record = breakdown(target, prediction, annotation)
        assert record["known_failures"] == result["selected"]["known_n"] - result["selected"]["known_passes"]
        duration_groups = list(record["groups"].values())[:6]
        assert sum(group["n"] for group in duration_groups) == result["selected"]["known_n"]
        assert sum(group["failures"] for group in duration_groups) == record["known_failures"]
        record["reporter_sha256"] = fingerprint(PROJECT_ROOT / "read_prediction/overwrite90_reporting.py")["sha256"]
        (folder / "error-breakdown.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
        details += [f"### {workload}", "",
                    f"Выбран `{result['chosen']}` из {len(selection['validation'])} рецептов. Новых model fits: {result['new_model_fits']}. Прежний победитель MAE-итерации имел на том же дне MAE {np.abs(target - previous_selected).mean():.3f} с.", "",
                    "| Интервал / диагностическая группа | N | Доля всей оценённой выборки | Проходят внутри группы | Доля подтверждённых нарушений |",
                    "|---|---:|---:|---:|---:|"]
        labels = {"zero": "0 с", "0_to_1ms": "0–1 мс", "1ms_to_1s": "1 мс–1 с",
                  "1s_to_1min": "1 с–1 мин", "1min_to_1h": "1 мин–1 ч", "over_1h": ">1 ч",
                  "read_before_overwrite": "Read до Write, только известные интервалы",
                  "overwrite_before_read": "Write до Read, только известные интервалы"}
        for name, group in record["groups"].items():
            details.append(f"| {labels[name]} | {group['n']:,} | {group['share_of_all_examples']:.2%} | {percentage(group['pass_fraction'])} | {percentage(group['share_of_known_failures'])} |")
        coverage = result["coverage"]
        details += ["", f"Покрытие исходных подходящих Write: {coverage['observed_targets']:,}/{coverage['writes']:,} ({coverage['observed_fraction']:.2%}). Остальные интервалы не завершились Read до конца окна и не имеют точной ошибки. Диагностические группы Read/Write пересекают группы длительности; их строки нельзя складывать.", "",
                    "Все validation-рецепты:", "",
                    "| Рецепт | Нижняя граница проходящих на дне 6 | MAE, с |",
                    "|---|---:|---:|"]
        for name, metric in sorted(selection["validation"].items(), key=lambda item: -item[1]["pass_lower_bound"]):
            details.append(f"| {name} | {metric['pass_lower_bound']:.2%} | {metric['mae_seconds']:.3f} |")
        details.append("")
    lines += ["", "## Что проверялось", "",
              "- Обновляемые задержки по адресу: последняя завершённая, медиана и среднее пяти последних, смеси с прежним прогнозом и фиксированные масштабы.",
              "- Четыре LightGBM-рецепта: raw-L1/log-L1 с равномерными и ограниченными обратными весами интервала до перезаписи. Обучение на свежем дне 5, затем refit выбранной модели на днях 5–6.",
              "- Ни история, ни обучающие веса не используют события после соответствующего момента доступности. Validation перезаписи после конца дня 6 считает неизвестными.",
              "- Выбор направлен на долю проходящих, а не минимум MAE; tie-break — MAE, затем имя.", "",
              "## Разбор подтверждённых нарушений", "", *details,
              "## Вывод и следующий шаг", "",
              "Порог 90% не достигнут. Его нельзя объявить выполненным по среднему времени жизни или по отобранной постфактум подгруппе. Следующий эксперимент должен учитывать судьбу конкретной записи: Read раньше повторной Write, Write раньше Read, либо незавершённое наблюдение. Для группировки версий данных также нужна согласованная блочная гранулярность. Если допускается отказ от прогноза, требуется отдельно фиксировать минимальное покрытие и проверять решение только по доступным в момент Write признакам.", "",
              "Перенос результата должен проверяться на новых данных: повторный подбор на днях 5–7 не создаёт независимый holdout.", "",
              "## Проверка и воспроизведение", "",
              "Независимо пересчитаны 15 validation-рецептов каждой нагрузки, все ошибки дня 7 и 64 причинных прогноза каждой нагрузки из предыдущих завершённых пар. Сверены hashes входов, моделей, кода и frozen selection. Протокол: `docs/protocols/overwrite90-protocol.md`.", "",
              "```bash", "uv run python -m read_prediction.experiments.overwrite90 usr_1",
              "uv run python -m read_prediction.experiments.overwrite90 prxy_1",
              "uv run python -m read_prediction.checks.overwrite90 usr_1",
              "uv run python -m read_prediction.checks.overwrite90 prxy_1",
              "uv run python -m read_prediction.overwrite90_reporting", "```", "",
              "Эксперимент отказывается перезаписывать существующие папки. Генератор отчёта читает готовые результаты и не обучает модели.", ""]
    path = PROJECT_ROOT / "reports/overwrite90.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
