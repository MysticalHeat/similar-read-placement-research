# Predicting Next-Read Time at Write Arrival: Mean Error and Overwrite-Based Reliability

Elmanov Ilia

Master's student

[University, city, country — to be confirmed]

Email: ilyaelmanov@gmail.com

Abstract — We examine next-Read issue-time prediction at Write arrival using two MSR Cambridge workloads and two address-matching rules. In development evaluation, selected predictors satisfy mean absolute error below mean overwrite delay in three of four pooled comparisons, using censoring-derived lower bounds. However, record-level pass fractions remain bounded between 45.79% and 52.72%, far below the 90% requirement. On the subset with both Read and overwrite observed, all four mean comparisons fail. These results distinguish aggregate error from overwrite-based reliability; they neither establish general learned-model superiority nor measure SSD performance.

Keywords — Censoring; Next-read prediction; Storage traces

## I. Introduction

Predicting when an address will next be read is a possible input to storage-policy design. At Write arrival, a predictor must use available history, not the future Read. Evaluation must specify both the predicted event and the error tolerance. We study this prediction question, not a deployed policy or its effect on device performance.

Our tolerance is the interval until the next matching Write. We ask whether mean absolute error (MAE) is below mean overwrite delay, and whether individual errors are below their overwrite delays for at least 90% of records. Comparing means does not establish reliability on most records, especially when delays vary or remain unobserved.

We report development results for proj_1 and prn_1 under same-start and byte-range matching. Three pooled mean comparisons satisfy the criterion, but none satisfies the 90% requirement. A subset with observed overwrite delays produces four failed mean comparisons. We retain these failures and distinguish them from an undetermined comparison, without claiming general predictive advantage.

## II. Related Work

The MSR Cambridge documentation attributes the traces to Narayanan, Donnelly and Rowstron's Write Off-Loading study [1]. Its abstract describes one-week block-level traces from 36 enterprise volumes in a spinning-disk power-management setting, not a modern SSD benchmark.

SepBIT infers block-invalidation times and groups data with similar estimates to reduce write amplification in log-structured storage [2]. This differs from next-Read prediction; its outcomes cannot validate our predictor or equate address-level overwrite intervals with physical data-version lifetimes.

LightGBM is a gradient-boosted decision-tree implementation [3], used here alongside an address-median baseline. Our saved configuration, not that reference, supports the feature, loss and parameter choices. This contextual comparison is not comprehensive and supports no novelty claim.

## III. Methods

### A. Workloads and Event Definitions

Source records identify approximately seven days each of proj_1 and prn_1, with 23,639,742 and 11,233,411 loaded events, respectively, ending at trace EOF. Requesting 168 hours does not certify exactly 168 observed hours or uninterrupted capture.

The same-start screen covered 36 traces, recording eight eligible: two earlier controls and six new candidates. Range confirmation covered only the six new candidates. Inspected code ranks label support within the initial 19.2 hours, not subsequent-day prediction errors, with one excluded boundary-row lookahead. This does not certify historical non-access to later data.

For a Write issued at t, target y is the next matching Read's issue timestamp minus t, in seconds. The dataset README defines Timestamp as I/O issue time and ResponseTime as completion duration. Label builders subtract timestamps and exclude ResponseTime. Thus y is issue-to-issue, not request latency, service time or completion-to-completion time.

Same-start matching requires identical starting Offset, regardless of size. Range matching requires nonempty intersection of half-open byte ranges [offset, offset + size); an intersecting Write need not completely overwrite the query. Next Read and next Write are found independently. Intervening Writes do not cancel the Read target; multiple Writes may share one target Read. This measures address access, not necessarily consumption of the written data version. Equal timestamps follow source-row order; a later row can yield a zero interval.

### B. Features, Training and Selection

The seven inputs are Offset, request size, prior Read count, prior Write count, time since the prior Read, time since the prior Write, and the most recent Read–Read interval. History is keyed by the same starting Offset even for range labels. Features are extracted before updating history with the current Write; missing history is NaN. Earlier rows with equal timestamps can contribute, so “earlier” means source-row order, not strictly earlier timestamps. prn_1 inputs use log1p transforms.

