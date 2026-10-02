# Synthetic practical runtime amendment v0.2
2026-10-02 · **PROSPECTIVE DRAFT / EXECUTION STOP** · Project: `/home/nomli/workspace/bdss_lab/research1`.
Все пути ниже относительно проекта. Единственная новая запись этого прохода — этот amendment; старые protocol/code/config/raw/state/claims сохранены без изменений.
Основание: `.research/README.md` decision о явном «согласен»; фактическая дата пользовательского approval practical mode — 2026-10-02 (дата записи README унаследована как 2026-10-01); brief; evidence-map C037; synthetic-temperature-demo-v0.1, preparation-approval, runtime-contract-v0.1, controlled-launch-v0.2; adapter fixes/review v0.2.
2026-10-02 · Дата заголовка исправлена ДО исполнения; caller scope — bootstrap-only, E004/E005 plumbing BLOCKED, implementation freeze pending. Это не passing/runnable claim и не execution approval.

## 1. Решение и prospective deviation
- **УЖЕ ПРИНЯТО человеком:** practical non-certified resource control для tiny synthetic illustration вместо strict whole-domain OS guarantees; численные targets и recipe сохранены.
- Rationale ДО любых данных: минимальный first-party caller без инфраструктурного framework; наблюдаемые worker расходы отделены от неизвестного control overhead. Это смена ресурсного режима, не спасение результата.
- **НЕ ПРИНЯТО:** точные bootstrap operations/argv, shell/import/compile/tests/probes/bootstrap/generation/fits/E004/E005; детальные предложения ниже остаются DRAFT до отдельного checkpoint.
- Этот новый versioned artifact сохраняет прежние версии и prospectively заменяет только их hard-containment/quota/complete-tail prerequisites для practical route; cgroup/quota/system facility больше НЕ prerequisites этого маршрута.
- Старый D-NATIVE с шестью OS reads не выбран и не разрешён. Hard closure/полная compliance не заявляются; R002 historical major **OPEN**, прошлый RAM не сертифицирован.

## 2. Неизменная научная задача и этапы
- Вопрос/C037: совпадает ли causal past→future READ pipeline с независимыми ручными/recipe ожиданиями и общими masks/keys на двух fixed artificial cases? Контрпример опровергает техническую гипотезу; обязательного X>Z/порога улучшения нет.
- Направленное ожидание engineered cycle и механизм past-count→next-state остаются предположениями конструкции, не evidence; H005/real predictability/layout/SSD throughput deferred, новых данных/источников нет.
- Recipe неизменен: 96×4KiB/6h, cycle+independent_negative seed42, history/H/step600s, labels0/1–2/≥3, прежние temporal splits/reset; Z,D,A,X custom CART depth3/minleaf50, tuning0.
- G1/E004 отдельно: два generated cases, trace-derived counter против independent recipe/manual fixtures, causal/split/shared-key/mutation checks; прежние 11 selected methods и **8 toy fits/0 benchmark fits**, не полный unittest/новый negative suite.
- G2/E005 отдельно после G1 review: **4 fixed benchmark fits**; ALL val+test predictions ОБОИХ cases durable committed перед ANY evaluation truth access. Статический порядок не dynamic proof; proof/receipts ещё pending.
- Units/analysis прежние: whole engineered case, не iid страницы/окна; описательные confusion/support/coverage/macro-F1/deltas, без p-values/power promises. Все valid negative outcomes сохраняются.

