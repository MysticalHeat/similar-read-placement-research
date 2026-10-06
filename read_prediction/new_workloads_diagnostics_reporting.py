"""Render verified budget/transfer diagnostics without fitting models."""

import json

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT

LABELS = {
    "zero": "0", "0_to_1ms": "(0,1 ms)", "1_to_10ms": "1–10 ms",
    "10_to_100ms": "10–100 ms", "100ms_to_1s": "100 ms–1 s", "1_to_10s": "1–10 s",
    "10s_to_1min": "10 s–1 min", "1_to_10min": "1–10 min", "10min_to_1h": "10 min–1 h",
    "at_least_1h": ">=1 h", "unknown": "неизвестен",
    "training_labelled": "есть завершённый training label",
    "training_seen_unlabelled": "адрес был в train, но label не завершился",
    "training_unseen": "адрес отсутствовал в train events",
    "up_to_512B": "<=512 B", "512B_to_4KiB": "512 B–4 KiB", "4_to_16KiB": "4–16 KiB",
    "16_to_64KiB": "16–64 KiB", "over_64KiB": ">64 KiB", "read_smaller": "Read меньше Write",
    "equal": "размеры равны", "read_larger": "Read больше Write",
    "under_1s": "<1 s", "1s_to_1min": "1 s–1 min", "1_to_6h": "1–6 h",
    "at_least_6h": ">=6 h", "none": "нет prior Read", "1_to_4": "1–4 prior Read",
    "at_least_5": ">=5 prior Read",
}


def pct(value):
    return f"{100 * value:.2f}%"


def number(value):
    return f"{value:,.2f}"


