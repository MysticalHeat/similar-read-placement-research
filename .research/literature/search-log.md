# SSD: ограниченный разведочный поиск

Дата: 2026-09-30. Тип: exploratory, НЕ systematic review. Направления: read prediction/prefetch; NAND/FTL placement and parallelism; prediction-guided placement and write costs. Англоязычные публичные запросы, foundational work и поиск recent work с 2026. Пользовательская формулировка не отправлялась дословно.

## Поиск библиотекаря (возвращённый журнал)
Provider: hosted Exa. Filters: none. Inspected — сообщённое библиотекарем число просмотренных результатов, не число полностью прочитанных статей.

| # | Query | Inspected | Selected/leads | Outcome |
|---|---|---|---|---|
| 1 | SSD internal parallelism NAND channel die plane flash translation layer data placement survey | 0 | none | HTTP 429; no retry |
| 2 | flash translation layer striping granularity parallel read latency multiple dies pages | 8 | S004/S011 unresolved leads | results inspected |
| 3 | read prefetching SSD prediction next block access learned prefetcher | 8 | S006 lead, S007, S008 | results inspected |
| 4 | prediction guided data placement flash SSD reorganization write amplification endurance | 8 | S009, S010 | results inspected |
| 5 | Design Tradeoffs for SSD Performance Agrawal Prabhakaran 2008 parallelism | 6 | S001 | metadata |
| 6 | SSD read performance page placement grouping parallel reads channel die plane | 8 | S002; S004/S005 unresolved leads | results inspected |
| 7 | NAND flash read-ahead prefetch internal parallelism SSD read latency | 8 | S003; S004 lead | results inspected |
| 8 | deep learning SSD read prediction prefetch 2025 2026 | 8 | S012 unresolved lead | results inspected |

## Direct fetches библиотекаря (12; все 2026-09-30)
| # | URL | Outcome/access |
|---|---|---|
| 1 | https://hlitz.github.io/papers/ecml2020.pdf | raw PDF bytes, no readable extraction |
| 2 | https://www.cs.bu.edu/~richwest/papers/rt_nand_rtss2018.pdf | raw PDF bytes, no readable extraction |
| 3 | https://www.usenix.org/system/files/fast26-kim-jeeyun.pdf | raw PDF bytes, no readable extraction |
| 4 | https://www.csc.lsu.edu/~bhou/publish/tos16 | raw PDF bytes, no readable extraction |
| 5 | https://www.mdpi.com/2076-3417/13/24/13017 | HTTP 403 |
| 6 | https://ar5iv.labs.arxiv.org/html/2104.12425 | full-text HTML S009 |
| 7 | https://arxiv.org/abs/2304.03864 | abstract and metadata S007 |
| 8 | https://proceedings.mlr.press/v80/hashemi18a.html | abstract and metadata S008 |
| 9 | https://ar5iv.labs.arxiv.org/html/1705.04627 | full-text HTML S003 |
| 10 | https://www.usenix.org/conference/fast26/presentation/kim-jeeyun | abstract and metadata S010 |
| 11 | https://www.usenix.org/conference/2008-usenix-annual-technical-conference/design-tradeoffs-ssd-performance | metadata S001 |
| 12 | https://api.crossref.org/works/10.1145/1995896.1995912 | metadata S002 |

Correction by orchestrator: this is 5 unsuccessful readable-text retrievals, not 4 as stated in librarian summary. Four returned unreadable PDF bytes and one returned 403. Query budget 8 and fetch budget 12 reached. Minimum requested 3 primary full-text sources NOT met: only 2 accessible. Librarian returned 12 source candidates despite requested 6-8; retain 7 sufficiently identified records, reserve unresolved IDs rather than silently treating all as verified.

## Independent orchestrator spot-checks (additional verification budget: 3 fetches)
2026-09-30: re-fetched S003 ar5iv, S009 ar5iv and S010 official USENIX page. Read exact supporting passages in S003 §§1, 2.1, 2.2, 4.2; S009 abstract and §§2.1, 2.3; S010 abstract/BibTeX. HTML outputs were truncated after substantial text; only inspected passages support claims, not a claim that orchestrator read every section. No shell, code execution or replication.

