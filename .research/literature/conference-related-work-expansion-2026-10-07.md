# Conference Related Work — bounded expansion (learned storage read/future-access prediction)

- Date: 2026-10-07
- Owner: librarian (literature). Sole artifact written this pass: this file.
- Scope: extend the Related Work of the English IACGN 2026 manuscript
  (`writing/conference-article-2026-10-07.md`) with **2–4 genuinely close references**, no padding.
  Manuscript topic: at each Write, predict **seconds until the next matching Read (issue time)**
  for same-start or byte-range matching, with MAE-vs-overwrite-mean and censoring-derived pass bounds,
  on MSR Cambridge `proj_1`/`prn_1`. **NOT** sequence-of-pages prediction, CPU cache service latency,
  or SSD speedup measurement.
- Budget actually consumed: **4 web searches attempted (3 returned, 1 failed with HTTP 429)**;
  **10 fetches attempted (6 usable, 4 blocked/unreadable)**. No shell, no downloads, no parsers,
  no third-party execution. Public topic terms only; the unpublished manuscript text was not sent anywhere.
- Write ownership honored: `papers.jsonl`, `source-notes.md`, `claims/evidence-map.md`,
  `citation-audit.md` and the manuscript were **not** modified. New IDs are **proposed** for the
  orchestrator to merge. `search-log.md` was appended (not overwritten).

## 1. Decision summary

Selected **3 additions** (2 proposed new S-IDs + 1 refresh of an existing ID):

| Proposed | Source | Type | Access depth | Why it is genuinely close |
|---|---|---|---|---|
| **S030** | Chakraborttii & Litz, *Learning I/O Access Patterns to Improve Prefetching in SSDs* | Learned **SSD/storage** block-access prediction | Official-repository abstract (+ provider-extracted body, see caveat) | Directly learns **future block accesses** for storage prefetching; SSD setting |
| **S031** | Li & Gu, *Learning Forward Reuse Distance* | Learned **future-access** prediction on the **same MSR traces** | arXiv v1 full text read | Predicts future access of a datum from a storage trace; evaluated on the **same MSR `proj`/`prn` volumes** |
| **S008** (refresh) | Hashemi et al., *Learning Memory Access Patterns* | Foundational learned access-pattern/prefetch prediction | Abstract (official PMLR) | Canonical learned access-pattern work; **CPU memory — explicitly marked memory, not disk** |

**Evaluated but not selected:** Zhou & Maas, *Learning on Distributed Traces for Data Center Storage
Systems* (MLSys 2021). Its official metadata/abstract were verified, and the paper is a genuine
"time-to-next-access" lead (it discusses next-access interarrival time for cache admission), **but**
the full-text PDF returned unreadable raw bytes on two direct retrievals and my reader cannot ingest
PDF attachments, so the interarrival-time detail was visible only in a search-provider extraction and
could not be verified to the standard required. Kept as a documented near-miss (see §5).

**Not pursued (budget/scope):** GFPP 2026 (Expert Systems with Applications) and the 2025/2026
streaming-ML prefetching papers surfaced by Q1/Q2; they predict file-system offsets/hotness rather
than seconds-to-next-access, and the 4-query budget was exhausted.

## 2. Search trail (source, query, date, observed counts)

Provider: hosted Exa (websearch). Filters: none. Date: 2026-10-07. "Inspected" = results returned
to me, **not** full papers read.

| # | Query | Result | Observed | Outcome |
|---|---|---|---|---|
| Q1 | `learned prefetching disk block read prediction storage neural network 2026` | OK | 8 results | Surfaced S030 lead, GFPP 2026, MDPI streaming-ML |
| Q2 | `predict next access time storage workload trace machine learning regression` | OK | 8 results | Surfaced S031, Zhou & Maas MLSys 2021, Tiresias, Lynx |
| Q3 | `"Learning I/O Access Patterns to Improve Prefetching in SSDs"` | OK | 8 results | Confirmed S030 identity + provider-extracted body |
| Q4 | `learning memory access patterns prefetcher CPU Hashemi neural network` | **FAILED HTTP 429** (provider rate limit; no retry within budget) | 0 | No results returned |

Fetch attempts (all 2026-10-07, 30 s timeout each):

