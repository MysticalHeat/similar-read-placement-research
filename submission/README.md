# Latest results: MAE, mean overwrite time and the 90% threshold

**On prn_1, MAE is below even the lower bound on mean time to overwrite, but the requirement that `error < overwrite` for at least 90% of records is not met.** These are two different criteria.

Predictors are selected by minimum validation MAE on day 4. For prn_1, the selection is a **25% log-L2 + 75% raw-L1** mixture in seconds; for proj_1, it is the per-address median. Days 5–7 have already been inspected: this is development evaluation, not a new holdout.

- `same_start`: the next Read/Write with the same starting Offset, regardless of size.
- `range`: the next Read/Write whose byte range intersects the written range; partial overlap is sufficient, not a complete overwrite.

## Main comparison: all writes with an observed Read, days 5–7

MAE and mean overwrite time refer to the same records. Unknown overwrite times are retained: the observation-window boundary gives only a lower bound on the interval, not its actual value. If MAE is below this lower bound on the mean, the condition is proven.

The 90% criterion is `P(abs(prediction − target) < overwrite) ≥ 0.90`. The lower bound counts confirmed passes; the upper bound additionally treats every unresolved case as a pass. If even the upper bound is below 90%, the condition definitely fails.

| Workload / rule | Method | Observed Read N / all Write N | MAE, s | Mean overwrite ≥, s | MAE / lower bound | MAE < mean | Fraction error < overwrite | ≥90% |
|---|---|---:|---:|---:|---:|---|---:|---|
| proj_1 / same_start | address_median | 211,844 / 1,022,738 | 18162.30 | 18974.56 | 0.9572 | proven | 51.35%–52.72% | no |
| proj_1 / range | address_median | 236,034 / 1,022,738 | 17146.95 | 16275.23 | 1.0536 | undetermined | 45.79%–47.17% | no |
| prn_1 / same_start | mix_log25 | 633,316 / 1,299,820 | 13715.20 | 19184.55 | 0.7149 | proven | 50.03%–50.36% | no |
| prn_1 / range | mix_log25 | 684,054 / 1,299,820 | 13741.74 | 16475.83 | 0.8341 | proven | 46.19%–46.51% | no |

For prn_1, the mean-time condition also holds on each of days 5, 6 and 7 separately. A condition on averages does not guarantee small errors for most records. MAE is undefined for writes without an observed Read, so this result does not extend to all writes.

## Control comparison: observed Read and known overwrite only

This is a different cohort. Here every evaluated candidate has MAE above mean overwrite time. Unknown intervals are excluded, so the conclusion differs from the main table.

| Workload / rule | Paired N | MAE, s | Mean overwrite, s | MAE / mean | MAE < mean |
|---|---:|---:|---:|---:|---|
| proj_1 / same_start | 188,375 | 17877.65 | 12825.59 | 1.3939 | no |
| proj_1 / range | 212,376 | 17074.68 | 10522.68 | 1.6227 | no |
| prn_1 / same_start | 522,581 | 12471.49 | 9183.09 | 1.3581 | no |
| prn_1 / range | 591,037 | 12551.49 | 8571.29 | 1.4644 | no |

## Evaluated candidates and the 90% threshold

| Workload / rule | Candidates | Highest upper bound on pass fraction | ≥90% reached |
|---|---:|---:|---|
| proj_1 / same_start | 5 | 58.76% | no |
| proj_1 / range | 5 | 58.64% | no |
| prn_1 / same_start | 8 | 55.48% | no |
| prn_1 / range | 8 | 50.76% | no |

Numerical results, daily metrics and source fingerprints are embedded in results.ipynb and saved in overwrite-results.json. Mean-overwrite calculations were independently verified for 20 windows; the parent long-history/mixture metrics were also verified.

Source results in the research repository: results/mean-overwrite/, results/long-history/{proj_1,prn_1}/, results/mixture/prn_1/. Protocol: docs/protocols/mean-overwrite-protocol.md.

# Dataset selection: screening all 36 MSR Cambridge traces

Before training, every trace was screened with fixed windows and thresholds (train 0–14.4 h, validation 14.4–19.2 h from the trace start). A label counts only if the first next Read completes inside its own window; writes censored at the window end are not training examples. Future days were never opened during screening, so selection uses data availability, not later accuracy.

| Trace | Train labels | Validation labels | Validation addresses | Validation target Reads | Same-start eligible |
|---|---:|---:|---:|---:|---|
| prxy_1 (control, earlier stage) | 2,826,821 | 922,870 | 1,737 | 395,912 | yes |
| usr_1 (control, earlier stage) | 65,710 | 24,804 | 8,953 | 9,112 | yes |
| proj_1 | 182,142 | 21,556 | 16,515 | 16,888 | yes |
| prn_1 | 75,329 | 11,833 | 3,646 | 4,928 | yes |
| hm_0 | 22,502 | 5,032 | 76 | 2,632 | yes |
| prn_0 | 13,636 | 3,691 | 985 | 1,239 | yes |
| usr_0 | 11,599 | 2,963 | 1,013 | 1,059 | yes |
| proj_0 | 11,085 | 2,229 | 1,033 | 1,049 | yes |

