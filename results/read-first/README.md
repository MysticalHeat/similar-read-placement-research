# Двухэтапный Read-first

Протокол: `../../docs/protocols/read-first-protocol.md`. Отчёт: `../../reports/read-first.ru.md`.

Обучение на дне 5, выбор 36 комбинаций classifier/time/threshold на дне 6, refit выбранных моделей на днях 5–6 и повторная диагностика дня 7. Нового holdout нет. История меток исхода обновляется только после Read; старые frozen-модели не меняются.

В каждой папке нагрузки:
- `selection.json` — все validation-комбинации, рецепты и hashes;
- `validation.predictions.npz`, `validation-*.lightgbm.txt` — вероятности gate, прогнозы времени и модели;
- `gate.lightgbm.txt`, опционально `time.lightgbm.txt` — refit-модели;
- `frozen.json` — hashes выбора и refit-моделей;
- `day7.predictions.npz` — вероятность, условное время и routed-прогноз для всех прежних завершённых примеров;
- `diagnostic.json` — precision, recall, coverage, ошибка в выбранной группе и на всём наборе;
- `verification.json` — независимые counts и причинная реконструкция.

Выборочные 90% при неполном покрытии не означают достижение общей цели. Выборка не содержит незавершённые Write: рабочая точность gate на всех Write пока не измерена. NPZ — внешние артефакты, JSON и LightGBM — Git-sized.