## Deduplication, inclusion and limitations
Not systematic: no PRISMA/screening totals asserted. Seven retained records have no duplicate DOI/arXiv or normalized title. S003 preserves publication/arXiv relationship; S007 and S009 preserve conference/preprint relationship. Metadata unknowns remain explicit. S001/S002 retained for foundational identity; S003 for mechanism; S007 for storage prefetch; S008 for memory-prefetch contrast; S009/S010 for placement objective contrast.

Unresolved leads S004, S005, S006, S011, S012 are documented in source-notes.md, not accepted claim evidence. Other uninspected branches: DS-FTL (403), FSPDA, Pattern+, ZNS/FDP/streams specifications, FEMU/OpenSSD feasibility. Patent mentions from search omitted until identifier/content verified. This finite search is not novelty proof.

Artifact handoff: librarian could not write files due to permission errors; orchestrator saved an evaluated, narrowed integration of the returned material. No permission bypass via shell. No claims based solely on search highlights promoted to verified status.

## S013: targeted repository audit after user's clarification
2026-09-30, not a literature search expansion. Source: user-provided public repository; inclusion reason: concrete proposed simulator for learned read prediction and migration. No queries, no dedup collision. Experimenter made 12 successful fetches: latest commit discovery via GitHub API, tree API, nine Python sources and LICENSE at commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21. Exact URLs, file inventory/blob hashes, access limitations and support locations: experiments/simulator-audit.md §§2–7,11. Did not inspect README/Makefile/FTLFactory.py/SSD.py/Page.py/.gitignore content. No installation or execution.
Orchestrator additional verification: 3 successful raw-source fetches of MiDaFTL.py, Statistics.py and FTL.py at the same commit; checked writing pointers, process_read, serial add_time, process loop and migrate_page. Not a benchmark. Repository retained as S013 with bibliographic unknowns null; no claim of complete source audit or physical validation.

## S014/S015: local dataset audit (not external discovery)
2026-09-30. No web queries or transmission. User supplied dataset/; two local CSV paths verified. Native first-120-line inspection per file by experimenter, first-five-line spot-check and bounded token search by orchestrator; exact access/failures/positive control and caveats: experiments/dataset-audit.md and claims/dataset-screening.md. Retained as data-sample sources with semantic metadata/version/checksum/license unknown; not accepted as verified read workloads. No deduplication/independence from filenames inferred.

## S016: few-minute public fallback discovery
2026-09-30. Librarian budget max2queries/3fetches; actual1 Exa query, 3 successful fetches. Query: MSR Cambridge block I/O traces SNIA IOTTA repository read LBA size timestamp; numResults8, primary candidate selected because documentation explicitly states read labels and address/size/time fields. Fetched https://iotta.snia.org/traces/block-io/388 , https://iotta.snia.org/traces/block-io/386/download?type=readme , https://iotta.snia.org/repository/download_license . Exact access/licensing/inspection limits in public-data-options.md. No trace download/license acceptance/decompression/model training. Orchestrator one additional successful README fetch independently verified §3, corrected ResponseTime to duration, not absolute timestamp. Filename resemblance not used to infer local provenance. No other datasets evaluated; finite single-option discovery, not systematic.

## S016: bounded public-text small-access check, 2026-10-01
Purpose: exact listed single-volume gzip access for small PoC, not novelty/suitability search. Librarian actual0queries/3successful fetches (budget1query/3fetches): https://iotta.snia.org/traces/block-io/388 (2 set-level listings; no per-volume URLs), https://iotta.snia.org/traces/block-io/386 (No items found), https://iotta.snia.org/traces/block-io/386/download?type=checksum (one line names msr-cambridge1.tar). Selected S016 retained for documentation; advertised bulk excluded from current proposed100MiB download cap. No other source added/deduplicated; no failures, no archive/sample bytes fetched, terms not accepted, gated pages not inspected. Exact notes: msr-access-check-2026-10-01.md. Orchestrator additional2successful fetches: same landing and checksum; directly spot-checked C018/C019 support. STOP pending access decision; no exhaustive absence or archive-member claim.
