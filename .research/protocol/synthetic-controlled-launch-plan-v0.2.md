# Synthetic controlled launch v0.2 — diagnostic exception, не запуск
2026-10-01 · **DRAFT / PERMISSION PENDING / E004–E005 BLOCKED** · Один локальный static revision-pass.
Основание: `reviews/synthetic-launch-plan-review-v0.1.md` R008–R013, `synthetic-controlled-launch-plan-v0.1.md`, runtime-contract/preparation-approval/code reviews/implementation notes, прочитанные в этом workflow.
Пути артефактов относительно `.research/`; проект `/home/nomli/workspace/bdss_lab/research1`. v0.1 сохранён без изменений; rationale ДО outcomes: убрать native build/supervisor и uncontained shell, сузить диагностику и явно раскрыть все исключённые guarantees.
Это подготовка НОВОГО permission request, НЕ human approval, public registration, runnable runner или закрытие findings. State/claims/code/config/raw/entrypoint не меняются.

## 1. Единственный условный runtime route
**УЖЕ предоставленный managed facility → один single-thread Python worker**, E004/E005 последовательно, без research children/нового supervisor/native binary/build/two-process amendment.
Маленький будущий `experiments/scripts/synthetic_artifact_adapter_v0.2.py` отсутствует; отдельно согласовать только его подготовку/inspection/freeze. Existing main `synthetic_temperature_demo.py` остаётся безусловно STOP.
Facility должна уже обеспечивать pre-start containment, quota, bounded termination и post-operation accounting/export; availability/interface/owner/bounds сейчас UNKNOWN. Если нет — STOP, не строить infrastructure и не менять route автоматически.
До worker startup нужны effective memory.max=1073741824, memory.swap.max=0, worker1/thread1/no children, защищённое membership/write scope; cgroup pids.max=1 само по себе не задаёт весь control scope.
Предсуществующий manager/tool server/kernel не объявляются whole-machine RAM domain. Research-specific facility requests, control processes, exports и own tails требуют явного domain/accounting; «existing» не освобождает overhead от учёта.
Если позже interface использует `systemd-run`, его control process/startup/exit/CPU/RAM/disk+manager attribution включить в отдельный B preview и approval; это НЕ готовая команда/permission и не скрытый второй research worker.

## 2. Сейчас только D-NATIVE: явно запрашиваемое diagnostic tool-control исключение
Executor/reader — **существующий tool-server `functions.read`**; writer — **orchestrator через существующий `functions.apply_patch`**, без нового helper/process/сборки. Ни одного OS read ниже сейчас не выполнено.
Запросить максимум ШЕСТЬ последовательных вызовов, по одному на path, без повторов/дополнительных reads/поиска. Initial paths — публичные OS metadata, не user/auth dirs; возможные host/mount identifiers не трактовать как credentials и не публиковать вне локального receipt.
Точные prospective tool arguments (не shell commands; `offset=1` для каждого):
| № | `functions.read.filePath` | `limit` | Scope |
|---|---|---:|---|
| 1 | `/proc/self/cgroup` | 32 | tool-serving process membership text |
| 2 | `/proc/self/mountinfo` | 512 | tool-serving process mount metadata |
| 3 | `/sys/fs/cgroup/cgroup.controllers` | 8 | root controllers text only |
| 4 | `/sys/fs/cgroup/cgroup.subtree_control` | 8 | root enabled controllers text only |
| 5 | `/sys/fs/cgroup/` | 64 | native listing, без traversal |
| 6 | `/run/systemd/` | 64 | native listing, без traversal |
Limits задают requested returned lines/entries, НЕ bound runtime/internal scan; если directory tool не соблюдает limit, отметить unknown/truncation, не повторять/не обходить shell. При failed access сохранить исход; шесть вызовов — максимум, не обязательство продолжить при риске.
`/proc/self` относится к обслуживающему tool процессу, НЕ worker. Из этих reads НЕ выводить effective worker/root limits, ancestors, delegation/write permission, facility service readiness или quota. Acceptance D — только доступный metadata inventory.
Amendment явно исключает **гарантию hard wall/aggregate CPU/RAM/disk/startup/control-tail** для native inventory+tool receipt write: tools НЕ watchdog/bounded runtime, их control scope/accounting/allocated footprint неизвестны.
Сохраняются planning targets120s/120CPU-s, worker1GiB и общий5MiB; prospectively резервировать inventory15/15 ИЗ120, не утверждать observed15s/расход0/remaining105. Числа не превращают exception в hard guarantee.
Это маленькое диагностическое исключение, не bootstrap authorization/limits proof; read-only относится к шести чтениям, receipt — явно разрешаемая единственная новая диагностическая запись.
Альтернатива человека: сохранить строгий исходный contract → **STOP, никаких OS/env reads**. Ни shell/timeout/stat/Python/import/compile/tests/generator/fits/cgroup writes/network/external search/installs в D-NATIVE нет.

