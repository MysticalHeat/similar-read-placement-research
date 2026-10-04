# Write-triggered next-read prediction: final bounded study

The empirical stage is complete for exact starting offsets on the first four days of usr_1 and prxy_1. Results are workload-dependent.

The target is elapsed seconds from each write to the first later read at the same starting byte offset. Models and training-only median baselines are frozen before future evaluation. Per-day metrics include only targets completed within that day.

| Workload | Day | Address median MAE, s | Selected MAE, s | MAE reduction | Observed / eligible writes | Coverage | Role |
|---|---:|---:|---:|---:|---:|---:|---|
| usr_1 | 2 | 9918.77 | 12153.36 | -22.5% | 66,654 / 373,657 | 17.8% | new_future_period |
| usr_1 | 3 | 13291.46 | 15071.47 | -13.4% | 3,577 / 170,813 | 2.1% | new_future_period |
| usr_1 | 4 | 16450.67 | 24658.94 | -49.9% | 215,104 / 614,645 | 35.0% | new_future_period |
| prxy_1 | 2 | 10.05 | 5.56 | +44.7% | 4,451,738 / 8,255,657 | 53.9% | previously_evaluated_replication |
| prxy_1 | 3 | 11.02 | 7.93 | +28.0% | 4,313,417 / 8,033,311 | 53.7% | new_future_period |
| prxy_1 | 4 | 13.67 | 9.65 | +29.4% | 4,270,777 / 7,950,726 | 53.7% | new_future_period |

A negative MAE reduction denotes a model worse than the per-address median. The usr_1 validation winner fails to beat that median on all three future days. The prxy_1 model without cumulative counts beats it in all three reported windows; day 2 is a replication of the previously evaluated window, while days 3--4 add new future periods. No future results were used to change the models.

The evidence supports a workload-specific advantage on prxy_1, not a workload-independent benefit. Censoring is substantial: unknown intervals are not assigned zero or infinity. Exact starting offsets do not represent arbitrary overlapping I/O ranges or data-version consumption. Consecutive days and requests are correlated; no significance or population-wide claims are made. SSD performance was not simulated.

The combined prefixes contain 118,918,261 events. The published future metrics cover 13,321,267 completed write-to-read targets, including prxy_1 day-2 replication. Models, predictions, frozen medians, source/code hashes and verification artifacts are retained. See [report.en.md](report.en.md) for full methods and metrics.
