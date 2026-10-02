# STATIC practical caller review v0.1
2026-10-02 · Один проход · Bootstrap-only · EXECUTION STOP · Gate: **NEEDS FIX**.
Все locators ниже относительно `.research/`; единственная новая запись — этот review, прежние reviews сохранены.
P=experiments/scripts/synthetic_practical_caller_v0.1.py; N=experiments/synthetic-practical-caller-notes-v0.1.md; A=protocol/synthetic-practical-runtime-amendment-v0.2.md.
F=reviews/synthetic-stage-adapter-fixes-review-v0.2.md; M=claims/evidence-map.md; D=protocol/synthetic-temperature-demo-v0.1.md.

## Scope / independently checked vs unavailable
- Полностью прочитаны P348/N69/A71/F46, README80, brief/question, D и preparation approval; просмотрены experiment-plan, M, literature catalog, analysis/draft, current review template, raw listing и E001 manifest.
- Проверены собственно predicates/data/call paths P, не только авторские утверждения N. Старый adapter/core заново не аудирован; F — история residual, не новый dynamic proof.
- Только native чтение и запись review: shell/import/compile/tests/envprobe/generation/fits/network/agents НЕ выполнялись. Идемпотентный research-state вернул created=[]; других файлов не записано.
- Actual runtime, file hashes, footprint, entry counts, stdout lengths, exit/durability/RSS/CPU/wall НЕ измерены; syntax/importability UNVERIFIED. E001 manifest — исторический артефакт, не проверка нынешнего runtime.
- Analysis EMPTY, draft OUTLINE; E004/E005 артефактов для проверки численных результатов нет. Нового внешнего S-ID или E-ID не присваивается; source counters здесь — точные локальные строки.
- Литература только локальный catalog/context: внешние pivotal claims в этом bootstrap audit не выдвигаются; novelty/baselines/leakage/statistics/generalization заново не подтверждены. C037/M42 остаётся UNVERIFIED, C017/H005 deferred.

## Permission / exact proposed operation B001
- Режим practical явно принят (README5,58; A7–11), но argv/B001/execution ещё НЕ разрешены. Brief88/M42,67 содержат старое PENDING: интеграцию делает orchestrator, не reviewer.
- Только после отдельного датированного решения **B001** и предъявления окончательного argv возможен ОДИН proposed direct invocation (не shell chain):
```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_practical_caller_v0.1.py --stage bootstrap --approval-ref B001
```
- B001 сейчас лишь proposed approval reference, НЕ authorization/security token. P274–275 допускает B001 без проверки человеческого решения; это намеренно внешний permission gate (A53), не дефект authentication.
- N16/A51 используют USER_BOOTSTRAP_PENDING: P271–280 отвергает его ДО Writer/создания файлов; пустые/запрещённые placeholder tokens тоже STOP. Возможный stdout/tool capture не равен scoped filesystem write самим caller.
- P276 всегда блокирует E004/E005 до Writer: auto G1/G2, полный unittest, генерация/fit отсутствуют. `/usr/bin/python3` existence/version UNKNOWN; P277–278 требует exact Linux/-B/-S/no fallback.
- A2/README4,58 имеют унаследованную дату 2026-10-01; N2 и review датированы сегодня 2026-10-02. Это НЕ даты исполнения; orchestrator должен корректно датировать новое approval, сейчас pending.

## R018 — minor / OPEN: project-only stat boundary и missing-ancestor contract
- Location: P103–119,137–146,178–180; N47,50; A42,54–55. Observation: `add(PROJECT / ".")` сначала вызывает `path.parent.exists()` (P143), то есть stat за пределами PROJECT; docstring P104 описывает только project-relative ancestors.
- Evidence/criterion: проверка принадлежности PROJECT выполняется лишь позднее внутри checked; внешний parent не нужен для census корня. Это конкретная лишняя metadata operation, НЕ чтение внепроектного содержимого или доказанная утечка.
- `checked(..., missing=True)` ловит FileNotFoundError только для leaf (P112–117), не ancestor lstat (P110). При нескольких отсутствующих intermediate ancestors census может аварийно STOP вместо обещанного допуска prospective dirs.
- Важное ограничение: обычное отсутствие только CONTROL при существующем experiments НЕ опровергает этот bootstrap — main279, census146 и последовательный create234–245 его допускают. Более глубокая missing chain — условный counterexample, не observed failure текущего дерева.
- Consequence: exact approval scope включает лишний внешний stat; generic missing-dir wording шире реализации. Requested fix: пропустить parent.exists для PROJECT и проверять внутри PROJECT без follow-first exists; missing ancestor при разрешённом missing возвращает absence, существующий symlink/non-directory всё ещё STOP. Либо сузить документированный missing contract до реально поддержанного дерева.
- Confidence высокая по control flow; current-tree достижимость missing-chain failure не измерена. Action: минимальная статическая правка/уточнение через orchestrator до B001, без framework/probes.

