# A Synthetic Demonstration of Future Read-Temperature Classification

**Provisional short technical report · 2 October 2026 · not submission-ready.**
Authors and affiliations: **TBD**. Venue: **TBD**. Internal evidence annotations are retained for inspection; human approval and independent manuscript-level citation verification remain required.

## Abstract

Future read-temperature classification is a possible input to storage placement decisions, but classification quality alone cannot establish an SSD performance benefit. This technical note reports a fixed synthetic demonstration of a pipeline that constructs past-only features, labels pages by future read counts, and compares methods on identical page–time keys. Two six-hour scenarios contain 96 logical pages each: an engineered three-state cycle and a fixed-seed negative scenario without the cycle's predictive dependency. A historical-frequency heuristic, an always-cold baseline, a count-only tree, and a four-feature tree are evaluated using temporal splits without tuning. Eleven selected checks passed, and evaluation predictions for both scenarios were committed before evaluation truth was opened in the comparison stage. In the cycle, both trees achieved macro-F1 of 1.000; on the negative test split, the four-feature tree scored 0.274 versus 0.331 for historical frequency. These observations support the pipeline only within the selected finite checks. Real-workload predictability, physical placement, migration costs, novelty, and SSD speedup remain unverified. [C037–C040]

## 1. Introduction and question

The motivating longer-term question is whether forecasts of future read activity could guide placement and, under appropriate resource and workload conditions, improve useful demand-read throughput. This remains a conditional hypothesis, H005, not a result of the present demonstration. Forecasting, placement, and concurrent service are distinct steps: logical temperature groups do not guarantee independent hardware resources or simultaneous ready requests. [C017: UNVERIFIED efficacy]

We therefore isolate a narrower question: can a fixed implementation construct causal features and future READ labels, agree with manual and recipe expectations, and evaluate methods using common masks and keys on two predefined artificial traces? Success does not require a trained model to win or exceed a practical improvement threshold. The deliverable is an inspectable pipeline demonstration rather than an SSD benchmark, literature reproduction, or novelty claim. [C037]

The synthetic scope also avoids treating unsuitable local files as read data. A prior structural inspection found 515,114 rows in `hm_0.csv` and 2,427,089 in `prxy_0.csv`, all with first token W. Under the relevant R/W interpretation, these files provide no read labels; their semantic provenance remains unknown. [C014/E001]

## 2. Related work: scheduling versus invalidation prediction

The verified literature supplies context, not evidence for our classifier's effectiveness. Sprinkler describes architecture-specific plane-sharing address constraints and FARO scheduling, which exposes requests to controllers early for transaction coalescing with spatial and temporal locality [1]. This concerns scheduling and command compatibility, not the future read-temperature classifier studied here. [C001, C004/S003]

Predictive grouping also appears in write-oriented storage work. SepBIT groups written blocks by inferred block invalidation time to reduce write amplification; its trace analysis considers only write requests [2]. DOGI's official abstract describes invalidation prediction and evaluations using simulations and a zoned-device prototype, with write amplification and write throughput as outcomes [3]. DOGI's full text was not read. Neither source establishes read-temperature predictability or read-parallelism gains for our pipeline. [C002/S009; C003/S010]

Separately, a static audit of the inspected FTLSim-MiDA source version found serial time accumulation rather than a concurrent completion timeline [4]. That inspected accounting cannot establish throughput gains from overlapping reads; the repository was not executed in this demonstration. [C010/S013] The bounded exploratory literature search through 30 September 2026 did not establish novelty. Differences in objectives are not proof of a research gap.

## 3. Methods

### 3.1. Fixed artificial workloads

Each case contains one namespace, `synthetic0`, with 96 logical 4 KiB pages over [0,21600) seconds, divided into 36 bins of 600 seconds. For page p and bin j, the cycle assigns

`c[p,j] = (0,1,4)[(p % 3 + j) % 3]`.

The negative case uses `random.Random(42)`: one `randrange(3)` per bin–page pair, with bins ascending and then pages ascending, selecting counts from (0,1,4). The seed was fixed, not searched. Count zero creates no READ; count one creates a READ at bin offset 300 seconds; count four creates READs at offsets 60,180,360,480. Every generated READ addresses one page. Registration WRITEs touch all pages at seconds 1,12001,16801. These preserve causal eligibility, including cold pages, without representing physical mappings. Gap events are generated but masked from analysis. [C037–C038]

### 3.2. Causal features, labels, and splits

