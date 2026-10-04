# Что сохраняем в Git

## Версионируемые файлы

- Код `read_prediction/`, tests, notebooks, документация и отчёты.
- `pyproject.toml` и `uv.lock` для воспроизводимого окружения.
- Все 10 небольших обученных моделей `results/**/*.lightgbm.txt`, включая модели сравнения и ранних этапов.
- JSON-записи экспериментов: metrics, selection, frozen, baseline, hashes и verification.
- Исторические тексты результатов и точные снимки исходного кода в `archive/`.
- `artifacts/manifest.json` с контрольными хешами и размерами файлов.

Модели и JSON-метаданные всех этапов занимают суммарно около 7 МиБ. Они сохраняются по первоначальным путям: это позволяет проверять ссылки и hashes в frozen-описаниях.

`.gitattributes` сохраняет точные байты моделей, исторических исходников и JSON-метаданных при checkout, включая окончания строк. Модели рассматриваются как целые артефакты; Git не объединяет строки деревьев при merge.

| Нагрузка | Итоговая модель | Описание |
|---|---|---|
| usr_1 | `results/next-read-24h/usr_1.lightgbm.txt` | `results/final-study/usr_1/frozen.json` |
| prxy_1 | `results/prxy-validation-diagnosis/no_counts_log_l2.lightgbm.txt` | `results/final-study/prxy_1/frozen.json` |

Модели предсказывают `log1p(seconds)`; результат переводится в секунды через `max(0, expm1(prediction))`. Нужны те же признаки и порядок столбцов, что при обучении; они описаны в коде и frozen-записях.

## Отдельные файлы

`.gitignore` исключает исходные трассы из `dataset/`, полные прогнозы и временные массивы из `results/`. На текущем эксперименте это несколько гигабайт.

Для переноса эксперимента скопируйте файлы с `storage: external` из манифеста в отдельное хранилище, сохраняя их относительные пути. При восстановлении поместите их по тем же путям внутри нового checkout. Официальная страница исходных MSR Cambridge traces: https://iotta.snia.org/traces/block-io/388. Полные сохранённые прогнозы копируются из текущего эксперимента; они не входят в исходный dataset.

Ранее добавленные в Git `dataset/hm_0.csv` и `dataset/prxy_0.csv` исключаются из дальнейшего отслеживания. Их локальные копии остаются в dataset; история прежних коммитов сохраняет прежние версии.

## После клонирования

Для просмотра отчётов и использования моделей достаточно файлов Git:

```bash
uv sync --python /usr/bin/python3.12 --extra notebook
uv run python -m read_prediction.artifacts verify
uv run python -m unittest discover -s tests -v
uv run --extra notebook python -m read_prediction.reporting --check-notebook
```

Для полной независимой проверки метрик восстановите внешние файлы:

```bash
uv run python -m read_prediction.artifacts verify --include-external
uv run python -m read_prediction.checks.study
```

Проверки исходной трассы сначала ищут архив в dataset текущего checkout, поэтому исторические абсолютные пути в results не мешают переносу проекта.

После нового эксперимента обновите манифест командой `uv run python -m read_prediction.artifacts record`. Коммит включает новые небольшие модели, метаданные и манифест; большие файлы переносятся отдельно.
