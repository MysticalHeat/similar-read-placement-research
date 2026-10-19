# Conference methods: bounded static audit

Date: 2026-10-07. Root: `/home/nomli/workspace/bdss_lab/research1`.
Status: **STATIC INSPECTION ONLY; partial artifact coverage.** User-authorized output is this new note only. No manuscript, protocol, hypotheses, evidence map, code or result edits.

## Scope, authority and limits

Objective: clarify R026 issue/completion semantics and R030 screening chronology/source duration using existing local primary artifacts. The original R026/R030 finding texts were not retrieved by the bounded searches; the labels below refer to the issues as described in the user request, not a formal reviewer closure.

Research state/decision log inspected: `.research/README.md:3–17,27–30,69–76`. Current conference work differs from the historical synthetic milestone; the 2026-10-07 decision permits preparation, not new training/experiments. State files were searched, not all read fully: `.research/{brief.md,question.md,hypotheses.md,claims/evidence-map.md,reviews/peer-review.md}` retain historical draft/proposed/empty or synthetic statuses. No new scientific-design approval is inferred. Scoped protocols were inspected as local documents, not independently authenticated preregistrations.

Exactly **15 native read/search calls** (7 grep, 7 read, 1 glob); some searches hit the tool's 100-match truncation. Only displayed text supports this note. Initialization reported `created: []`; no raw artifact operation occurred. No shell, import, execution, recomputation, web, test, fitting or experiment. Commands run: **none**; exit codes: **not applicable**; E-IDs/raw manifests: **none created**. Existing checksum strings were inspected, never recalculated. Tool retrieval of a file is not execution verification or historical-access verification.

## R026: target is issue-to-issue, not completion latency

**Direct code support.** In `read_prediction/pipeline.py:68–82`, the seven-column parser unpacks `ts, host, disk, kind, offset, size, response`; `Event` retains only timestamp/kind/offset/size (`:34–39,75`). ResponseTime is checked for nonnegativity (`:78–79`) but not retained in the event. The next-read target is

`(Timestamp[next Read] - Timestamp[current Write]) / 10_000_000`

at `pipeline.py:118–132` (tick conversion `:21`). There is no addition of Read or Write ResponseTime. The compact path likewise stores only timestamp/offset/size/is_read (`read_prediction/extended.py:23–26,48–70`) and computes target by timestamp subtraction (`:136–140`). Range labeling explicitly describes issue-to-issue intervals and uses the same subtraction (`read_prediction/range_label.py:165–172,191–198`).

**Bounded conclusion:** these inspected label builders implement **Read issue timestamp minus Write issue timestamp**, not read completion minus write completion, service time, or end-to-end SSD latency. ResponseTime is an input-validity check, excluded from the inspected target and feature vectors. This is a local implementation/construct finding; official dataset timestamp documentation was not re-retrieved in this audit.

### Next Read, next Write and partial overlap

| Method fact | Exact support | Qualification |
|---|---|---|
| Same-start next Read is the first later source row with identical starting Offset. Intervening Writes do not cancel it. | `pipeline.py:92–97,118–132`; `docs/protocols/data-sufficiency-protocol.md:11–15`; `docs/protocols/long-history-protocol.md:17–18` | Address access, not consumption of the data version produced by that Write. Multiple Writes can target the same Read. |
| Same-start future-candidate matcher requires a row after the query and identical Offset. | `range_label.py:109–132`, especially `:126–131` | Generic matcher inspected; full same-start overwrite caller was not inspected within budget. |
| Range next Read and overwrite are found independently: earliest later Read and earliest later Write whose byte range intersects the query Write. | `range_label.py:52–56,94–106,175–189` | Any nonempty overlap suffices; it is not necessarily a full overwrite. |
| Ranges are half-open `[offset, offset+size)` and the implementation requires nonnegative aligned offsets and positive 512-byte-aligned sizes. | `range_label.py:1–8,19–23,73–74,188–189` | Grid enforcement code is inspected; no trace-wide alignment recomputation. |
| Range overwrite delay/lifetime is next intersecting Write timestamp minus query Write timestamp in seconds. | `range_label.py:183–198` | Not completion time, full invalidation time, or guaranteed data-version lifetime. |
| Read-first/Write-first is decided by row-index comparison. | `range_label.py:135–142` | `read < overwrite`; missing candidates are represented separately. This state does not itself cancel the independent next-Read target. |

The inspected submission reporting source also spells out partial range overlap (`read_prediction/submission_overwrite.py:93–96`, retrieved by search). It describes unknown overwrite intervals as window-derived lower bounds, not actual delays (`:96–97`); the protocol gives the same rule (`docs/protocols/mean-overwrite-protocol.md:14–28`). This reporting statement is not independent verification of its numerical output.