## R019 — major / OPEN: bounded summary может заменить failure необработанным exception
- Location: P49–50,322–343; N53–54,61; A44,57,63. Observation: primary и secondary `reason` урезаны до256 Unicode characters, но ensure_ascii=True раздувает JSON; require≤2048 расположен ПОСЛЕ try/except/finally.
- Evidence/criterion: одна non-BMP code point сериализуется двумя ASCII `\uXXXX` escapes (12 bytes), поэтому256 таких characters в одном reason уже превышают2KiB без остальных полей. Два менее широких escaped reasons также могут превысить cap; это статическая арифметика, НЕ выполненный тест.
- Consequence: P342 бросает новый необработанный RuntimeError вместо обещанного bounded primary/secondary summary; возможен stderr traceback без собственного byte guard. Existing partials остаются, но внешний failure handoff теряет штатную форму.
- Requested fix: ограничить error fields по фактическим serialized bytes и оставить заранее bounded fallback summary с primary/secondary type, явным truncation и owned/durable pointer; финальный formatter/print failure не должен превращаться в uncaught traceback. Не расширять2KiB cap или reserves.
- Confidence высокая для counterexample; occurrence в текущем run UNKNOWN (run отсутствует). Action: минимальная correction до первой B001 permission; последующие negative checks только отдельно разрешённые, через orchestrator.

## Checked dispositions / residual risks
- P5–15 импортирует только stdlib; P289–295 читает prepared files как DATA/hash, config сохраняет plaintext UTF-8. Никакого compile/exec/import computational code, thread/subprocess/network creation в P нет; фактические OS thread counts/runtime доверены извне и UNKNOWN.
- Scope P178–198/N44–48: README/brief и claims ЦЕЛИКОМ, recursive synthetic snapshots/notes/reviews/protocols/configs/control; baseline extras учитываются консервативно. Dataset/E001/documentation contents не hash/read; plaintext config и локальные scope paths/hash state — не privacy certificate.
- P152/174/227 fail closed на entry/enumeration/future-entry caps256; сортировка ПОСЛЕ полного bounded scan, не truncated success. Enumeration включает unmatched names; полного census нынешнего дерева не заявляем.
- P284–297 создаёт dirs ДО capture; во время capture собственных writes нет. Signature P122–133/297 включает dev/inode/size/mtime/ctime/blocks, не atime: read-only capture не имеет неизбежного self-induced directory mismatch. External mutation/races остаются residual, не sandbox claim.
- P159–162 дедуплицирует logical/allocated device+inode hardlinks; P219–231/250–263 резервирует64KiB normal +8KiB failure и metadata512/entry/rounding4096 estimates. Это inspected arithmetic, не измеренный disk footprint/metadata hard bound; tool captures UNKNOWN.
- Writer публикуется ДО create (P281–284); created/owned сразу после mkdir ДО fsync (P240–245); exclusive xb и charged attempted payload сохраняют partials. Primary/secondary outer path есть; preownership/I/O/crash failure record лишь best-effort. R019 ограничивает final reporting.
- Alarm P69–71/304–305/326–335 использует absolute12→15s внутри inventory15, не новый cap; failure не продлевает15s, finally отменяет alarm до UNKNOWN print/exit tail. CPU absolute process_time charged once; RSS SELF Linux KiB×1024. Practical targets120s/120CPU-s/1GiB/5MiB, overhead UNKNOWN, НЕ certification.
- Future writes P233–264: optional `.research/experiments/control/`, exclusive `control/synthetic-practical-v0.2/` и `.../bootstrap-001/`; только freeze.json→receipt.json→ledger.json и best-effort failure.json. Нет raw/E004/E005 или processed writes; occupied namespace STOP/no retry/delete/overwrite.
- R014/F18–20 caller adapter provenance остаётся OPEN: bootstrap только hash-as-data, не binding исполняемого adapter. R005 dynamic pending/R004 partial; R002 historical major OPEN. A10–11 отменяет старые cgroup/quota certification prerequisites только prospectively для practical mode, НЕ закрывает исторические certificate findings.

## Strongest counterargument / handoff
- «Безопасный metadata-only bootstrap обязан хотя бы штатно отказать»: read-only computational scope не спасает extra-scope stat и unbounded serialized-error tail. Сильнейший возможный ответ — ASCII errors/существующее дерево обычно проходят — не устраняет конкретные branch/encoding counterexamples; это альтернатива reviewer, не цитата автора.
- Discriminating check: сначала статически исправить R018/R019; затем только по отдельному разрешению bounded synthetic missing-ancestor/escaped-error checks с exact argv и immutable receipts, без computational imports/gen/fits и без расширения bootstrap permission автоматически.
- Required reanalysis сейчас NONE: результатов нет. Через orchestrator запросить минимальные corrections и scoped inspection, потом новый человеческий B001 checkpoint; после единственного будущего bootstrap STOP/review, G1/G2 отдельно. No finding по прочим путям НЕ доказывает validity; сейчас никакого исполнения.
