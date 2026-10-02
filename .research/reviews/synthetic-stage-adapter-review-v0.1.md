# Независимый ограниченный STATIC adapter audit v0.1
2026-10-01 · Один локальный проход · Library preparation only / EXECUTION STOP.
Locators относительно `.research/`: B=experiments/scripts/synthetic_stage_adapter_v0.1.py; N=experiments/synthetic-stage-adapter-notes-v0.1.md.
P/M/O/T=experiments/scripts/{synthetic_temperature_demo.py,synthetic_models.py,synthetic_expectations.py,test_synthetic_temperature_demo.py}; C=experiments/configs/synthetic-temperature-demo-v0.1.json.
D/K/L=protocol/{synthetic-temperature-demo-v0.1.md,synthetic-runtime-contract-v0.1.md,synthetic-controlled-launch-plan-v0.2.md}.

## Scope: проверено и недоступно
- Полностью прочитаны B425/N74/P236/M166/O45/T273/C72/D76/K45/L79, preparation approval21, README/evidence-map C037, обе code reviews, launch review R008–R013 и исторический SPC review R002.
- Прочитаны brief/question/hypotheses/current peer-review, literature-map, analysis/draft и raw/E001/manifest.json; raw listing содержит только E001. Analysis EMPTY, draft OUTLINE, общий peer-review NOT REVIEWED — не результаты и не текущий audit.
- Первичная опора findings — непосредственно локальные predicates/call sites; counterexamples ниже НЕ выполнены. Исторические S013/S018/E001 hashes/measurements и внешние публикации не переверифицированы; нового novelty/search/citation claim нет.
- Никаких shell/import/compile/tests/probes/environment/web/network/delegation, вычисленных hashes, generation/fits или reanalysis. Syntax/importability, durable I/O behaviour, callback behaviour и ресурсы динамически UNKNOWN.
- Единственная запись — этот новый датированный review; старые reviews, peer-review.md, state/claims/code/config/raw не меняются. Integration принадлежит orchestrator.

## Сводка и прослеженные пути — НЕ passing tests
**До implementation freeze нужны R014–R017 corrections; R014 — major reproducibility gate, остальные — локальные defensive/error-handling defects. Запуск не разрешён.**
- B34–63 буквально соответствует прочитанному C по recipe/model/windows/resources; semantic JSON equality B150 не исполнена. Null freeze в C остаётся placeholder, не permission.
- E004 B243–255 импортирует O/T только в preparation; TOYS исключает RecipeChecks, поэтому импорт T сам не вызывает его generator test. B254 содержит единственный generate_csv/case; затем parse сохранённых bytes с SHA256 comparison, не повторную generation.
- B258–295 сравнивает actual READ scans с O29–45: 36×96=3456 bin checks/case; grid17/5/7 даёт2784 decision keys/case. Это арифметика recipe, не observed counts. O не вызывает production counting/window/reset helpers.
- P116–187 сохраняет U из R/W issue<t после reset, past [t−600,t), future READ [t,t+600); B279–293 проверяет segment replay, masks и disjoint request IDs. Не найдено нового causal overlap/key/feature-column defect в этом пути.
- TOYS B26–33/216–236 содержит11 test methods: T67–68 дают2 toy fits, T164/166/168/170/173/177 ещё6; запрещённый refit T77 не увеличивает count при fitted tree. Итого8, benchmark0; guard подставлен вместо T.check до вызовов. Это статический счёт, не receipt.
- E005 B357–376: case cycle→negative, train sorted(decision,page), A→X, bare matrices без IDs/time/recipe; один fit call site в loops 2cases×2methods даёт4 prospective invocations, no tuning/refit. Проверяются train labels0/1/2, feature domains и exact expected keys.
- B379–392 сохраняет predictions ВСЕХ val+test ОБОИХ cases и models, fsync files/directories, exclusive prediction-commit с readback hash; только после него B394 делает literal frozen mutation без fit, B399/403 открывает и hash-checks eval truth/audit.
- До commit B348 читает E004 manifest с metadata hashes, B358–359 — только features/trainlabels; B145 исключает O/T из E005 scoped hashing. Eval truth bytes/raw trace/recipe не прочитаны этим явным путём до commit. Это не OS sandbox и зависит от R014/caller callbacks.
- Postcommit interface names корректны: B401 вызывает P208 score_release, B412 — P190 metrics; Z/D/A/X insertion order и shared keys проверяются P214–220. Split release val→test, отдельные strata/per-decision/paired deltas, unseen coverage и selected censored0; pooled winner не создаётся.
- Table B305–317 reject schema/width/duplicate keys; B361–363 reject wrong split/key/domain, P190–193 reject invalid truth/prediction classes. Короткая audit row B408 остановится исключением; строгая audit width/unique unseen keys не проверяется, хотя fixed E004 пишет valid rows и пустой unseen. Это ограничение defensive coverage, не наблюдённое загрязнение результата.
- Exclusive mkdir/xb и attempted-set B99/104/113–119 запрещают reuse/overwrite обычного output; partial payload charged до I/O, deletion/retry отсутствуют. Main B424–425 безусловно STOP; callable API требует external context, но не authenticates approval.

