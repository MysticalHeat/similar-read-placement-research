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

## Methods

The MSR trace schema is Timestamp, Hostname, DiskNumber, Type, Offset, Size, ResponseTime. Offsets and request sizes are bytes. FILETIME differences are divided by 10^7 to obtain seconds. Both endpoints of the target are request issue timestamps, not I/O completion timestamps; ResponseTime is unused. Each trace is checked for one logical volume and chronological order.
The seven candidate features are log1p starting offset, size, prior read count, prior write count, seconds since the last read, seconds since the last write, and the last completed read-to-read interval. Missing history is NaN. Stable grouping is a computational shortcut preserving source row order. Future reads construct labels only. Intervening writes do not cancel a sample, so this predicts address access rather than version consumption.
Day one uses the original 60/20/20 temporal cutoffs. Training labels must complete before the training cutoff, and validation labels before the validation cutoff. The already inspected day-one final segment is not presented as a new unbiased test. Per-address and global medians use only completed training labels and remain frozen.
Selection compares four LightGBM configurations (all/no cumulative counts crossed with log-L2/raw-L1), two medians and a past read-period heuristic. There are three new fixed fits per workload, since the original fit already exists. All share 150 trees, 31 leaves, learning rate 0.05, min_child_samples 50, L2 regularization 1, seed 42, two threads, and no early stopping or tuning. The minimum validation MAE selects original_log_l2 for usr_1 and no_counts_log_l2 for prxy_1. No new fits occur in the future windows.
The frozen choices are evaluated over hours [24,48), [48,72), and [72,96) from each trace's first event. Per-address feature history evolves from observed events, but the models and median values do not. Each window is censored at its own end. All outcomes are retained. prxy day 2 reproduces prior evidence; only its days 3--4 are additional future periods.

## Day-one validation selection

| Workload | Candidate | Validation MAE, s |
|---|---|---:|
| usr_1 | global_median | 7554.6631 |
| usr_1 | address_median | 6855.6415 |
| usr_1 | period_remaining | 15332.8193 |
| usr_1 | original_log_l2 | 4892.6615 |
| usr_1 | no_counts_log_l2 | 5108.8853 |
| usr_1 | all_features_raw_l1 | 5182.8864 |
| usr_1 | no_counts_raw_l1 | 4906.8251 |
| prxy_1 | global_median | 9.5378 |
| prxy_1 | address_median | 9.1552 |
| prxy_1 | original_log_l2 | 17.2826 |
| prxy_1 | no_counts_log_l2 | 3.8986 |
| prxy_1 | all_features_raw_l1 | 4.1558 |
| prxy_1 | no_counts_raw_l1 | 3.9848 |
| prxy_1 | previous_read_period_remaining | 37.5230 |

## Complete future metrics

