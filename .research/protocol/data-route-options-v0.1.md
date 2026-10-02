# Data-route options for a tiny future-READ temperature PoC
2026-10-01 · v0.1 · **DRAFT / ALL ROUTES PROPOSED / EXECUTION STOP**
This is a decision aid, not an executable protocol, approval, source retrieval or result.
Ownership: only this new file; existing protocol, hypotheses, state, claims and raw artifacts remain unchanged.

## What is known, and limits of the record
- Approved numerical task: logical 4 KiB pages; history/H/step=600 s; cold=0, warm=1–2, hot≥3 future READ requests per page. See `temperature-poc-checkpoint-2026-10-01.md` §§Answer/Scope (Russian headings).
- Existing ceilings remain: download100 MiB, decode1 GiB, prefix250k requests/10k pages, train50k examples; RAM1 GiB whole process tree, 2 threads, wall15 min, aggregate CPU10 min, new disk1536 MiB; other v0.1 subcaps also remain. Caps are not permission or certified feasibility.
- C014/E001 contains all-W literal tokens, not usable READ labels under the R/W schema. C010 blocks parallel-throughput inference from the audited serial simulator; C017/H005 efficacy is unverified.
- Local evidence read: `../README.md`, `../brief.md`, `../claims/evidence-map.md`, `../temperature-scoping.md`, legacy question/hypotheses, literature map, v0.1/checkpoint and temperature review.
- Source locators: `../literature/alternative-read-source-discovery-2026-10-01.md` §§Budget/Exact support/Scoped negative; `../literature/spc-format-reading-2026-10-01.md` §§Exact support/Execution; `../reviews/spc-document-audit-2026-10-01.md` R002/R003.
- Discovery exhausted its 3 queries/5 fetches/3 families. No candidate has passed the documented-small-file metadata gate; no actual data suitability or quality has been established. This is finite inspected coverage, NOT proof that suitable data do not exist; novelty remains unresolved.
- Additional metadata below was independently retrieved by the orchestrator and supplied in this assignment (2026-10-01), NOT re-fetched here or integrated into the evidence map. Exact new retrieval artifacts/versions are not supplied here; confidence is in the reported metadata, not trace contents.
- Official Alibaba README: byte offsets/lengths, microsecond timestamps, R/W; reported tarball181 GB. No affordable small-file route established.
- Curated cacheMon README: CC BY/provenance links and full plain-text R/W formats are distinct from OracleGeneral `(timestamp,obj_id,obj_size,next_access_vtime)`. OracleGeneral loses R/W and carries a future-access link: NOT a substitute for ordinary block-I/O READ requests; never use that link as a feature/baseline.
- Supplied S3 plain-MSR listing at `cache_dataset_txt/2008_msr/`: three objects (tar1/tar2/zip), 3282677760/2022451200/5441159985 bytes, all>100 MiB. These are curated-object metadata, not measurements of official MSR downloads.
- Supplied S3 plain-Tencent listing at `cache_dataset_txt/2020_tencentBlock/`: README2052 bytes and `tencentBlock.zst`137224724902 bytes; data object>100 MiB. A small README is not a small trace.
- CloudPhysics remains a partial derivative lead: no actual small file known; documented sectors do NOT directly establish sector-to-byte size. Earlier note's broad unit/readiness language and Alibaba recommendation do not establish a current usable route.

## A — separate SYNTHETIC pipeline illustration (recommended for the short intent)
- Proposed goal: illustrate past-only features → future-window request counts → hot/warm/cold labels → identical evaluation keys for the heuristic/model, on a deliberately constructed fixture population.
- Proposed outcomes: inspectable request/label tables, boundary/leakage checks and, only if later separately approved, descriptive confusion/F1 and resource accounting. Hand-specified expected counts are expectations, NOT observed outputs; there are no classification/F1 results now.
- This changes the data population and scientific goal, not merely the source URL. Keep the real-trace question deferred; request explicit approval of a separate exploratory fixture question/hypothesis scope. Do not silently fix or strengthen H005.
- Retain approved page/H/labels as proposed illustration conventions; no SSD placement/speedup claim and no practical efficacy threshold for this illustration. The real PoC's ≥0.05 macro-F1 screen stays deferred, not transplanted as proof.
- Any fitted model on contrived data tests only those chosen rules; even high F1 or a designed advantage cannot validate real predictability, learned advantage or the proposed physical mechanism. Seeds are fixtures, not independent real workloads.
- Proposed cost boundary for a later design: zero network/download, no installs/paid services, within existing data/compute/storage ceilings; aim for a small bounded fixture, not to fill those caps. Runtime feasibility remains UNKNOWN, not promised in a few minutes.
- Gate before generation or fitting: exact approved versioned protocol specifying generator, request semantics, population/universe, expected checks, seeds/counts, splits, models/hyperparameters, analysis, resource enforcement and stopping rule. Those parameters are NOT selected here.
- A does not clear R002. Startup-through-cleanup whole-tree RAM/CPU/wall accounting and inspected code/environment must be defensible before any future execution; RLIMIT_AS arithmetic is insufficient. R003 remains open for SPC, not solved by avoiding it.