## Новые findings
### R014 — major · loaded implementation не привязана к frozen file identities · OPEN
- Location: B145–150,172,218–219,243–244,345–346; E005 freshness gate B342; criterion D71/K38/L44,57–58: inspected frozen code и actual call paths.
- Observation/evidence: Session hashes project paths, но bare imports используют sys.path/sys.modules. Статический контрпример: ранее импортированная иная `synthetic_models` остаётся в cache; B342 запрещает только O/T, поэтому её BudgetGuard/Cart/prediction_payload могут использоваться при совпавших hashes совершенно другого файла M на диске. Другой search path аналогично касается P/O/T и самого adapter.
- Consequence: записанные identities не доказывают, какой implementation произвёл features/predictions; иной P/M способен нарушить fixed recipe или pretruth barrier. Фактической подмены/утечки не наблюдалось, наличие такого модуля в среде UNKNOWN.
- Requested correction через orchestrator ДО freeze: связать approved caller/import resolution с exact frozen paths, запретить stale/preloaded computational modules до их использования, защитить frozen inputs от drift и проверять actual module provenance. Не добавлять loader/framework/probe по умолчанию; если invariant обеспечивает caller, предъявить его inspectable code/contract. Одного hashes dict недостаточно.
- Required future check: отдельно разрешённый negative test stale module/wrong import path должен STOP до generation/fit/truth access; valid pinned path сохраняет counts. Confidence высокая по Python import semantics и отсутствию binding checks; resolution отсутствует.

### R015 — minor · Session.record принимает повторно старый persisted filename · OPEN
- Location: B166–169/187/192/372/392; N15,62; criterion K25: новые uniquely named accounting artifacts.
- Observation/evidence: membership в writer.outputs не проверяет freshness. Callback может первый раз записать `receipt-start.json`, а затем всегда возвращать это имя, не вызывая writer.put; все следующие record проходят. Авторское сообщение о reused filename независимо подтверждено predicate, не исполнением.
- Consequence: start/fit/commit/finalization checkpoints могут не получить отдельных durable receipts, хотя код продолжит работу. Sample monotonicity B171–176 этого не исправляет; prediction files сами этим контрпримером не отменяются.
- Requested correction: snapshot output/attempt state до callback; принимать только новый успешно persisted nonreserved filename этой invocation, сохранять point→artifact link. Добавить literal reused-name/no-write/failed-write rejection specifications; fresh unique path acceptance. Не выдавать freshness за authentication/полноту external ledger.
- Confidence высокая, прямой counterexample; status OPEN, исправить до freeze, не новая доказанная resource violation.

### R016 — minor · обычный output может занять reserved bookkeeping paths · OPEN
- Location: B103–119/169/205/210; N59–63; criterion C65/K17,33: сохранение manifest/failure reservation.
- Observation/evidence: reserved-name restriction применяется только при truthy slot. `put("manifest.json", small_bytes)` или `put("failure-001.json", small_bytes)` с slot=None проходит normal allowance и занимает имя навсегда. Receipt callback имеет Writer; ошибка naming может сделать последующий finish/fail невозможным. Отказ record после такой записи не возвращает reserved path.
- Consequence: заявленное N63 «reserved paths закрыты» не enforced для general writes; logical reserve не защищает namespace. Нет overwrite/delete, но теряется возможность штатного финального/failure artifact.
- Requested correction: bidirectional exact name↔slot validation ДО charging/attempt/open; reserved names запретить slot=None, сохранить single-use и full partial charge. Добавить reserved-name ordinary-write и mismatched-slot rejection specifications, valid manifest/failure acceptance.
- Confidence высокая по ветвлению; status OPEN, локальный guard defect, не whole-disk/quota finding и не resource certification.

