# Что читать

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
