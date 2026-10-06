# proj_1 / prn_1: обучение и будущая проверка

Протокол фиксируется после скрининга train/validation, до просмотра будущих метрик.
Workloads выбраны по объёму/разнообразию labels, не по будущей точности.
Источники — исходные gzip из MSR tar. Отдельные модели на каждый volume.
Результаты: `results/new-workloads/{proj_1,prn_1}/`, без перезаписи старых запусков.

## Данные и постановки

Читаем первые 168h от первого timestamp либо до EOF; cap 100 млн событий,
достижение cap — ошибка, не усечённый эксперимент. Хронология, один volume,
512-byte сетка; issue-to-issue, ties по порядку строк. Disk-backed cache/features.

Два label: первое Read с тем же начальным Offset (как в submission) и первое
Read с любым пересечением диапазонов. Перезапись определяется соответствующим
правилом. Write-first не исключаем из основного observed-набора: прогнозируем
чтение адреса/диапазона, не обязательно сохранившейся версии. Read-first
публикуется отдельно как oracle-диагностика, без представления её как gate.

## Train / validation и кандидаты

Первый день: train [0,14.4h), validation [14.4h,19.2h); labels должны завершаться
внутри своего окна. Последние 4.8h дня 1 не используются. Сверяем labels с
предыдущим screening (same-start и range), до fit. Семь существующих same-start
past-only признаков (и для range моделей); историю обновляем, веса замораживаем.

Для каждой постановки ровно два LightGBM log-L2: all-features / no-counts.
150 trees, 31 leaves, learning_rate .05, min_child_samples 50, reg_lambda 1,
seed 42, 2 threads, deterministic, без tuning/early stopping. Baselines:
global median и per-address median только завершённых training labels.

Основной frozen метод среди четырёх кандидатов выбираем по максимальной
validation нижней подтверждённой доле `abs(error) < overwrite_delay`;
при равенстве — меньше MAE, затем имя. Дополнительно до будущей оценки
фиксируем MAE-best метод, чтобы не подменять качество времени критерием.
Не дообучаем на validation; сначала записываем frozen.json, затем дни 2–7.

## Оценка

Каждый будущий день — отдельное 24h окно, labels ограничены его концом.
Все кандидаты и все дни публикуем, не меняем frozen selection по будущим результатам.
Основной знаменатель — все Write с наблюдаемым Read в окне. При ненаблюдаемой
перезаписи remaining window time — нижняя граница бюджета; неподтверждённые
случаи дают upper bound, а не failures. Публикуем N/coverage от всех Write,
pass lower/upper, MAE, median/P90/RMSE, исходы всех Write, и confirmed pass
от всех Write отдельно. Условный Read-first набор не заменяет основной.
Pooled метрики считаем по строкам (P90 — по объединённым ошибкам).

Дни 2–7 — первые будущие оценки этих workloads в этой серии. Они не являются
независимым источником данных вне MSR. Публикуем отрицательные результаты.

## Проверки

- Source/labels train и validation совпадают с прежним скринингом.
- До 128 Write каждого будущего окна и каждой постановки сверяем линейным поиском.
- Saved-model прогнозы сверяем на первых 128 строках каждого дня.
- Отдельный checker пересчитывает метрики/pooled и frozen выбор из NPZ,
  проверяет hashes и границы labels, не обучая модели.
- Сохраняем model/baseline, labels/predictions, source prefix SHA256,
  hashes кода/протокола и артефактов; запускаем unit suite и manifest verify.