def main():
    for name in ("new-workloads-diagnostics", "new-workloads-horizon"):
        verification = json.loads((PROJECT_ROOT / "results" / name / "verification.json").read_text())
        assert verification["passed"]
        for path, expected in verification["hashes"].items():
            assert fingerprint(PROJECT_ROOT / path) == expected, path
    lines = [
        "# proj_1/prn_1: где теряем точность и почему проигрываем медиане", "",
        "Диагностика сохранённых frozen прогнозов, без переобучения и без изменения выбора. "
        "Validation первого дня и дни 2–7 уже просмотрены: это development анализ.", "",
        "## Основные выводы", "",
        "1. Нулевой budget не объясняет провал: в proj_1 его нет, в prn_1 — около 0,54–0,56% "
        "наблюдаемого future набора. Математический ceiling от нулей около 99,44–100%, не 50–60%. "
        "Это верхний предел, не обещание достижимости 90%.",
        "2. Критерий проваливается и при ненулевых budgets: у proj_1 проходы при 10 min–1 h "
        "только 5,86–8,64%; даже при >=1 h — около 76,5%. У prn_1 при >=1 h — 68,2–69,4%.",
        "3. Главный источник MAE — долгие ожидания >=6 h и их занижение. Они дают "
        "73,92%/71,99% суммарной ошибки proj_1 и 86,32%/85,42% prn_1 (same-start/range). "
        "На этом срезе адресная медиана значительно точнее модели; на коротких интервалах модель часто лучше.",
        "4. Совсем новые адреса не главный источник проигрыша: их доля 1,77–2,00% proj_1 "
        "и 7,20–8,35% prn_1. На prn_1 модель на новых адресах даже лучше fallback медианы. "
        "Большая часть проигрыша возникает на адресах с training labels.",
        "5. Разная длина окон сильно влияет на observed-набор. Validation — 4,8 h, train — "
        "14,4 h, future — 24 h. При одинаковых 4,8 h future MAE модели становится 3,79–4,42 тыс. с "
        "на proj_1 и 1,59–1,71 тыс. с на prn_1; на этом коротком срезе модель лучше адресной медианы. "
        "Этот срез сохраняет только 37–44% исходных observed labels и не заменяет основную оценку.",
        "6. Нулевой прогноз проходит основной критерий чаще модели (proj_1 69,16%/65,45%; "
        "prn_1 62,36%/58,27%), хотя хуже по MAE. Для Read-first target < overwrite, поэтому "
        "ноль естественно проходит. Один pass-rate не измеряет качество прогноза времени.", "",
        "**Интерпретация:** текущая модель плохо переносится на длинные observed интервалы; "
        "короткий validation не может проверить качество на >=4,8 h targets. "
        "Связь с log-L2, длительностью train, режимами нагрузки — гипотезы для отдельного "
        "эксперимента, не установленные причинные эффекты. Все labels цензурируются границей окна.", "",
        "## Как читать таблицы", "",
        "Основной знаменатель — Write с наблюдаемым Read внутри своего исходного дня; "
        "same-start/range отдельно. Все методы сравниваются на идентичных строках. "
        "Pass — lower bound строгого error < overwrite; неизвестные перезаписи отдельно. "
        "Error share — доля группы в сумме абсолютных ошибок модели. ΔMAE — вклад группы "
        "в общую разницу MAE(model) − MAE(median), в секундах; положительный — проигрыш.", "",
    ]
    for workload in ("proj_1", "prn_1"):
        diagnosis = json.loads((PROJECT_ROOT / "results/new-workloads-diagnostics" / f"{workload}.json").read_text())
        control = json.loads((PROJECT_ROOT / "results/new-workloads-horizon" / f"{workload}.json").read_text())
        for rule, result in diagnosis["rules"].items():
            lines.extend([f"## {workload} / {rule}", "", "### Распределение target и прогноза", "",
                          "| Набор | N | Target mean, s | Target median, s | Target P90, s | Model median, s |",
                          "|---|---:|---:|---:|---:|---:|"])
            train = result["train_target_distribution"]
            lines.append(f"| train | {train['n']:,} | {number(train['mean_seconds'])} | {number(train['q50'])} | {number(train['q90'])} | — |")
            for name, window in result["windows"].items():
                target = window["target_distribution"]
                lines.append(f"| {name} | {target['n']:,} | {number(target['mean_seconds'])} | {number(target['q50'])} | {number(target['q90'])} | {number(window['model_prediction_distribution']['q50'])} |")
            future = result["windows"]["future"]
            lines.extend(["", "### Направление ошибок future", "",
                          "| Метод | MAE, s | Pass lower–upper | Занижений | Завышений | Bias, s | Вклад занижений в MAE, s |",
                          "|---|---:|---:|---:|---:|---:|---:|"])
            for method, metrics in future["overall"].items():
                lines.append(f"| {method} | {number(metrics['mae_seconds'])} | {pct(metrics['pass_lower'])}–{pct(metrics['pass_upper'])} | {pct(metrics['under_share'])} | {pct(metrics['over_share'])} | {number(metrics['bias_seconds'])} | {number(metrics['under_mae_contribution_seconds'])} |")
            lines.extend(["", f"Ceiling только от нулевых budgets: **{pct(future['zero_budget_ceiling'])}**.", ""])
            for family, title in (("budgets", "Время до перезаписи"), ("addresses", "Адреса относительно train"),
                                  ("write_sizes", "Размер Write"), ("read_write_size", "Размер matched Read относительно Write"),
                                  ("target_intervals", "Длительность до Read"), ("prior_read_history", "История same-start Read")):
                lines.extend([f"### {title}", "", "| Группа | N / share | MAE model / median, s | Pass model / median | Error share | ΔMAE, s |",
                              "|---|---:|---:|---:|---:|---:|"])
                for name, group in future[family].items():
                    if not group["n"]:
                        lines.append(f"| {LABELS.get(name, name)} | 0 | — | — | — | — |")
                        continue
                    model, median = group["methods"]["model"], group["methods"]["address_median"]
                    contribution = (model["absolute_error_sum_seconds"] - median["absolute_error_sum_seconds"]) / future["n"]
                    error_share = model["absolute_error_sum_seconds"] / future["overall"]["model"]["absolute_error_sum_seconds"]
                    lines.append(f"| {LABELS.get(name, name)} | {group['n']:,} / {pct(group['share'])} | {number(model['mae_seconds'])} / {number(median['mae_seconds'])} | {pct(model['pass_lower'])} / {pct(median['pass_lower'])} | {pct(error_share)} | {contribution:+.2f} |")
                lines.append("")
            lines.extend(["### Контроль одинаковой длины окна: 4,8 h", "",
                          "| Набор | N | Target mean, s | Target median, s | Target P90, s |",
                          "|---|---:|---:|---:|---:|"])
            for name in ("train", "validation", "future"):
                target = control[rule][f"{name}_target_distribution_4_8h"]
                lines.append(f"| {name} | {target['n']:,} | {number(target['mean_seconds'])} | {number(target['q50'])} | {number(target['q90'])} |")
            lines.extend(["", f"Сохранено **{pct(control[rule]['retained_observed_fraction'])}** исходных future observed строк.", "",
                          "| Метод | Future MAE, s | Pass lower–upper | Занижений | Bias, s |",
                          "|---|---:|---:|---:|---:|"])
            for method, metric in control[rule]["future_metrics_4_8h"].items():
                lines.append(f"| {method} | {number(metric['mae_seconds'])} | {pct(metric['pass_lower'])}–{pct(metric['pass_upper'])} | {pct(metric['under_share'])} | {number(metric['bias_seconds'])} |")
            lines.extend(["", "Горизонт сокращён и состав строк изменён: не считать это улучшением основной модели.", "",
                          "### По будущим дням", "", "| День | N | Target median / P90, s | MAE model / median, s | Занижений модели |",
                          "|---|---:|---:|---:|---:|"])
            for day, group in future["days"].items():
                target = group["target_distribution"]
                model, median = group["methods"]["model"], group["methods"]["address_median"]
                lines.append(f"| {day} | {group['n']:,} | {number(target['q50'])} / {number(target['q90'])} | {number(model['mae_seconds'])} / {number(median['mae_seconds'])} | {pct(model['under_share'])} |")
            lines.append("")
    lines.extend(["## Проверки и воспроизведение", "",
                  "Все slice partitions восстановили N, pass counts и сумму абсолютных ошибок validation/pooled. "
                  "Over/under вклады восстанавливают MAE и bias. Входные frozen/provenance hashes проверены. "
                  "86 unit-тестов прошли; тесты покрывают budget boundaries, strict inequality, unknown budgets, signed error и границы одинакового горизонта.", "",
                  "Протоколы: `docs/protocols/new-workloads-diagnostics-protocol.md`, `docs/protocols/new-workloads-horizon-protocol.md`.",
                  "Результаты: `results/new-workloads-diagnostics/` и `results/new-workloads-horizon/`. Полные срезы validation также в JSON.", "",
                  "```bash", ".venv/bin/python -m read_prediction.experiments.new_workloads_diagnostics",
                  ".venv/bin/python -m read_prediction.experiments.new_workloads_horizon",
                  ".venv/bin/python -m read_prediction.new_workloads_diagnostics_reporting", "```", "",
                  "Эксперименты отказываются перезаписывать готовые каталоги. Reporting читает проверенные JSON."])
    report = PROJECT_ROOT / "reports/new-workloads-diagnostics.ru.md"
    report.write_text("\n".join(lines) + "\n")
    print(report)


if __name__ == "__main__":
    main()
