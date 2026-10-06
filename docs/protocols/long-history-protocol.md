# Трёхдневный train и суточный validation: proj_1/prn_1

Протокол до новых fit/метрик, после диагностики длинных ожиданий.
Дни этих нагрузок уже просмотрены: весь этап development, не новый holdout.
Старые frozen модели/выборы/результаты не меняем. Новый каталог
`results/long-history/{proj_1,prn_1}/`.

## Разделение и данные

Read-only events/features из проверенного `results/new-workloads/`.
Train [0,72h), validation [72h,96h), оценка дней 5–7 каждое 24h окно отдельно.
Train label должен завершиться до 72h; validation и evaluation label — до
конца своего окна. Семь прежних same-start causal признаков, без новых признаков.
Вес модели/адресная медиана не обновляются после train. История признаков
причинно обновляется как раньше. Проверяем прежние source/provenance hashes.

Две постановки separately: точный Offset и любое пересечение диапазонов.
Write-first не отменяет target будущего чтения адреса/диапазона.
Train допускает интервалы до 72h, evaluation — до 24h; это сохраняем явно,
не называем их одинаковыми наблюдательными горизонтами.

## Ровно три кандидата на постановку

1. LightGBM log-L2, все 7 признаков.
2. LightGBM raw-L1, все 7 признаков, objective regression_l1 на секундах.
3. Per-address median только завершённых training labels, global fallback.

Для обеих моделей: 150 trees, num_leaves 31, learning_rate .05,
min_child_samples 50, reg_lambda 1, seed 42, 2 threads, deterministic,
без early stopping/tuning. Прогнозы неотрицательны.
Основной выбор — maximum validation lower pass; tie-break меньше MAE, затем имя.
MAE-best тоже замораживаем отдельно. Не дообучаем на validation.
Сначала frozen.json, затем дни 5–7.

## Сравнение и метрики

Новая log-L2 против прежней выбранной all_features log-L2 на identical rows —
эффект расширения train. Raw-L1 против новой log-L2 — эффект objective.
Новая медиана против прежней training-only медианы — эффект истории для baseline.
Прежние модели/медианы — только benchmarks, не дополнительные кандидаты выбора.

Главный denominator — все Write с observed Read внутри дня. Strict
abs(error) < overwrite_delay; unknown overwrite budgets дают lower/upper bounds,
не исключаются и не считаются failures. N, coverage, MAE/P90, under/over/bias
и все Write исходы публикуем. Два target-среза: <6h / >=6h, на тех же строках
для всех методов. Oracle target-срезы не используются для причинного выбора.
Pooled N/MAE/P90/pass по дням 5–7 считаем по объединённым строкам.
Никакой смены frozen метода по будущим результатам.

## Проверки

Train labels и границы, validation/day5–7 labels точно совпадают с прежними
суточными labels; до 128 train Write независимо проверяем линейным поиском.
Saved-model predicts сверяем, address median пересчитываем из train truth.
Независимый checker воспроизводит selection, metrics/bounds, signed ошибки,
оба target-среза и pooled из NPZ; hashes входов/кода/моделей сохраняем.
Unit suite и manifest verify. Улучшение не является независимым подтверждением
до отдельной проверки frozen рецепта на ещё не оценённом workload.