At decision time t, U(t) contains pages observed in READ or WRITE events with issue time strictly less than t since the segment reset. Features use [t−600,t); the target counts READs in [t,t+600). Cold means zero, warm one or two, and hot at least three future requests. These thresholds are chosen conventions, not literature-supported optimal SSD temperatures. A request contributes one count to each overlapping logical page, not one per byte; manual fixtures cover multi-page boundaries and timestamp ties.

The four features, in order, are 600-second read count, 300-second read count, read recency clipped at 600 seconds, and 600-second write count. Recency defaults to 600 without a past read. Page identifiers, addresses, absolute time, generator phase, seed, and future information are not model inputs. Keys are `(case,split,namespace,page,decision_seconds)`.

Train spans 0–180 minutes, validation 200–260, and test 280–360, with two 20-minute gaps. Each segment resets history and eligibility and requires ten minutes of warmup. Decisions run from segment start plus ten minutes through end minus ten minutes, inclusively, every ten minutes. The 17/5/7 grids contain 1,632/480/672 page–time examples per case. Incomplete windows are censored with reasons, not labeled cold. Unseen pages use a cold default outside primary eligible-page scoring. [C037–C038]

### 3.3. Comparators and evaluation order

Z applies the temperature thresholds to historical 600-second read count; D always predicts cold. A is count-only CART; X uses all four features. Each case has its own A/X pair, fitted only on that case's training data: four benchmark fits overall, zero tuning, no refitting. Validation is a sanity report, not a selection set.

The custom standard-library implementation uses root depth zero, maximum depth three, minimum leaf size 50, and unweighted Gini impurity. Adjacent distinct training values define midpoint candidates; Gini gains and thresholds use exact `Fraction` arithmetic. Positive-gain splits are selected greedily, with ties resolved by feature order and then smallest threshold. Class ties resolve cold, warm, hot. There is no pruning, class weighting, or randomized splitting. This is not a replication of an external library implementation.

In E005, both cases' validation and test predictions and models were written exclusively and fsynced before any evaluation-truth file was opened. Truth had already been created offline in E004; the claim concerns access order in E005, not absence of truth anywhere. Both trained pairs underwent the finite future-mutation check without additional fitting. Source order and commit receipts support this bounded sequencing claim, not OS-level isolation. [C037–C038]

### 3.4. Metrics and units

Confusion matrices use true-class rows and predicted-class columns in cold/warm/hot order. For each class, F1 = 2TP/(2TP+FP+FN); macro-F1 is the mean across the three fixed classes, not accuracy. A zero denominator yields computational zero with a flag. Hot precision without hot predictions and recall without hot support are NA. Scores and paired differences are descriptive. The whole constructed case is the reporting unit; dependent pages and windows are not independent replicates. No pooled score, p-value, confidence interval, or power claim is reported.

## 4. Results: observations

E004 records 6,048 cycle events and 6,174 negative events, totaling 12,222. Eleven selected test methods passed with eight toy fits and no benchmark fits. Counts and labels matched recipe expectations in 6,912 bin comparisons and 5,568 decision comparisons. The full unit-test suite and separate defensive adapter-negative suite were not run. E005 records four benchmark fits, zero tuning fits, and a passed frozen-model mutation check. [C038]

**Table 1. Macro-F1 and descriptive contrasts.** N denotes page–time keys, not independent workloads. Values are rounded from stored all-stratum scores; differences use unrounded scores. [C039–C040]

| Case / split | N | Z | D | A | X | X−Z | X−A |
|---|---:|---:|---:|---:|---:|---:|---:|
| phase_cycle / validation | 480 | 0.000 | 0.167 | 1.000 | 1.000 | 1.000 | 0.000 |
| phase_cycle / test | 672 | 0.000 | 0.167 | 1.000 | 1.000 | 1.000 | 0.000 |
| independent_negative / validation | 480 | 0.326 | 0.162 | 0.251 | 0.259 | −0.067 | 0.009 |
| independent_negative / test | 672 | 0.331 | 0.162 | 0.248 | 0.274 | −0.057 | 0.025 |

Cycle true support is 160 per class on validation and 224 on test; A/X have diagonal confusion matrices. Negative true support is 154/173/153 on validation and 216/227/229 on test. Neither negative-case tree predicts cold on these held-out keys, giving cold F1 zero. D's hot precision is NA, not zero. Both trained methods trail Z on both negative splits; the exact test X−Z difference is −0.05689211147220635. [C039–C040]

All four evaluation audits show read-incidence coverage one and no unseen future pages; selected censored-window counts are zero. All 96 pages are eligible at each decision by construction. Thus the held-out scores do not demonstrate generalization to previously unseen pages. [C037–C040]

## 5. Interpretation