| Workload | Day | Method | N | MAE, s | Median AE, s | P90 AE, s | RMSE, s | MAE log1p(s) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| usr_1 | 2 | global_median | 66,654 | 12202.8738 | 11766.5119 | 20846.4901 | 14546.7164 | 1.5846 |
| usr_1 | 2 | address_median | 66,654 | 9918.7737 | 8599.5089 | 16838.8134 | 13204.9291 | 1.4283 |
| usr_1 | 2 | original | 66,654 | 12153.3621 | 6149.6478 | 33813.0745 | 18452.4589 | 1.9859 |
| usr_1 | 2 | selected | 66,654 | 12153.3621 | 6149.6478 | 33813.0745 | 18452.4589 | 1.9859 |
| usr_1 | 3 | global_median | 3,577 | 12381.5052 | 13513.1063 | 21363.8070 | 13970.1837 | 2.2359 |
| usr_1 | 3 | address_median | 3,577 | 13291.4578 | 13032.5862 | 26825.4603 | 16193.8238 | 2.1545 |
| usr_1 | 3 | original | 3,577 | 15071.4704 | 13911.9287 | 34016.3881 | 20267.6148 | 3.8680 |
| usr_1 | 3 | selected | 3,577 | 15071.4704 | 13911.9287 | 34016.3881 | 20267.6148 | 3.8680 |
| usr_1 | 4 | global_median | 215,104 | 16606.6782 | 13053.7280 | 36466.2892 | 21706.8022 | 1.0048 |
| usr_1 | 4 | address_median | 215,104 | 16450.6661 | 12085.3962 | 38117.4558 | 22492.7194 | 1.0387 |
| usr_1 | 4 | original | 215,104 | 24658.9428 | 22197.4321 | 49376.1890 | 30579.2838 | 3.5690 |
| usr_1 | 4 | selected | 215,104 | 24658.9428 | 22197.4321 | 49376.1890 | 30579.2838 | 3.5690 |
| prxy_1 | 2 | global_median | 4,451,738 | 10.5021 | 5.0686 | 24.9846 | 159.3711 | 0.2023 |
| prxy_1 | 2 | address_median | 4,451,738 | 10.0481 | 5.4719 | 22.7893 | 159.3014 | 0.1950 |
| prxy_1 | 2 | original | 4,451,738 | 18.2403 | 6.4271 | 62.8116 | 161.2606 | 0.7149 |
| prxy_1 | 2 | selected | 4,451,738 | 5.5598 | 4.3555 | 8.6639 | 158.7832 | 0.0922 |
| prxy_1 | 3 | global_median | 4,313,417 | 11.6548 | 6.7177 | 25.9757 | 229.5169 | 0.2053 |
| prxy_1 | 3 | address_median | 4,313,417 | 11.0153 | 6.8461 | 23.8385 | 229.4522 | 0.1950 |
| prxy_1 | 3 | original | 4,313,417 | 18.1560 | 7.5207 | 60.1125 | 230.7043 | 0.6824 |
| prxy_1 | 3 | selected | 4,313,417 | 7.9260 | 6.7972 | 10.7237 | 229.1891 | 0.1274 |
| prxy_1 | 4 | global_median | 4,270,777 | 14.4958 | 9.3117 | 31.8771 | 125.1580 | 0.2843 |
| prxy_1 | 4 | address_median | 4,270,777 | 13.6656 | 9.2030 | 29.6402 | 125.0127 | 0.2710 |
| prxy_1 | 4 | original | 4,270,777 | 17.9000 | 8.9511 | 57.9455 | 124.1157 | 0.6704 |
| prxy_1 | 4 | selected | 4,270,777 | 9.6476 | 8.8105 | 12.8977 | 121.3568 | 0.1746 |

The error distribution is heavy-tailed. MAE improvements do not imply improvements in every metric; inspect P90 and RMSE. In particular, usr day 2 has a lower selected-model median error but worse MAE, P90 and RMSE than the per-address median.

## Reproduction

Use a clean result tree with both downloaded archives in dataset/. Existing runs are not overwritten. uv.lock pins dependencies. Saved artifacts can be verified without fitting. The scripts separate validation selection from frozen evaluation.

```bash
uv sync --python /usr/bin/python3.12 --extra notebook
uv run python -m unittest discover -s tests -v
# Historical prerequisites: day-one preparation and prxy validation selection
uv run python -m read_prediction.pipeline
uv run python -m read_prediction.extended --hours 24 --output results/next-read-24h
uv run python -m read_prediction.experiments.diagnosis
# prxy day-two evaluation also creates the historical frozen median artifact
uv run python -m read_prediction.experiments.day2
uv run python -m read_prediction.experiments.study select-usr
uv run python -m read_prediction.experiments.run_study usr_1
uv run python -m read_prediction.experiments.run_study prxy_1
uv run python -m read_prediction.checks.study
uv run python -m read_prediction.reporting --check-notebook
```

Evaluation stops if a 96h prefix cannot be reached within 130 million events. Compact disk-backed preparation still requires several GiB of RAM; it is not a streaming fit. Successful caches are removed. Evaluation time and process peak RSS are recorded separately per workload. The usr selection stage was not separately resource-measured and is excluded from those observations.

## Verification and limitations

Sixteen unit tests passed. All 13,321,267 future rows and their four methods' five metrics were independently checked from stored predictions, along with validation selection, daily boundaries and frozen baseline/model hashes. Raw sources were independently scanned to audit 448 selected histories and recompute both prefix hashes. This is a sample history audit, not a second complete relabeling of every event.
Results are conditional on next reads observed within each day; low usr day-3 coverage is particularly restrictive. Rows and days are correlated; no p-values, confidence intervals or workload-population claims are made. Exact starting-offset equality does not capture overlapping ranges. The first four days do not constitute the entire trace week. No SSD throughput or placement effect was measured.
The bounded empirical task is complete with mixed results: prxy_1 shows an advantage for the frozen no-counts model, while usr_1 shows failure of its validation-selected model to beat medians on future days. Choosing a replacement after examining these windows would be a new selection step requiring new future evidence.

## Data attribution

Schema and attribution are from MSR-Cambridge/README.txt in the local archives. Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.
https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf
