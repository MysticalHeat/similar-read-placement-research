# Citation audit — initial scoping, not manuscript verification

Verifier: orchestrator, 2026-09-30. Metadata ≠ exact support. No numerical gain claims promoted.

| Claim | Source identity/access | Locator | Support | Caveat/action |
|---|---|---|---|---|
| C001 | S003 title/byline verified in full-text HTML; HPCA publication relationship visible, exact arXiv revision unknown | §2.2 Challenge | direct for that architecture | Check modern device command restrictions before protocol |
| C002 | S009 title/byline and FAST 22 relationship visible; full-text HTML | Abstract; §2.3 | direct for stated objective/sample | Not read prediction or physical NAND placement evidence |
| C003 | S010 official USENIX abstract and BibTeX checked; FAST 26, 2026, pp.543-559 | Abstract | direct for author-reported purpose/setup | Full-text unavailable in readable fetch; no replication |
| C004 | S003 same identity/access as C001 | §4.2 | direct for scheduling mechanism | No guarantee for future-page placement |
| C005 | User hypothesis, no external source or E-ID | brief.md | unverified | Retain hypothesis; no claim of improvement |
| C006 | S013 immutable commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21, repo source | MiDaFTL.py L19,58–72,78 | direct; independent raw-source spot-check | Write allocation, not read prediction |
| C007 | S013 same commit/source | MiDaFTL.py L21–28 | direct; independently checked | Mapping skip for invalid page; no execution |
| C008 | S013 same commit/source | Statistics.py L111–124; FTL.py L36–100 | direct; independently checked both raw files | Serial simulated time, no validated overlap |
| C009 | S013 same commit/source | FTL.py L63–67,36–48 | direct; independently checked | Existing migration costs only, not future method |
| C010 | S013 partial repository audit, exact version fixed | simulator-audit.md §§4–6 and C008 chain | supported inference, not measured result | Need concurrent timing model for parallelism claim; audit lists uninspected files |
| C011 | S014 mutable local file, sample only, no checksum | hm_0.csv lines 1–120, specialist audit §§2–3; orchestrator lines 1–5 | direct for token in inspected sample | Provenance/schema/full op mix UNKNOWN; not write-only proof |
| C012 | S015 mutable local file, sample only, no checksum | prxy_0.csv lines 1–120, specialist audit §§2–3; orchestrator lines 1–5 | direct for token in inspected sample | Same semantic/access limits as C011 |
| C013 | S014/S015 native grep/glob, no full row validation | claims/dataset-screening.md search log | direct for bounded search outcome, partial for any all-reads-absent interpretation | No matches returned ≠ validated full-file op mix; need schema/profile |

Independent reviewer 2026-09-30 (reviews/protocol-review-v0.1.md) re-read lines 1–120 in each current CSV, confirming C011/C012 sample tokens without hashes or semantic provenance. Reviewer did NOT repeat C013 search, primary source code or article claim checks. No evidence of read predictability or throughput exists; conditional protocol and review are design artifacts, not experiment support.

2026-09-30 quick-scope update: C014 supported by completed E001 literal profile (EOF, stable identity, exact op counts and input SHA256); native-search uncertainty superseded for literal file content, but semantic/provenance limits remain. C015 independently verified in S016 README §3. Correction to librarian shorthand: ResponseTime is DURATION/time taken to complete, not absolute completion timestamp. Dataset docs verified, actual archives neither downloaded nor inspected. No model/read-throughput outcome exists.

S001/S002 are metadata-only, S007/S008 abstract-only inspected by librarian; not pivotal exact-support claims in this map. Unresolved source leads S004/S005/S006/S011/S012 remain outside verified evidence. Independent spot-check did not verify every source or every full-text section.

## 2026-10-01 access-only verification (orchestrator)
| Claim | Source identity/access | Locator | Support | Caveat/action |
|---|---|---|---|---|
| C018 | S016 SNIA IOTTA official landing, public HTML metadata | /traces/block-io/388 table: all2items, File Size3.06/1.88GB and set-level Download actions; independently re-fetched2026-10-01 | direct for inspected listing; limited absence claim only | Detail page inspected by librarian only. Per-volume/gated list not checked; metadata sizes not measured bytes. Small-budget direct single-gzip access unresolved, no download |
| C019 | S016 official checksum endpoint, public text | /traces/block-io/386/download?type=checksum, entire response names msr-cambridge1.tar and SHA1 28ef578dcafa98b94ba9d9fd1205e7eec58f43d8; independently re-fetched2026-10-01 | direct metadata, not byte/integrity verification | No tar bytes/members fetched; published SHA1 not applied to any local file |

No new efficacy claim promoted. Proposed numeric design/screen in temperature-poc-v0.1.md is an explicit choice, not citation-backed empirical performance. Independent design review is not primary-source/archive replication.
