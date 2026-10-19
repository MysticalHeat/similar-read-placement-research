# Predicting Next-Read Time at Write Arrival: Mean Error and Overwrite-Based Reliability

Elmanov Ilia — Master’s student

DSTU, Rostov-on-Don, Russia

Email: ilyaelmanov@gmail.com

Abstract — We examine next-Read issue-time prediction at Write arrival using two MSR Cambridge workloads and two address-matching rules. In development evaluation, selected predictors satisfy mean absolute error below mean overwrite delay in three of four pooled comparisons, using censoring-derived lower bounds. However, record-level pass fractions remain bounded between 45.79% and 52.72%, far below the 90% requirement. On the subset with both Read and overwrite observed, all four mean comparisons fail. These results distinguish aggregate error from overwrite-based reliability; they neither establish general learned-model superiority nor measure SSD performance.

Keywords — Censoring; Next-read prediction; Storage traces

## I. Introduction

Next-Read timing could inform storage policies. Predictors at Write arrival must use available history, not future Reads. We evaluate prediction and error tolerance, not a deployed policy or device performance.

Our tolerance is the interval until the next matching Write. We ask whether mean absolute error (MAE) is below mean overwrite delay, and whether individual errors are below their overwrite delays for at least 90% of records. Comparing means does not establish reliability on most records, especially when delays vary or remain unobserved.

We evaluate proj_1 and prn_1 under same-start and range matching. Three pooled mean comparisons succeed, none meets 90%, and four paired-cohort means fail. Undetermined comparisons remain distinct from failures; no general predictive advantage is claimed.

## II. Related Work

The MSR Cambridge documentation attributes the traces to Narayanan, Donnelly and Rowstron's Write Off-Loading study [1]. Its abstract describes one-week block-level traces from 36 enterprise volumes in a spinning-disk power-management setting, not a modern SSD benchmark.

SepBIT infers block-invalidation times and groups data with similar estimates to reduce write amplification in log-structured storage [2]. This differs from next-Read prediction; its outcomes cannot validate our predictor or equate address-level overwrite intervals with physical data-version lifetimes.

LightGBM is a gradient-boosted decision-tree implementation [3], used alongside an address-median baseline. Features, losses and parameters follow our saved configuration. This limited comparison supports no novelty claim.

## III. Methods

### A. Workloads and Event Definitions

Source records identify approximately seven days each of proj_1 and prn_1, with 23,639,742 and 11,233,411 loaded events, respectively, ending at trace EOF. Requesting 168 hours does not certify exactly 168 observed hours or uninterrupted capture.

The same-start screen covered 36 traces, recording eight eligible: two earlier controls and six new candidates. Range confirmation covered only the six new candidates. Inspected code ranks label support within the initial 19.2 hours, not subsequent-day prediction errors, with one excluded boundary-row lookahead. This does not certify historical non-access to later data.

For a Write issued at t, target y is the next matching Read's issue timestamp minus t, in seconds. The README distinguishes issue Timestamp from completion-duration ResponseTime, which label builders exclude. Thus y is issue-to-issue, not request latency, service time or completion-to-completion time.

Same-start matching requires identical starting Offset, regardless of size. Range matching requires nonempty intersection of half-open byte ranges [offset, offset + size); an intersecting Write need not completely overwrite the query. Next Read and next Write are found independently. Intervening Writes do not cancel the Read target; multiple Writes may share one target Read. This measures address access, not necessarily consumption of the written data version. Equal timestamps follow source-row order; a later row can yield a zero interval.

### B. Features, Training and Selection

The seven inputs are Offset, size, prior Read/Write counts, time since prior Read/Write, and the most recent Read–Read interval. History uses the same starting Offset even for range labels. Features precede the current Write's history update; missing history is NaN. Equal-timestamp earlier rows can contribute: “earlier” means source-row order, not strictly earlier timestamps. prn_1 inputs use log1p transforms.

Training uses [0, 72 hours), validation [72, 96 hours), and daily evaluation windows on days 5–7. Labels require target Read issue before their window's exclusive end; unresolved Writes are censored, not given artificial targets. Training spans 72 hours versus at most 24 per evaluation window, with the final boundary clipped to the recorded endpoint. Models and medians remain fixed after training; feature history updates.