| # | URL | Result |
|---|---|---|
| F1 | `https://dl.acm.org/doi/10.1007/978-3-030-67667-4_26` | **403** — no metadata |
| F2 | `https://arxiv.org/abs/2007.15859` | OK — S031 metadata/abstract |
| F3 | `https://proceedings.mlsys.org/paper_files/paper/2021/file/efe0df3ea...-Paper.pdf` | raw PDF bytes, **unreadable** |
| F4 | `https://proceedings.mlr.press/v80/hashemi18a.html` | OK — S008 refresh metadata/abstract |
| F5 | `https://link.springer.com/chapter/10.1007/978-3-030-67667-4_26` | JS challenge page, **no metadata** |
| F6 | `https://proceedings.mlsys.org/paper_files/paper/2021/hash/efe0df3ea...-Abstract.html` | OK — Zhou & Maas metadata/abstract |
| F7 | `https://par.nsf.gov/biblio/10187652-learning-access-patterns-improve-prefetching-ssds` | OK — S030 official-repository record/abstract |
| F8 | MLSys PDF, `format=text` | raw PDF bytes, **unreadable** (second attempt) |
| F9 | `https://arxiv.org/html/2007.15859v1` | OK — S031 full text |
| F10 | `https://dblp.org/rec/conf/pkdd/ChakraborttiiL20.html` | Anubis JS challenge, **no metadata** |

Coverage limitations: 3 of the 4 databases/routes named were reachable; ACM, Springer and DBLP
bibliographic pages were blocked (403 / JS challenge), so S030's **venue string, pages and DOI are
UNVERIFIED** from official publisher metadata. The MSR Cambridge README was not re-attempted this
pass (no budget); S016 status is unchanged.

## 3. Candidate screening (max 5 considered)

| Candidate | Include? | Reason |
|---|---|---|
| Chakraborttii & Litz 2020 | **Yes → S030** | Closest learned **storage/SSD** block-access prediction; official-repository identity + abstract |
| Li & Gu 2020 (`2007.15859`) | **Yes → S031** | Learned future-access prediction; **same MSR `proj`/`prn` traces**; full text readable on arXiv |
| Hashemi et al. 2018 | **Yes → S008 refresh** | Foundational learned access-pattern prediction; the one allowed CPU-memory cross-domain ref |
| Zhou & Maas, MLSys 2021 | No (documented) | Direct time-to-next-access lead, but full text unreadable this session; only provider-extracted support |
| GFPP 2026 / streaming-ML 2025–26 | No | File-system offset/hotness prediction, not seconds-to-next-access; budget exhausted |

Deduplication: **S030 is the paper previously reserved as unresolved lead `S006`** (same title,
same candidate DOI `10.1007/978-3-030-67667-4_26`, same author copy). It was never catalogued.
Orchestrator should either promote `S006` or record `S030` and mark `S006` superseded — do not keep both.
**S031** collides with nothing existing. **S008** already exists; this pass refreshes it, no new ID.

## 4. Selected records (reference-ready)

### S030 (proposed) — Learned SSD block-access prediction / prefetch
- **Full authors:** Chandranil Chakraborttii; Heiner Litz
- **Title:** Learning I/O Access Patterns to Improve Prefetching in SSDs
- **Year:** 2020 (repository date 2020-07-01)
- **Venue:** ECML PKDD 2020 — **UNVERIFIED exact string**; the NSF PAR record lists an abbreviated
  venue `ICML-PKDD`, and search-index leads (BibSonomy, SlidesLive) report ECML/PKDD, LNCS 12460,
  pp. 427–443. Official Springer/ACM page not retrievable this session. **Pages and DOI not verified.**
- **Candidate DOI (UNVERIFIED):** `10.1007/978-3-030-67667-4_26` (search leads only)
- **Version:** accepted manuscript, NSF Public Access Repository ID 10187652
- **URL:** `https://par.nsf.gov/biblio/10187652-learning-access-patterns-improve-prefetching-ssds`
- **Access:** abstract (official repository) + provider-extracted body passages (not independently parsed)
- **Exact support (abstract, verbatim):** "Prefetching predicts future block accesses and preloads
  them into main memory ahead of time. … we … present a neural network based prefetching approach that
  significantly outperforms the state of the art. … we address the challenges of prefetching in very
  large sparse address spaces, as well as prefetching in a timely manner by predicting ahead of time."
