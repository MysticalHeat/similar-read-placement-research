# Что читать

- **`mean-overwrite.ru.md`** — новая цель MAE < среднего времени до перезаписи: выбор по validation MAE, одинаковые выборки, нижние границы при неизвестных overwrite.
- **`mixture.ru.md`** — три фиксированные смеси log-L2/raw-L1 на prn_1: MAE улучшается ценой основного критерия, frozen fallback log-L2.
- **`long-history.ru.md`** — train дней 1–3, суточный validation и сравнение log-L2/raw-L1/медианы на днях 5–7; development.
- **`new-workloads-diagnostics.ru.md`** — бюджеты перезаписи, направление ошибок, адреса/размеры и контроль одинаковой длины окна для proj_1/prn_1.
- **`new-workloads.ru.md`** — первые замороженные будущие оценки proj_1 и prn_1, сравнение критерия и MAE с медианой.
- **`data-sufficiency.ru.md`** — проверка объёма train/validation во всех 36 трассах и диапазонное подтверждение шести новых кандидатов до обучения.
- **`prxy0-check.ru.md`** — новая нагрузка prxy_0: низкое покрытие чтениями, исходы и фиксированные модели на будущих днях 2–7.
- **`range-refit.ru.md`** — gate и прогноз времени переобучены на диапазонных метках; выборочный и общий критерии разделены.
- **`range-label.ru.md`** — проверка единицы данных: разметка по диапазонам байтов (сетка 512 Б) против точного начального Offset, частичные перекрытия и чувствительность критериев.
- **`all-write.ru.md`** — полная выборка Write, признаки серий I/O и трёхклассовый прогноз до окна; общий и выборочный критерии разделены.
- **`read-first.ru.md`** — двухэтапный прогноз Read-first: точность отбора, покрытие и общий критерий 90% без исключения сложных записей.
- **`overwrite90.ru.md`** — новая итерация с порогом 90%, обновляемой историей и выбором по доле ошибок меньше перезаписи; повторная диагностика дня 7.
- **`overwrite-comparison.ru.md`** — сравнение ошибок со временем до следующей записи адреса, с учётом неизвестных интервалов и порядка чтения/перезаписи.
- **`mae-improvement.ru.md`** — новый эксперимент снижения MAE: выбор на уже известных днях 2–4 и замороженная проверка на днях 5–7.
- **`simple-summary.ru.md`** — простое объяснение всей работы.
- **`summary.ru.md`** — короткие выводы и основная таблица.
- **`report.ru.md`** — полный русский отчёт.
- **`summary.en.md`** — короткий английский итог.
- **`report.en.md`** — полный английский отчёт для сеньора.
- **`metrics.csv`** — все дневные метрики.

Итоговый notebook: `../notebooks/final_results.ipynb`. Артефакты запусков: `../results/final-study/`.

Основные отчёты собираются из проверенных результатов (simple summary, prxy0-check, data-sufficiency и new-workloads написаны вручную):

```bash
uv run --extra notebook python -m read_prediction.reporting --check-notebook
```

Команда запускается из корня проекта и не обучает модели.

Диагностика новых нагрузок: `.venv/bin/python -m read_prediction.new_workloads_diagnostics_reporting`.

Длинная история обучения: `.venv/bin/python -m read_prediction.long_history_reporting`.

Новый отчёт собирается отдельно, после проверки `results/mae-improvement/`:

```bash
uv run python -m read_prediction.mae_reporting
```

Сравнение с перезаписью: `uv run python -m read_prediction.overwrite_reporting`.

Разметка по диапазонам: `uv run python -m read_prediction.range_label_reporting` (после проверки `results/range-label/`).

Переобучение на диапазонных метках: `uv run python -m read_prediction.range_refit_reporting` (после проверки `results/range-refit/`).
