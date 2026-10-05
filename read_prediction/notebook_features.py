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