### Event ties versus model-selection ties

Equal timestamp events follow **original source row order**, not response/completion order or an invented Read-before-Write priority. Nondecreasing timestamps are enforced, so equal timestamps are allowed (`pipeline.py:80–82,95–96`; `extended.py:53–54,90–96`). A later row at the same timestamp can give a zero target interval. A prior row at the same timestamp can already contribute to history. Thus “past-only” here means **earlier source rows**, not strictly smaller timestamps. Generic same-start matching starts after the query row (`range_label.py:126`); range matching is documented and implemented by row indices (`:52–56,94–106`).

Selection ties are different: long-history specifies maximum validation lower pass, then lower MAE, then method name, with a separate MAE-best selection (`docs/protocols/long-history-protocol.md:31–33`). Final mean-overwrite selection specifies minimum observed-Read validation MAE, then method name (`docs/protocols/mean-overwrite-protocol.md:7–12`). The selection helper implementations were not read; these tie rules are protocol support, not a runtime check.

## Temporal boundaries and causal-history semantics

**Boundary facts:**

- Screening: per-trace origin; train `[0,14.4h)`, validation `[14.4h,19.2h)` (`docs/protocols/data-sufficiency-protocol.md:9–15`). Separate counters are created (`read_prediction/experiments/data_sufficiency.py:96–101,122–124`), so pending Writes in one window cannot be completed by Reads in the other. Prefix checks explicitly subset each window (`:80–93`).
- Initial pipeline: time cuts use `searchsorted(..., side="left")`; Write membership is half-open and a completed label must have its Read before the split's exclusive end (`pipeline.py:140–172`). Unresolved Writes are censored, not synthetic negative/long labels.
- Long-history: train `[0,72h)`, validation `[72h,96h)`, daily development evaluation days 5–7; train labels must finish before 72h and other labels before their own window end (`docs/protocols/long-history-protocol.md:10–20`). Code constructs day cuts and calls `local_labels` on train/validation slices (`read_prediction/experiments/long_history.py:76–85`). Days 5–7 reuse saved labels (`:123–138`). The inherited `local_labels` implementation and its complete boundary behavior were not retrieved in the final truncated search. Protocol intent and visible caller bounds are supported; complete implementation verification is unresolved.
- Train horizon can be 72h while each evaluation horizon is 24h; do not describe identical observation horizons (`docs/protocols/long-history-protocol.md:19–20`). Final-day calculations clip the observation boundary to recorded `last_timestamp` (`long_history.py:135–137`), rather than treating requested duration as observed coverage.

**History facts:**

- Seven inputs: offset, size, prior Read count, prior Write count, time since prior Read, time since prior Write, most recent Read–Read interval. `pipeline.py:22–26,43–48,100–116` and `submission/models.json:2–14` agree on names and same-start Offset history for both label rules.
- Forward implementation extracts the current Write's vector **before** incrementing that Write's history (`pipeline.py:104–112`). Read events update counts and last Read–Read gap (`:113–116`). Missing history becomes NaN, and each available input is transformed with `log1p` (`:107–108`).
- Compact construction sorts by Offset stably, preserving source order within each address, then scatters back to chronological Write order (`extended.py:90–105,118–140`). Counts/recencies use preceding positions, while next-Read truth is constructed separately. The current Write is excluded from prior Write counts (`:120–129`).
- Feature history is **same-start**, even when labels use range overlap (`submission/models.json:14`). A Read starting elsewhere and intersecting a range is not automatically included in that range's feature history.
- Long-history protocol freezes weights/address medians after train, while history continues to update causally (`docs/protocols/long-history-protocol.md:13–15`). The visible runner uses precomputed features and fits on completed train rows only (`long_history.py:73–74,80–106`), with models retained for later predictions (`:116–134`). It does not establish a physically isolated online feature service or retrospective absence of access to future arrays.

**Safe wording:** “Features describe earlier events in source-row order at the same starting Offset, before the current Write; fitted predictors are not updated on evaluation labels.” Do not strengthen this to “all data strictly precede the Write timestamp,” “range-aware history,” or universal leakage freedom.

## R030: selection-prefix access is not proof of historical non-access

### What the protocol and current screening code support

The screening protocol says to inspect the prefix through the first event at/after 19.2h or EOF, not days 2–7 (`docs/protocols/data-sufficiency-protocol.md:9–10`), and to rank eligible new traces by validation distinct target Reads, then train distinct target Reads, excluding three control workloads; no future MAE/pass selection (`:42–44`).

The implementation streams each gzip member and breaks at the first timestamp at/after the 19.2h threshold (`data_sufficiency.py:102–118`). Importantly, it **reads and parses that first excluded row** before deciding to stop; it does not process/count/hash that boundary row (`:119–127`). Hashes cover included source lines, not the complete archive/member. Gzip/tar buffering and archive member metadata enumeration are not equivalent to semantic use of subsequent events (`:102–104,150–154`).

