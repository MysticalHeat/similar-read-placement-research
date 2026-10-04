# Write → next read: MSR Cambridge 24-hour follow-up

Target: seconds from a write to the first later read with the same starting byte offset.
Same-timestamp events follow trace row order; zero intervals are permitted.
Separate fixed LightGBM models; 60/20/20 duration cuts aligned to timestamps; no tuning.
Features are past-only, ResponseTime is not used. Baselines use completed training intervals only.

## Test metrics (completed intervals only)

| Workload | Method | N | MAE, s | Median AE, s | P90 AE, s | MAE log1p(s) |
|---|---|---:|---:|---:|---:|---:|
| usr_1 | global_median | 17039 | 7819.3475 | 8746.9804 | 10368.4073 | 0.9467 |
| usr_1 | address_median | 17039 | 6770.5285 | 7078.8261 | 10829.7011 | 0.8404 |
| usr_1 | lightgbm | 17039 | 4623.5028 | 4114.2835 | 9120.6545 | 1.2191 |
| prxy_1 | global_median | 914339 | 8.7030 | 5.1458 | 20.1084 | 0.1458 |
| prxy_1 | address_median | 914339 | 8.3640 | 5.2379 | 17.9373 | 0.1407 |
| prxy_1 | lightgbm | 914339 | 18.1148 | 4.5240 | 63.6336 | 0.6241 |

## Observation coverage

| Workload | Split | Writes | Observed next reads | Right-censored | Observed fraction |
|---|---|---:|---:|---:|---:|
| usr_1 | train | 333256 | 65710 | 267546 | 19.7% |
| usr_1 | validation | 162688 | 24808 | 137880 | 15.2% |
| usr_1 | test | 143665 | 17039 | 126626 | 11.9% |
| prxy_1 | train | 5225909 | 2826821 | 2399088 | 54.1% |
| prxy_1 | validation | 1722950 | 922870 | 800080 | 53.6% |
| prxy_1 | test | 1711773 | 914339 | 797434 | 53.4% |

## Scope and limitations

- Each prefix covers the first 24-hour window, not the full week. The last included event is slightly before the 24-hour boundary.
- Evaluation excludes writes without a read before their split ends. Long intervals are disproportionately excluded: metrics are conditional on observed next reads, not all writes.
- Exact starting offsets are used, not intersecting byte ranges or 4 KiB pages.
- Intervening writes do not cancel a sample: this predicts address access, not data-version consumption.
- Address medians are frozen at the training cutoff; training scores are descriptive in-sample scores.
- Correlated requests and a single prefix do not establish generalization across a full week or SSD performance gains.
- The log-space model optimizes squared log error; this need not minimize MAE in seconds.

Data attribution: Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.
https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf
