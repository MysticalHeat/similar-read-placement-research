# S018 document-only audit — inspection and fixed execution plan

New unique documentation directory, NOT E-ID/raw/trace/model evidence.
Approval: user request and protocol/temperature-poc-checkpoint-2026-10-01.md
last section; related unresolved claim C022. Existing state is read-only.

Script: ../../scripts/inspect_spc_doc_v1.py (first-party, stdlib only).
One implementation and one execution pass; no debug executions or retries.
Agent will read the entire created script before the command below. This is
the prospective inspection checklist, not a claim of a test execution.
Installed tool inspected through local poppler-utils copyright/metadata,
and at runtime through native ELF header + SHA256 and installed versions.
No Poppler source-level/dependency security audit claimed.

Inventory actually executed successfully (exit 0, shell timeout 5000ms):
`ulimit -t 1 && ulimit -v 65536 && ls -ld ".research/experiments" ".research/experiments/scripts" && command -v python3 && command -v pdftotext && times`
Python: /home/linuxbrew/.linuxbrew/bin/python3; pdftotext: /usr/bin/pdftotext.
Inventory `times` rounded self/children user/system CPU to 0.00s each;
wall value not measured separately, <=5s tool timeout. No installs or git.

Authorized intended command, from project root, shell timeout 55000ms:
`ulimit -t 7 && ulimit -v 65536 && ls -ld ".research/experiments/documentation/S018-2026-10-01-docaudit-a91c7e" && exec /home/linuxbrew/.linuxbrew/bin/python3 -I -S ".research/experiments/scripts/inspect_spc_doc_v1.py"`
The ls verifies the exact created parent before runtime output creation.
exec avoids keeping a separate shell alongside Python and extractor.

Inspection checklist: fixed URL only; default certificate verification;
proxies/redirects/HTTP compression/transfer encoding rejected; exactly one
opener.open; explicit Content-Length and body counter <=1MiB; exclusive
output opens; stdout text<=2MiB and stderr<=16KiB; capped JSON/logs; no
downloaded-code execution; no trace links, license acceptance or actions.
PDF saved as source.pdf even on failure; completeness comes from manifest,
not filename. Failed/partial files must never be rewritten/deleted.

Budgets: inventory<=5s plus shell<=55s; script watchdog45s with cleanup
deadline50s. Controlled CPU ceilings: inventory shell1+ls1, execution
shell/Python7+ls1, extractor20 =30 CPU-s. Simple exec/one-child lifecycle.
Concurrent address-space limits Python64MiB+extractor192MiB<=256MiB;
inventory shell64+ls64<=128MiB. RLIMIT_AS is not RSS/cgroup enforcement.
Child RLIMIT_NPROC0, CPU20, FSIZE2MiB, CORE0; minimal fixed environment.
Child seccomp denies network/socket, process creation, io_uring and file
write-open/create/rename/unlink calls. Parent verifies seccomp support before
network. Not a full sandbox: filesystem reads/other syscalls remain possible,
system binaries/libraries are trusted, host/DNS/kernel resources not cgroup
accounted. pdftotext is invoked only for text extraction, never PDF actions.
Source body cap excludes HTTP headers/TLS overhead; wire bytes unmeasured.

Limits fail closed on unsupported platform/uid/tool. SIGALRM kills and reaps
the sole child through finally; outer tool timeout is a last-resort bound.
Hard kill/OOM can prevent final manifest; preserve partial files and STOP.
No synthetic/ML harness or confirmatory matrix applies to this source audit.

Reproduction: do not rerun the command in this used directory. A future audit
requires fresh human authorization, inspected version with a new unique
directory, and a new one-attempt budget. Offline reading of saved PDF/text
and comparison with manifest hashes does not re-fetch or examine traces.
Manifest records script/protocol/config/output hashes, runtime/compiler,
OS/CPU, selected local packages, exact commands, timers, rusage and failures.
Git commit and complete shared-library dependency lock are unresolved; no
git commands/installs/network dependency retrieval are authorized here.