Training uses [0, 72 hours), validation [72, 96 hours), and evaluation separate daily windows for days 5–7. A label is observed only if its target Read is issued before its own window's exclusive end. Writes without such a Read are censored, not assigned artificial long targets. The training observation horizon is 72 hours, whereas each evaluation horizon is at most 24 hours; the final boundary is clipped to the recorded endpoint. Fitted models and address medians remain fixed after training, while feature history continues to update.

The current selection rule minimizes observed-Read validation MAE on day 4, breaking ties by method name, with no pass-count constraint. There are three selection candidates per proj_1 rule: log-L2 regression, raw-L1 regression and address median. prn_1 adds mixtures with log-L2 weights 0.75, 0.50 and 0.25, giving six selection candidates. Earlier predictors and medians are comparison benchmarks only. Including them gives five evaluated methods per proj_1 rule and eight per prn_1 rule; these are not the selection-pool sizes.

The selected proj_1 predictors are per-address training medians with global-median fallback. Both selected prn_1 predictors combine 0.25 log-L2 and 0.75 raw-L1 predictions in seconds, not logarithms. Log-L2 trains on log1p target seconds and converts predictions back using expm1; raw-L1 trains on seconds. Predictions are nonnegative. Each learned component uses 150 trees, 31 leaves, learning rate 0.05, minimum child samples 50, regularization lambda 1, seed 42 and two threads, without early stopping.

Current MAE selection differs from earlier maximum-lower-pass and pass-constrained mixture rules; historical selections remain preserved. Days 5–7 were already inspected during development. Freezing the current choice does not create an untouched confirmatory holdout.

### C. Censoring-Aware Criteria

Let C contain the N Writes with an observed next Read inside their own evaluation window, and let e_i = |prediction_i − y_i|. All mean comparisons use this same cohort. Partition C into K, with known overwrite delay B_i, and U, with unobserved overwrite delay. For i in U, let L_i be the remaining time from Write issue to its observation boundary. L_i is a lower bound, not an imputed overwrite delay.

The exact finite-cohort lower-bound calculation is:

M_L = (Σ_{i∈K} B_i + Σ_{i∈U} L_i) / N ≤ mean_C(B).

MAE_C = Σ_{i∈C} e_i / N < M_L therefore establishes MAE_C < mean_C(B). If MAE_C is not below M_L and overwrite delays remain unknown, the comparison is undetermined, not automatically failed. When all relevant overwrite delays are observed, the strict mean comparison is directly decidable. Pooled values concatenate the daily records rather than averaging daily means.

Record-level reliability instead concerns the strict condition e_i < B_i. Known-delay records are decided directly, with equality a failure. An unknown-delay record with e_i < L_i is a confirmed pass. Records with e_i > L_i can remain unresolved; equality e_i = L_i is conservatively unresolved unless strict boundary semantics establish B_i > L_i. If q records are confirmed passes and r remain unresolved, the pass fraction lies between q/N and (q + r)/N. These are censoring identification bounds, not confidence intervals. An upper bound below 0.90 rules out the requirement within C, but says nothing definitive about Writes without observed Reads.

### D. Reproducibility Materials

The package contains predict.py, models.json, two median tables and four LightGBM files, with recorded sizes, hashes and parent paths. The results notebook, overwrite-results.json and linked mean-overwrite, long-history and mixture artifacts document outputs and protocols; pyproject.toml and uv.lock provide dependency pointers. These describe an inspectable recipe, not fresh-environment replication. Static and cross-artifact review did not independently rehash full data, audit every parent array or certify hardware/runtime provenance.

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

TABLE II. Selected-predictor mean comparisons on observed-Read records. M_L is the overwrite-mean lower bound; “Satisfied” denotes MAE < M_L.

| Key | Predictor | MAE, s | M_L, s | Mean criterion |
|---|---|---:|---:|---|
| P-S | Median | 18,162.30 | 18,974.56 | Satisfied |
| P-R | Median | 17,146.95 | 16,275.23 | Undetermined |
| N-S | Mixture | 13,715.20 | 19,184.55 | Satisfied |
| N-R | Mixture | 13,741.74 | 16,475.83 | Satisfied |

Three comparisons establish MAE below the overwrite mean. P-R is undetermined: its MAE exceeds the lower bound, not necessarily the actual mean. Both prn_1 rules also satisfy the mean condition on each evaluation day, without establishing record-level reliability.

TABLE III. Selected-predictor pass bounds on observed-Read records, and a separate paired-cohort control. Paired ratio is paired MAE divided by exact paired mean overwrite delay.

