# Synthetic stage adapter v0.1 — STATIC / UNRUN / launch STOP
2026-10-01. Один implementation-pass; только два новых файла, без state/protocol/core/config edits.
Прочитаны README/decision log, brief/question/hypotheses/C037, synthetic protocol,
preparation approval/runtime contract/controlled launch v0.2, обе code reviews,
core/models/expectations/test/config и implementation notes/fixes.
Ничего не импортировано/скомпилировано/исполнено; commands=0, exit codes отсутствуют.

## Library API и внешний caller
`scripts/synthetic_stage_adapter_v0.1.py`: `prepare_e004(context)` / `compare_e005(context)`.
Это НЕ launcher/CLI; main безусловно STOP, нет approval flags/автоперехода E004→E005.
Context — dict: project absolute path; dispatch с operation_ref/owner/approval_reference/
prestart_record/quota_record/postexit_record_locator; resource_receipt; provenance;
frozen_hashes ровно по SCOPED (+oracle/test для E004); writer_limits;
checkpoint(stage,point)→dict с matching operation_ref;
persist_resource_receipt(writer,stage,point,receipt)→имя нового durable файла через writer.put;
sample()→cumulative(active-wall,aggregate-CPU); origin(phase,None|fit_number)→внешние coords.
E005 дополнительно e004_manifest_sha256, проверенный отдельным G2 review/caller.
Все четыре callable обязательны; отсутствующие/пустые external objects и checkpoint
отвергаются до writes. No default no-op. Reference/receipt не authenticates human permission.
Provenance fields: runtime,OS,CPU,RAM,compiler,repo_revision,dirty_state,
secret_free_environment,commands; caller должен передать frozen environment/ledger данные,
не credentials. Unknown явно null; структура dict не подтверждает полноту/достоверность.
Runtime hashing ограничен перечисленными local scoped files; нет git/OS/runtime probes.
FIXED — полный буквальный existing JSON; любой drift STOP, freeze отдельно в context.
Stdlib-only/third-party lock=[]; exact Python/stdlib supplied externally, сейчас UNKNOWN.

## E004 finite preparation
Оба cases cycle→negative; generate_csv ровно один раз/case → exclusive CSV+fsync →
parse именно сохранённых bytes с проверкой SHA256. Никаких benchmark fits.
11 явно перечисленных tests TOYS, НЕ RecipeChecks/НЕ full suite; tests.check заменён
на E004 guard до вызовов, Cart на counted subclass. 8 выполняемых toy fits:
Fties/Fmutation 2 + exact_CART 6; одна запрещённая попытка refit не обучает модель.
Остальные literal fixtures/reset/ties/unseen/domain/metrics/guard tests не fit.
Checklist prospective, dynamic count/успех UNVERIFIED; mismatch/ошибка STOP.
E00435/35 и shared120/120 охватывают checks/toys, нет нового бюджета на tests.
Отдельный oracle сравнивается с actual READ scans: 36×96=3456 bin checks/case,
17/5/7 decisions×96=2784 decision-label/key checks/case, всего6912/5568 соответственно.
Это design arithmetic, не наблюдения. Segment replay/disjoint IDs/masks/feature bounds
проверяются отдельно. Outputs/case: trace,recipe,features,trainlabels,2 eval truth,
3 audits (9 файлов). Ещё config/checks/receipts/manifest; failures retain, no retry.
Raw event upper bound28224 + fixture allowance100 ≤30000, не измеренный count.

## E005 release и immutability
Отдельный свежий worker: oracle/test уже в sys.modules→STOP; compare их не импортирует.
E004 manifest только LOCAL_WORKER_COMPLETE, его metadata label hashes читать можно.
До predictions: verify manifest/identity и только features+trainlabels input file hashes;
ни eval truth/audit/raw trace/oracle не открывать и не hash. Bare matrices,
train sorted(decision,page), case cycle→negative/A→X, ровно4 fits/40/40, per-fit10/10.
Внешние cumulative origins не вычисляются/не сбрасываются adapter.
Frozen trees+Z/D/A/X predictions всех val+test обоих cases → exclusive fsync files,
fsync run+raw dirs → НОВЫЙ prediction-commit.json+fsync → commit checkpoint receipt.
Только затем literal future-mutation каждого benchmark frozen pair без fits/refit,
actual eval truth/audit hash validation, shared keys и score val→test percase.
Fmutation обязательна: missing/failure не даёт LOCAL_WORKER_COMPLETE.
Report: confusion/support/F1/deltas, per-decision/zero-history/write-only seen strata,
unseen cold-default classes/errors/metrics/coverage и selected censored0; no pooled winner.

## Limits, reproduction и exact remaining STOP
Writer exclusive mkdir/files; existing STOP. writer_limits positive per_file/total/
manifest_reserve/failure_reserve: caller residual logical allowance ≤5MiB, заранее
резервирует manifest/failure; partial attempts charged, no deletion/overwrite/retry.
Receipt callback обязан писать новый уникальный filename через writer; reserved paths
закрыты. failure-001.json новый, existing/error→STOP, не rewrite; hard-crash receipt — facility.
Софт guards/byte bounds НЕ whole RAM/time/disk/quota/metadata/own-tail certification.
Все prepared source/snapshots/plans/reviews/эти2файла/receipts/raw входят в5MiB;
footprint и output/reserve feasibility UNKNOWN, estimates/bounds не observations.
Reproduction только позже: frozen approved external caller → E004 → exit+external
accounting/review/G2 → новый worker E005. Native parent read сейчас: raw только E001.
Нет созданных E004/E005, measured hashes/manifests/results или external certification.
LOCAL_WORKER_COMPLETE всегда final_external_accounting/global_resource_certification=null.
Original prestart containment/quota/census/terminal own-tail/ledger gates, G1/G2,
runtime-contract acceptance/freeze и launch approval отсутствуют: REAL LAUNCH STOP.
Syntax/importability, dynamic tests, counts, budget feasibility UNVERIFIED; C037 не закрыта,
H005/SSD effect deferred. Pure library не OS sandbox; interpretation — analyst.