## 3. Один worker и честные границы измерения
- Runtime proposal: один stdlib Python caller+worker **в SAME process/thread**, последовательные invocations, no children; никаких новых threads/subprocess/watchdog/native build/supervisor. Existing tool-server/shell-control — не второй research worker и не бесплатно учтённый domain.
- Targets: cumulative active wall120s/CPU120s; worker RAM1GiB (1073741824 bytes); worker1/thread1/children0; ALL new disk5MiB (5242880 bytes). No network/install/GPU/paid/remote.
- Worker wall измерять `time.monotonic`, CPU — `time.process_time`; записывать initial/final counters, deltas и phase attribution. Первый clock начинает наблюдаемый interval: interpreter startup ДО него явно EXCLUDED/UNKNOWN, не silently zero.
- Initial process_time может включать preclock process CPU; сохранять значение/семантику, не терять и не double-count его. Ненаблюдаемые startup/exit/last-write CPU/wall/RAM остаются null/unknown.
- Tool elapsed где доступен — отдельное approximate operation observation с locator и границами; не складывать с вложенным worker wall. Совместный coverage возможен только при доказанных непересекающихся/покрывающих intervals; иначе non-combinable.
- Неизмеренные tool-server/shell-control overhead/startup/tool-tail CPU/wall/RAM отмечать `OVERHEAD_UNKNOWN`; это блокирует hard-compliance/full-COMPLETE claim, **не автоматически practical pilot**, если scoped permission и остальные practical STOP gates соблюдены.
- Предложение stop: main-thread soft `signal` alarm + cooperative wall/CPU checks на phase/loop/write boundaries; optionally existing tool timeout только после inspection его interface/scope. Scheduling/kernel I/O/termination latency не bounded; превышение возможно.
- RAM: bounded worker `resource.getrusage` и, если отдельно frozen/approved, scoped `/proc` observations; units/cadence/source записать. Это не whole-RAM guarantee; RLIMIT_AS НЕ RAM, арифметического proof нет; отсутствие telemetry раскрывать.

## 4. Накопительный бюджет, не reset на stage
- Один persistent worker-ledger: bootstrap + repeated startup + E004 + E005 + failure/finish/checks/receipts; каждый invocation читает прежний ledger, создаёт новый immutable linked snapshot. Missing/несогласованный ledger → STOP, не новый120s.
- Phase cumulative targets wall/CPU (s): inventory/startup15/15; E00435/35; E005 fits40/40 (**each10/10**); prediction/metrics15/15; finalization15/15. TOTAL120/120 имеет приоритет, failed attempts учитываются.
- До операции проверить phase/global remaining по наблюдаемому ledger и непотраченные termination/failure reserves; расходы одного interval не относить дважды к phases. Unknown overhead отдельно, remaining — только measured-worker estimate, не whole-domain остаток.
- Bootstrap использует **remaining inventory15/15**, не отдельные новые15s: proposed soft work target≤12s/12CPU-s и reserve≥3s/3CPU-s для finish/failure ВНУТРИ остатка; при меньшем остатке/нет резерва STOP до dispatch.
- Позднее G1/G2 явно резервируют termination/failure внутри своих phase/global targets и finalization15/15; точные stage reserves freeze ДО permission, не расходовать их на дополнительные fits/повторы.
- Human wait исключён только ПОСЛЕ worker return/exit и доступного tool return record; no live waiting worker. Ненаблюдаемый tail не становится нулём. Code-preparation wall не runtime execution, но её новые files входят в disk.

## 5. Disk: dynamic census и application guard, не quota certificate
- До будущего dispatch фиксировать path-scope/unchanged pre-CODEPREP baseline: только старые неизменённые artifacts исключены; новые additions к existing notes/state учитываются консервативно по declared snapshot/delta rule, UNKNOWN не baseline.
- Census охватывает все prepared sources/config/tests/snapshots/testplans/reviews/notes/protocols, caller, control/freeze receipts, raw/processed/failed/partials и новые state additions с начала CODEPREP; relocation не выводит из scope.
- Для каждого scoped file/dir bounded census записывает logical bytes, allocated bytes=`st_blocks*512`, тип/ссылки и metadata **estimate** с явным способом; hardlinks не double-count, symlink escapes/неясный scope → STOP до работы.
- Для logical И allocated отдельно проверять used+future-output/failure reserves+metadata estimate≤5MiB; это два сравнения, не два allowance. Динамический census перед/после stage/write batches + writer logical guard; materialized reserve не считать повторно.
- Metadata estimate очевидно НЕ certified bound; no quota/no hard metadata guarantee. Unmeasured metadata и persisted tool captures: scoped count/notes/locators и unknown flags, не full certification; stdout/stderr тоже bounded proposal, не невидимое исключение.
- Preflight footprint≥5MiB ИЛИ недостаточно reserves/невозможно bounded census → **STOP**. Все partials/failed/snapshots сохраняются; no delete/truncate/overwrite для budget, no automatic retry/расширение.

