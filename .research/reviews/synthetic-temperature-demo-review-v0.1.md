# Независимая design review synthetic-temperature-demo v0.1
Дата: 2026-10-01. Один локальный проход; подготовительный дизайн, не результаты/approval.
`plan:L…` = `.research/protocol/synthetic-temperature-demo-v0.1.md`; все пути ниже относительно `.research/`.

## Scope: проверено / недоступно
- Прочитаны все 76 строк plan, README/brief с последним выбором «давай», question.md, data-route-options-v0.1.md, temperature-poc-checkpoint-2026-10-01.md, evidence-map, papers.jsonl, temperature-poc review и SPC audit R002/R003.
- Осмотрены raw/ (только E001), E001/manifest.json, analysis/analysis.md, writing/draft.md и peer-review.md. Анализ/драфт/текущий общий review — шаблоны; синтетических таблиц, кода/config, E004/E005 и runtime measurements нет.
- Первичная опора нынешних численных утверждений — сам рецепт plan:L14–29; арифметика ниже сверена вручную. E001 manifest прочитан как запись, не повторный профиль/hash/resource audit. Первичные S013/S018 и литература заново не проверялись; их записи не выдаются за independent claim verification этого прохода.
- Нет web/source retrieval, shell, запуска, генерации, fit, installs, делегации или reanalysis. Записан только этот новый review; прежние документы/state/claims/raw не изменены.

## Суждение о готовности
**Достаточно для checkpoint подготовки кода и статической схемы лимитов; НЕ runnable.** Нового major-дефекта метода этим проходом не установлено; два вопроса реализации/accounting ниже открыты. No finding не устанавливает validity.
Review не о недостатке пользовательского согласия: Route A уже выбран для плана. Метод ограничен проверкой искусственного pipeline, а не H005/C017 или практической полезности.

## Проверки метода и арифметики
- Causal access (L26–33): past `<t`, future `[t,t+600)`, writes не дают READ-label; U строится после reset, а не из будущих readers. Cold/write-only сохраняются registration. Grid даёт train t=600..10200, val12600..15000, test17400..21000: 17/5/7 решений, 1632/480/672 examples/case; windows полны и не пересекают split/gap boundaries.
- Reset обнуляет историю, но НЕ обученные веса (L28,50–51); это намеренный сегментный cold-start, не непрерывное deployment. Gap-generated события должны отсутствовать во входе counting сегмента, а не только в итоговых metrics.
- Bound L22 верен: 96×36×4+3×96=14112/case; 28224+100=28324<30000. Для cycle рецепт задаёт ровно 32 страницы каждого состояния/bin: 36×32×(0+1+4)+288=6048 events. Это ожидание, НЕ run count; negative count остаётся неизвестным.
- При полной U cycle даёт ожидаемые supports каждого класса 544/160/224 для train/val/test. Эти числа можно использовать как invariants, не как основание менять дизайн или обещать измеренную точность.
- Fixtures L36–43 согласованы с границами: R300 включён в последние300s Fties, R600 только future, R1200 исключён; overlap4095/size2 добавляет по одному incidence двум pages. Funseen/U-at-t/censor/mutation/reset различают ошибки eligibility, leakage и censor-as-cold. Совпадающие tuples с разными IDs не должны дедуплицироваться.
- Модель/генератор (L23,32,43,50): запреты recipe/phase/time features, independent counter и future-mutation checks уместны. Изоляция model state от generator/expectation/test labels ещё не проверена кодом; одни декларации запрета её не доказывают.
- CART L48–50 задаёт точные Gini/midpoints/ties/depth/minleaf; четыре benchmark fits без tuning разумно конечны. Toy проверки CART — отдельные tests, не дополнительные benchmark/quality trials. Fraction-сортировка/сканирование могут быть дороже простого tree; 10s/fit неизвестны без реализации, не доказаны малым n.
- Baseline специально anti-persistent: cycle отображает прошлый count 0→warm, 1→hot, 4→cold. A может выразить это двумя count splits с leaf544 и depth≤2; X не обязан дать дополнительный сигнал. Z не «сильный» empirical comparator, но это честно раскрыто в L8–9,58 и допустимо для иллюстрации.
- Negative не гарантирует Δ=0: finite seed/зависимые windows могут дать случайную корреляцию. L8,56–57 корректно сохраняют любые quality outcomes, запрещают regeneration и не используют страницы/решения как iid replicas, p-values или power.
- Metrics/support/NA/strata/coverage и cases separately (L54–59) ограничивают cherry-picking и unseen optimism. Fixed-class F1 может быть низким при absent class; это не implementation failure. Качество val не даёт права менять frozen fit/test.
- Новизна не заявлена (L11); bounded поиск не comprehensive. Synthetic issuance counts≠completed reads/co-access/throughput; engineered phases и 96 pages не представляют реальные workloads. Никакой вывод о model quality, SSD novelty или реальных чтениях не следует.

