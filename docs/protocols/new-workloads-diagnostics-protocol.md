# Диагностика proj_1/prn_1: budgets и ошибки без переобучения

Первые два пункта плана: (1) трудность критерия по времени до перезаписи;
(2) почему выбранная модель уступает медиане. Используем только сохранённые
модели/прогнозы `results/new-workloads/`, не меняем frozen selection.
Новый каталог `results/new-workloads-diagnostics/`. Будущие дни уже просмотрены;
это development диагностика, не новый holdout и не причинный эксперимент.

Постановки same-start и range отдельно, identical observed rows для сравнения
выбранной модели, адресной медианы и нуля. Validation отдельно от pooled дней
2–7. Главный знаменатель — Write с наблюдаемым Read внутри окна.

## 1. Время до перезаписи

Наблюдаемые бюджеты: ноль; (0,1ms); [1ms,10ms); [10ms,100ms); [100ms,1s);
[1s,10s); [10s,1min); [1min,10min); [10min,1h); >=1h.
Неизвестная перезапись — отдельная группа, не приравнивается к оставшемуся
времени окна. Для неё remaining time лишь lower budget и даёт lower/upper
pass bounds. Публикуем N/share, MAE/P90, pass и вклад в общую абсолютную ошибку.
Строгое error < 0 невозможно; ceiling 1 - zero-budget share — только
математический верхний предел, не оценка достижимой точности при малых budgets.

## 2. Ошибки и перенос

- Train labels, validation и дни 2–7: N/coverage и распределение target
  (mean, q10/q50/q90/q99); prediction distribution на validation/future.
- Signed error = predicted - actual: over/under/exact share, mean bias,
  over/under contribution to MAE и median error/target ratio.
- Адреса Write: (а) имел завершённый training label; (б) встречался в training
  events, но без завершённого label; (в) отсутствовал в training events.
  Это **same-start адреса** даже для range модели; проверяем модельные признаки
  и адресный baseline, не полноту истории пересекающихся блоков.
- Размер Write: <=512B; (512B,4KiB]; (4KiB,16KiB]; (16KiB,64KiB]; >64KiB.
- Размер matched Read относительно Write: меньше / равен / больше.
- Target: <1s; [1s,1min); [1min,10min); [10min,1h); [1h,6h); >=6h.
- История до Write: prior same-start Read 0 / 1–4 / >=5 (из causal features).
- Каждый день отдельно: N, MAE/criterion, направление ошибок, target median/P90.

Slice показатели не заменяют общие. Разложение суммы абсолютных ошибок
показывает источники потерь, но не доказывает причину. Address-median может
пользоваться global fallback для адресов без завершённых training labels.

## Проверки

Входные metrics/provenance и frozen hashes должны совпасть. Все наблюдаемые
строки сохранённых NPZ включены ровно один раз в каждой семье buckets.
Проверяем N/confirmed pass/unknown pass и взвешенную MAE с опубликованными
validation/pooled, восстановление over+under MAE, суммы категорий.
Отдельные unit cases для нулевого/неизвестного budget, строгого неравенства
и направления ошибок. Source train/range labels берём из проверенного screening;
same-start train truth пересчитываем только в train окне.