Eligibility uses fixed counts/address support and distinct target-Read support (`data_sufficiency.py:59–77`). Ranking uses only those screen outputs, not model performance (`:165–172`). Multiple pending Writes completed by one Read are explicitly distinguished from the number of distinct completing Reads (`:26–38,43–55`; protocol `:33–40`). Those support counts do **not** establish statistically independent experimental units.

**Supported implementation claim:** “The inspected screening implementation bases eligibility/ranking on the initial 19.2-hour same-start label-support window, with one excluded boundary-row lookahead, not on subsequent-day prediction errors.”

**Unresolved historical claim:** “No later-day data or results had ever been accessed before workload selection.” Code and a protocol cannot prove that chronology. The original reviewer records, execution timestamps/access records, selection artifact chronology and any screening verification artifact were not retrieved sufficiently to establish it. No formal R030 closure is warranted on that proposition.

The long-history protocol explicitly says the workloads' days were already inspected and this is development, not a new holdout (`docs/protocols/long-history-protocol.md:3–4`). The final mean-overwrite protocol reiterates days 5–7 were already viewed (`docs/protocols/mean-overwrite-protocol.md:26–28`). `long_history.py:117–138` writes a frozen selection before its evaluation loop, but a current code path does not erase earlier inspection. Describe days 5–7 as **development evaluation**, not untouched confirmatory evidence.

### Source duration: approximately seven days, not exactly 168 observed hours

Both source records identify `dataset/msr-cambridge1.tar` and their respective gzip members/volumes (`results/new-workloads/proj_1/source.json:2–7`; `results/new-workloads/prn_1/source.json:2–7`). Each records requested hours 168, cap 100,000,000, `stop_reason: "end_of_trace"`, and no excluded timestamp (`:10–15` in each). Recorded endpoints:

| Workload | First timestamp | Last timestamp | Exact locator |
|---|---:|---:|---|
| proj_1 | 128166372003314839 | 128172419997366338 | `results/new-workloads/proj_1/source.json:13–14` |
| prn_1 | 128166372003457261 | 128172419953311946 | `results/new-workloads/prn_1/source.json:13–14` |

With the inspected 10,000,000-ticks/second convention (`pipeline.py:21`; `range_label.py:165`), these endpoints support the coarse description **approximately seven days**. No exact duration was recomputed here. `requested_hours` is a loader setting, not observed elapsed time, complete 168-hour coverage, or proof of uninterrupted capture. The loader distinguishes EOF from reaching the requested boundary (`extended.py:38,57–59,80–86`).

Existing provenance strings, **not independently rehashed**:

- proj_1 prefix SHA256: `a6961cdc5380ba5567972aa60ee18487cc89067dfd120bebefb6912feb6e815e` (`source.json:8`); loaded events 23,639,742 (`:9`).
- prn_1 prefix SHA256: `db1dba179e02637d33112562bb639e18867db716a5aa9e377997867322aff3c7` (`source.json:8`); loaded events 11,233,411 (`:9`).
- Screening per-workload endpoint fields were visible at `results/data-sufficiency/proj_1.json:8–9` and `prn_1.json:8–9`. They are prefix endpoint records, not complete historical access logs.

## Feature transforms, packaged predictors and reproducibility pointers

`submission/models.json:11–16` records log1p inputs for prn_1, raw Offset for proj_1, NaN missing history, days 1–3 training and day 4 observed-Read MAE selection. For proj_1 the selected predictor is an address median, so this metadata alone should not be described as a separate raw-feature LightGBM recipe.

There are **four workload/rule predictor entries**, not six selected learned models: proj_1 same-start/range use two separate address-median tables; prn_1 same-start/range each use `mix_log25` with log-L2 weight 0.25 and separate log-L2/raw-L1 model files (`models.json:17–47`). Thus the package references **four LightGBM files plus two median tables** (`:50–73,79–85`). The actual mixture arithmetic/predictor implementation was not inspected; the complementary weight and functional behavior are not independently established by this metadata alone.

The long-history fitting code trains log-L2 on log1p seconds and raw-L1 on seconds; both use the same supplied feature arrays. Fixed recipe: 150 estimators, learning rate .05, 31 leaves, minimum child samples 50, lambda 1, seed 42, 2 threads, deterministic and column-wise flags (`long_history.py:96–106`). Log predictions are mapped by expm1 and all predictions clamped nonnegative (`:23–25`). No early-stopping/tuning is specified by the protocol (`docs/protocols/long-history-protocol.md:28–30`). These flags are not a demonstrated bitwise reproducibility guarantee.