## 3. Единственный будущий D receipt и accounting consequence
Единственный receipt path: `/home/nomli/workspace/bdss_lab/research1/.research/experiments/control/synthetic-launch-v0.2/discovery-001.md`, **сейчас НЕ создавать**; если занят — STOP, не overwrite/новый attempt.
Orchestrator после D approval пишет его один раз через apply_patch, максимум **16384 bytes UTF-8** текста включая headers; предварительно ограничить excerpt selection, длинные outputs оставить по tool-output pointers, не bash truncation/log files.
Receipt: approval reference; все attempted/not-attempted calls/args/status/failed accesses; bounded excerpts и tool-output locators; tool start/end timestamps where available; missing pointers/times явно null; line-limit/truncation flags и диагностические ограничения.
Unknown CPU, startup/exit/control-tail, memory и logical/allocated/metadata disk measurements — **null**, не оценка0; timestamp difference не aggregate CPU и не complete active-wall measure. Byte guard для текста НЕ filesystem quota/allocation/whole-disk proof.
Если output pointer недоступен, указать это и сохранить доступный failure/excerpt в16KiB, не утверждать full raw capture. При write failure retain tool-output/failure pointer где доступен, diagnostic INCOMPLETE, без повторной записи/retry.
Unknown D usage НЕ допускается в **COMPLETE cumulative ledger**. E004/E005 BLOCKED до восстановимого полного D/control/export учёта ИЛИ ЕЩЁ отдельного human budget-domain amendment; такого amendment здесь НЕ предлагается как выданного/автоматического.
D metadata само не устраняет этот gate. Review receipt отдельно; никакого auto-bootstrap/дальнейших probes, даже если controllers/systemd directory существуют.

## 4. Будущий bootstrap B — отдельный permission, не инфраструктура
До B предъявить существующий facility contract/interface/owner/external operation-record locator, exact controls/commands/process scope, accounting/stop latency/headroom, protected quota/census/reserves и inspected frozen adapter/runtime/code/config hashes; missing→STOP.
B допустим только с восстановленным полным accounting либо отдельно одобренным новым domain; bootstrap/repeated startup-through-export используют **измеренный remaining inventory15/15**, не новые15s и не вычитание фиктивного D расхода.
Facility pre-start containment → один worker adapter `--stage bootstrap`: только effective controls/membership/counters/runtime provenance/quota/receipt checks, без production model imports/generator/fixtures/toy fits/full unittest; exact operations freeze ДО approval.
Prospective worker argv-spec для B/E004/E005: `[FROZEN_ABSOLUTE_PYTHON, '-B', '-S', ABSOLUTE_FUTURE_ADAPTER, '--stage', STAGE]`; это НЕ существующий runnable interface, значения/runtime/facility submission сейчас UNKNOWN, команды не выполнять.
Facility должна после worker exit/empty domain сохранить final counters/memory events/peak/exit, собственные control/export CPU/wall/disk и final external managed-operation record. Pre-exit worker manifest НЕ закрывает observer own tail.
Если outer event/owner/locator/charging/failure reserve отсутствуют, mark INCOMPLETE/limits UNKNOWN→STOP; не добавлять observer, не выдавать append/hash-chain за полное accounting.
memory.max — условный charge bound; cpu.max — rate, НЕ aggregate cap. Polling/timeout/guards без обеспеченного termination+tail bound не certifies120/120/per-fit; границы и emergency reserve подтвердить ДО dispatch, иначе STOP.

