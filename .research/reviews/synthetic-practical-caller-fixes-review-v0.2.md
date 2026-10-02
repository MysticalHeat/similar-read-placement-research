# STATIC practical caller fixes review v0.2
2026-10-02 · Один узкий follow-up R018/R019 · EXECUTION STOP.
**Gate: READY_FOR_SEPARATE_BOOTSTRAP_PERMISSION**, НЕ execution approval, passing tests или certification.
Locators относительно `.research/`: P=experiments/scripts/synthetic_practical_caller_v0.1.py; V=experiments/scripts/synthetic_preparation_versions/caller-v0.1/synthetic_practical_caller_v0.1.py.
F=experiments/synthetic-practical-caller-fixes-v0.2.md; R=reviews/synthetic-practical-caller-review-v0.1.md.

## Checked / unavailable
- Полностью прочитаны P397/V348/F42/R55; сопоставлены изменённые predicates, capture/reporting call sites и прежние counterexamples. Snapshot сохраняет прежние defects; byte hash/identity не вычислялись.
- Проверка первичного source code, не принятие author closure F. Core/adapter/method/литература/старые resource findings заново не аудировались; scope прежнего review не расширяется.
- Никаких execution/shell/import/compile/tests/probes/network/agents/gen/fits. Единственная запись — этот NEW review; старые reviews/code/config/protocol/state/raw не меняются.
- Syntax/importability, реальное дерево/счётчики/footprint/hashes, exit/stdout delivery/durability/ресурсы динамически UNVERIFIED. Ни нового S-ID/E-ID, ни результатов C037 нет.

## R018 — minor: STATIC FIXED; dynamic UNVERIFIED
- V103–119/140–146/192/236–237/279–280 заменены P104–121/142–146/190–195/236–240/328–330. Удалены явные parent.exists/follow-first exists/is_dir predicates; census root больше не делает stat PROJECT.parent.
- P106 отвергает outside PROJECT и lexical `..`; root lstat P107–110 вне missing-handler: root missing/non-directory/symlink STOP даже при missing=True. Below-root ancestors обходятся от старшего к leaf, каждый через lstat.
- P113–120 возвращает None при первом отсутствующем below-root intermediate/leaf, но отвергает существующий symlink и non-directory intermediate ДО следующего компонента. Для missing=False отсутствие по-прежнему STOP.
- Existing CONTROL допускается лишь directory (P328–329/236–239); absent CONTROL и absent PRACTICAL обрабатываются checked, occupied/partial PRACTICAL STOP (P330). Census190–195 проверяет directory base до scandir, existing matching control descendants остаются recursive P162–164/187–195.
- Последствие: прежние extra-scope explicit stat/missing-chain counterexamples устранены статически. Confidence высокая по predicate/order; дополнительная correction R018 не требуется. Это не OS sandbox/защита от concurrent rename/symlink races или сертификат внешних ancestors runtime.

## R019 — major: STATIC FIXED; dynamic UNVERIFIED
- V322–343 заменены P268–313/372–393. Main явно задаёт code=2 при primary; error_record сохраняет полный reason либо explicit UNAVAILABLE при сбое str(error), не бросая обычный conversion error наружу.
- P281–303 ограничивает preview64/type24 с omission flags и проверяет фактические encoded bytes≤2048 ВНУТРИ formatter handler. Overflow выбирает fixed-field/path fallback с bounded types: максимум2×24×12=576 escaped type bytes плюс фиксированные ASCII поля/пути; fallback также проверен guard.
- P304–310 ловит formatter/cap exception, задаёт nonzero и fixed emergency literal<256bytes с UNKNOWN pointer. Прежний secondary cap raise больше не выходит как traceback; ни cap, ни reserve не расширен. Это source arithmetic, не выполненный encoding test.
- P311–313 делает ровно ОДИН os.write, без flush/retry/stderr fallback: short write/error →return2, не silent success. Доставленный summary может содержать прежний intended0 ДО ошибки доставки: фактический tool exit/return record обязателен, intended status сам по себе недостаточен.
- P383–392 защищает alarm cancellation; ending failure делает code2 и не заменяет existing primary. P377 использует прежний absolute15s, не renew; reporting остаётся после наблюдаемого pre-exit ledger, tail UNKNOWN.
- Полные details только best-effort failure slot8KiB (P252/378–382; F20–23): oversize/I/O/crash →durable detail может отсутствовать; secondary не дописывается, summary лишь preview/type. Pointer выдаётся только из writer.outputs (P280/291), иначе UNKNOWN; emergency/delivery failure тоже UNKNOWN.
- Последствие: конкретный oversized escaped summary больше не создаёт необработанный cap exception. Confidence высокая по handler/return flow; дополнительная correction R019 не требуется. Память/фатальный crash/actual delivery не гарантированы.

## Exact candidate / future scope / residual handoff
```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_practical_caller_v0.1.py --stage bootstrap --approval-ref B001
```
- Один будущий direct tool argv, proposed tool timeout **15000ms, best effort**, не hard termination guarantee. B001 — будущее отдельное датированное human decision, сейчас PENDING; reference не security token. Missing executable STOP/no fallback (P326–327), existence UNKNOWN; placeholder reject ДО Writer (P320–331).
- P325 блокирует E004/E005; P339–345 hash/read prepared code как DATA, не computational load/compile/import/gen/fit. Один stdlib worker; новых children/threads/network paths нет. R014 actual adapter-caller provenance OPEN для E004, не требование исполнения adapter в bootstrap.
- Только future control mkdir при необходимости и exclusive `experiments/control/synthetic-practical-v0.2/bootstrap-001/`; freeze/receipt/ledger + best-effort failure (P233–264/356–380). No raw/E004/E005/processed writes; no retry/delete/overwrite. Normal64KiB+failure8KiB/stdout2KiB входят в5MiB estimates (P35–37/217–231), footprint/tool capture UNKNOWN.
- R002 historical major OPEN; прежние hard-guarantee findings НЕ certified/closed. Принятый practical route не требует cgroup/quota certificate; CPU/wall/RSS/disk targets и неизвестный overhead не превращаются в whole-domain compliance. R004 partial/R005 dynamic pending/C037 UNVERIFIED сохраняются.
- Сильнейший residual counterargument: bounded branches не доказывают actual syscall delivery/durability или race safety. Различающий check — отдельно разрешённые narrow failure-path observations с immutable receipts/tool exit, не автоматические тесты под B001. Required reanalysis NONE; через orchestrator предъявить exact B001 permission, затем один bootstrap и STOP/review; G1/G2 отдельно. No finding не устанавливает validity.
