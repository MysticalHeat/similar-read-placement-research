# S018 doc-only handoff: extraction complete; memory accounting caveat

2026-10-01. Agent read all191 lines of extracted.txt, manifest.json,
audit.log, empty extractor.stderr.log and manifest.sha256 using read tools.
No additional execution, web access, trace access or delegation follows.
This NEW first-party handoff note does not edit the immutable runtime manifest
or existing C022/state/protocol/literature. Orchestrator must independently
verify exact source support before integrating claims. This is not ML/SSD
evidence, read counts, actual trace content or a dataset-suitability pass.

## Actual command and status

From /home/nomli/workspace/bdss_lab/research1, shell timeout55000ms:
`ls -ld ".research/experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0" && exec /home/linuxbrew/.linuxbrew/bin/python3 -I -S -B ".research/experiments/scripts/inspect_spc_doc_v2.py"`
Exit0. Internal child command: `/usr/bin/pdftotext -layout -enc UTF-8 -eol unix - -`,
exit0, PDF delivered through stdin, UTF-8 stdout captured exclusively.
Source requests1 (previous v1 requests0), runtime retries0, redirects0.
HTTP200, application/pdf, identity, Content-Length127256; body and PDF magic
validated. TLS used existing system CA bundle, no proxies/credentials.

Python runtime3.403616837s through final bounded stdout; transfer3.321873093s,
PDF-input/text extraction0.012340401s. These are operation timings, NOT a
benchmark. Child was launched once beforehand to verify inherited/actual
limits and seccomp before any network request; no separate probe/helper.
Final process-tree CPU0.093322s, including waited children where inherited;
parent pre-final user0.045640/system0.020745s, children user0.013393/system
0.012176s. Prior inventory separate<=5s/<=2CPU-s; its exact timings unknown,
displayed times rounded0.00s. Shell setup/ls wall not separately measured,
whole call bounded55s; no invented exact combined wall/CPU.

Started2026-10-01T05:37:49.105675+00:00, source body completed
2026-10-01T05:37:52.437954+00:00, runtime ended
2026-10-01T05:37:52.451682+00:00.
OS Linux7.0.0-34-generic x86_64; logical CPUs22; exact CPU model=null.
Python3.14.6 / GCC13.3.0; OpenSSL3.6.3. Extractor package version/full
dynamic-library lock/commit=null, exact installed binary hashes in manifest.
No RNG/warmup/concurrency benchmark/model/split/independent replicate applies.

## Enforcement observed and limitation requiring disclosure

Manifest records initial AS/CPU/FSIZE unlimited (so inventory tiny limits
were NOT inherited). Before network parent AS soft67108864/hard201326592,
CPU8/20s, FSIZE1048576/1048576, CORE0. Child handshake records inherited
parent ceilings and actual AS201326592/201326592, CPU20/20s,
FSIZE1048576/1048576, NPROC0/0, CORE0, seccomp mode2, no_new_privs1 and
parent-death SIGKILL. Parent never raised its AS soft cap; end-of-run check
confirmed it remained64MiB. Child network/fork/write-open syscalls denied,
fixed minimal environment, no credential forwarding. Operation watchdog45s,
cleanup deadline50s; no timeout/failure occurred. All output opens exclusive.

**RSS compliance is NOT certified.** RUSAGE_SELF.ru_maxrss reports
1111816KiB (above256MiB); waited children maxrss20068KiB. Linux high-water
rusage can include process history across exec, so the parent value may
reflect pre-interpreter process history. Attribution is UNKNOWN: this script
did not separately sample current Python RSS/VmHWM or isolate execution in a
cgroup. Do not substitute AS soft64+192MiB for measured RSS. Runtime
`status=complete` certifies download/extraction checks, NOT resolution of this
memory-accounting anomaly or total-host memory compliance. No extra helper
or execution to investigate it is authorized here; disclose and STOP further
execution. Child/parent AS enforcement is not a complete OS sandbox; system
Poppler/shared libraries trusted and filesystem reads remain possible.
Wire/TLS/header/DNS overhead unmeasured; download byte cap is application body.

## Artifacts/checksums

Runtime old+new documentation AND v1/v2 scripts total215692 bytes before this
new handoff note, far below5MiB. This note is separately bounded below12KiB,
so combined artifacts remain below228000 bytes (<5MiB); note's exact byte
size/hash not measured, no second execution added. Manifest stays unchanged.
PDF127256 bytes, text10383 bytes, stderr0, audit.log446, config1547,
manifest9619, manifest.sha25680. Runtime hashes:

| Artifact | SHA256 |
|---|---|
| source.pdf | 442b3c6c64fec10ebcc7221b088640925f0ca3cc3f6e2c6e9f30acf7e9c9ae06 |
| extracted.txt | 46f6ce13476746a7d753b7bdd365310f56e8e1dac49f0406ebd7881b7cba9ddf |
| inspect_spc_doc_v2.py | 256eb1ac0faddadefe3aea94ea99868216563c921b081ac98193f8e027f73e94 |
| config.json | 617d916257ad8d0bc7b43d8820b8dcaa3c4fb0ed8755cc7d3adfb2a2c3250918 |
| manifest.json | 94493b5fc74efeee6fc485199508866b11b0ddeca0fa20f336246f07414f29ce |

