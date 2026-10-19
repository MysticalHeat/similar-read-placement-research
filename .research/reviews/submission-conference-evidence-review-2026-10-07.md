# Independent submission evidence review

Date: 2026-10-07. Reviewer returned this report to orchestrator after its write
was denied; orchestrator saved this concise, faithful integration. Scope was
20 native reads/searches, no execution/network/recomputation. Fully inspected
submission/{README,overwrite-results,dataset-comparison,models}, protocols
mean-overwrite/long-history/mixture/data-sufficiency/final-study, reports
mean-overwrite/data-sufficiency and results/mean-overwrite/{metrics,frozen,verification}.
No production/checker code, raw tar/NPZ joins, independent hashes or replication.
Stored checker passed:true is evidence of a receipt, not reviewer replication.

## Supported results
Selected methods and mean-overwrite values agree across export/primary metrics/
frozen/report. Pooled observed-Read cohort: proj_1 same_start median MAE18162.30,
meanLB18974.56, pass51.35–52.72%; proj_1 range median17146.95/16275.23,
45.79–47.17%; prn_1 same_start mix_log25 13715.20/19184.55,50.03–50.36%;
prn_1 range mix_log25 13741.74/16475.83,46.19–46.51%. First/third/fourth
mean comparisons satisfied; second undetermined. All four upper pass bounds
below90%. Bounds are censoring bounds, not confidence intervals.

Primary mean exact support: results/mean-overwrite/metrics.json
$.{workload}.{rule}.windows.pooled.methods.{selected}.{observed_read,paired},
and pooled cohort/bounds; proj_1 same_start lines394–455, range884–945;
prn_1 same_start1568–1580/1695–1709, range2298–2310/2425–2439.
Pass support: submission/overwrite-results.json selected_results entries with
window=pooled, fields confirmed_pass_count/unknown_pass_count/pass_lower/pass_upper.
No independent pass-array audit in this review.

## Findings and required actions
| ID | Severity | Exact support | Requested action | Disposition for manuscript |
|---|---|---|---|---|
| R026 | question | final-study-protocol.md:7; models.json:13; submission/README.md:51; long-history-protocol.md:12–13 | Clarify issue vs physical completion, ResponseTime, row/boundary rules through code | Static audit clarifies issue-to-issue; local archive README §3 independently read by orchestrator confirms issued Timestamp/separate ResponseTime. Use issue-time wording; no full runtime audit |
| R027 | major | submission/README.md:82 "independent events" vs data-sufficiency-protocol.md:36–40 and reports/data-sufficiency.ru.md:18–21 | Distinct target Reads do not imply independence; remove IID implications and no per-Write binomial CIs | Address through manuscript wording: dependent records, descriptive results, no IID tests/CIs; source README not modified |
| R028 | minor | submission/README.md:98 vs14/18–21/91–96 | "roughly half" is not proj_1; upper bounds below90 definitively fail within observed-Read cohort | Address through workload-specific coverage and explicit 90% failure, no all-Write generalization |
| R029 | question | long-history-protocol.md:31–33; mixture-protocol.md:11–17,27; mean-overwrite-protocol.md:7–12,26–28; frozen.json | Disclose changed objectives/selection and already-seen days; distinguish evaluated benchmarks from selection candidates | Retain development scope/current MAE rule, no prospective confirmation. Historical access chronology not certified |
| R030 | question | submission/README.md:51,79–85; dataset-comparison.json:943–951/986–1002; data-sufficiency-protocol.md:9–10/42–53 | requested168h/EOF != exact observed168h; code/protocol != historical no-access certificate | Source endpoints inspected, use approximately7days. Prefix-support ranking inspected statically; historical no-access remains unresolved/disclosed |

## Counterevidence and remaining limits
All saved methods fail pooled paired mean criterion (mean-overwrite metrics
methods.*.paired.passed=false). Different cohort, not contradiction.
Selected mixture is not universally best on future MAE: prn_1 same_start
raw_l1=13545.95 vs mixture13715.20; range median13606.78 vs mixture13741.74.
Selection remains frozen, not retrospectively replaced. Aggregate mean success
may reflect long overwrite tails/cohort selection, not majority reliability.
No generalization, universal ML advantage, SSD benefit, novelty, historical
leakage freedom or full-environment/byte-integrity certificate established.
No new computation required for bounded descriptive article; stronger claims
would require separately approved untouched-data study and dependency-aware
analysis. Reviewer did not certify screening execution or parent pass arrays.