Dependency/environment pointers located by glob: root `pyproject.toml` and `uv.lock`. Their contents/runtime correspondence were not retrieved before budget exhaustion. `pipeline.py:305–312` and `extended.py:242–251` show runtime/version/code-hash/resource fields intended by older runners, but their historical values are not an environment certificate for the current submission. `long_history.py:144–153` records provenance hashes and parent paths; `models.json:49–85` records package file sizes/hashes and source pointers. Neither was rehashed here; hardware/OS/runtime/compiler/revision/dirty state remain unaudited for the conference results.

## Proposed bounded claim entries (for orchestrator integration only)

Provisional IDs below are note-local proposals, not additions to the shared evidence map. Source IDs likewise denote inspected local files, not literature or new E-runs.

| Proposed C-ID | Bounded claim | Proposed S-ID / exact support | Verification, confidence rationale, caveat |
|---|---|---|---|
| C-CMS-001 | The inspected label builders measure Write-issue to next-Read-issue seconds; ResponseTime is excluded from target/features. | S-CMS-P: `pipeline.py:68–82,104–108,129–132`; S-CMS-R: `range_label.py:171–172,191–198`; S-CMS-E: `extended.py:23–26,48–70,136–140` | Direct static code support; high confidence in arithmetic/fields; official timestamp semantics not externally reauthenticated, execution unverified. |
| C-CMS-002 | Range overwrite means the first later intersecting Write issue, including partial overlap, not necessarily full invalidation. | S-CMS-R: `range_label.py:52–56,175–198` | Direct static support; high confidence in definition, no runtime/trace-wide grid verification. |
| C-CMS-003 | Equal timestamps use source-row order; features precede the current Write in that order. | S-CMS-P: `pipeline.py:95–116`; S-CMS-E: `extended.py:90–140`; S-CMS-M: `submission/models.json:14` | Direct static support; same-time prior rows can contribute; not strict timestamp precedence or universal leakage freedom. |
| C-CMS-004 | The current screening logic selects on first-19.2h support counts, not later-day MAE/pass. | S-CMS-D: `experiments/data_sufficiency.py:59–77,102–127,165–172`; S-CMS-DP: `docs/protocols/data-sufficiency-protocol.md:9–15,42–44` (code path relative to `read_prediction/`) | Direct implementation/protocol support; high confidence in visible selection inputs, historical non-access/chronology unresolved; boundary row read. |
| C-CMS-005 | Source records describe approximately seven-day EOF traces, with 168h requested, not exactly 168h observed. | S-CMS-SP: `results/new-workloads/proj_1/source.json:10–15`; S-CMS-SN: `results/new-workloads/prn_1/source.json:10–15`; S-CMS-P: `pipeline.py:21` | Direct metadata plus coarse endpoint interpretation; no exact duration recomputation, capture completeness or rehash. |
| C-CMS-006 | Days 5–7 are development evaluation, not a new untouched holdout. | S-CMS-LP: `docs/protocols/long-history-protocol.md:3–4`; S-CMS-OP: `docs/protocols/mean-overwrite-protocol.md:26–28` | Direct disclosure; high confidence in documented scope, no historical access chronology reconstructed. |
| C-CMS-007 | The submission specifies two address-median predictors and two prn_1 mixture predictors referencing four LightGBM files. | S-CMS-M: `submission/models.json:17–47,50–73,79–85` | Direct configuration support; high confidence in package metadata, no predictor execution or independent file-hash verification. |

## Unresolved issues and bounded next action

1. **R026 construct clarified statically**, but the reviewer finding text/status and conference prose were not inspected. Integration should replace completion-latency wording if present; do not announce formal reviewer closure.
2. **R030 historical screening chronology remains unresolved.** Current prefix-only selection logic is not proof of no earlier future-day access. The protocols themselves disclose development inspection.
3. A targeted search for `results/data-sufficiency/{verification,source}.json` returned no displayed matches. This does not establish their absence under other names. The verification artifact, checker output and complete recommendation list were not inspected; do not claim screening execution was independently verified. Several broader searches were truncated.
4. Full `local_labels` boundary handling, same-start overwrite caller, final mixture prediction arithmetic, package execution, lock/environment content and code-to-artifact identity were not verified. Narrow claims accordingly.
5. No request count/support statistic establishes independent units; no significance, efficacy, SSD performance or universal leakage claim follows from this audit.

Recommended next step: integrate only the bounded wording and exact locators above into the evidence map/manuscript. If historical R030 closure is essential, request a separately bounded native inspection of the original reviewer note and existing dated screening/selection verification records; no new experiment is needed merely to resolve documentation provenance. To reproduce **this audit**, inspect the cited local lines read-only; there is no computational rerun command or new run ID.