- **Exact support beyond abstract (provider-extracted, treat as partial):** §4.1 states the model uses
  the MSR Cambridge traces and converts consecutive LBAs to LBA deltas (top-1000 coverage 91.66% for
  "MSR 1"); §4.3 measures inference latency (734 µs) and SSD read latency (300 µs) for timeliness.
  **These numbers were not independently parsed and must not be quoted in the manuscript.**
- **Bounded manuscript sentences (1–2):** "Chakraborttii and Litz train a neural network to predict
  future block accesses for prefetching in SSDs, explicitly targeting large sparse address spaces and
  predicting far enough ahead to be timely [S030]." / "Their target is which block (and size) will be
  accessed next, not the elapsed time until the next matching access at a Write, and their timeliness
  budget is a prefetch-lead-time constraint rather than an overwrite tolerance."
- **Difference from our task:** predicts *which/where* (next LBA delta and size), not *when in seconds*;
  Read-side prefetching, not Write-arrival conditioning; no censoring/overwrite criterion.
- **Limitations:** venue/pages/DOI unverified; body-level details only provider-extracted.

### S031 (proposed) — Learned forward reuse distance on MSR storage traces
- **Full authors:** Pengcheng Li (Damo Academy, Alibaba Group); Yongbin Gu (Oregon State University)
- **Title:** Learning Forward Reuse Distance
- **Year:** 2020 (arXiv v1, 31 Jul 2020)
- **Venue:** **None listed — arXiv preprint** (`Comments: 13 pages`; no journal reference on the arXiv record)
- **arXiv ID / DOI:** `arXiv:2007.15859`; DOI `10.48550/arXiv.2007.15859` (arXiv-issued)
- **URL / version:** `https://arxiv.org/abs/2007.15859` ; `arXiv:2007.15859v1`
- **Access:** full text (arXiv HTML v1 read)
- **Exact support:**
  - Abstract: "we propose a learning-aided approach to predict future data accesses … based on only a
    cache trace as input … evaluate it upon 13 real-world storage workloads from Microsoft Research."
  - §I: "Forward reuse distance just foresees the future access time." (§II-A defines reuse distance as
    "the number of accesses between two consecutive accesses to the same datum".)
  - §VI-C: "We tested upon a set of storage traces collected by Narayanan et al. [35]." Table II lists
    both **`proj`** and **`prn`** (the manuscript's two volumes) among the 13 MSR traces.
  - §V: the predicted value is stored as "the next access time for a cache entry" used for eviction.
- **Bounded manuscript sentences (1–2):** "Li and Gu use an LSTM to predict a block's forward reuse
  distance from a storage trace alone, evaluated on 13 MSR traces that include proj and prn [S031]." /
  "Their target is access-count distance between reuses of the same datum for cache eviction, whereas we
  predict elapsed seconds to the next matching Read at Write arrival and judge each error against an
  overwrite delay."
- **Difference from our task:** reuse *distance in access counts*, not wall-clock seconds; cache
  replacement objective, not Write-arrival conditioning, address-matching rules, or censoring bounds;
  no overwrite tolerance.
- **Limitations:** preprint only (no peer-reviewed venue verified); full-text observations are from
  arXiv v1 and may differ from any later version.

### S008 (refresh — existing ID, no new ID)
- **Full authors:** Milad Hashemi; Kevin Swersky; Jamie Smith; Grant Ayers; Heiner Litz; Jichuan Chang;
  Christos Kozyrakis; Parthasarathy Ranganathan
- **Title:** Learning Memory Access Patterns
- **Year:** 2018
- **Venue (verified):** Proceedings of the 35th International Conference on Machine Learning (ICML 2018),
  PMLR 80:1919–1928
- **URL:** `https://proceedings.mlr.press/v80/hashemi18a.html`
- **Access:** abstract (official PMLR page + BibTeX)
- **Exact support (abstract, verbatim):** "We focus on the critical problem of **learning memory access
  patterns**, with the goal of constructing accurate and efficient **memory prefetchers**. … recurrent
  neural networks can serve as a drop-in replacement. … neural networks consistently demonstrate superior
  performance in terms of precision and recall."
- **Bounded manuscript sentence (1–2):** "In computer architecture, Hashemi et al. learn memory access
  patterns with recurrent networks for CPU/cache prefetchers [S008]." / "That setting is processor
  memory, not secondary storage, and it predicts the next memory access rather than the elapsed time to
  the next matching access."
- **Difference from our task:** CPU memory, not disk/storage; predicts access patterns/prefetch
  precision-recall rather than seconds-to-next-access; no address-matching or overwrite semantics.
- **Refresh note:** earlier records were "abstract lead, not refreshed." This pass re-verified title,
  all authors, venue, pages and abstract directly on the official PMLR page. Still abstract-level only.

## 5. Documented near-miss (not selected)
- **Zhou, G.; Maas, M. "Learning on Distributed Traces for Data Center Storage Systems," MLSys 2021.**
  Official metadata/abstract verified at
  `https://proceedings.mlsys.org/paper_files/paper/2021/hash/efe0df3ea4a53a04614ad79e7a8a57de-Abstract.html`
  (Proceedings of Machine Learning and Systems 3). Abstract verbatim: "Our models improve prediction
  accuracy by 11–33% over non-ML baselines, which translates to significantly improving the hit rate of
  a caching task, as well as improvements to an SSD/HDD tiering task, on production data center storage
  traces." **Not selected** because the specific next-access/interarrival-time content appears only in a
  search-provider extraction of a PDF whose bytes I retrieved but could not parse (reader cannot ingest
  PDF; two direct attempts). It remains the best-known **direct time-to-next-access** lead and is a
  recommended next search/fetch (HTML or ar5iv equivalent).

## 6. Proposed `papers.jsonl` lines (orchestrator merge; do not auto-merge)
```json
{"id":"S030","title":"Learning I/O Access Patterns to Improve Prefetching in SSDs","authors":["Chandranil Chakraborttii","Heiner Litz"],"year":2020,"doi":null,"arxiv_id":null,"url":"https://par.nsf.gov/biblio/10187652-learning-access-patterns-improve-prefetching-ssds","version":"ECML PKDD 2020 (exact venue string UNVERIFIED; NSF PAR record 10187652 lists 'ICML-PKDD'); accepted manuscript; pages/DOI not verified","retrieved_at":"2026-10-07","access":"abstract","metadata_status":"title/authors/year verified on NSF Public Access Repository 2026-10-07; abstract read; venue/pages/DOI UNVERIFIED (ACM 403, Springer and DBLP blocked); body-level detail provider-extracted only; previously reserved as unresolved lead S006","note_path":".research/literature/conference-related-work-expansion-2026-10-07.md#s030"}
{"id":"S031","title":"Learning Forward Reuse Distance","authors":["Pengcheng Li","Yongbin Gu"],"year":2020,"doi":"10.48550/arXiv.2007.15859","arxiv_id":"2007.15859","url":"https://arxiv.org/abs/2007.15859","version":"arXiv:2007.15859v1, 31 Jul 2020; preprint, no venue listed on arXiv record","retrieved_at":"2026-10-07","access":"full-text","metadata_status":"title/authors/date/arXiv ID verified on official arXiv record 2026-10-07; arXiv HTML v1 read; no peer-reviewed venue on the record","note_path":".research/literature/conference-related-work-expansion-2026-10-07.md#s031"}
```

## 7. Bounded coverage, limitations, recommended next action
- **Bounded exploratory search, not systematic**: 4 queries / 10 fetches, one provider 429, three
  blocked bibliographic routes. Saturation is claimed only within these searched sources.
- **Access asymmetry**: S031 was readable at full text; S030 and S008 are abstract-level; S030's
  body claims are provider-extracted and must not be quoted.
- **No venue inflation**: S031 is a preprint; S030's venue/pages/DOI are UNVERIFIED — the manuscript
  should cite only what is verified or mark it accordingly.
- **No performance numbers imported**; no experiments proposed; no global C-IDs assigned.
- **Recommended next action (orchestrator):** (1) merge S030/S031 proposals and refresh S008 note;
  (2) if a direct time-to-next-access ref is wanted, obtain a machine-readable copy of Zhou & Maas
  (MLSys 2021) via an HTML/ar5iv route, then re-verify the interarrival-time passage; (3) do **not**
  promote S030's DOI/pages until an official publisher page is fetched.

## Handoff
- Artifact: `.research/literature/conference-related-work-expansion-2026-10-07.md` (this file).
- Proposed new IDs: **S030**, **S031**. Refreshed existing: **S008**. Near-miss documented: Zhou & Maas (MLSys 2021).
- `search-log.md` appended. `papers.jsonl` / claim map / manuscript untouched.
