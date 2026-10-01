# Исследовательский вопрос: обучаемый прогноз и throughput

Status: PROVISIONAL v0.2, 2026-09-30; question/H-ID/protocol/budget approval PENDING.
Это скопинг, не протокол или публичная регистрация; обучения, исполнения и результатов нет.
Предпочтения пользователя: обучаемый predictor по предложению руководителя, симулятор допустим, цель — read throughput; перенос уже записанных страниц вероятен, но не утверждён.

## Термины и проверенное основание
Пользователь назвал writing point «указателем следующего чтения». Это расходится с семантикой выбранного кода, не с правом пользователя определить свою задачу.
S013: FTLSim-MiDA commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21; статический аудит без исполнения, получен 2026-09-30. Используются проверки оркестратора, не новый аудит кода.
- C006/S013, MiDaFTL.py L19,58–72,78: writing_pointers — активные блоки назначения следующих записей по группам, не predicted read addresses.
- C007/S013, MiDaFTL.py L21–28: mapped read получает PPN через l2p; INVALID пропускается. Прогноз read target и обновление write allocation — разные сущности.
- C008/S013, Statistics.py L111–124; FTL.py L36–100: NAND durations суммируются последовательно в elapsed, не concurrent completion timeline.
- C009/S013, FTL.py L63–67,36–48: существующая migrate_page учитывает source read + destination write. Это не полный overhead предлагаемой proactive migration/inference.
- C010/S013, simulator-audit.md §§4–6: проверенное accounting не устанавливает throughput gain от channel/die/plane overlap; нужна проверенная concurrent timing model.
Точная поддержка/URLs/access: claims/evidence-map.md, claims/citation-audit.md, experiments/simulator-audit.md. Инспекция исходника не валидирует физическую точность модели.

## Q-C: отдельная оценка обучаемого predictor
Вопрос: на отложенных по времени workloads превосходит ли trained causal predictor простые sequential/frequency/transition baselines по прогнозу будущих read targets при равных k, горизонте, допустимых features и сопоставимых tuning budgets?
Система/популяция: имеющийся по сообщению пользователя dataset; путь, schema, происхождение, лицензия, размеры и число независимых traces UNKNOWN.
X — модель, обученная только на train; Z — лучший простой baseline, выбранный на validation. Архитектура не выбрана; GPU не предполагается необходимым.
Кандидат Y/M — precision@k при согласованных coverage/горизонте; timeliness отдельно при доступных timestamps и модели времени действий. Практический порог δP PENDING.
Нужно определить target: следующий read LPN либо k будущих страниц; общий поток или конкретная queue/thread; гранулярность page и address namespace.
Предлагаются temporal train/validation/test, правила границ горизонтов и online-adaptation только по уже доступному прошлому. Нельзя случайно перемешивать зависимые события или выбирать параметры по test.
Prediction success не доказывает throughput. Без arrival/concurrency данных throughput assumptions выбираются отдельно, не восстанавливаются из точности прогноза.

## Q-A: end-to-end migration → read throughput
Вопрос: в согласованной модели SSD увеличивает ли causal trained forecast + tentative migration уже записанных страниц пропускную способность успешных demand-read относительно обычного layout без proactive migration, при фиксированных workload/concurrency и учёте затрат?
X — predictor и отдельный causal decision layer: forecast → разрешённое relocation action. Миграция tentative; порог действия/confidence, k, частота и cost caps PENDING.
Z — обычная политика модели с сопоставимым tuning budget. Разделяющие сравнения: тот же predictor без миграции; миграция по простой causal/nonpredictive политике при тех же ограничениях действий.
Популяция: выбранные traces/workloads и проверенная timing model; вывод не переносится автоматически на реальные SSD.
Условия: независимые ресурсы, shared bus/command constraints, arrivals/dependencies, queue depth и одинаковый scheduler/cache state; прогноз не разрешает предъявлять будущие demand-запросы раньше их готовности.
Кандидат endpoint: T_bytes = useful bytes успешно завершённых исходных demand-read / simulated completion makespan (s); альтернативно T_IOPS = число таких завершённых запросов / тот же makespan.
Выбрать одну primary unit. Не включать internal reads/GC/copies в числитель, не считать покрывающие NAND pages полезными bytes частичного host request, не считать skips завершениями; сохранять исходные request IDs и проверять completeness/correctness (C007/S013; audit §§4,6).
Makespan — от согласованного начала до завершения фиксированного workload с правилом учёта вызванной миграции и её хвоста; использовать concurrent simulated completions, не сумму service times или wall-clock Python replay (C008–C010/S013; audit §§5–6).
Read/write mix, offered load, concurrency и окно одинаковы для X/Z; при ограниченном offered load потенциал throughput может быть скрыт. Измерять replay throughput или saturation capacity — отдельный выбор.
Затраты source read/destination write, mapping/GC/free space и inference включать в согласованный timeline; CPU/RAM, extra writes и WA/WAF показывать отдельно. Training budget отдельно от simulated service cost. Не подменять throughput WAF и не вычитать несопоставимые величины.