### R017 — minor · failure-reporting exception заменяет первичную ошибку; mkdir failure window · OPEN
- Location: B99–101/185–186/208–213/300–302/419–421; criterion D66/L60: immutable failure/partial reason и STOP.
- Observation/evidence: при primary error обработчик без защиты вызывает s.fail. Если reserve слишком мал, I/O/fsync fails или failure path занят (R016), наружу выходит secondary exception вместо primary; original обычно остаётся __context__, но primary машинный error type меняется. Если mkdir успешен, а constructor sync_dir падает, assignment self.writer не завершён: созданный partial dir остаётся без возможности s.fail его описать.
- Consequence: partials не удаляются, но штатная failed record/primary reason не гарантирована даже для catchable errors; N63 не описывает эти windows. Это не требование обеспечить запись при неисправном filesystem или hard crash.
- Requested correction: retain/re-raise primary, сообщить secondary reporting error без retry/overwrite (exception context/note и external failure pointer); сделать созданный directory state доступным для best-effort failure reporting либо явно contract этот window внешнему owner. Failed COMPLETE-looking manifest не считать успехом без outer failure review.
- Required future check: отдельно разрешённые simulated mkdir-sync/failure-write/reserve failures сохраняют primary+secondary reasons и partials, не COMPLETE/авторетрай. Confidence высокая по assignment/exception order; status OPEN.

## Контраргумент, handoff и остаточные риски
- Сильнейший контраргумент к R014–R017: будущий frozen fresh caller может гарантировать правильный sys.path/cache, новые callback names и reserved-name discipline, а facility сохранит любые I/O errors. Это возможно, но caller не предъявлен; notes обещают более сильные локальные guards, чем B обеспечивает. Разрешение — inspectable binding/callback/error contract плюс небольшие code corrections, не доверие названию fresh worker.
- Контраргумент к будущему X>Z: engineered anti-persistence Z и count-only mapping A, не дополнительный feature signal или SSD mechanism. Уже заданные A−Z/X−A, trees/confusions по двум cases после отдельных G1/G2 способны различить эти объяснения; X≈A и случайный nonzero negative delta допустимы. Новый seed/tuning/benchmark не запрашивается.
- **R002 historical major OPEN; R004 partial; R005 dynamic pending; C037 UNVERIFIED.** R008–R013 остаются OPEN: новый library artifact не закрывает hard RAM/whole-domain/control/allocated disk-quota/terminal own-tail gates. Шесть инфраструктурных findings здесь не пересказываются и независимо не закрываются.
- Primary claim/run IDs: C037, SYN001 proposed, E004/E005 planned; C017/H005 deferred. S013/S018/S014/S015/E001 — только historical context, новых S-ID/results нет. Числа8/4/3456/2784 — code/recipe arithmetic, не run measurements.
- Required reanalysis сейчас NONE: classifier artifacts отсутствуют. Через orchestrator сначала отдельный author correction pass R014–R017 без исполнения, затем bounded static diff review до implementation freeze; будущие negative/checklist checks требуют отдельного permission и immutable receipts, не full-suite/bootstrap loophole.
- Cases/pages/windows не iid; descriptive F1/deltas без tests/CIs не устанавливают efficacy. Fixed negative сохранён, tuning/exclusions/pooling не найдены в явном inspected path; audit corruption/callback trust/common-mode interpretation/partial I/O остаются рисками. Search конечен, novelty не установлена; engineered issuance counts не completed SSD reads/throughput.
- Эта review входит в prospective5MiB scope; footprint UNKNOWN. Нет pass-tests verdict, approval/resource amendment или сертификата runnable/compliant/valid. «No finding» в остальных путях не устанавливает validity. STOP после одного прохода.
