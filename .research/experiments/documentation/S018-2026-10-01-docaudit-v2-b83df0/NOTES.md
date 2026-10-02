# S018 document audit v2 — preparation-only correction

2026-10-01. New unique directory; no E-ID/raw/trace/model artifact.
v1 and its blocked manifest remain unchanged. Previous source download,
network and extractor attempts were0. Orchestrator explicitly permits a new
reversible preparation version under the existing one-attempt doc permission;
v1's recommendation for fresh user approval was not a human decision.
No scientific protocol/labels/hypotheses/numerical budget change or rescue of
outcomes: there were no observed source/experiment outcomes in v1.

Version2 script: ../../scripts/inspect_spc_doc_v2.py. Read entire file before
execution and create a NEW inspection-result record, not edits to this note.

Inheritance fix: parent AS soft64MiB/hard192MiB, CPU soft8/hard20,
FSIZE soft/hard1MiB. Parent never raises its own AS soft limit. Child may
raise its own soft limits within inherited ceilings, then lowers/locks
AS192MiB/CPU20s/FSIZE1MiB/NPROC0/CORE0. The sole real installed pdftotext
starts waiting for stdin BEFORE networking; a bounded pre-exec handshake
records inherited/actual limits and seccomp. This is not a helper/probe run
and is the only extractor invocation. Failure of preflight means STOP/no
request. It processes the saved PDF via stdin after the single download.

Remaining wall<=55s (internal45s operation + bounded cleanup deadline50s),
CPU<=28s after prior inventory<=2s. Parent softCPU8 uses default SIGXCPU;
child CPU20. RLIMIT timing has kernel/scheduling granularity, actual rusage
reported. AS soft caps sum64+192=256MiB; AS is NOT RSS/cgroup memory.
Child minimal environment contains no credentials; seccomp denies networking,
process creation/io_uring and file write-open/create/unlink/rename syscalls.
It is a denylist, not a complete OS sandbox; filesystem reads remain possible,
installed tool/libraries trusted, no Poppler source audit claimed.

One exact HTTPS URL only, no proxies/redirects/retries, verified TLS using
existing system CA bundle, identity PDF MIME/magic, unambiguous Content-Length
plus body counter<=1MiB. Body cap excludes TLS/headers/DNS wire overhead.
PDF1MiB+text1MiB+stderr16KiB+bounded metadata/scripts/old preparation<5MiB;
script will measure old/new owned bytes before writing final manifest.
All outputs exclusively created; preserve partial/failed outputs and STOP.
No downloaded-code/PDF-action execution, trace links, terms acceptance,
installs/git changes/state/claim/literature/raw edits or delegation.

Actual authorized execution command is intended from project root, timeout
55000ms; no additional inventory and NO inherited tiny inventory ulimit setup:
`ls -ld ".research/experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0" && exec /home/linuxbrew/.linuxbrew/bin/python3 -I -S ".research/experiments/scripts/inspect_spc_doc_v2.py"`
ls verifies the exact new parent before runtime writes. Script inspects
getrlimit and fails BEFORE networking if lower hard/soft limits were inherited.
exec avoids an extra waiting shell process while parent+extractor coexist.

Reproduction: do not reuse this directory or rerun a failed/source attempt.
Future fetches require a new authorized budget and unique inspected version.
Offline saved text/PDF/hash comparison is distinct from a new source access.
Manifest records hashes of both implementations, protocol, config, installed
Python/extractor executables and old/new artifacts; exact Poppler version and
full dynamic-library lock may remain null, with no extra inventory subprocess.