The remaining 28 traces failed at least one threshold; the most common reasons are `validation_too_few_labels` (27), `train_too_few_labels` (25), `validation_too_few_labelled_offsets` (22), `train_too_few_labelled_offsets` (18). For example, `src1_0` and `src1_1` have many train labels but zero validation labels under this protocol.

## Range confirmation of the six new candidates

The six eligible new traces were re-labeled by byte-range intersection on the 512-byte grid and re-checked against the same thresholds.

| Trace | Train labels | Validation labels | Train target Reads | Validation coverage | Range eligible |
|---|---:|---:|---:|---:|---|
| proj_1 | 219,900 | 26,664 | 133,163 | 20.66% | yes |
| prn_1 | 82,136 | 16,739 | 61,508 | 21.46% | yes |
| hm_0 | 24,346 | 5,225 | 10,803 | 8.57% | yes |
| prn_0 | 32,249 | 5,629 | 5,107 | 3.66% | yes |
| usr_0 | 36,664 | 3,631 | 6,023 | 7.65% | yes |
| proj_0 | 19,484 | 2,345 | 3,818 | 3.48% | yes |

## Why proj_1 and prn_1 were chosen

- **Most training signal.** proj_1 has 182,142 train and 21,556 validation same-start labels; prn_1 has 75,329 and 11,833 — ranks 1 and 2 among the six new candidates.
- **Many distinct target events, also under range.** proj_1 reaches 133,163 distinct completing Reads in train (20,166 in validation) and prn_1 61,508 (5,886). Our per-record criteria (mean overwrite, ≥90% pass) need many independent events, not repeated writes to one address.
- **Most diverse addresses.** The largest single-address share of validation labels is 0.35% for proj_1 and 7.97% for prn_1, with effective address counts 8306 and 80.5. By comparison, hm_0 concentrates 20.33% on one address (effective count 11.7). A per-address median baseline and per-address history features need that diversity.
- **Both labeling rules supported.** same_start and range pass the thresholds, so the same workflow evaluates both rules on the same traces.
- **Full traces available for future days.** Both traces run the full 168 h (`end_of_trace`), so frozen evaluation on days 5–7 is possible without running out of trace. This is what our development results use.

## How this connects to the task results

The screening thresholds are a starting filter, not a guarantee of predictive quality. What the selected traces actually delivered in our evaluation:

| Trace / rule | Observed Read / all Write, days 5–7 | Coverage |
|---|---:|---:|
| proj_1 / same_start | 211,844 / 1,022,738 | 20.71% |
| proj_1 / range | 236,034 / 1,022,738 | 23.08% |
| prn_1 / same_start | 633,316 / 1,299,820 | 48.72% |
| prn_1 / range | 684,054 / 1,299,820 | 52.63% |

Roughly half of the writes have an observed Read within their day window, and the rest are censored. That is why MAE is reported only for observed-Read records and the ≥90% criterion is bounded rather than declared failed outright. Full details: `results.ipynb`, `reports/mean-overwrite.ru.md` and the protocols under `docs/protocols/`.

## Submission contents

- `results.ipynb` — both new criteria, the 36-trace dataset screening and the earlier usr_1/prxy_1 comparison; already executed, with no raw traces needed for viewing.
- `overwrite-results.json` — a portable snapshot of verified metrics, daily results and fingerprints.
- `dataset-comparison.json` — the 36-trace screening snapshot and the reasons proj_1/prn_1 were selected.
- `predict.py` and `models.json` — selected predictor loading, feature order, mixture weights and fingerprints.
- `prn_1.{same_start,range}.{log_l2,raw_l1}.lightgbm.txt` — four models, two for each mixture.
- `proj_1.{same_start,range}.address_medians.json` — selected address medians; the global fallback is specified in models.json.
- `training.ipynb` — standalone prn_1/proj_1 training on days 1–3, selection on validation day 4 and export to trained/long-history-retrain; requires DATASET containing msr-cambridge1.tar.
- `usr_1.lightgbm.txt`, `prxy_1.lightgbm.txt` — earlier frozen models for the legacy inference section in results.ipynb.

Build from the research project root: `.venv/bin/python -m read_prediction.submission`.

Verify the metric snapshot and notebook execution outside the repository: `.venv/bin/python -m read_prediction.checks.submission`.
Test the training notebook on an artificial four-day trace: `.venv/bin/python -m read_prediction.checks.training_notebook`.