## 6. Точный будущий bootstrap-only checkpoint
- Caller `.research/experiments/scripts/synthetic_practical_caller_v0.1.py` — first-party FUTURE preparation/inspection; существование/работоспособность НЕ установлены. `/usr/bin/python3` existence/version тоже UNKNOWN; missing path → STOP, no autosubstitution.
- Ровно один proposed direct tool argv, не shell chain; сейчас НЕ выполнять:
```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_practical_caller_v0.1.py --stage bootstrap --approval-ref USER_BOOTSTRAP_PENDING
```
- `--approval-ref` — ссылка на отдельное решение, НЕ permission token; placeholder означает отсутствие permission. Реальная ссылка и окончательный argv предъявляются человеку перед единственным вызовом.
- Только stdlib/runtime version, own worker stats, bounded prepared logical/allocated census и scoped SHA256 files **как DATA, не executable load**; secret-free bounded repo text metadata при наличии, без git commands. No authfiles/secrets/env dumps.
- Exact allowlist/hash list freeze при caller inspection: caller/amendment/original protocols/config/adapter/core/tests/declared preparation inventory; no datasets/production/model-adapter loading/compile/import, no testing/generator/oracle/fixtures/fits. Stdlib imports внутри future caller — только после bootstrap permission.
- Единственная новая bootstrap control directory: `.research/experiments/control/synthetic-practical-v0.2/bootstrap-001/`, exclusive create; occupied → STOP. Только receipt/ledger/freeze/failure records, НЕ raw/E004/E005; сейчас directory/receipts не создавать.
- Proposed total normal bootstrap outputs≤64KiB + separately reserved failure slot≤8KiB (≤72KiB together), включая full hash/path list; заранее file-count/allocated/metadata/tool-capture reserves. Если полный список не помещается — STOP, не truncate/omit для успеха.
- Freeze payload: actual captured hashes/config bytes, command/approval refs, runtime/version/stdlib provenance, census scope, estimates/reserves, counters/clock boundaries, statuses/exit/primary+secondary errors, unknowns и amendment link; tail/tool record отдельно при наличии.

## 7. Freeze, failures, незавершённые решения
- Original config **UNCHANGED**, включая FIXED recipe/resources и null freeze fields; proposal freeze не actual runtime freeze. Новый отдельный receipt связывает amendment+original config/hash и approved practical interpretation, не silent hardcode override; incompatibility caller/adapter → STOP/checkpoint.
- Bootstrap не загружает adapter. До G1 нужен inspected captured-source caller binding adapter bytes к внешнему frozen SHA256; computational paths/code остаются прежними. R014 caller residual и R005 dynamic pending не закрыты этим текстом.
- Каждый output новый unique/exclusive/immutable, statuses scoped: `BOOTSTRAP_OBSERVED`, `LOCAL_WORKER_COMPLETE`, `FAILED`, `INCOMPLETE` плюс `OVERHEAD_UNKNOWN`; ни один не означает whole-domain COMPLETE/certification. Каждый failed attempt и primary/secondary error сохранять best-effort; write/crash failure → pointer/unknown, не обещание durable receipt.
- CPU/wall target exceeded, RAM concern, hash/scope/causal/schema/commit mismatch, insufficient reserves, missing records → STOP; no quality F1 для incomplete models. IDs E001/E002/E003 historical preserved; E004/E005 planned only, directories сейчас не создаются.
- Unresolved перед permission: exact caller operations/allowlist/stdlib policy, disk baseline/census/metadata estimate/file-count/reserves, remaining ledger, optional timeout/RAM cadence, output statuses/failure capture; unknown overhead раскрыть, не требовать OS certification для practical route.
- Любое позднее detailed numeric/scope alteration — новый dated versioned amendment+rationale и human checkpoint ДО новых runs; после результатов exploratory, не confirmatory. Local freeze НЕ public time-stamped registration.

## 8. Ограничения и рекомендация начинающему
- Internal: common-mode counters/CART bugs/leakage/non-sandbox callbacks; external: engineered cases не real workloads; construct: read counts≠SSD throughput/RSS≠whole RAM; conclusion: finite dependent fixtures и неполный overhead не доказывают correctness/efficacy/compliance.
- Уже известно только согласование практического режима и inspectable static preparation. Неизвестно, запустится ли caller и уложится ли работа; альтернативы — остановиться, либо подготовить/прочитать minimal caller без исполнения, затем отдельно разрешить bootstrap-only и review.
- **Рекомендация:** сначала caller preparation + static inspection и exact bounded bootstrap permission; затем STOP/review, отдельные G1 и G2. Этот проход: никаких shell/import/compile/tests/probes/bootstrap/generation/fits/network/agents; никаких результатов/финальных SSD выводов.