## Findings — только новые вопросы
### R004 — question: точная граница runtime/accounting пока неоднозначна
- Location: plan:L62–65,69–74. Observation: общий startup-through-cleanup120s/120CPU-s/5MiB, два отдельных E-stage с человеческим G2 и «1 Python process/no children» должны сосуществовать с launcher/watchdog/systemd и включённым overhead; L65 дополнительно пишет «1process». Проверенного wrapper/bootstrap нет, availability UNKNOWN прямо признана.
- Evidence/criterion: subcaps15+35+40+15+15=120 арифметически верны, но не определяют суммирование двух startup/cleanup, ожидания G2, supervisor processes и bytes/allocated-disk scope. Cgroup existence не доказывает доступную delegation или заранее установленную containment.
- Consequence: нельзя из этих чисел получить исполнимый cap/accounting contract; возможен конфликт процессного лимита с enforcement. Это unresolved readiness question, не наблюдённое превышение и не новый major.
- Requested action via orchestrator: до G1 зафиксировать bounded accounting domain и total ledger E004+E005 (включая повторный startup/checks/cleanup), правило wall при ожидании G2, процессный scope launcher/watchdog и disk measure/reserve. Указать, что можно установить статически, а какой минимальный bootstrap потребует отдельного разрешения и containment до startup; если scope нельзя обеспечить — STOP, не автоматическое расширение caps.
- Confidence: высокая в неоднозначности/отсутствии wrapper, неизвестна feasibility. Status: open; plan уже требует STOP при невозможности containment.
### R005 — question: операционный критерий независимости label check
- Location: plan:L23,43,56,58,71. Observation: обещаны independent READ counter и recipe expectation table, но ещё не определено, какие counting/overlap/window/reset routines им разрешено разделять. Реального ошибочного reuse не наблюдается.
- Evidence/criterion: два выхода из одной ошибочной counting routine могут согласоваться; recipe agreement и fixtures тогда не независимая защита common-mode bugs.
- Consequence: «exact counts passed» без inspection разделения не удостоверит заявленную техническую проверку pipeline.
- Requested action via orchestrator: в статическом code review проследить отдельный trace-derived counter и expectation path, без общих label/window/reset вычислений; fit получает только разрешённые train features/labels, не recipe/test expectation. До fit сверить per-page/bin и decision-level labels с ручными fixtures; после fit mutation меняет только future data и не refits/state. Сохранить check artifacts и inspected code hashes в E004/E005.
- Confidence: высокая в необходимости различить paths; actual independence UNKNOWN. Status: open, разрешается спецификацией/инспекцией, не требованием нового workload.

## Контраргумент и минимальная различающая проверка
Сильнейшее альтернативное объяснение любого cycle X>Z — обучение обратной эвристике частоты, заранее встроенной в рецепт, а не полезность дополнительных features. Уже запланированные A−Z и X−A на общих keys вместе с tree splits/confusions различают это объяснение; X≈A не дефект, а ожидаемое ограничение. Negative и mutation проверяют другие угрозы, но не внешнюю переносимость. Просьба только через оркестратора после отдельного разрешения; сейчас reanalysis нет и не требуется.

## Handoff / изменения / checkpoint
- **Обязательных количественных изменений не выявлено:** 4KiB/600s/labels, 96pages/36bins, splits, depth3/minleaf50, seed42, четыре fits и caps не нужно менять по этой review. Требуются уточнения R004/R005, не повышение бюджета; никаких измеренных runtime/disk обещаний.
- **Опциональное упрощение:** generator+fixtures без обучения уменьшит implementation cost; custom exact CART — дополнительный проверяемый код ради демонстрации, не научная необходимость. Это отдельная versioned scope choice до outcomes, не замена/fallback без согласования; A полезен против threshold explanation, удалять его ради красивого X>Z нельзя.
- **Исторический R002 major OPEN:** SPC audit:L20–26; plan:L64 его сохраняет. Tiny fixtures/будущий compliant run не ретроспективный сертификат прошлого RAM. R003 OPEN только в прежнем SPC scope (audit:L28–34); synthetic recipe не решает blocksize/capture compatibility.
- IDs: SYN001 предложен, E004/E005 planned, не evidence; C017/H005 deferred/UNVERIFIED. S013/C010, S018/R003 и E001/C014 — контекст из локальных записей, не новая source/result verification. Остаточные риски: common-mode bugs, finite PRNG correlations, engineered baseline disadvantage, implementation/runtime/bootstrap неизвестность и отсутствие external/SSD validity.
- Осторожный checkpoint: «Принимаем recipe/четыре fixed fits и предлагаемые caps для подготовки кода/config и независимой статической проверки схемы лимитов БЕЗ исполнения? Если выбран fixture-only вариант — сначала новая версия. Availability/bootstrap сейчас неизвестны; запуск проверки окружения, затем E004 и E005 требуют отдельных scoped разрешений и артефактных gates». Это не approval и не обещание runnable readiness.
STOP после одного прохода; дальнейших действий нет.
