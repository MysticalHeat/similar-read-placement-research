# Dataset screening: exact access and limits

2026-09-30; local read-only native tools, no shell, training, installation or network. This is a data-suitability check, not prediction/performance evidence.

Experimenter inspected S014 dataset/hm_0.csv lines 1–120 and S015 dataset/prxy_0.csv lines 1–120. See experiments/dataset-audit.md for full bounds and semantic uncertainties. Orchestrator independently read lines 1–5 of each: space-delimited three fields, first token W. Does not independently verify every line 1–120; specialist sample inspection supplies C011/C012 support.

## Additional native searches by orchestrator
1. grep `^[Rr][ \t]+`, path dataset/, include `{hm_0,prxy_0}.csv`: tool response `No files found`. Pattern/include matching not yet established for brace filter; not used alone to claim absence.
2. glob `*.csv` at dataset/: two paths returned, hm_0.csv and prxy_0.csv.
3. grep `^[Rr][ \t]+`, path dataset/, include `*.csv`: response `No files found` (no matching files/lines returned).
4. Positive-control grep anchored to the exact first observed W line in hm_0.csv, include hm_0.csv: matches returned, truncated at 100 with more available. Raw addresses intentionally not copied here. This establishes native content search operated on at least hm_0.csv; not a row count or op mix profile.

C013 wording is limited to this search outcome: no matches returned for the specified R/r line-start form in the two-file CSV directory. Not a completed validation of all rows, encoding, alternate read labels, leading whitespace, units or semantic schema. No conclusion of 'all rows are writes' is promoted. Without hashes, this refers to files observed at that date; mutable local inputs may change.

Filename is not provenance. Source, license, preprocessing, address/length units and original ordering UNKNOWN. No original reads reconstructed or invented. If documentation/full profile confirms absent read events, STOP next-read experiment; request original mixed/read traces or a separately approved question change.

Proposed next step: user confirms provenance/schema and separately permits bounded local read-only Python profiling (aggregate counters/checksums/metadata, no data modification/network). Profiling budget remains proposed, not authorized. Exact EOF counts/SHA256/op mix/hardware not established here. Native read's displayed total line figures not treated as verified profiling results.
