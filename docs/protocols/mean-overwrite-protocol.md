# MAE относительно среднего времени до перезаписи

Цель: строгое `MAE < mean(overwrite_seconds)` на одинаковых записях.
Используем сохранённые long-history прогнозы proj_1/prn_1 и mixture прогнозы
prn_1. Нового обучения нет. Same-start и range оцениваются отдельно.

Выбор фиксируется по минимальной MAE на всех observed-Read записях validation
дня 4; при равенстве — имя метода. Кандидаты: log_l2, raw_l1, address_median,
для prn_1 дополнительно mix_log75/mix_log50/mix_log25. Previous методы служат
сравнением, в новый выбор не входят. Pass count больше не ограничивает выбор.
Будущий overwrite и фактический target не используются для выбора ветки
прогноза. Предыдущие frozen записи остаются историческими результатами.

Для validation, каждого дня 5–7 и pooled:
- paired: Read и overwrite наблюдались; MAE и средний overwrite на этой же
  выборке, отношение MAE/mean, запас mean−MAE и строгое условие;
- observed-Read: MAE на всех записях с Read и нижняя граница среднего overwrite.
  Для неизвестного overwrite используем remaining только как нижнюю границу,
  не как фактическое время. Если MAE ниже границы — успех доказан; если все
  времена известны — точное решение; иначе статус «не определено»;
- количество всех Write, observed Read, paired и неизвестных overwrite.

Pooled считается конкатенацией записей, не средним дневных средних.
Нулевой средний интервал не даёт определённого отношения; равенство не успех.
При пустой paired выборке показатели null. Не исключаем нулевые интервалы.
MAE для Write без наблюдаемого Read не определена: никаких выводов на все
Write из этой оценки. Дни 5–7 уже просмотрены, это development, не новый
holdout. Скрипт не объявляет окончательное подтверждение на новом holdout.

Входные fingerprints проверяются до расчёта. Новые результаты и fingerprints
пишутся в results/mean-overwrite/, отчёт — reports/mean-overwrite.ru.md.
Независимый checker восстанавливает суммы ошибок, интервалы и выбор из
исходных массивов. Команды:

```bash
.venv/bin/python -m read_prediction.experiments.mean_overwrite
.venv/bin/python -m read_prediction.checks.mean_overwrite
```