The cycle result has a simple explanation: both trees learn count 0 → warm, 1 → hot, 4 → cold. The engineered cycle defeats persistence-based Z by construction. A equals X, so no additional-feature benefit was observed in this case; this does not establish that the extra features are generally useless. [C039]

The negative case shows that successful technical checks do not imply model superiority. Its finite realization can contain chance correlations, and the observed absence of cold predictions matters to the macro-F1 result. This outcome is retained without seed selection or regeneration; it is not proof that every unpredictable workload must produce these scores. [C040] Neither result tests placement or the conditional forecast-to-throughput mechanism.

## 6. Reproduction record and operational outcome

The local bundle contains raw traces, features, labels, audits, models, predictions, checks, manifests, and reported source/configuration hashes. The scientific recipe is v0.1; practical runtime amendments and approval D001 govern the executed sequence. First-party Python standard-library code ran on Linux; exact runtime information is recorded in the freeze, but its long metadata tail was not fully inspected here. Hardware and repository revision/dirty-state metadata remain unresolved. This is a local archive, not a published release or DOI-backed deposit.

An earlier B001 bootstrap stopped before artifact creation at a kernel high-water RSS guard. Its numerical costs and current memory remain unknown. A subsequently approved amendment provided a separate additional 120-second observed-worker wall/CPU allowance and guarded sampled current VmRSS, retaining B001 separately rather than resetting historical costs. One worker/thread, a 1 GiB worker target, and 5 MiB for all new files were practical controls, not certified OS limits.

The three D001 calls report cumulative observed worker wall time 10.4577 seconds and CPU time 10.2074 seconds, with maximum sampled VmRSS 36,003,840 bytes (approximately 34.34 MiB). The separately recorded kernel peak is 1,778,753,536 bytes, with unattributed cause. E004's maximum sampling gap, 0.250056926 seconds, slightly exceeded the soft 0.25-second target. Tool records report intended return zero but separate OS exit null. Startup, tool, exit-tail, and B001 costs remain unknown; final footprint has not been recertified. [C041]

## 7. Limitations

Two contrived cases do not represent real workloads. Temporal separation still repeats the cycle's engineered relationship and page population. READ issue counts are not completed SSD reads, co-access, latency, or throughput. Registration is not mapping, and no physical intervention or migration-cost measurement occurred.

Internal checks reduce selected risks involving boundaries, resets, keys, and future leakage, but do not prove universal correctness. The trace counter and separately coded recipe expectations share RNG conventions; they are not independent replications. Custom CART bugs and common-mode errors remain possible. Reviewers inspected all-stratum metrics but only prefixes of long JSON records: other strata and complete provenance were not fully inspected. No full raw join, independent digest recomputation, or experimental replication was performed.

Independent outcome review found no new major defect requiring reanalysis for the bounded descriptive report. Historical R002 remains open, however, and no whole-domain RAM/time/disk compliance certificate exists. Earlier pre-outcome wording in preserved records is historical, not a current absence-of-results claim. Novelty and publication readiness remain unestablished.

## 8. Future work

Optional next work would use lawfully available real read traces, independently validate the counting and prediction artifacts, and compare fairly budgeted train-only transition or other simple predictors. An SSD study is separate: approve a concurrent timing model, physical mapping policy, workload/concurrency controls, and complete inference, relocation, and GC cost accounting before measuring useful demand-read throughput. These are proposals, not authorized experiments or current results.

## 9. Conclusion

The selected synthetic checks provide finite technical support for the pipeline. The count alone explains perfect cycle classification, while trained models underperform historical frequency in the fixed negative case. This demonstration establishes neither real read predictability nor an SSD performance benefit. [C037–C040]

## References

Metadata and support below follow local records retrieved 30 September 2026; no new retrieval was performed. Exact arXiv revisions are unknown. Source findings were not replicated.

1. Myoungsoo Jung and Mahmut T. Kandemir. *Sprinkler: Maximizing Resource Utilization in Many-Chip Solid State Disks*. HPCA, 2014 publication relationship recorded; inspected arXiv rendering submitted in 2017, not the original publication version. https://arxiv.org/abs/1705.04627. [S003; inspected full-text HTML passages]
2. Qiuping Wang, Jinhong Li, Patrick P. C. Lee, Tao Ouyang, Chao Shi, and Lilong Huang. *Separating Data via Block Invalidation Time Inference for Write Amplification Reduction in Log-Structured Storage*. FAST, 2022. https://arxiv.org/abs/2104.12425. [S009; inspected HTML abstract and §2.3; conference-version relationship recorded]
3. Jeeyun Kim, Seonggyun Oh, Jungwoo Kim, Jisung Park, Jaeho Kim, Sungjin Lee, and Sam H. Noh. *DOGI: Data Placement with Oracle-Guided Insights for Log-Structured Systems*. FAST, 2026, pp. 543–559. https://www.usenix.org/conference/fast26/presentation/kim-jeeyun. [S010; official abstract/BibTeX only]
4. `MysticalHeat/FTLSim-MiDA-implementation`. Software repository, commit `a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21`. https://github.com/MysticalHeat/FTLSim-MiDA-implementation/commit/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21. [S013; inspected source subset; bibliographic authors/year/title unknown]