Selection minimizes day-4 observed-Read validation MAE, breaking ties by method name, without a pass-count constraint. proj_1 has three candidates per rule: log-L2, raw-L1 and address median. prn_1 adds mixtures with log-L2 weights 0.75, 0.50 and 0.25, totaling six candidates. Earlier predictors/medians are benchmarks only, giving five evaluated methods per proj_1 rule and eight per prn_1 rule, distinct from the selection pools.

The selected proj_1 predictors are per-address training medians with global-median fallback. Both selected prn_1 predictors combine 0.25 log-L2 and 0.75 raw-L1 predictions in seconds, not logarithms. Log-L2 trains on log1p target seconds and converts predictions back using expm1; raw-L1 trains on seconds. Predictions are nonnegative. Each learned component uses 150 trees, 31 leaves, learning rate 0.05, minimum child samples 50, regularization lambda 1, seed 42 and two threads, without early stopping.

Current MAE selection differs from earlier maximum-lower-pass and pass-constrained mixture rules; historical selections remain preserved. Days 5–7 were already inspected during development. Freezing the current choice does not create an untouched confirmatory holdout.

### C. Censoring-Aware Criteria

Let C contain the N Writes with an observed next Read inside their own evaluation window, and let e_i = |prediction_i − y_i|. All mean comparisons use this same cohort. Partition C into K, with known overwrite delay B_i, and U, with unobserved overwrite delay. For i in U, let L_i be the remaining time from Write issue to its observation boundary. L_i is a lower bound, not an imputed overwrite delay.

The exact finite-cohort lower-bound calculation is:

M_L = (Σ_{i∈K} B_i + Σ_{i∈U} L_i) / N ≤ mean_C(B).

MAE_C = Σ_{i∈C} e_i / N < M_L therefore establishes MAE_C < mean_C(B). If MAE_C is not below M_L and overwrite delays remain unknown, the comparison is undetermined, not automatically failed. When all relevant overwrite delays are observed, the strict mean comparison is directly decidable. Pooled values concatenate the daily records rather than averaging daily means.

Record-level reliability instead concerns the strict condition e_i < B_i. Known-delay records are decided directly, with equality a failure. An unknown-delay record with e_i < L_i is a confirmed pass. Records with e_i > L_i can remain unresolved; equality e_i = L_i is conservatively unresolved unless strict boundary semantics establish B_i > L_i. If q records are confirmed passes and r remain unresolved, the pass fraction lies between q/N and (q + r)/N. These are censoring identification bounds, not confidence intervals. An upper bound below 0.90 rules out the requirement within C, but says nothing definitive about Writes without observed Reads.

### D. Reproducibility Materials

The package includes predict.py, models.json, two median tables and four LightGBM files, with recorded sizes, hashes and parent paths. results.ipynb, overwrite-results.json and linked mean-overwrite, long-history and mixture artifacts document outputs/protocols; pyproject.toml and uv.lock provide dependency pointers. Review did not independently rehash full data, audit all parent arrays or certify hardware/runtime provenance.

## IV. Results

For compact presentation, P-S denotes proj_1/same_start, P-R proj_1/range, N-S prn_1/same_start and N-R prn_1/range. All tables pool days 5–7. Duration and error quantities are in seconds; counts and ratios are dimensionless.

TABLE I. Observed-Read coverage of evaluation Writes.

| Key | Read-observed N | All Write N | Coverage |
|---|---:|---:|---:|
| P-S | 211,844 | 1,022,738 | 20.71% |
| P-R | 236,034 | 1,022,738 | 23.08% |
| N-S | 633,316 | 1,299,820 | 48.72% |
| N-R | 684,054 | 1,299,820 | 52.63% |

Coverage is 20.71–23.08% for proj_1 versus 48.72–52.63% for prn_1. MAE is undefined for remaining Read-censored records. Range matching changes both the target rule and the evaluated cohort.

TABLE II. MAE and lower bound on mean overwrite delay (seconds).

| Key | Predictor | MAE, s | M_L, s | Mean criterion |
|---|---|---:|---:|---|
| P-S | Median | 18,162.30 | 18,974.56 | Satisfied |
| P-R | Median | 17,146.95 | 16,275.23 | Undetermined |
| N-S | Mixture | 13,715.20 | 19,184.55 | Satisfied |
| N-R | Mixture | 13,741.74 | 16,475.83 | Satisfied |

