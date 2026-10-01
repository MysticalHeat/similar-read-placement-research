# Гипотезы-кандидаты

Status: PROPOSED / candidate v0.2, 2026-09-30; approval каждого H-ID PENDING.
Нет confirmatory/preregistered гипотез, обучения, E-ID или результатов. Вопрос и бюджет не утверждены.

## Общие условия и evidence
Популяция — согласуемые traces/workloads и timing model; dataset сообщён, но путь/schema/units UNKNOWN. Кандидат независимой единицы — trace/workload, не запрос/окно; seeds не заменяют независимые workloads.
k/горизонт/features/метрики/практические δ/action threshold/caps/splits/budgets PENDING. Temporal train/validation/test, tuning на validation, causal inference/online adaptation только по прошлому. Oracle изолирован: diagnostic only, не deployable/test-lookahead baseline.
C005 — непроверенная идея. C006–C007/S013 (MiDaFTL.py L19,21–28,58–72,78): write allocation и read l2p разные; next-read target не writing pointer. C008/S013 (Statistics.py L111–124; FTL.py L36–100) — serial elapsed; C009/S013 (FTL.py L63–67,36–48) — учёт существующего migration read+write; C010/S013 (audit §§4–6) — parallel-throughput требует concurrent timing model.
S013 commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21, static audit 2026-09-30 без исполнения. Поддержка/URLs: claims/evidence-map.md, claims/citation-audit.md, experiments/simulator-audit.md. Это не evidence нашего эффекта или physical validation.

## H001 — learned prediction против простого causal baseline (Q-C)
Status: PROPOSED v0.2; approval PENDING.
Гипотеза: trained predictor X даёт ΔP > δP на temporal held-out workloads против лучшего простого causal Z, выбранного на validation, при одинаковых k/горизонте/features и сопоставимых tuning/resource budgets.
Outcome/estimand: разность выбранной prediction metric по workloads; кандидат precision@k с coverage, timeliness отдельно. Без timestamps вывод только об адресном прогнозе.
Null: ΔP ≤ δP либо преимущество нарушает budgets/coverage/timeliness. Prediction: больше полезных правильных прогнозов, эффект UNKNOWN.
Mechanism (INFERENCE): обучение может извлечь повторяющиеся паттерны; наличие сигнала UNKNOWN. C005 — мотивация, S007/S008 — context-only abstracts, не поддержка результата.
Falsifier: достаточно точная held-out оценка исключает useful gain либо выигрыш исчезает без leakage. Неточная оценка оставляет неопределённость.
Rivals/controls: sequentiality, memorization, большой k; sequential/frequency/transition baselines, временные splits и равные ограничения. Decision: dataset/task/page/queue target, δP, budget и split approval; H001 не доказывает throughput.

## H002 — layout и concurrent service (Q-A)
Status: PROPOSED v0.2; approval PENDING; текущая serial model этот механизм не тестирует (C010/S013).
Гипотеза: при одинаковых causal forecasts, scheduler/cache/resources и фактически готовых demand-запросах tentative placement/migration увеличивает допустимое перекрытие обслуживания на независимых ресурсах и снижает выбранную service/queue latency более δlayout против обычного layout.
Outcome/estimand: парная разница concurrent-service measure и latency по workloads; это механизм, не полный net throughput. Конкретные меры/δlayout PENDING.
Null: нет нужного увеличения concurrent service либо latency gain ≤ δlayout. Prediction: меньше конфликтов/больше допустимого overlap; величина UNKNOWN.
Mechanism (INFERENCE): прогнозный layout может согласовать физические и временные условия; C001/C004/S003 §§2.2,4.2 поддерживают лишь условия той архитектуры, не наш эффект.
Falsifier: нет overlap; useful gain исключён достаточно точной оценкой; результат требует ранней подачи будущих demands/другого scheduler/cache. Serial service-cost improvement — другой механизм, не доказательство H002.
Rivals/controls: batching, queue depth, cache, scheduler, непрогнозная миграция; одинаковые arrivals и action caps, тот же predictor без миграции, простая policy. Decision: timing route/validation, tentative migration, ресурсы/команды, concurrency/метрики; oracle не подтверждает H002.

## H003 — net end-to-end read throughput (Q-A)
Status: PROPOSED v0.2; approval PENDING; throughput заменяет latency-кандидат до результатов.
Гипотеза: полный causal trained forecast + tentative migration даёт G_T > δT против настроенного обычного Z при фиксированном workload/concurrency, корректных завершениях и согласованных cost caps.
Outcome/estimand: парный throughput gain G_T=(T_X−T_Z)/T_Z при T_Z>0. T = useful bytes либо исходные успешно завершённые demand-read requests / simulated completion makespan(s); primary unit PENDING.
Makespan требует concurrent timeline (C008–C010/S013), общего окна и правила учёта tail migration. Internal reads/copies не входят в числитель; skips не completions (C007/S013; audit §§4,6). Не использовать wall-clock replay или WAF вместо read throughput.
Null: G_T ≤ δT либо нарушены completeness/correctness или caps. Prediction: throughput gain сохраняется с inference/source read/destination write/GC и конкуренцией; размер UNKNOWN.
Mechanism (INFERENCE): выгода concurrent service может превысить затраты. C005 — предположение; C009/S013 поддерживает лишь существующий read+write accounting, не полный overhead будущего метода. C002/C003 мотивируют write-cost контроль, не доказывают read gain.
Falsifier: достаточно точная оценка исключает useful gain; полный учёт затрат убирает выигрыш; превышены caps или возвращаются неактуальные данные. Precision/oracle сами не подтверждают H003.
Rivals/controls: cache, меньше выполненных запросов, иной load/queue depth, неравный tuning, отброшенный migration tail; одинаковые workload/arrivals/scheduler, validation budgets, correctness и полный agreed cost horizon.
Decision: timing model/validation, bytes/s или IOPS, replay load либо saturation, δT/action threshold/caps, units/precision и budget. Training cost отдельно; model result не доказывает real SSD benefit.

## Версии и checkpoint
v0.1 дословно сохранена в hypotheses-v0.1.md до ревизии; H-ID сохранены. v0.2: H001 уточнена как learned vs simple causal; H002 сохраняет concurrent-service conditions; H003 latency-кандидат заменён throughput по предпочтению пользователя ДО результатов. v0.1 — историческая, не утверждённая версия; это не retrospective rescue.
Первый предлагаемый milestone — dataset audit + learning-task/split/protocol design, НЕ training. Нужны scope/access approval, затем протокол и finite budget; timing extension/replacement требует отдельного решения. Публичной регистрации нет; power не гарантируем, non-significance не равно falsification. Новизна unresolved S005/S012; никаких runs или approvals от имени пользователя.
