# Finite synthetic analysis v0.3
2026-10-02. Static analysis, no execution/rehash/replication.
Paths relative to `.research/`; raw/state unchanged. C-IDs are proposals only.

## Design and access
Recipe: `protocol/synthetic-temperature-demo-v0.1.md` sections2-6; practical
amendment v0.2/deadline-demo v0.3, approved by
`protocol/synthetic-deadline-approval-D001-2026-10-02.md` lines3-15.
D001 replaces old gates; config placeholders/state remain pre-outcome wording.
96 pages of 4KiB/case,6h; history/horizon/step600s; future READ counts0/1-2/>=3
label cold/warm/hot. Train/val/test0-180/200-260/280-360min, gaps/reset/warmup10min.
Z=past frequency,D=always cold,A=count-only CART,X=four-feature CART;
depth3/minleaf50/seed42/tuning0. Target: finite same-key macro-F1 contrasts.
One realization/case, not iid; pages/windows dependent. No practical threshold,
CI/p-value/power/multiplicity test; planned description, not efficacy inference.
Full reads: checks/configs/audits/models/commit/return records/core/adapter.
Manifests/scores/freeze/outcomes prefix-only(2000 characters): used
`seen_strata.all` visible, other decision/zero-history/write-only strata partial.

## Observed results
E004 `checks.json` line1: status/invariants LOCAL_CHECKS_PASSED, 11 selected
methods/8 toy fits/0 benchmark. Events6048 cycle/6174 negative=12222;
bin comparisons3456 each=6912, decision comparisons2784 each=5568;
selected masks null. Bounded checks, not all inputs/full-suite proof.
E005 manifest prefix `checks`: benchmark_fits4/tuning_fits0,
frozen_mutation LOCAL_CHECKS_PASSED/all_predictions_committed_before_truth=true.
Commit line1: ALL_PREDICTIONS_DURABLE/evaluation_truth_opened=false.
Adapter `synthetic_stage_adapter_v0.1.py` lines415-476: BOTH cases' val/test
commit before truth(line457); not replay.

Dimensionless macro-F1, 3 decimals; `metrics.csv` exact stored values,
4 score + 4 delta rows, NOT 8 runs.
Source: `experiments/raw/E005/<case>.<split>.score.json` line1,
`seen_strata.all.methods.<method>` and `seen_strata.all.paired_delta`.

|Case/split|N|true cold/warm/hot|Z|D|A|X|X-Z|X-A|A-Z|
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
|cycle/val|480|160/160/160|0.000|0.167|1.000|1.000|1.000|0.000|1.000|
|cycle/test|672|224/224/224|0.000|0.167|1.000|1.000|1.000|0.000|1.000|
|negative/val|480|154/173/153|0.326|0.162|0.251|0.259|-0.067|0.009|-0.076|
|negative/test|672|216/227/229|0.331|0.162|0.248|0.274|-0.057|0.025|-0.082|

Confusion rows=true, columns=prediction, order cold,warm,hot. Cycle q=160
(val),224(test): A=X=[[q,0,0],[0,q,0],[0,0,q]];
D=[[q,0,0],[q,0,0],[q,0,0]]; Z=[[0,0,q],[q,0,0],[0,q,0]].
Negative val: A=[[0,48,106],[0,60,113],[0,60,93]];
D=[[154,0,0],[173,0,0],[153,0,0]];
X=[[0,78,76],[0,93,80],[0,88,65]];
Z=[[52,48,54],[52,60,61],[48,60,45]].
Negative test: A=[[0,60,156],[0,72,155],[0,85,144]];
D=[[216,0,0],[227,0,0],[229,0,0]];
X=[[0,120,96],[0,135,92],[0,131,98]];
Z=[[77,60,79],[76,72,79],[71,85,73]].
Manual supports agree. F1c=2*diagonal/(true+predicted support); macro=mean3.
cycle D=0.5/3; negative test X=(0+270/613+196/515)/3=0.273680,
Z=(154/440+144/444+146/460)/3=0.330572. Bounded arithmetic checks,
not replication. All absent-class/zero-denominator flags false;
D hot precision NA (no hot predictions).

## Coverage, exclusions and sensitivity
E004 `<case>.<split>.audit.csv` lines 2-6(val)/2-8(test) show unseen=[]
and seen=all at every decision: coverage1, unseen-default errors0.
Incidence denominators (manual sums): cycle val800/test1120, negative
val785/test1143. Incidences/decision: cycle160; negative val132-168,
test154-179. Run/task/dataset variance unestimable; censored_selected=0.
No selected rows/classes/cases excluded; gaps/warmup excluded by design.
B001 operational failure has no classifier score; cost UNKNOWN, not zero.
Sensitivity: validation repeats test directions; A=X cycle, both trail Z
negative val/test. No pooled winner/regeneration/seed selection.

## Interpretation / speculation
`models.json` line1: cycle A=X, feature0 thresholds1/2,5/2:
count0->warm,1->hot,4->cold. Engineered anti-persistence defeats Z, not extra
feature benefit. Negative A/X never predict cold on observed held-out keys
(true cold154/216), not counterfactual real data. Negative result retained.
SPECULATION: finite random correlations may affect trees; no population effect
estimated. No real traces/SSD simulation/layout/latency/throughput; H005 deferred.
Confidence direct for stored values, bounded for gates, no real-system support.

## Provenance, resources and handoff
Raw manifests: `experiments/raw/{E004,E005}/manifest.json`.
Declared manifest SHA256, E004 (commit/outcome):
`fe1901fe3ac9eca68149b265ed75c529027b2cb58d781910c1b26d5e0d6a12d5`.
E005 manifest SHA256 (outcome):
`07502d0395e22c515bfc0700e186bda3e7dc1a3d581c9b383ccdac7953b8d980`.
E005 `config_hash`/`identities`/`adapter_loading`: config/core/models/adapter
v0.1; commit `inputs`: features/train labels. Hashes NOT rehashed.
Runtime beyond freeze prefix; hardware/repo/dirty unknown. No processing script.
Historical argv: `/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_deadline_caller_v0.3.py`
plus `--stage bootstrap --approval-ref D001`, `--stage E004 --approval-ref D001.E004`,
`--stage E005 --approval-ref D001.E005`. Executed; occupied dirs, UNSAFE TO RERUN.
Control `experiments/control/synthetic-deadline-v0.3/{bootstrap-002,E004-001,E005-001}/return-record.json`:
intended0/no tool timeout/error/failure; actual_tool_OS_exit=null, not exit0.
Latest E005 `stdout.observed_totals`: wall10.457738917015377s,
CPU10.207397824000001s. Max sampled worker RSS36003840 bytes (~34.34MiB);
kernel peak1778753536 bytes separate/unattributed, not current worker RAM.
E004 max gap0.25005692600097973s slightly exceeds soft0.25s cadence.
Sparse samples/overhead/B001 unknown: no whole-domain120s/RAM/disk certificate.
Proposed C038 bounded checks/C039 finite cycle/C040 finite negative, locators above.
Pending independent outcome review/provenance/strata/hash/join audit and
orchestrator integration. STOP; no further execution authorised.
