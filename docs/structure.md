# Где что лежит

## Если нужно понять результат

1. `reports/simple-summary.ru.md` — объяснение простым языком.
2. `notebooks/final_results.ipynb` — итоговые таблицы в notebook.
3. `reports/report.en.md` — полный отчёт для сеньора.
4. `reports/report.ru.md` — те же методы и результаты на русском.

`reports/metrics.csv` содержит подробные дневные метрики. Прогнозы и модели находятся в `results/`, а не в каталоге отчётов.

## Python-код

| Модуль | Назначение |
|---|---|
| `read_prediction.pipeline` | чтение небольшого префикса, признаки, labels, baseline, обучение |
| `read_prediction.extended` | компактная подготовка суточных и многодневных трасс |
| `read_prediction.experiments.diagnosis` | сравнение вариантов prxy_1 по train/validation |
| `read_prediction.experiments.day2` | первая замороженная проверка вторых суток prxy_1 |
| `read_prediction.experiments.study` | выбор usr_1 и многодневная оценка |
| `read_prediction.experiments.run_study` | фиксация baseline перед итоговой оценкой |
| `read_prediction.checks.*` | проверка результатов, hashes и историй исходной трассы |
| `read_prediction.reporting` | сборка отчётов из сохранённых результатов |
| `read_prediction.submission` / `submission_overwrite` | переносимый results notebook, mean overwrite и критерий ≥90% из проверенных метрик |
| `read_prediction.submission_models` / `submission_predict` | выбранные prn_1 смеси и proj_1 адресные медианы с переносимым inference |
| `read_prediction.submission_datasets` | скрининг 36 трасс и обоснование выбора proj_1/prn_1 для submission |
| `read_prediction.training_notebook` / `notebook_selected_training` | самостоятельный notebook обучения новых prn_1/proj_1 моделей и экспорта выбранных предикторов |
| `read_prediction.checks.training_notebook` | выполнение training notebook на искусственной четырёхдневной трассе вне репозитория |
| `read_prediction.checks.submission` | сверка submission с источниками и выполнение notebook вне репозитория |
| `read_prediction.paths` | единые пути проекта |
| `read_prediction.provenance` | проверка fingerprints старого и нового кода |
| `read_prediction.artifacts` | манифест файлов и проверка Git-комплекта моделей |

Команды запускаются из корня проекта:

```bash
uv sync --python /usr/bin/python3.12 --extra notebook
uv run python -m unittest discover -s tests -v
uv run --extra notebook python -m read_prediction.reporting --check-notebook
```

Последняя команда собирает отчёты и выполняет итоговый notebook без обучения. Полная проверка исходных данных занимает больше времени:

```bash
uv run python -m read_prediction.checks.study
```

Для нового обучения в чистом каталоге результатов используйте последовательность из `reports/report.en.md`. Текущие результаты не перезаписываются экспериментальными командами.

## Notebooks

- `submission/results.ipynb` — комплект для сдачи: mean overwrite и недостижение ≥90%, сравнение 36 датасетов и обоснование выбора proj_1/prn_1, затем ранний usr_1/prxy_1 inference. Метрики встроены; `.venv/bin/python -m read_prediction.submission` пересобирает notebook и снимки JSON.
- `notebooks/final_results.ipynb` — основная точка входа: новые mean-overwrite/90% результаты, выбранные модели, inference и дневные показатели, затем ранний этап.
- `notebooks/history/next_read_prediction.ipynb` — последовательность ранних этапов.
- `notebooks/reference/lgb_src1_2_log.ipynb` — исходный пример сеньора.

Выберите kernel `.venv/bin/python`. Наши notebooks находят корень проекта при открытии как из корня, так и из вложенного каталога notebooks. Исходный reference notebook предназначен для изучения присланного примера; его внешние пути принадлежат оригинальному коду.

## Данные, результаты и история

- `dataset/` — скачанные архивы и исходные файлы; схема описана в его README.
- `results/` — артефакты запусков. Список этапов — в `results/README.md`.
- `docs/protocols/` — планы, определённые до экспериментов.
- `archive/code-before-restructure/` — точные исходные версии скриптов до реорганизации. Старые results ссылаются на их hashes; данные checks сверяют с этими снимками, если текущий модуль уже отличается.
- `.research/` — материалы предшествующего исследовательского этапа, включая синтетические эксперименты.
- `artifacts/` — размеры и hashes моделей, метаданных и отдельно хранимых больших файлов. Правила Git и восстановление данных: `docs/git-storage.md`.

Исторические записи запусков сохраняют первоначальные пути и команды как описание выполненного эксперимента. Для работы сейчас используйте модульные команды из README и отчётов в `reports/`.