## Feasibility и выбор timing model
Проверено в исходнике: write allocation, l2p read path и существующие migration costs (C006–C009/S013). Не проверены работоспособность, correctness и пригодность dataset.
Serial model может дать лишь явно ограниченную последовательную диагностическую оценку после проверки completions/accounting; не доказательство parallel-throughput benefit (C010/S013).
Решение PENDING: существенно расширять существующую модель конкурентным временем/ресурсами либо выбрать другой simulator после отдельной проверки timing и интерфейса migration. Ни один альтернативный simulator сейчас не объявляется подходящим.
Расширение сохраняет знакомый scaffold, но требует собственной валидации и бюджета; другая модель требует аудита, интеграции и проверки переноса нагрузки. Обучение не устраняет timing gap.
Q-B/prefetch из v0.1 не выбран и не заменяет placement. Диагностика oracle возможна только отдельно: недостижимое знание будущего, не baseline/обучение/tuning; без оптимальности не строгая верхняя граница.

## Механизм, falsifiers и validity
INFERENCE: forecast → своевременная migration/layout → concurrent service → net read throughput. C005 остаётся гипотезой, не evidence. Ни co-location, ни spreading не гарантируют эффект.
Отказы: нет сигнала/drift/leakage; миграция опаздывает/дорога; нет совместно готовых чтений; shared resource/scheduler сериализует; GC/inference поглощают выигрыш. Нет полезного concurrent service или net gain — свидетельство против механизма в выбранных условиях.
Internal confounds: cache/warmup, occupancy/GC, scheduling, queue depth/load, extra writes, migration budget и predictor overhead; держать одинаковыми либо явно разделять ablations.
Construct: precision ≠ throughput, serial elapsed ≠ concurrent makespan; успешность/актуальность mapping обязательны. External: пределы dataset, модели и версии; реальный SSD эффект UNKNOWN.
Conclusion/leakage: кандидат независимой единицы — отдельная trace/workload с парным сравнением; запросы/окна зависимы, seeds не заменяют workloads. Test reuse запрещён; sample-size/power не обещаем, неточная оценка — неопределённость.

## Новизна и следующий milestone
По ограниченному поиску до 2026-09-30 novelty НЕ установлена: S005/S012 unresolved. C001/C004/S003 — условия/scheduling; C002/C003/S009/S010 — invalidation/write objectives. Различие целей не доказывает gap; S013 — аудит кода, не проверка новизны. Новых поисков здесь нет.
Рекомендуемый первый milestone: после разрешения доступа — dataset audit и проектирование learning task/features/splits, простых baselines и будущего протокола/бюджета; НЕ training. Это подготовка к условному C → A, не обещание feasibility.
До training нужны человеческое утверждение вопроса/плана и finite training/tuning budget; до throughput runs дополнительно — выбор и проверка concurrent timing model. Дизайн протокола предлагается как следующий этап, здесь протокол не создаётся.
Checkpoint: (1) путь/schema/units/timestamps/queues/license dataset; (2) deadline/hardware/budget; (3) audit+design сейчас и tentative migration, выбор timing route; (4) bytes/s или IOPS, load/concurrency, useful δ, action threshold/caps и cost horizon. Всё неуточнённое PENDING.

## История версии
v0.1 сохранена дословно в question-v0.1.md до ревизии. v0.2, 2026-09-30: latency-кандидат заменён throughput по уточнению пользователя ДО результатов; добавлены trained prediction и аудит S013, migration остаётся tentative. Это не retrospective rescue и не approval; v0.1 не утверждалась. Другие state/protocol/evidence файлы не изменены.
