# Final inspection: BLOCKED BEFORE EXECUTION

2026-10-01. This final inspection supersedes ONLY the prospective execution
plan in INSPECTION.md; both files and the first implementation are preserved.
No source-document result exists. No script/extractor execution or network
request occurred. The sole shell operation was the authorized inventory.

## Inspection actually performed

Agent read the entire newly created first-party
`../../scripts/inspect_spc_doc_v1.py`, lines 1–407, through the read tool.
No test execution, compilation or sandbox probe was performed. All proposed
runtime checks, hashes and environment observations remain unexecuted.
Local `/usr/share/doc/poppler-utils/copyright` lines 1–220 were inspected;
this is package attribution, not a Poppler source/dependency security audit.

## Decisive implementation defect (agent-owned, not dataset evidence)

`limit()` L97–103 sets BOTH soft and hard limits to the requested value.
Parent L237–239 therefore hard-limits AS to 64MiB, CPU to 7s and FSIZE to
1MiB. Child L148–154 requests AS192MiB, CPU20s and FSIZE2MiB. These hard
limits are inherited and cannot be raised by an unprivileged child. In fact
L99–100 would reject them before setrlimit. The proposed shell ulimits would
also constrain inheritance. Thus the intended child setup is impossible
for this version. The defect was found statically; no failed child/network
execution is being claimed.

The network request L283 precedes Popen/child setup L319–322. Running this
version would consume the allowed download attempt before the already-known
enforcement failure. The correct decision is STOP before execution, not a
test run, an in-place fix or a competing second implementation.

Additional mismatch: parent FSIZE1MiB also limits its own text-output file
below the planned2MiB pipe cap. This is conservative but not the advertised
effective cap. Other code/limits were inspected, not empirically validated.

## Actual accounting and artifacts

Inventory command (project root; tool timeout5000ms), exit0:
`ulimit -t 1 && ulimit -v 65536 && ls -ld ".research/experiments" ".research/experiments/scripts" && command -v python3 && command -v pdftotext && times`

Returned Python `/home/linuxbrew/.linuxbrew/bin/python3` and extractor
`/usr/bin/pdftotext`. `times` reported self/child user/system CPU each0.00s
at displayed precision; these are rounded, not exact zero consumption.
Actual inventory wall/RSS/exact CPU were not separately measured. The shell
was bounded by timeout5s; AS64MiB per shell/ls, CPU1s per shell/ls were
requested successfully. RLIMIT_AS is NOT a RSS/cgroup cap. No Python or
pdftotext version command ran. No runtime seccomp filter was installed.

New first-party script and this directory's three documentation files only:
INSPECTION.md, INSPECTION-RESULT.md, manifest.json. PDF/text/config/runtime
logs are absent. Download attempts/body bytes=0; source/text checksums=null.
Exact local artifact byte sizes/checksums were not measured: no second shell
or helper execution is added to the one-pass budget merely for hashes.
Preparation is small bounded text, not a measured downloaded/extracted output.

## Source support remains unknown

For S018/C022: PDF title/byline/date/revision, schema and section/page locators,
address block size, size/time units, opcodes, ASU meaning, workload-specific
units/durations and dataset-specific rights all remain null. No inference
of512-byte address units, actual reads, trace duration or usable license.
Only existing state/documentation leads were read; no primary PDF text.
Orchestrator must independently verify exact support after any later
authorized successful extraction. No existing claims/state were edited.

## Next action / reproduction boundary

Do NOT execute this blocked script or reuse this directory. No further pass
is authorized here. A later user-authorized version should distinguish
parent soft ceilings from inherited hard ceilings (or use a separately
reviewed supervisor design), configure them BEFORE downloading, keep the
parent at64MiB and child at<=192MiB, enforce the same aggregate CPU/wall/disk
budgets, and inspect the whole corrected version before one new attempt.
This is a repair proposal, not a validated launcher or scientific approval.
Preserve this version and its failure-of-preparation record; no changes to
protocol/hypotheses/raw/literature/evidence-map/Git and no E-ID were made.
