FEATURE_DESCRIPTION = """**Features** — history of the same starting offset, available at the time of the write.

| Column | Feature before transformation |
|---|---|
| 0 | Write offset, bytes |
| 1 | Write size, bytes |
| 2 | Number of previous reads at this offset |
| 3 | Number of previous writes at this offset |
| 4 | Seconds since the previous read at this offset |
| 5 | Seconds since the previous write at this offset |
| 6 | Most recent completed interval between reads at this offset, seconds |

Each feature is transformed with `log1p`. Missing history is represented by `NaN`. usr_1 uses all seven columns; prxy_1 uses `[0, 1, 4, 5, 6]`.

**Label** — seconds from a write to the first subsequent read with the same starting offset. Intervening writes do not invalidate the sample. Samples without a read before the end of their time window are excluded from training/evaluation. The model is trained on `log1p(label)`; predictions in seconds are obtained as `max(0, expm1(prediction))`.
"""

RESULTS_NOTE = """*Note: MAE is the average absolute prediction error in seconds; lower is better. On days 2–4, the prxy_1 model reduces MAE by 28–45% compared with the training-only per-address median, while the usr_1 model performs worse on all three days. Thus, the benefit is workload-dependent. Scores include only writes followed by a read within the same day; coverage indicates the fraction evaluated. Day 2 of prxy_1 repeats a previously evaluated period.*"""

TRAINING_NOTE = """*Note: These are first-day validation errors, not future-day performance. The usr_1 validation result does not translate into a baseline advantage on later days; see results.ipynb for the frozen-model comparison.*"""