| Key | Pass bounds | Paired N | Paired ratio |
|---|---:|---:|---:|
| P-S | 51.35–52.72% | 188,375 | 1.3939 |
| P-R | 45.79–47.17% | 212,376 | 1.6227 |
| N-S | 50.03–50.36% | 522,581 | 1.3581 |
| N-R | 46.19–46.51% | 591,037 | 1.4644 |

All four upper pass bounds are below 90%, demonstrating failure on observed-Read records. The paired subset requires both Read and overwrite observed. All four paired ratios exceed one, failing the paired mean criterion; every saved compared method also fails it. These denominators differ from Table II, so the findings do not contradict each other.

Nor is the selected mixture universally MAE-best. On pooled N-S records, raw-L1 gives 13,545.95 seconds versus the mixture's 13,715.20; on N-R, address median gives 13,606.78 versus 13,741.74. These counterexamples do not trigger retrospective reselection.

## V. Interpretation

Mean success and reliability failure coexist because means aggregate errors and overwrite delays separately, whereas the pass fraction compares each error with its own delay. Favorable means do not establish operation within individual overwrite budgets.

The paired control shows why censoring policy matters: removing unknown delays changes the cohort and both means. Neither analysis invalidates the other. Longer overwrite tails or differences between observed and censored records could explain the contrast, but these summaries establish neither mechanism.

Range matching changes endpoint meaning, not just prediction quality. Partial intersection can shorten an overwrite budget without replacing all query bytes, while same-start history omits intersecting accesses starting elsewhere. Range results should not be interpreted as complete physical invalidation. Aggregate error, censoring and individual tolerances require separate treatment before policy application.

## VI. Limitations

These two selected HDD-era traces do not represent current storage systems generally. Screening establishes label support, not predictive validity. Writes, addresses, repeated target Reads and adjacent days are dependent, not independent replications. We report descriptive values and identification bounds without p-values or inferential confidence intervals.

Read censoring restricts the findings to observed targets; unequal training/evaluation horizons also affect cohort membership. These MAEs do not identify performance on all Writes, including those read beyond the window or never read. Approximate trace duration does not resolve this limitation.

Development inspection and changed selection preclude prospective confirmation. Prefix-based screening and earlier-row features do not prove historical no-access chronology or universal leakage freedom. Checker receipts and consistent exports are not independent replication. Full code-to-artifact integrity, parent pass-array auditing and hardware/runtime provenance remain incompletely verified.

Finally, overwrite delay here is an address-matching interval, not a guaranteed lifetime of the written version. No placement intervention, flash write amplification, throughput, latency improvement or prediction overhead was measured. Any SSD application remains a separate research goal.

## VII. Future Work

A stronger evaluation should fix the matching rule, observation horizons, selection objective and both reliability criteria before accessing new workloads. Untouched-data evaluation should retain Read-censored Writes explicitly, document boundary semantics and account for dependence through justified workload or temporal replication units rather than treating each Write as independent.

Future work should distinguish address access from version use and partial intersection from complete overwrite. An SSD placement study must separately measure device outcomes and inference/migration costs against baselines. Better MAE or overwrite-criterion satisfaction alone does not demonstrate storage benefit.

## VIII. Conclusion

In these development results, three of four selected-predictor comparisons establish MAE below mean overwrite delay on observed-Read records; proj_1/range remains undetermined. Nevertheless, every selected predictor fails the 90% record-level requirement, and every selected paired-cohort mean comparison fails. The bounded conclusion is that aggregate mean success does not establish overwrite-based reliability. The findings motivate explicit endpoint, cohort and censoring definitions, not a general advantage of learned prediction or a measured SSD speedup.

## References

[1] D. Narayanan, A. Donnelly, and A. Rowstron, “Write Off-Loading: Practical Power Management for Enterprise Storage,” in 6th USENIX Conference on File and Storage Technologies (FAST 08), 2008.

[2] Q. Wang, J. Li, P. P. C. Lee, T. Ouyang, C. Shi, and L. Huang, “Separating Data via Block Invalidation Time Inference for Write Amplification Reduction in Log-Structured Storage,” in 20th USENIX Conference on File and Storage Technologies (FAST 22), 2022, pp. 429–444.

[3] G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, “LightGBM: A Highly Efficient Gradient Boosting Decision Tree,” in Advances in Neural Information Processing Systems 30, 2017.
