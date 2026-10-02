# v2 final static inspection — approved for one bounded runtime attempt

2026-10-01. Agent read the FINAL entire first-party inspect_spc_doc_v2.py
lines1–428 with read tool after preparation edits, before any execution.
This is static inspection, not a successful runtime/filter or source audit.
v1 and all its docs remain unchanged. v2 is a preparation correction under
the orchestrator's explicit current instruction, not a source-access retry.
Previous source requests/downloads/extractions=0. No scientific design or
total numerical resource cap changes; no model/data/SSD evidence produced.

## Reviewed protections

- Parent L18–35 reads inherited limits and configures AS soft64/hard192MiB,
  CPU8/20s (default SIGXCPU), FSIZE1/1MiB, CORE0. Rejects inherited ceilings
  below needed values; parent never raises its own softAS thereafter.
- Child L174–188 raises ONLY child soft limits within inherited hard ceilings
  to AS192/192MiB, CPU20/20s, FSIZE1/1MiB; locks NPROC0/CORE0. A bounded
  handshake records inherited and actual values. Parent verifies BEFORE
  request L334. One actual installed pdftotext child waits for PDF on stdin,
  no separate inventory/probe/helper subprocess. It is the sole extractor.
- PR_SET_PDEATHSIG SIGKILL plus parent-pid race check binds child lifetime to
  parent even on default CPU signal/outer kill; extractor non-setuid/setgid
  verified before execution. Ordinary wall alarm kills/reaps child in finally.
- Child seccomp BPF reviewed: native x86_64 arch check, no x32; deny network
  sockets/process creation/io_uring and write-open/create/unlink/rename.
  JEQ/JSET relative jumps and flag-argument offsets reviewed. Parent installs
  arch-only filter to check kernel support; child handshake verifies filter
  mode2/no_new_privs1 before networking. Not a complete sandbox/security audit;
  installed ELF and system libraries trusted, filesystem reads remain possible.
- Child environment is a fixed minimal dictionary, no credentials/proxies.
  Python invocation adds -B to prevent bytecode-cache writes. This final actual
  command supersedes the prospective command in NOTES.md ONLY in adding -B.
- One opener.open, fixed authorized HTTPS URL, existing CA bundle verified
  TLS, no proxy/redirect/retry/compression; PDF MIME/magic required. Strict
  Content-Length<=1MiB and bounded body counter. Failed/partial source retained.
- Source/text/error output opens are exclusive; text<=1MiB, stderr<=16KiB,
  metadata/logs bounded. Read-only hash/byte accounting covers preserved v1
  script/docs plus v2 docs/script within5MiB. No raw/E-ID/state/claims changes.
- Operation watchdog45s, total deadline50s, tooltimeout55s; previous inventory
  <=5s/CPU<=2s. New parentCPU8+child20 within remaining28s subject to ordinary
  OS CPU signal granularity. RLIMIT_AS is NOT RSS/cgroup measurement, and host
  processes/kernel/network overhead are not cgroup-accounted. rusage/byte
  results will report actually observed usage, never simulated values.
- UTF-8/form-feed validation precedes completeness. Exact section/title/unit/
  rights support still requires reading extracted.txt; no source-snippet
  promotion and no512-byte LBA assumption. Exact dependency versions may be
  null; script/config/runtime/compiler and binary hashes recorded instead.

## Final command, not yet executed at inspection time

Project root, tool timeout55000ms; no inventory ulimits reused:
`ls -ld ".research/experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0" && exec /home/linuxbrew/.linuxbrew/bin/python3 -I -S -B ".research/experiments/scripts/inspect_spc_doc_v2.py"`
ls verifies existing exact parent before runtime writes. The fresh interpreter
checks getrlimit; incompatible inheritance stops before any source request.
Any failure means preserve all artifacts and STOP with no runtime retry.
Do not reuse this directory after execution. Offline inspection of saved
artifacts is the authorized handoff; another fetch needs its own new budget.
