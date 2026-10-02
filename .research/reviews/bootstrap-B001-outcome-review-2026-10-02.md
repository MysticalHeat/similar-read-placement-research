# Независимый bounded review исхода B001 — 2026-10-02
## Scope / источники
Только локальное чтение и этот NEW review; никаких execution/probes/import/compile/tests/gen/fits/network/agents или code fixes. Старые reviews/state/raw сохранены.
Locators относительно `.research/`: O=claims/bootstrap-B001-outcome-2026-10-02.md; P=experiments/scripts/synthetic_practical_caller_v0.1.py; A=protocol/synthetic-practical-runtime-amendment-v0.2.md.
Прочитаны O25/P397/A72, caller notes69/fixes42 и независимый fixes-review37; README/brief/question/hypotheses, оба relevant protocol, evidence-map C037, literature catalog/search-log, analysis/draft, historical R002 review и raw/E001/manifest.json.
Независимые native directory reads: experiments/control — File not found; experiments/raw — только E001. Нет доступных freeze/receipt/ledger/failure B001 или E004/E005 tables для проверки.
Проверены primary stdout, predicates/order в текущем source и локальный E001 manifest; hashes/runtime identity не пересчитаны, совпадение текущего P с исполненными bytes не удостоверено freeze.
Analysis — EMPTY, draft — OUTLINE ONLY. Литературные metadata не support verification; внешние primary papers здесь не перепроверялись и для объяснения отказа не используются.
## Наблюдение и точный code proof
O13–15: RuntimeError `worker RSS concern`, created=[], owned_directory=null, outputs={}, durable_failure_pointer=null, secondary=null, local_return_intended=2.
O16: отдельные OS exit, elapsed/CPU, timestamps и численный ru_maxrss tool не экспортировал; intended2 ≠ independently observed OS exit2, UNKNOWN ≠ zero.
P74–85: sample берёт SELF ru_maxrss×1024; check требует peak<1073741824 bytes. При соответствии P исполненному коду сообщение означает ложность именно этого strict predicate: sample peak≥1GiB, не опубликованное точное значение.
Первый guard расположен ДО mkdir и scoped hashing: main P331–334 → writer.space P217–218 → census P176–178 → add P142–144 → budget.check P80–85. Самый первый add('.') проверяет бюджет даже ДО своего checked(path).
Следовательно, этот failure path останавливает initial space до writer.create P334/mkdir P241, второго census P335 и hash loop P339–343; предварительные path checks P328–330 уже предшествуют ему.
P372–382 пишет failure.json лишь при writer.owned; здесь ownership не возникло. Отсутствие durable failure при этом исходе согласуется с best-effort contract, не новая доказанная reporting defect.
Это code-supported реконструкция порядка, не runtime trace; импорты stdlib/caller были выполнены по record O25, но hashlib import не означает hashing prepared files.
## Допустимая интерпретация / scientific claims
Поддержан один bootstrap STOP по peak-threshold guard. Не поддержаны actual current RAM, OOM, memory leak, причина peak, whole-domain compliance или actual budget violation.
Не экспортированы runtime version/stdlib origins, captured hashes, census totals и usage values: запланированные поля P348–370 не являются измеренными metadata B001; E001 environment нельзя переносить на B001.
C037 UNVERIFIED: computational modules/tests/generator/fits не выполнялись; B001 не проверяет causal labels/masks/CART/model quality. Bootstrap failure ≠ computational pipeline failure и не опровержение C037/H005.
Нет новых efficacy/novelty/baseline/statistical результатов для аудита; зависимые страницы/окна и engineered cycle не дают generalization. Отрицательный operational исход сохраняется, не исключается ради успешного запуска.
## Findings / residual status
Нового подтверждённого defect/question сверх уже disclosed UNKNOWN telemetry не установлено; новые R-ID не присваиваются. Это не validation и не закрытие dynamic checks R018/R019.
R002 historical major остаётся OPEN: его прошлый peak не ретродиагностирует B001 и наоборот; accepted practical mode A8–12/28–30 не требует cgroup/hard accounting framework.
Основной blocker — неизвестный расход failed B001 и отсутствующий ledger (A32–38/65), НЕ доказанное превышение actual RAM. B001 spent: no autoretry, no fresh15/120 или фиктивного remaining105s.
Residual integration: README3–5/85 и evidence-map C037 сохраняют pre-attempt wording; O — более поздний outcome. Через orchestrator обновить только status/provenance, не scientific evidence или approval scope.
## Сильнейший контраргумент / различающий diagnostic design
Контраргумент к «bootstrap действительно использовал ≥1GiB текущей RAM»: high-water statistic может отражать более раннюю историю, не contemporaneous working set. Inherited pre-exec peak — лишь HYPOTHESIS, не наблюдённая причина; genuine high current RSS также не исключён.
Минимальный различающий follow-up: в одном будущeм worker сохранить earliest reported SELF ru_maxrss и близкий по времени current VmRSS из bounded `/proc/self/status`, затем pre-guard пару; указать units/source/sample boundaries, missing/parse failure как UNKNOWN.
Низкий current VmRSS при высоком peak различит current/high-water показатели, но НЕ установит происхождение peak и НЕ разрешит проигнорировать1GiB guard; высокий current также не докажет OOM. Диагностика не восстановит численный sample B001.
## Следующий human checkpoint — proposal only, STOP
Известно: один разрешённый B001 потрачен, peak predicate STOP до mkdir/hash; неизвестны exact peak/current RSS, cause, runtime provenance и failed-attempt costs/остаток.
Выбор: остановиться; либо разрешить подготовку ОДНОЙ малой versioned memory-measurement correction proposal с immutable предыдущей версией, без изменения recipe/targets и без исполнения.
Рекомендован второй выбор: earliest/pre-guard telemetry сохранять даже при preownership failure в bounded outcome; guard/STOP оставить, semantic change только отдельным rationale+approval. Никаких code edits этим review.
После static inspection — ОТДЕЛЬНОЕ разрешение одного bounded diagnostic-only вызова, НЕ повтор B001/ bootstrap/tests/G1/G2: заранее exact scope/argv, time/CPU/disk/output reserves, explicit failed-cost accounting treatment и сохранение UNKNOWN overhead.
Нельзя молча reset15/120 из-за отсутствия measurements: существующие costs восстанавливать только из доступных records, иначе отдельно согласовать versioned accounting treatment до dispatch; не выдумывать нули или остатки.
Required reanalysis сейчас NONE: нет numerical B001 samples или classifier tables для перерасчёта. Запрос через orchestrator — только указанная preparation и будущая отдельная diagnostic approval; команда здесь не выдаётся/не выполняется.
Residual risks: unbound runtime bytes, неизвестные sample/tail/control costs и disk footprint (новый review тоже в5MiB scope), race/durability и dynamic correctness не проверены; no finding не устанавливает validity.