## B — user's lawful small real read trace (preferred for an empirical PoC if supplied)
- Proposed goal/outcome: retain the deferred real question—fixed depth-3 tree vs past-frequency heuristic, paired test macro-F1 difference≥0.05 with existing hot guardrails—on one eligible six-hour namespace prefix, not SSD throughput.
- No such file is assumed available. Ask for an existing lawful file AND source/version/rights, schema, timestamp capture, namespace identity and documented address/length units; sector-byte conversion must be explicit, not inferred as512.
- Ordinary primary events must identify original requests, R/W, time, address and length. Curated full R/W derivatives need explicit provenance/conversion acceptance; caching-derived OracleGeneral is excluded as a replacement.
- Proposed cost boundary: download0 if already local; otherwise≤100 MiB only after separate access approval; decoded≤1 GiB and all existing preparation/training/time/RAM/disk caps unchanged.
- Metadata first; freeze deterministic file/namespace choice before contents. Later bounded suitability must establish six-hour coverage, actual reads, cardinality and train support; no selecting traces by test labels, balance or expected model gain.
- Gate: source-specific parser/provenance adaptation, environment/limits/code/config freeze, then separate preparation permission and later fit/test permission. Failure/missing classes/censoring/cap excess means STOP/inconclusive, not relabeling or threshold rescue.

## C — original MSR bulk access under a separately expanded access/storage plan
- Proposed goal/outcome: eventually attempt B's unchanged real classification question using documented original MSR R/W byte-unit data (C015/S016); source access does not promise suitability or model benefit.
- C018/C019: inspected official pages advertise3.06/1.88 GB sets and first checksum names `msr-cambridge1.tar`. No archive bytes/members inspected; advertised sizes differ in evidentiary status from curated S3 byte listings above.
- Current100 MiB download cap excludes this bulk route. NOT recommended for a few-minute request; no download, range/archive shortcut or execution permission exists.
- Gate BEFORE access: human accepts lawful terms and a separate finite plan for exact archive/member selection, wire bytes, full integrity/decode work, temporary/storage footprint, wall/CPU/RAM and failures. Expanded numbers are unresolved, NOT approved or chosen here.
- Preserve page/H/labels and the classifier's caps by default; any additional budget/split/population change needs its own versioned decision. Early six-hour prefix suitability may still fail250k requests/10k pages or other gates; do not filter pages/shorten windows to force a pass. No promise it works.

## Human checkpoint and approval stops
- Recommendation: choose A only as a clearly labeled illustration if a quick tangible next milestone matters most; choose B if a documented lawful small file is already available. C is a longer separately budgeted path, not an automatic fallback.
- Optional future curated-file metadata verification is a separately requested finite task with named family/prefix, fixed query/fetch cap and STOP on exhaustion; not another unbounded search. Nothing further is searched now.
- Unresolved choices: A's changed population/question scope and whether any fitting is wanted; B's actual file/docs/rights; C's expanded access/storage budget. All routes still require credible runtime accounting; source metadata does not resolve read density/classes/coverage or expected efficacy.
- Validity: A has no real-workload external validity; B/C face coverage, provenance, drift, seen-universe bias and dependent page/window samples (one workload≠many independent replicates). All face leakage and construct mismatch; class F1≠SSD speedup. No power or success guarantee.
- Proposed decision question: **Prepare a separate synthetic fixture-only protocol (A), wait for your documented lawful small real trace (B), or design a separately expanded original-MSR access/storage plan (C)?** Selection approves only the next design step, not generation, downloads, fitting or test release.
- Before any method/hypothesis amendment preserve the prior version and record dated rationale/human approval BEFORE new runs; disclose later outcome-driven work as exploratory. There are no classifier outcomes to rescue here; local documentation is not public timestamped preregistration.
- Remain STOP: no training/results, data/model execution, source fetch, permission grant or R002/R003 closure follows from this document. Orchestrator records any future human decision; this file cannot approve it.
