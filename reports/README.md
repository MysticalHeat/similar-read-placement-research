# Что читать

- **`overwrite-comparison.ru.md`** — сравнение ошибок со временем до следующей записи адреса, с учётом неизвестных интервалов и порядка чтения/перезаписи.
- **`mae-improvement.ru.md`** — новый эксперимент снижения MAE: выбор на уже известных днях 2–4 и замороженная проверка на днях 5–7.
- **`simple-summary.ru.md`** — простое объяснение всей работы.
- **`summary.ru.md`** — короткие выводы и основная таблица.
- **`report.ru.md`** — полный русский отчёт.
- **`summary.en.md`** — короткий английский итог.
- **`report.en.md`** — полный английский отчёт для сеньора.
- **`metrics.csv`** — все дневные метрики.

Итоговый notebook: `../notebooks/final_results.ipynb`. Артефакты запусков: `../results/final-study/`.

Отчёты, кроме написанного вручную simple summary, собираются из проверенных результатов:

```bash
uv run --extra notebook python -m read_prediction.reporting --check-notebook
```

Команда запускается из корня проекта и не обучает модели.

Новый отчёт собирается отдельно, после проверки `results/mae-improvement/`:

```bash
uv run python -m read_prediction.mae_reporting
```

Сравнение с перезаписью: `uv run python -m read_prediction.overwrite_reporting`.