## 5. Только последующие G1/E004 и G2/E005
Recipe/goal без изменений: два96-page/6h cases, seed42 negative, past/future600s, labels0/1–2/≥3, fixed splits/reset; Z,D,A,X depth3/minleaf50; tuning0, four benchmark fits. C037 UNVERIFIED, H005/SSD benefit deferred.
G1 отдельно после COMPLETE B review: exclusive raw/E004 → traces/event-total≤30000 → validate/manual fixtures/independent recipe vs READ counter/causal masks+keys+mutation → отдельные features/train labels/eval truth/audits; immutable manifest и terminal receipt.
Toy-fit checklist/точное число/phase allocation сейчас UNKNOWN: freeze конкретные tests и count ДО G1, не произвольное≤8/скрытый full suite. E00435/35 включает согласованные prep/toys; benchmark fits0 в E004.
Все research operations/accounting должны завершиться до human G2 wait; исключать ожидание только после exit/control export. G2 отдельный, только COMPLETE E004 input hash/resources/checks review; occupied E004/E005 ID→STOP, E001/E002/E003 не reuse.
E005 case cycle→negative, A→X: ровно4 benchmark fits в40/40, каждый10/10; predict Z,D,A,X для ВСЕХ val И test keys ОБОИХ cases, exclusive durable files+SHA256+fsync(files/directories)+commit receipt ПРЕЖДЕ любого eval truth access.
Adapter до commit получает только features/train labels, не eval truth/raw trace/expectations; truth opens AFTER commit с capture access/order checks. Reviewed guard не OS sandbox; no refit/tuning/test reuse, val→test один release.
Prediction/metrics15/15; finalization/checksums/worker exit/facility tail15/15. Ledger D+B+E004+E005+failures+all controls/tails≤120/120: active nonoverlapping intervals и aggregate CPU без parent/child double count; unknown→INCOMPLETE.
Сохранить все low/negative outcomes, partials и ошибки schema/hash/causal/commit/quota/OOM/timeout/control failure/missing telemetry; no auto retry/delete/overwrite. Comparative F1 не выдавать для incomplete models; результаты отдельно от compliance/correctness.

## 6. Disk/records/validity gates
Одновременно logical+metadata reserve И allocated+metadata reserve≤5242880 bytes, peak/temp/partials/quota rounding included. Prepared code/config/tests/snapshots/notes/оба launch plans/NEW review/этот документ/D receipt/future adapter/raw/processed/control exports входят, не baseline.
Footprint/path-owner census/pre-codeprep unchanged baseline/quota/metadata/worst-case outputs/failure+terminal reserve сейчас UNKNOWN; шестью reads НЕ измеряются. D16KiB text cap не решает R012; diagnostic disk-guarantee exception явно scoped только D control/receipt, не исключает их из5MiB ledger.
До certified B/G1 нужны conservative measured census+защищённая quota всех новых namespaces+logical writer guard+обеспеченные failure/export reserves; без этого STOP, не «5MiB достаточно», перенос prepared в baseline или удаление failures.
Records capture approval/argv/tool args, protocol/code/config/runtime/input/output identities, split/checks/fit counts, resource sources/phase+total usage, timestamps/exit/reason и deviation links; неизвестное=null. Subsequent revision — новый artifact+rationale/approval ДО runs, outcomes-triggered changes exploratory.
Units — whole engineered case, windows/pages зависимы; descriptive confusion/F1/support/coverage/deltas без p-values/power guarantee. Leakage/common-mode bugs/non-sandbox access и engineered anti-persistence Z/count-only transform — альтернативы, не доказательство real predictability/SSD/novelty.

## 7. Disposition — proposed-static-response / NOT REVIEW-CLOSED
Support ниже — разделы этого draft и exact review sections, НЕ execution evidence; все R008–R013 остаются reviewer/human gates.
| ID | Proposed static response; support | Remaining |
|---|---|---|
| R008 | §1 убирает native build/supervisor; review R008 | Existing facility/adapter отсутствуют или UNKNOWN; B/G1/G2 blocked |
| R009 | §§2–3 named read server/writer/single receipt; review R009 | Accounting/ownership гарантий tool-tail UNKNOWN; diagnostic exception pending, certified execution blocked |
| R010 | §2 шесть metadata-only reads, self≠worker; review R010 | Ни delegation/quota/route availability из D не выводится |
| R011 | §§2–4 все hard guarantees явно исключены только для D; review R011 | Unknown cumulative usage требует recovery/отдельного amendment; hard B/G1/G2 blocked |
| R012 | §§3,6 notes+review/prepared+receipt в5MiB; review R012 | Whole logical/allocated/quota/metadata/reserve UNKNOWN; certified B/G1/G2 blocked |
| R013 | §§3–5 explicit terminal own-tail/failure gate; review R013 | External operation record/charging/export bound UNKNOWN; certified B/G1/G2 blocked |
**R002 historical major OPEN; R004 partial; R005 dynamic pending. Запрос сейчас — только D-NATIVE amendment §§2–3; approval PENDING.** Никаких OS reads/commands/imports/tests/network/runs/receipt creation сейчас; единственная запись — новый v0.2, исходные артефакты сохранены.
