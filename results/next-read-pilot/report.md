# Write → next read: MSR Cambridge pilot

Target: seconds from a write to the first later read with the same starting byte offset.
Same-timestamp events follow trace row order; zero intervals are permitted.
Separate fixed LightGBM models; 60/20/20 duration cuts aligned to timestamps; no tuning.
Features are past-only, ResponseTime is not used. Baselines use completed training intervals only.

## Test metrics (completed intervals only)

| Workload | Method | N | MAE, s | Median AE, s | P90 AE, s | MAE log1p(s) |
|---|---|---:|---:|---:|---:|---:|
| usr_1 | global_median | 796 | 3107.1760 | 2589.3289 | 3785.2529 | 1.0257 |
| usr_1 | address_median | 796 | 3107.1760 | 2589.3289 | 3785.2529 | 1.0257 |
| usr_1 | lightgbm | 796 | 2587.3329 | 2293.0939 | 3355.2245 | 0.9141 |
| prxy_1 | global_median | 33693 | 19.6975 | 12.7779 | 48.6715 | 0.4518 |
| prxy_1 | address_median | 33693 | 18.5530 | 11.8295 | 46.4209 | 0.4337 |
| prxy_1 | lightgbm | 33693 | 16.8264 | 6.9483 | 56.1979 | 0.5627 |

## Observation coverage

| Workload | Split | Writes | Observed next reads | Right-censored | Observed fraction |
|---|---|---:|---:|---:|---:|
| usr_1 | train | 42294 | 403 | 41891 | 1.0% |
| usr_1 | validation | 7014 | 0 | 7014 | 0.0% |
| usr_1 | test | 77394 | 796 | 76598 | 1.0% |
| prxy_1 | train | 207848 | 109549 | 98299 | 52.7% |
| prxy_1 | validation | 68143 | 32874 | 35269 | 48.2% |
| prxy_1 | test | 69528 | 33693 | 35835 | 48.5% |

## Scope and limitations

- This is a bounded initial prefix, not the full workload. Prefixes cover different durations.
- Evaluation excludes writes without a read before their split ends. Long intervals are disproportionately excluded: metrics are conditional on observed next reads, not all writes.
- Exact starting offsets are used, not intersecting byte ranges or 4 KiB pages.
- Intervening writes do not cancel a sample: this predicts address access, not data-version consumption.
- Address medians are frozen at the training cutoff; training scores are descriptive in-sample scores.
- Correlated requests and a single prefix do not establish generalization across a full week or SSD performance gains.
- The log-space model optimizes squared log error; this need not minimize MAE in seconds.

Data attribution: Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.
https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf
