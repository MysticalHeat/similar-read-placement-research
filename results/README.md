# Сохранённые эксперименты

| Каталог | Этап |
|---|---|
| `next-read-pilot/` | первый миллион событий каждой нагрузки |
| `next-read-24h/` | первые сутки обеих нагрузок, исходные модели |
| `prxy-validation-diagnosis/` | выбор улучшенного prxy_1 по validation |
| `prxy-day2/` | замороженная проверка выбранной модели на вторых сутках |
| `final-study/usr-selection/` | выбор usr_1 по первому validation |
| `final-study/usr_1/` | замороженная проверка usr_1 на днях 2–4 |
| `final-study/prxy_1/` | проверка prxy_1 на днях 2–4 с воспроизведением дня 2 |
| `mae-improvement/` | ограниченный поиск log-L1/log-L2, early stopping, смесей и причинной истории; development 2–4, новый holdout 5–7 |
| `overwrite-comparison/` | диагностика MAE относительно следующей Write по адресу на днях 5–7, без обучения |

В этих каталогах хранятся `results.json`, модели `.lightgbm.txt`, прогнозы `.npz`/`.csv`, baseline, frozen и verification записи. Они позволяют воспроизвести вычисленные метрики.

Готовые итоговые тексты находятся в `../reports/`, протоколы — в `../docs/protocols/`. Описания ранних этапов внутри каталогов результатов сохраняются как история.

Git сохраняет здесь модели `.lightgbm.txt`, JSON-метаданные и Markdown-описания. Прогнозы `.npz`/`.csv` и рабочие массивы хранятся отдельно. Для проверки комплекта моделей: `uv run python -m read_prediction.artifacts verify`. Манифест всех артефактов: `../artifacts/manifest.json`; восстановление больших файлов описано в `../docs/git-storage.md`.

Hashes исходного кода в прежних results проверяются по точным снимкам `../archive/code-before-restructure/`. Эти hashes не заменены fingerprints реорганизованного кода. Новые запуски записывают пути текущего пакета `read_prediction`.
