# Узкий STATIC follow-up adapter fixes v0.2
2026-10-01 · Один проход R014–R017 · Preparation only / EXECUTION STOP.
Locators относительно `.research/`: B=experiments/scripts/synthetic_stage_adapter_v0.1.py; U=experiments/scripts/test_synthetic_stage_adapter_v0.1.py; F=experiments/synthetic-stage-adapter-fixes-v0.2.md.
V=experiments/scripts/synthetic_preparation_versions/adapter-v0.1/synthetic_stage_adapter_v0.1.py; R=reviews/synthetic-stage-adapter-review-v0.1.md.

## Scope / что проверено и что нет
- Полностью прочитаны B483/U223/F68/V425/R64; сопоставлены touched predicates/call sites с V и критериями R014–R017. Snapshot сохраняет прежние дефектные predicates; полная byte identity/checksum не вычислялась.
- P/M/O/T/config/protocol/infrastructure заново не аудировались; их прежний ограниченный static scope сохраняется. Новые первичные опоры здесь — B/U/V, не авторский статус в F.
- Никаких execution/import/compile/tests/probes/environment/web/network/delegation/hash computation. Compile/exec в B/U прочитаны как будущие code operations, НЕ выполнены reviewer.
- Tests — UNRUN specifications. Ни test results, ни actual caller/loading receipt, ни runtime/resource/failure artifacts не проверены. Единственная запись — этот NEW review; old/state/code/protocol/raw не меняются.

## Независимые dispositions
### R014 — major: STATIC ADDRESSED для computational binding; caller-provenance residual OPEN
- V145–150/172–181/218–219/243–244/345–346 hash-then-bare-import заменены B176–193/219–229/303–306/404. Sources capture один раз; identities считаются из тех же bytes, которые передаются bound_source; config повторно с диска не читается.
- B80–94/153/186 отвергают все четыре computational cache names до callback и после initial checkpoint. Exact canonical project-derived paths, ModuleType registration до source exec, compile captured bytes без sys.path/pyc loader; failed load остаётся cached, no retry/unload/fallback.
- B187–193 задаёт E004 P→M→O→T и проверяет T.prod/T.Cart/T.recipe_expectations на bound objects. E005 capture/load только P/M; O/T не читаются/не hash/не exec этим branch. Это inspected-source binding, не authentication или sandbox.
- Все relevant computational uses прослежены через Session references: sample/guard B220/227; toy B278–306 получает bound T/M.Cart; prepare B303–304 — bound P/O; compare B404/428/439/452/459/470 — bound P/M. Поздняя замена sys.modules сама не меняет эти references; мутация objects/globals trusted callback исключается contract F31–32.
- Adapter остаётся отдельной caller obligation: B170–182 проверяет exact __file__/path и adapter_loading declaration, но НЕ доказывает происхождение исполняемого adapter. F20–32 явно требует separately inspected/frozen caller, external hash comparison и exec именно captured adapter bytes; self-provenance claim не сделан.
- U71–130 специфицирует stale/preload/hash/path/caller-contract/captured-vs-disk/provenance/E005-no-O/T cases; U84/94/124 намеренно patch __file__ для test stubs, поэтому это НЕ доказательство загрузки настоящего caller.
- Confidence высокая по прямым data/call paths. Локального дополнительного binding defect не выявлено; original stale/bare-import counterexample устранён статически. До implementation freeze actual caller/import policy/protected-source contract ещё предъявить через orchestrator; end-to-end R014 НЕ объявлен CLOSED, dynamic checks pending.

### R015 — minor: STATIC FIXED; dynamic freshness/durability pending
- V166–169 membership-only заменено B209–217: outputs/attempts snapshots ДО обоих callbacks, returned name должен быть новым в ОБОИХ sets и nonreserved; outputs публикуется только после успешного I/O/fsync B142–147.
- Point single-use B210–211, включая failed attempt; point→name links B217 сохраняются в manifest B246 и failure B261. Старое persisted filename/no-write/failed-write counterexamples теперь отвергаются predicate.
- U132–159 содержит fresh two-links acceptance и duplicate-point/no-write/reuse/fsync-partial rejection specifications. Проверки содержания receipt/authenticity/полноты accounting этим не установлены; trusted callback не должен напрямую фальсифицировать Writer state.
- Confidence высокая; дополнительная correction по прежнему R015 не требуется. Статус только STATIC FIXED, не «receipt tests passed».

