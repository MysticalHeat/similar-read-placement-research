"""Render the range-refit diagnostic report."""

import json

from read_prediction.paths import PROJECT_ROOT


def pct(value):
    return f"{value:.2%}"


def load(workload):
    folder = PROJECT_ROOT / "results/range-refit" / workload
    if not (folder / "verification.json").exists():
        raise ValueError(f"Verify range-refit/{workload} first")
    return json.loads((folder / "diagnostic.json").read_text())


def main():
    records = {workload: load(workload) for workload in ("usr_1", "prxy_1")}
    lines = [
        "# Переобучение gate и времени на диапазонных метках",
        "",
        "После исправления разметки по диапазонам байтов gate и модели времени были заново обучены на днях 5–6 и заморожены до повторной диагностики дня 7. Использованы прежние 17 причинных признаков и те же caps, рецепты, пороги и правила выбора, что в all-write. Признаки не пересчитывались. Все дни уже просмотрены: независимого holdout нет.",
        "",
        "## Результат выборочного режима дня 7",
        "",
        "Coverage — доля всех Write, попавших в выбранную группу. Обе нижние доли учитывают цензурированные selected-записи консервативно. MAE считается только на selected с наблюдаемым Read.",
        "",
        "| Нагрузка | Выбрано / все Write | Coverage | Read-first, нижняя граница | Подтверждённая доля error < overwrite | MAE наблюдаемых selected, с | Выбор проходит 90% режим |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for workload in ("usr_1", "prxy_1"):
        result = records[workload]
        metric = result["all_write_selective"]
        lines.append(
            f"| {workload} | {metric['selected_n']:,}/{metric['all_writes']:,} | {pct(metric['coverage'])} | "
            f"{pct(metric['read_first_lower'])} | {pct(metric['confirmed_error_lt_overwrite_lower'])} | "
            f"{metric['observed_selected_mae_seconds']:.3f} | {'да' if metric['qualifies'] else 'нет'} |"
        )
    lines += [
        "",
        "Выбор: `usr_1` — `gate_31/current/0.6`; `prxy_1` — `gate_63/current/0.5`. В обоих случаях для времени выбран прежний `current`; новые raw-L1/log-L1 диапазонные регрессоры в замороженный рецепт не попали.",
        "",
        "## Доли исходов на всех Write дня 7",
        "",
        "| Нагрузка | Все Write | Read-first | Write-first | Цензурированные |",
        "|---|---:|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        out = records[workload]["outcomes"]
        n = out["all_writes"]
        lines.append(
            f"| {workload} | {n:,} | {out['read_first']:,} ({out['read_first']/n:.2%}) | "
            f"{out['write_first']:,} ({out['write_first']/n:.2%}) | "
            f"{out['censored']:,} ({out['censored']/n:.2%}) |"
        )
    lines += [
        "",
        "## Сопоставление знаменателей и прежнего критерия",
        "",
        "Не смешивать три разных результата: selected-режим (только выбранная подгруппа), range-набор (все Write с наблюдаемым пересекающим Read) и прежний same-start набор. Текущий routed-прогноз совпадает с `current`, поскольку в обоих замороженных рецептах выбран `current` для времени.",
        "",
        "| Нагрузка | Метрика / набор | N | Подтверждённая доля | MAE, с |",
        "|---|---|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        result = records[workload]
        selected = result["all_write_selective"]
        old = result["original_observed_routed"]
        ranged = result["range_observed_routed"]
        lines.extend([
            f"| {workload} | selected, диапазонные targets | {selected['selected_n']:,} (из {selected['all_writes']:,}) | {pct(selected['confirmed_error_lt_overwrite_lower'])} | {selected['observed_selected_mae_seconds']:.3f} |",
            f"| {workload} | прежний same-start наблюдаемый набор | {old['n']:,} | {pct(old['pass_lower_bound'])} | {old['mae_seconds']:.3f} |",
            f"| {workload} | range-набор: все наблюдаемые пересекающие Read | {ranged['n']:,} | {pct(ranged['pass_lower_bound'])} | {ranged['mae_seconds']:.3f} |",
        ])
    lines += [
        "",
        "## Нулевой прогноз и польза временной модели на selected",
        "",
        "| Нагрузка | Selected N | Наблюдаемый selected N | Нулевой прогноз: подтверждённая доля / MAE, с | Выбранный current: подтверждённая доля / MAE, с |",
        "|---|---:|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        result = records[workload]
        zero = result["zero_on_selected"]
        selected = result["all_write_selective"]
        lines.append(
            f"| {workload} | {zero['selected_n']:,} | {zero['observed_selected_n']:,} | "
            f"{pct(zero['zero_pass_lower'])} / {zero['zero_mae_seconds']:.3f} | "
            f"{pct(selected['confirmed_error_lt_overwrite_lower'])} / {selected['observed_selected_mae_seconds']:.3f} |"
        )
    lines += [
        "",
        "## Выводы",
        "",
        "- **usr_1:** новый range-gate выбрал 34.10% всех Write, против 8.33% у прежнего window-gate; подтверждённая доля выросла с 46.96% до 54.44%. Но на validation ни один рецепт не прошёл выборочный порог 90%, а на дне 7 новый режим также дал лишь 54.44%. Время осталось `current`; на прежнем same-start наборе результат поэтому остался 47.49%. Нулевой прогноз на selected даёт 53.88% и MAE 13 470 с против 54.44% и 12 724 с у current: выигрыш по критерию небольшой.",
        "- **prxy_1:** выборочный режим прошёл условия 90%: покрытие 23.99%, нижняя Read-first 96.32%, подтверждённая доля error<overwrite 95.84%. Это сильный выборочный результат, но не общий результат: на всех 8 458 026 Write Write-first остаётся 75.76%, а на прежнем same-start наборе routed-доля осталась 68.80%. По сравнению с прежним window-gate coverage выросло с 23.12% до 23.99%, но нижняя подтверждённая доля снизилась с 99.41% до 95.84%; семантика targets и gate изменилась, так что это диагностическое сопоставление, не строго идентичное сравнение.",
        "- На prxy_1 current сильно выигрывает у нулевого прогноза по MAE selected (6.14 с против 58.07 с), хотя доля error<overwrite чуть ниже (95.84% против 96.32%). Значит критерий пользователя не заменяет метрику качества времени.",
        "- **90% на всей выборке не достигнуты** ни для одной нагрузки. На prxy_1 достигнут только режим на отобранной подгруппе; эти результаты нельзя выдавать за общие 90%.",
        "",
        "## Проверка и воспроизведение",
        "",
        "Checker для каждой нагрузки подтвердил hashes моделей/входов/кода, точное совпадение day-7 меток с `range-label`, совпадение независимой медленной разметки на 32 случайных Write дней 5–6 (RNG42), replay выбора и пересчёт критериев. Checker не обучает модели.",
        "",
        "```bash",
        "uv run python -m read_prediction.experiments.range_refit usr_1",
        "uv run python -m read_prediction.experiments.range_refit prxy_1",
        "uv run python -m read_prediction.checks.range_refit usr_1",
        "uv run python -m read_prediction.checks.range_refit prxy_1",
        "uv run python -m read_prediction.range_refit_reporting",
        "```",
        "",
        "Протокол: `docs/protocols/range-refit-protocol.md`. Все числа — повторная диагностика просмотренного дня 7, не независимая оценка.",
        "",
    ]
    path = PROJECT_ROOT / "reports/range-refit.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
