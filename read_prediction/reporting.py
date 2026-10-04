"""Render RU/EN final reports from verified artifacts; no model fits."""

import argparse
import csv
import json

from read_prediction.paths import NOTEBOOKS, PROJECT_ROOT, REPORTS

ROOT = PROJECT_ROOT
FOLDER = ROOT / "results/final-study"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-notebook", action="store_true")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    records = {w: json.loads((FOLDER / w / "results.json").read_text()) for w in ("usr_1", "prxy_1")}
    verification = json.loads((FOLDER / "verification.json").read_text())
    selection = json.loads((FOLDER / "usr-selection/selection.json").read_text())
    prxy_selection = json.loads((ROOT / "results/prxy-validation-diagnosis/results.json").read_text())
    future_rows = sum(v["prediction_rows_verified"] for v in verification["workloads"].values())
    loaded_rows = sum(record["source"]["loaded_events"] for record in records.values())
    wins = {workload: sum(d["metrics"]["selected"]["mae_seconds"] < d["metrics"]["address_median"]["mae_seconds"] for d in record["days"].values()) for workload, record in records.items()}
    summary = ["# Итог: прогноз следующего чтения в момент записи", "",
               "**Эмпирический этап завершён для выбранной постановки и первых четырёх суток двух трасс. Результат зависит от нагрузки.**", "",
               "Предсказываем, через сколько секунд после записи тот же начальный адрес будет прочитан. Модели выбраны по первым данным и заморожены; последующие дни не использовались для их настройки.", "",
               f"- **prxy_1:** выбранная модель лучше медианы адреса в {wins['prxy_1']} из 3 опубликованных дневных окон. День 2 повторяет ранее проверенный результат; дни 3–4 добавляют новые будущие периоды.",
               f"- **usr_1:** модель лучше медианы адреса в {wins['usr_1']} из 3 будущих дней. Хороший результат первого validation не перенёсся на следующие сутки. Это отрицательный результат, он сохранён.", "",
               "## Средняя абсолютная ошибка: меньше — лучше", "",
               "| Нагрузка | День | Единица | Медиана адреса | Выбранная модель | Снижение ошибки модели | Проверено / всего записей | Покрытие |",
               "|---|---:|---|---:|---:|---:|---:|---:|"]
    english_table = ["| Workload | Day | Address median MAE, s | Selected MAE, s | MAE reduction | Observed / eligible writes | Coverage | Role |",
                     "|---|---:|---:|---:|---:|---:|---:|---|"]
    csv_rows = []
    for workload, record in records.items():
        for day, entry in record["days"].items():
            coverage, metrics = entry["coverage"], entry["metrics"]
            base, chosen = metrics["address_median"]["mae_seconds"], metrics["selected"]["mae_seconds"]
            change = 100 * (base - chosen) / base
            unit, divisor = ("минуты", 60) if workload == "usr_1" else ("секунды", 1)
            summary.append(f"| {workload} | {day} | {unit} | {base/divisor:.2f} | {chosen/divisor:.2f} | {change:+.1f}% | {coverage['observed_targets']:,} / {coverage['writes']:,} | {coverage['observed_fraction']:.1%} |")
            english_table.append(f"| {workload} | {day} | {base:.2f} | {chosen:.2f} | {change:+.1f}% | {coverage['observed_targets']:,} / {coverage['writes']:,} | {coverage['observed_fraction']:.1%} | {entry['evaluation_role']} |")
            for method, metric in metrics.items():
                csv_rows.append({"workload": workload, "day": int(day), "evaluation_role": entry["evaluation_role"], "method": method, **metric,
                                 "eligible_writes": coverage["writes"], "right_censored": coverage["right_censored"], "observed_fraction": coverage["observed_fraction"]})
    summary += ["", "Знак минус в колонке снижения означает, что модель **хуже** простого правила. Это величина ошибки, не время ожидания чтения.", "",
                "## Что можно утверждать", "",
                "На prxy_1 есть подтверждённое преимущество выбранного прогноза на следующих временных периодах. На usr_1 преимущество обученной модели на будущем не подтверждено. Универсального выигрыша на обеих нагрузках нет; для usr_1 более сильным ориентиром по основной метрике оказалась медиана адреса.", "",
                "**Покрытие важно:** оцениваются только записи, для которых чтение произошло до конца соответствующего дня. Для остальных полный интервал неизвестен. Особенно ограничена оценка usr_1 на третьем дне (около 2,1% записей). Дни зависимы, это не независимые статистические эксперименты.", "",
                "Сопоставляются одинаковые начальные Offset, а не пересекающиеся диапазоны или версии данных. Промежуточные перезаписи не отменяют target. Результат не доказывает качество на всей неделе, всех записях или ускорение SSD.", "",
                "## Что готово", "",
                f"Обработано **{loaded_rows:,} событий** первых 96 часов двух трасс; проверены **{future_rows:,} будущих записей** в таблице. День 2 prxy_1 включён как воспроизведение, не новая независимая проверка.",
                "Выбор usr_1 завершён по семи фиксированным вариантам на первом validation; prxy_1 сохраняет ранее выбранную модель без накопленных счётчиков. На будущих днях переобучений нет. Отрицательные результаты не заменены новой настройкой.",
                "Все прогнозы, baseline и модели сохранены. Пересчитаны пять метрик всех четырёх методов; подтверждены hash замороженных моделей и baseline. Исходные трассы независимо проверены для 448 выбранных историй (64 относятся к validation usr_1, 384 — к будущим дням); hash обоих полных префиксов перепроверен.",
                "16 unit-тестов прошли. Итоговый ноутбук — [notebooks/final_results.ipynb](../notebooks/final_results.ipynb); подробные отчёты — [report.ru.md](report.ru.md), [report.en.md](report.en.md); таблица метрик — [metrics.csv](metrics.csv).", "",
                "## Что показать сеньору", "",
                "Отчёт описывает завершённый ограниченный эксперимент: постановка → разметка → baseline → выбор модели → будущая проверка → выводы. Вопрос о требуемой блочной гранулярности остаётся предметом согласования: текущий вариант использует точный начальный байтовый адрес. Переход к покрытым блокам будет отдельной постановкой, а не исправлением этих метрик.", ""]
    (REPORTS / "summary.ru.md").write_text("\n".join(summary))
    en_summary = ["# Write-triggered next-read prediction: final bounded study", "",
                  "The empirical stage is complete for exact starting offsets on the first four days of usr_1 and prxy_1. Results are workload-dependent.", "",
                  "The target is elapsed seconds from each write to the first later read at the same starting byte offset. Models and training-only median baselines are frozen before future evaluation. Per-day metrics include only targets completed within that day.", "",
                  *english_table, "",
                  "A negative MAE reduction denotes a model worse than the per-address median. The usr_1 validation winner fails to beat that median on all three future days. The prxy_1 model without cumulative counts beats it in all three reported windows; day 2 is a replication of the previously evaluated window, while days 3--4 add new future periods. No future results were used to change the models.", "",
                  "The evidence supports a workload-specific advantage on prxy_1, not a workload-independent benefit. Censoring is substantial: unknown intervals are not assigned zero or infinity. Exact starting offsets do not represent arbitrary overlapping I/O ranges or data-version consumption. Consecutive days and requests are correlated; no significance or population-wide claims are made. SSD performance was not simulated.", "",
                  f"The combined prefixes contain {loaded_rows:,} events. The published future metrics cover {future_rows:,} completed write-to-read targets, including prxy_1 day-2 replication. Models, predictions, frozen medians, source/code hashes and verification artifacts are retained. See [report.en.md](report.en.md) for full methods and metrics.", ""]
    (REPORTS / "summary.en.md").write_text("\n".join(en_summary))
    appendix = ["| Workload | Day | Method | N | MAE, s | Median AE, s | P90 AE, s | RMSE, s | MAE log1p(s) |",
                "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for row in csv_rows:
        appendix.append(f"| {row['workload']} | {row['day']} | {row['method']} | {row['n']:,} | {row['mae_seconds']:.4f} | {row['median_absolute_error_seconds']:.4f} | {row['p90_absolute_error_seconds']:.4f} | {row['rmse_seconds']:.4f} | {row['mae_log1p_seconds']:.4f} |")
    validation_table = ["| Workload | Candidate | Validation MAE, s |", "|---|---|---:|"]
    for workload, metrics in [("usr_1", selection["metrics"]), ("prxy_1", prxy_selection["metrics"]["validation"])]:
        for method, metric in metrics.items():
            validation_table.append(f"| {workload} | {method} | {metric['mae_seconds']:.4f} |")
    commands = ["```bash", "uv sync --python /usr/bin/python3.12 --extra notebook", "uv run python -m unittest discover -s tests -v",
                "# Historical prerequisites: day-one preparation and prxy validation selection", "uv run python -m read_prediction.pipeline",
                "uv run python -m read_prediction.extended --hours 24 --output results/next-read-24h",
                "uv run python -m read_prediction.experiments.diagnosis", "# prxy day-two evaluation also creates the historical frozen median artifact", "uv run python -m read_prediction.experiments.day2",
                "uv run python -m read_prediction.experiments.study select-usr", "uv run python -m read_prediction.experiments.run_study usr_1", "uv run python -m read_prediction.experiments.run_study prxy_1",
                "uv run python -m read_prediction.checks.study", "uv run python -m read_prediction.reporting --check-notebook", "```"]
    methods_ru = ["## Методы", "",
                  "Исходные MSR-Cambridge CSV читаются из локальных tar/gzip. Timestamp — FILETIME, Offset/Size — байты; интервалы получены из разности целых timestamps / 10⁷. Каждый файл проверяется как один logical volume, хронология валидируется. ResponseTime не используется: момент прогноза — поступление write.",
                  "Признаки: log1p адреса, размера, числа предыдущих чтений/записей, времени с предыдущего чтения/записи, последнего завершённого read→read интервала. Отсутствующая история — NaN. usr_1 сохраняет все семь признаков; prxy_1 исключает два накопленных счётчика. Расчёт через стабильную группировку сохраняет порядок событий; future reads доступны только для truth, не features.",
                  "На первых сутках обучение/validation разделены прежними 60/20/20 временными cutoffs; последняя часть первых суток уже просмотрена ранее и не считается новой независимой оценкой. Train labels не пересекают training cutoff; validation labels не пересекают validation cutoff. Две median baseline вычислены только из завершённых training labels.",
                  "На каждой нагрузке выполнен ограниченный выбор среди четырёх LightGBM вариантов (all/no-counts × log-L2/raw-L1), двух медиан и истории read-period. Исходный вариант уже обучен; выполнялись ровно три новых fit для каждого workload на соответствующем этапе. 150 деревьев, 31 leaf, learning rate 0.05, min_child_samples 50, reg_lambda 1, seed 42, два потока, без early stopping. usr_1 выбран original_log_l2; prxy_1 — no_counts_log_l2. Основной критерий выбора — validation MAE секунд.",
                  "Проверка проводится в календарных окнах от первого события каждого файла: [24h,48h), [48h,72h), [72h,96h). История обновляется наблюдаемыми событиями, но модели и median baseline не обновляются. Первый последующий read должен быть раньше конца своего окна. Все окна публикуются; ни положительные, ни отрицательные исходы не используются для новой настройки.", "",
                  "## Выбор по первому validation", "", *validation_table, "",
                  "## Все метрики будущих периодов (секунды)", "", *appendix, "",
                  "RMSE и P90 показывают, что средняя ошибка не полностью описывает редкие крупные промахи. Сравнение по MAE не означает преимущества по всем метрикам: например, у usr_1 во втором дне медианная ошибка выбранной модели меньше baseline, но MAE/RMSE и хвост хуже.", "",
                  "## Воспроизведение", "",
                  "Команды ниже предназначены для чистого каталога результатов. Существующие этапы не перезаписываются; архивы оставить в dataset/. Готовые сохранённые результаты можно проверять без обучения. uv.lock фиксирует зависимости. Выбор usr и будущая оценка разведены по командам.", "", *commands, "",
                  "Новый study cap — 130 млн событий на 96h prefix; 96h должны быть достигнуты, иначе STOP. Сортировка и mmap требуют нескольких GiB RAM. Временные кэши удалены после успеха. Для каждой оценки runtime/RSS записаны в results.json; стоимость отдельного этапа usr selection не измерена и не включена в эти значения.", "",
                  "## Ограничения и итог", "",
                  "Оценка условна на завершённых интервалах и может исключать длинные задержки. Особенно низкое coverage usr_1 day3 не позволяет описать качество на всех записях. Корреляции внутри адресов/дней сохраняются, CI/p-values не рассчитывались. Положительная проверка prxy на нескольких днях не доказывает общую предсказуемость всех storage workloads. usr selection не подтвердил устойчивый перенос на будущее; постфактум заменять модель медианой и объявлять новую победу не следует.",
                  "Для прикладного следующего этапа нужны согласование блочной гранулярности и отдельное рассмотрение цензурирования/горизонта. Для проверки SSD throughput потребуются модель размещения и симуляция; это вне текущего задания. Эмпирический этап в текущей постановке завершён с положительным prxy и отрицательным usr результатом.", "",
                  "## Источник данных", "", "Схема и атрибуция: MSR-Cambridge/README.txt внутри локальных архивов. Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.",
                  "https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf", ""]
    (REPORTS / "report.ru.md").write_text("\n".join([*summary, *methods_ru]))
    methods_en = ["## Methods", "",
                  "The MSR trace schema is Timestamp, Hostname, DiskNumber, Type, Offset, Size, ResponseTime. Offsets and request sizes are bytes. FILETIME differences are divided by 10^7 to obtain seconds. Both endpoints of the target are request issue timestamps, not I/O completion timestamps; ResponseTime is unused. Each trace is checked for one logical volume and chronological order.",
                  "The seven candidate features are log1p starting offset, size, prior read count, prior write count, seconds since the last read, seconds since the last write, and the last completed read-to-read interval. Missing history is NaN. Stable grouping is a computational shortcut preserving source row order. Future reads construct labels only. Intervening writes do not cancel a sample, so this predicts address access rather than version consumption.",
                  "Day one uses the original 60/20/20 temporal cutoffs. Training labels must complete before the training cutoff, and validation labels before the validation cutoff. The already inspected day-one final segment is not presented as a new unbiased test. Per-address and global medians use only completed training labels and remain frozen.",
                  "Selection compares four LightGBM configurations (all/no cumulative counts crossed with log-L2/raw-L1), two medians and a past read-period heuristic. There are three new fixed fits per workload, since the original fit already exists. All share 150 trees, 31 leaves, learning rate 0.05, min_child_samples 50, L2 regularization 1, seed 42, two threads, and no early stopping or tuning. The minimum validation MAE selects original_log_l2 for usr_1 and no_counts_log_l2 for prxy_1. No new fits occur in the future windows.",
                  "The frozen choices are evaluated over hours [24,48), [48,72), and [72,96) from each trace's first event. Per-address feature history evolves from observed events, but the models and median values do not. Each window is censored at its own end. All outcomes are retained. prxy day 2 reproduces prior evidence; only its days 3--4 are additional future periods.", "",
                  "## Day-one validation selection", "", *validation_table, "",
                  "## Complete future metrics", "", *appendix, "",
                  "The error distribution is heavy-tailed. MAE improvements do not imply improvements in every metric; inspect P90 and RMSE. In particular, usr day 2 has a lower selected-model median error but worse MAE, P90 and RMSE than the per-address median.", "",
                  "## Reproduction", "",
                  "Use a clean result tree with both downloaded archives in dataset/. Existing runs are not overwritten. uv.lock pins dependencies. Saved artifacts can be verified without fitting. The scripts separate validation selection from frozen evaluation.", "", *commands, "",
                  "Evaluation stops if a 96h prefix cannot be reached within 130 million events. Compact disk-backed preparation still requires several GiB of RAM; it is not a streaming fit. Successful caches are removed. Evaluation time and process peak RSS are recorded separately per workload. The usr selection stage was not separately resource-measured and is excluded from those observations.", "",
                  "## Verification and limitations", "",
                  f"Sixteen unit tests passed. All {future_rows:,} future rows and their four methods' five metrics were independently checked from stored predictions, along with validation selection, daily boundaries and frozen baseline/model hashes. Raw sources were independently scanned to audit 448 selected histories and recompute both prefix hashes. This is a sample history audit, not a second complete relabeling of every event.",
                  "Results are conditional on next reads observed within each day; low usr day-3 coverage is particularly restrictive. Rows and days are correlated; no p-values, confidence intervals or workload-population claims are made. Exact starting-offset equality does not capture overlapping ranges. The first four days do not constitute the entire trace week. No SSD throughput or placement effect was measured.",
                  "The bounded empirical task is complete with mixed results: prxy_1 shows an advantage for the frozen no-counts model, while usr_1 shows failure of its validation-selected model to beat medians on future days. Choosing a replacement after examining these windows would be a new selection step requiring new future evidence.", "",
                  "## Data attribution", "", "Schema and attribution are from MSR-Cambridge/README.txt in the local archives. Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.",
                  "https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf", ""]
    (REPORTS / "report.en.md").write_text("\n".join([*en_summary, *methods_en]))
    with (REPORTS / "metrics.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    if args.check_notebook:
        import nbformat
        from nbclient import NotebookClient
        notebook = nbformat.read(NOTEBOOKS / "final_results.ipynb", as_version=4)
        nbformat.validate(notebook)
        NotebookClient(notebook, timeout=60, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOKS)}}).execute()
        print("Final notebook executed successfully without training.")
    print("Saved RU/EN summaries, full reports and metrics.csv from verified results.")


if __name__ == "__main__":
    main()
