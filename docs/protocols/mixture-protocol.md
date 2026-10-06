# prn_1: фиксированные смеси log-L2/raw-L1

Development эксперимент на сохранённых прогнозах `results/long-history/prn_1/`.
Новые модели не обучаем, старые результаты/выборы не меняем.
Новый каталог `results/mixture/prn_1/`. Same-start и range отдельно.

Три кандидата: prediction = w * log-L2 + (1-w) * raw-L1,
w = 0.75, 0.50, 0.25; смешиваем секунды, не логарифмы.
Benchmarks — обе несмешанные модели. Validation — полный день 4.

**Основное правило выбора:** смесь допустима, только если её validation MAE
строго меньше log-L2 MAE и её confirmed pass count не меньше log-L2 на тех же
observed строках. Среди допустимых — минимальная MAE, затем максимальный pass,
затем имя. Если нет допустимых, frozen метод — log-L2 (fallback), без ослабления
условий и подстройки weights. Дополнительно фиксируем MAE-best среди трёх
смесей как диагностический benchmark, а не замену primary.
Сначала записываем frozen.json, затем оцениваем дни 5–7.

Main denominator — все Write с observed Read внутри соответствующего дня,
strict abs(error) < next_overwrite_delay; unknown overwrite gives lower/upper
bounds. Сохраняем MAE/P90, pass bounds, N/coverage, under/bias,
срезы target <6h / >=6h. Pooled по объединённым строкам, identical rows у
всех пяти методов. Все кандидаты/дни публикуются. Успешная замена требует
MAE меньше log-L2 и pass lower не меньше log-L2 в будущем; будущие результаты
не меняют замороженный метод. 90% остаётся отдельной незакрытой целью.

Дни уже просмотрены: это диагностика компромисса, не независимое подтверждение.
После этого этапа не запускаем новую нагрузку автоматически. Независимый checker
восстанавливает смеси из parent NPZ, проверяет selection, metrics/slices/pooled,
hashes. Unit suite и manifest verify.
