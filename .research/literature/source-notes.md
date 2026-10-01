# Reading notes / source evaluation

Дата доступа для всех: 2026-09-30. Результаты авторов не воспроизведены. Ниже различаются метаданные, аннотация и доступный полный текст. Непроверенные цифры из поисковых выдержек не используются.

## S001
Official USENIX metadata inspected by librarian. Foundational placement/SSD design lead; original PDF not independently read. Search-provider extracted passages are not sufficient for our exact claims. URL in papers.jsonl. Claim support pending.

## S002
Crossref identity verified by librarian for DOI 10.1145/1995896.1995912. Potentially relevant parallelism/allocation study; full text not independently inspected. No generalized performance or allocation rankings accepted from provider snippets. Claim support pending.

## S003
Full-text HTML: https://ar5iv.labs.arxiv.org/html/1705.04627 . Title/byline visible. Header states published at 20th HPCA and that this material includes additional garbage-collection data. Do not equate arXiv rendering with original publication version.

Exact independently inspected support:
- §2.1: “FTL translates virtual addresses of the memory requests coming from NVMHC into physical addresses, and scatters them over available flash controllers.”
- §2.2: “to take advantage of plane sharing, addresses of the memory requests in a transaction should indicate the same page and die offset in the flash chip, but different block addresses (or plane addresses).”
- §4.2: FARO brings requests to controllers early, allowing coalescence into a transaction with spatial and temporal transactional locality.
- Abstract: evaluation uses a “cycle-accurate large-scale SSD simulation framework”.

Evaluation: primary, directly useful for proposed physical mechanism; architectural and timing conditions matter. It studies request scheduling, NOT learned future-read placement. No promised gain for user's workload. Multi-plane grouping can be compatible with parallelism; neither indiscriminate co-location nor indiscriminate spreading is a universal solution. Supported C001, C004.

## S007
Primary abstract/metadata: https://arxiv.org/abs/2304.03864 . Librarian verified landing page; no full text read. Storage-prefetch direction based on graph/stream prediction. Numerical claims from abstract deliberately not integrated into our conclusions; benchmark applicability and latency metric need full-text evaluation. Context-only for question alternatives.

## S008
Primary abstract/metadata: https://proceedings.mlr.press/v80/hashemi18a.html . Librarian verified. Memory/cache access prediction, not SSD physical-page placement. Abstract compares precision/recall; cannot transfer those results to SSD performance. Context-only conceptual baseline.

## S009
Full-text HTML: https://ar5iv.labs.arxiv.org/html/2104.12425 . Header/byline independently checked; header states conference version appeared at FAST 22.

Exact independently inspected support:
- Abstract: “SepBIT ... aims to infer the BITs of written blocks from storage workloads and separately place the blocks into groups with similar estimated BITs.” Objective is reducing write amplification.
- §2.1: GC “works by reading a segment of blocks, removing any stale blocks, and writing back the remaining live blocks” (the same explanation also appears in introduction); §2.1 defines WA as user-written plus GC-rewritten blocks divided by user-written blocks.
- §2.3: “We only consider write requests as they are the only contributors of WA.”

Evaluation: primary, useful for predicted placement and cost controls, not evidence of next-read prediction or read-parallelism benefit. Cloud log-structured storage is not automatically a device FTL. Supported C002.

## S010
Official abstract and BibTeX independently checked: https://www.usenix.org/conference/fast26/presentation/kim-jeeyun . FAST 26, 2026, pp. 543-559, byline verified. PDF fetch by librarian returned unreadable bytes; full text not read.

Exact support, abstract: “DOGI predicts invalidation times for data blocks ... dynamically tunes group configurations ... fine-grained data placement and misprediction penalty.” Evaluation described as simulations and prototype on a zoned device; outcomes named WAF and write throughput. Supports narrow objective contrast C003, not a read-latency claim.

## Unresolved leads (reserved IDs, NOT verified evidence)
- S004 candidate “Internal Parallelism of Flash Memory-Based Solid-State Drives”; https://www.csc.lsu.edu/~bhou/publish/tos16 . Bibliographic details unresolved; direct readable-text retrieval failed. Do not use provider-extracted performance figures.
- S005 candidate “RDA: A Read-Request Driven Adaptive Allocation Scheme for Improving SSD Performance”; https://ieeexplore.ieee.org/document/10614397/ . Metadata and original support not independently verified; promising placement comparator, further retrieval needed.
- S006 candidate “Learning I/O Access Patterns to Improve Prefetching in SSDs”; https://hlitz.github.io/papers/ecml2020.pdf . Candidate DOI 10.1007/978-3-030-67667-4_26 returned by librarian; original byline and readable text not verified here. Do not claim universal insufficiency of next-block prediction from a snippet.
- S011 candidate PaRT-FTL; https://www.cs.bu.edu/~richwest/papers/rt_nand_rtss2018.pdf . Exact title/byline and year not accepted from filename alone; PDF text unavailable. Claimed striping/interleaving comparison requires original text.
- S012 candidate “Design of a Dynamic Correlation-Aware Prefetching Mechanism for Back-End Parallelism”; https://exa.ai/library/publication/v9hb3gx15n9 . Third-party record only, date/byline/venue and exact support UNVERIFIED. Important possible near prior work to retrieve before novelty judgment.