### R016 — minor: STATIC FIXED; dynamic namespace/I/O pending
- V103–112 односторонний slot guard заменён B130–141, особенно RESERVED mapping B23 + equality B134 ДО used/attempt/open. Reserved name с slot=None и ordinary name с reserved slot отвергаются; exact manifest/failure пары сохраняются.
- U161–173 задаёт rejection без charge/attempt/file, valid slots и повторную failure-write rejection. B139–147 сохраняет charge full attempted normal payload и exclusive xb; запрета overwrite/delete не ослабляет.
- Confidence высокая по predicate/order; прежнее занятие reserved namespace обычным put устранено. Дополнительная correction по R016 не требуется; STATIC FIXED не означает quota/allocated-footprint guarantee.

### R017 — minor: STATIC FIXED для primary propagation/owned mkdir window; dynamic failure capture pending
- V97–101/185–186 заменены B119–128/231–235: Writer constructor без I/O, object опубликован ДО create; ownership created=True выставляется после успешного exclusive mkdir ДО fsync. Occupied mkdir не даёт ownership, fail B257 не пишет туда.
- V300–302/419–421 заменены B360–362/477–479: best-effort report_failure, затем bare raise первичного exception. Secondary B267–275 сохраняется на Session, по возможности на primary/в add_note; custom exception отказ не заменяет primary.
- U175–219 задаёт primary identity, secondary/reserve failure, owned mkdir-sync и occupied-root cases. F43–54 прямо раскрывает невозможность гарантировать durable receipt при I/O/crash и UNKNOWN external pointer; COMPLETE-looking partial не является успехом при outer exception.
- Confidence высокая по assignment/exception order; дополнительная correction по прежнему R017 не требуется. Actual outer capture primary+secondary, в особенности при отказе custom exception от annotations, остаётся caller obligation и динамически не проверена.

## Неизменные counts, ограничения и handoff
- B31–38/278–296 сохраняет11 выбранных methods/exact8 toy fits/benchmark0; B306 не добавляет U в E004. B415–434 сохраняет2cases×2methods=4 benchmark fits/no tuning. Это static code arithmetic, НЕ observed run counts; core toy methods заново не исполнялись/не аудировались.
- B437–450 сохраняет all-case val+test durable commit перед truth B457/461; postcommit mutation B452 без fit. Main B482–483 безусловно STOP. Runtime importability/durability/counts/compliance UNKNOWN.
- Сильнейший контраргумент к полному closure: верные bound-source predicates не доказывают adapter caller provenance или честность callbacks. F20–32 это признаёт; resolves только inspectable approved caller и отдельно разрешённые narrow negative checks с immutable receipts, не self-hash/test stubs.
- **R002 OPEN; R004 partial; R005 dynamic pending; R008–R013 остаются OPEN; C037 UNVERIFIED.** Hard RAM/quota/terminal-tail gates не переаудировались и не закрываются этими fixes. E004/E005 planned, no efficacy/SSD/new source support.
- Два отмеченных отклонения целевой длины notes (original74, fixes68 строк) — minor documentation-only, не новые научные findings; limits для этого review соблюдаются. Новых ясных critical counterexamples не выявлено, R018 не присваивается; это не validation остальных путей.
- Required reanalysis сейчас NONE; результатов classifier нет. Следующее через orchestrator — inspect actual caller contract до freeze; dynamic checks только после отдельного permission, без скрытого расширения checklist/budget. New snapshot/U/F/этот review входят в prospective5MiB, footprint UNKNOWN.
- Только этот artifact передан; никаких pass-tests/resource certificates, approval/amendment или framework proposal. STOP после одного узкого STATIC прохода; integration статусов — orchestrator.
