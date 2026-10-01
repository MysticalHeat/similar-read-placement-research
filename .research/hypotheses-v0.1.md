# Гипотезы-кандидаты

Status: PROPOSED v0.1, 2026-09-30; human approval PENDING.
Нет подтверждённых, confirmatory или preregistered гипотез, E-ID или результатов. Кандидаты для Q-C/Q-A; при выборе Q-B потребуется отдельная формулировка. Ни один H-ID не утверждён.

## Общие условия
Traces/workloads/model UNKNOWN; кандидат независимой единицы — отдельная trace/workload, не запрос или окно. k/горизонт/метрики/budgets/практические δ/splits PENDING. Временной split, tuning на validation, online-прогноз только по прошлому; oracle изолирован для диагностики, не test-lookahead baseline. C005 — замысел, не evidence ожидаемого выигрыша. Точная поддержка и пределы источников — question.md и claims/citation-audit.md. Правдоподобие механизма не доказательство; недостаточная точность оценки оставляет неопределённость, non-significance не опровергает практически полезный эффект.

## H001 — полезная предсказуемость (Q-C)
Status: PROPOSED v0.1; approval PENDING.
Гипотеза: на временно отложенных traces causal predictor даёт преимущество ΔP > δP над лучшим простым causal baseline, выбранным на validation, при одинаковых k/горизонте и ресурсных пределах.
Outcome/estimand: разность выбранной prediction metric по workloads; кандидат precision@k с согласованными coverage/timeliness. Без timestamps вывод только об адресном прогнозе.
Null: ΔP ≤ δP либо преимущество нарушает coverage/timeliness/budgets. Prediction: больше полезных правильных прогнозов при сопоставимом объёме прогнозирования. Величина UNKNOWN.
Mechanism (INFERENCE): повторяющиеся переходы могут содержать сигнал; наличие UNKNOWN. C005 мотивирует проверку; S007/S008 context-only abstracts не поддерживают предсказуемость нашей нагрузки.
Falsifier: достаточно точная held-out оценка исключает преимущество > δP либо преимущество исчезает после устранения future leakage. Неточная оценка не даёт определённого вывода.
Alternatives/controls: sequential pattern, memorization и большой k; sequential/frequency/transition baselines, равные budgets и temporal splits.
Decision needed: данные/features, k/горизонт, метрика/δP, coverage/timeliness/splits. H001 не доказывает ускорение чтения.

## H002 — layout создаёт полезный параллелизм (Q-A)
Status: PROPOSED v0.1; approval PENDING.
Гипотеза: при одинаковых causal прогнозах, scheduler/cache/resources и фактически готовых demand-запросах placement снижает выбранную модельную service/queue latency более δlayout относительно обычного layout через увеличение допустимого совместного обслуживания.
Outcome/estimand: парный выигрыш latency по workloads и наблюдаемое concurrent service; механизм, ещё не полный net-cost эффект.
Null: gain ≤ δlayout либо нет увеличения совместного обслуживания, необходимого для заявленного механизма. Prediction: меньше конфликтов, больше допустимого перекрытия и меньше latency; величина UNKNOWN.
Mechanism (INFERENCE): подходящее размещение может позволить параллельную службу готовых запросов. C001/C004, S003 §§2.2/4.2 поддерживают значение пространственно-временных условий той архитектуры, не наш эффект. Доступ к layout/concurrency UNKNOWN.
Falsifier: нет изменения concurrent service; достаточно точная оценка исключает полезный gain; результат требует ранней подачи будущих demand-запросов или изменения cache/scheduler. Latency gain без concurrent service допускает иной механизм, не подтверждает заявленный.
Alternatives/controls: batching, queue depth/cache/scheduler/непрогнозная группировка; тот же forecast без layout, группировка без forecast, равные arrivals. Не создавать готовность зависимых запросов искусственно.
Decision needed: page/writing point/resources/commands, первоначальная запись или перенос, concurrency, metric/δlayout/наблюдаемость. Oracle не подтверждает H002.

## H003 — end-to-end выигрыш после затрат (Q-A)
Status: PROPOSED v0.1; approval PENDING.
Гипотеза: полный causal forecast+layout даёт практически полезный выигрыш G > δL против настроенного обычного baseline по выбранной demand-read metric при correctness и согласованных cost caps.
Outcome/estimand: кандидат mean latency, G=(Lbaseline−Lmethod)/Lbaseline при Lbaseline>0; метрика, δL и caps не утверждены.
Null: G ≤ δL либо нарушены пределы extra writes/WA/CPU/RAM/correctness. Prediction: выигрыш сохраняется с затратами predictor/переноса/конкурирующих записей/GC; величина UNKNOWN.
Mechanism (INFERENCE): экономия concurrent service может превысить overhead. C005 — исходная гипотеза; C001/C004 — условия; C002/S009 и C003/S010 мотивируют контроль write costs, их результаты не переносим на reads.
Falsifier: достаточно точная оценка исключает useful gain; включение затрат убирает выигрыш; превышен cap либо чтения не возвращают актуальные данные. Accuracy/oracle сами H003 не подтверждают.
Alternatives/controls: cache state, меньшая нагрузка/пропуски, tuning inequality, отсутствие GC/warmup, удобный горизонт; равные validation budgets/arrivals, контроль cache/scheduler, correctness и полный учёт операций.
Decision needed: workload/read-write mix, metric/δL/cost caps, горизонт амортизации, units/precision. Если initial placement/migration исключены, ограничить вывод steady-state. Model success не доказывает real SSD success.

## История и gate
v0.1 2026-09-30: кандидаты методолога до результатов, сохранены оркестратором после отказа записи инструмента. Предыдущих содержательных гипотез нет. Сохранять версии и rationale до новых runs; outcome-driven изменения не confirmatory. Публичной регистрации нет. Условная рекомендация C → A не разрешает запуск. Уточнить S005/S012 до заявления novelty. Approval PENDING.