Table II reports M_L, the overwrite-mean lower bound; “Satisfied” means MAE < M_L. Three comparisons establish MAE below the overwrite mean. P-R is undetermined: its MAE exceeds the lower bound, not necessarily the actual mean. Both prn_1 rules also satisfy the mean condition on each evaluation day, without establishing record-level reliability.

TABLE III. Pass bounds and paired-cohort control.

| Key | Pass bounds | Paired N | Paired ratio |
|---|---:|---:|---:|
| P-S | 51.35–52.72% | 188,375 | 1.3939 |
| P-R | 45.79–47.17% | 212,376 | 1.6227 |
| N-S | 50.03–50.36% | 522,581 | 1.3581 |
| N-R | 46.19–46.51% | 591,037 | 1.4644 |

All four upper pass bounds are below 90%, demonstrating failure on observed-Read records. The paired subset requires both Read and overwrite observed; its ratio is paired MAE divided by exact paired mean overwrite delay. All four ratios exceed one, failing the paired mean criterion; every saved compared method also fails it. These denominators differ from Table II, so the findings do not contradict each other.

Nor is the selected mixture universally MAE-best. On pooled N-S records, raw-L1 gives 13,545.95 seconds versus the mixture's 13,715.20; on N-R, address median gives 13,606.78 versus 13,741.74. These counterexamples do not trigger retrospective reselection.

## V. Interpretation

Mean success and reliability failure coexist because means aggregate errors and overwrite delays separately, whereas the pass fraction compares each error with its own delay. Favorable means do not establish operation within individual overwrite budgets.

Removing unknown overwrite delays changes the cohort and both means, without invalidating either analysis. Longer tails or observed/censored-cohort differences could explain the contrast; these summaries establish neither mechanism.

Range matching changes endpoint meaning: partial intersection can shorten a budget without replacing all bytes; same-start history omits intersecting accesses starting elsewhere. These are not complete-invalidation results. Aggregate error, censoring and individual tolerances require separate treatment before policy application.

## VI. Limitations

These two selected HDD-era traces do not represent current storage systems generally. Screening establishes label support, not predictive validity. Writes, addresses, repeated target Reads and adjacent days are dependent, not independent replications. We report descriptive values and identification bounds without p-values or inferential confidence intervals.

Read censoring and unequal horizons restrict the evaluated cohorts. These MAEs do not identify performance on all Writes, including later or never-read Writes; approximate trace duration does not resolve this.

Development and changed selection preclude prospective confirmation. Prefix screening and earlier-row features certify neither historical non-access nor universal leakage freedom. Checker/export consistency is not replication; code-to-artifact integrity, parent pass arrays and hardware/runtime provenance remain incompletely verified.

Finally, overwrite delay here is an address-matching interval, not a guaranteed lifetime of the written version. No placement intervention, flash write amplification, throughput, latency improvement or prediction overhead was measured. Any SSD application remains a separate research goal.

## VII. Future Work

Before accessing untouched workloads, fix matching rules, horizons, selection and both criteria. Retain Read-censored Writes and boundary semantics; address dependence through justified workload or temporal replication units, not individual Writes.

Future work should distinguish address access from version use and partial intersection from complete overwrite. An SSD placement study must separately measure device outcomes and inference/migration costs against baselines. Better MAE or overwrite-criterion satisfaction alone does not demonstrate storage benefit.

## VIII. Conclusion

Three of four development comparisons establish MAE below mean overwrite delay on observed-Read records; proj_1/range remains undetermined. Every selected predictor fails the 90% requirement, and every selected paired-cohort mean comparison fails. Aggregate mean success therefore does not establish overwrite-based reliability, general learned-prediction advantage or measured SSD speedup.

## References

[1] D. Narayanan, A. Donnelly, and A. Rowstron, “Write Off-Loading: Practical Power Management for Enterprise Storage,” in 6th USENIX Conference on File and Storage Technologies (FAST 08), 2008.

[2] Q. Wang, J. Li, P. P. C. Lee, T. Ouyang, C. Shi, and L. Huang, “Separating Data via Block Invalidation Time Inference for Write Amplification Reduction in Log-Structured Storage,” in 20th USENIX Conference on File and Storage Technologies (FAST 22), 2022, pp. 429–444.

[3] G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, “LightGBM: A Highly Efficient Gradient Boosting Decision Tree,” in Advances in Neural Information Processing Systems 30, 2017.