Source URL: https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf .
v1 script and all its docs fingerprinted read-only in manifest; no changes.
Each artifact resolves in this directory except scripts in ../../scripts/.
No E-ID/raw/artifact deletion/overwrite/Git command/install/terms acceptance.

## Source identity and pagination

Title exactly visible: **SPC TRACE FILE FORMAT SPECIFICATION** (L1).
Cover credit exactly visible: **Storage Performance Council (SPC)** (L7).
Personal author/byline list=null. Cover revision **1.0.1** (L2).
Cover copyright **1999, 2002 Storage Performance Council** (L15), NOT
automatically a publication date. Separate document issue date=null.
DOCUMENT HISTORY on physical PDF page2 (L33–37) lists Effective Date
**28-Feb-99**, Version**1.0.0**, Initial draft; and **17-Jul-02**,
Version**1.01**, Allowed white space characters in field contents /
Miscellaneous formatting changes. Preserve cover/history version notation
disagreement, do not silently normalize1.01 to1.0.1.

Extraction contains6 form-feed delimiters/6 nonempty pages. Physical PDF
page index by delimiters:1 cover,2 membership/history,3 introduction,
4 format/fields1–4,5 opcodes/timestamp/optional fields/example,
6 example explanation. Printed pagination disagrees with physical indices:
physical3 prints Page2of6; physical4 prints Page3of6; physical5 prints
Page4of6; physical6 prints Page5of6. Locators below give BOTH where visible.
The literal sample records are specification examples, NOT downloaded traces.

## Proposed exact-support verification record for C022 (not claim-state edit)

| Item | Visible primary support | Limits |
|---|---|---|
| Record/schema | Physical4 (printed3), §§1.1–1.2, L75–89: variable-length textual records, comma(hex2C) separated, newline terminated; one I/O command per record; five required fields plus optional fields at end. Field order is ASU,LBA,Size,Opcode,Timestamp in §§1.2.1–1.2.5. | Format specification, not proof any listed file conforms. Required whitespace may only appear between comma and beginning of next field. |
| ASU | Physical4 (printed3), §1.2.1, L91–97: “Application specific unit (ASU)”; “zero based, monotonically increasing number”; first record need not ASU0 but unit0 must exist; complete trace with n units includes at least one record for each0..n-1. | Also calls it “positive integer”; retain literal wording/zero convention. References SPC Global Parameter document, NOT retrieved. Does not prove ASU equals physical disk/volume or one ASU per listed file. |
| LBA/address block | Physical4 (printed3), §1.2.2, L99–105: LBA “describes the ASU block offset”; “the size of a block is contained in the description of the trace file”; offset zero based and within ASU capacity in blocks. | Generic spec does NOT give fixed512-byte block size. Concrete workload descriptor/block size=null. Do not infer address units from sample Size values. |
| Request size | Physical4 (printed3), §1.2.3, L107–113: “number of bytes transferred”; zero legal/I/O subsystem dependent; “majority ... anticipated to be modulo512” but “this constraint is not required.” | Bytes for Size, not bytes per LBA block. Address+size/capacity language is not a conversion formula; no invented unit resolution. |
| Operation | Physical4–5 (printed3–4), §1.2.4, L115–125: single case-insensitive character; R/r read (ASU to host), W/w write (host to ASU). | Defines opcodes, not actual READ presence/counts in named workload files. |
| Timestamp | Physical5 (printed4), §1.2.5, L127–133: positive real offset “in seconds ... from the start of the trace”; s.d requires integer+fractional portions; nondecreasing across records; first record need not0.0. | Seconds, not Windows FILETIME. Precise issuance-versus-completion capture convention=null; per-file chronology/duration not examined. Equal timestamps permitted; physical6/printed5 L183–185 discusses possible simultaneous hosts or poor capture resolution. |
| Optional fields | Physical5 (printed4), §1.2.6, L135–151: contents not defined, may vary per trace, number may change within file, may be absent per record. | Parser should not assume exactly5 fields or fixed optional count; no parser/protocol adaptation performed here. |
| Rights | Physical1 cover L15 copyright only; entire extracted191 lines read. | No dataset-specific license/use/access terms found in this text. Rights=null; no terms accepted, no CC-BY transfer from website footer. |
| Workload-specific duration/units | Entire extracted text; §1.3 physical5–6 (printed4–5), L153–185 explicitly labels example records. | Financial/WebSearch recording span, concrete block size, continuous6h, ASU mix, actual data/read/class support all=null; example timestamps are NOT workload duration. |

This resolves generic schema/unit documentation support only for subsequent
independent orchestration review. It leaves crucial dataset-specific gates
unresolved; it does NOT approve E002/E003/download/training/SSD efficacy.

## Reproduction boundary

Saved source.pdf/extracted.txt and manifest/config/script hashes allow offline
inspection of what was retrieved and how. The exact executed command above
is recorded, NOT permission to run it again: the directory is used and exclusive
creation intentionally prevents reuse. No runtime/source retry permitted.
A future fetch or memory-harness repair needs a new authorized operation and
new immutable directory/version; interpretation/significance is analyst-owned.