## Appendix A. Drafting claim/source ledger

Paths are relative to `.research/`. P = `protocol/synthetic-temperature-demo-v0.1.md`; R4/R5 = `experiments/raw/E004/` and `experiments/raw/E005/`; K = `experiments/control/synthetic-deadline-v0.3/`. This ledger preserves existing claim IDs; it does not amend the evidence map.

| Claim / draft location | Evidence and exact locator | Qualification |
|---|---|---|
| C001, C004 / §2 | S003, `literature/source-notes.md` S003: inspected HTML §2.2 plane-sharing constraints; §4.2 FARO scheduling | Architecture-specific; context only |
| C002 / §2 | S009, notes S009: abstract grouping/BIT; §2.3 write-only requests | Write amplification, not read efficacy |
| C003 / §2 | S010, notes S010: official abstract invalidation prediction, zoned prototype, WAF/write throughput; catalog line 7 | Abstract only, not full-paper verification |
| C010 / §2 | S013, `experiments/simulator-audit.md` §§4–6; `Statistics.py` L111–124, `FTL.py` L36–100 at pinned commit | Static serial-accounting inference |
| C014 / §1 | E001, `experiments/raw/E001/profile.json` line 1: `files[].counts.rows`, `first_tokens`, `status`, `eof`, `stable` | Literal structure; semantics unknown |
| C037–C038 / §§1,3,4 | E004/E005; P §§2–6; R4 `config.json`; `checks.json` line 1: `checklist,status,invariants,toy_fits,benchmark_fits,cases`; R5 `manifest.json#checks` | Selected checks, not full suite |
| C037–C038 / §3.3 | R5 `prediction-commit.json#status,outputs,evaluation_truth_opened`; `resource-11.json#point`; adapter L415–457; results review L30–36 | Both cases/val/test before E005 truth access; finite mutation |
| C039 / §§4,5 | E005, R5 `phase_cycle.{val,test}.score.json` line 1: `seen_strata.all.methods.{Z,D,A,X}.{macro_f1,confusion,true_support}`, `paired_delta`; `models.json#phase_cycle` | Engineered inverse-count map; no extra-feature benefit observed |
| C040 / §§4,5 | E005, R5 `independent_negative.{val,test}.score.json`, same exact keys plus `predicted_support`; `metrics.csv` score rows 4–5/delta rows 8–9 in processed report | Negative finite result; no population estimate |
| C037–C040 / §4 coverage | R4 `{case}.{val,test}.audit.csv#seen,all,unseen`; four R5 score prefixes `censored_selected` | Coverage one; unseen generalization untested |
| C041 / §6 | K `{bootstrap-002,E004-001,E005-001}/return-record.json#stdout.observed_totals,memory,local_return_intended`; `actual_tool_OS_exit` | Observed worker/sampled memory only; B001 unknown |
| C017 / §§1,8,9 | `temperature-scoping.md` H005; evidence-map C017 | UNVERIFIED efficacy; no supporting SSD run |

### Historical commands — executed, not rerun instructions

```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_deadline_caller_v0.3.py --stage bootstrap --approval-ref D001
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_deadline_caller_v0.3.py --stage E004 --approval-ref D001.E004
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_deadline_caller_v0.3.py --stage E005 --approval-ref D001.E005
```

D001 permission is spent. E004/E005 are occupied immutable IDs. Independent reruns require new IDs/paths and a separately approved plan; do not execute these commands against existing artifacts. Exact approval: `protocol/synthetic-deadline-approval-D001-2026-10-02.md`. Detailed observations: `experiments/processed/synthetic-deadline-v0.3/analysis.md` and `metrics.csv`; latest outcome review: `reviews/synthetic-deadline-results-review-v0.3.md`.

## Declarations and publication checkpoint

Authors, affiliations, contributions, funding, conflicts, ethics requirements, release/license permissions, and venue-specific AI disclosure: **TBD by accountable humans**, not asserted absent or exempt. AI-assisted code preparation, writing, and review form part of this workflow; the final disclosure requires human checking and the applicable venue policy. No AI-model performance benchmark is reported. See [open-issues.md](open-issues.md). Polished wording is not scientific validation.
