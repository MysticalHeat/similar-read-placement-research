# Conference manuscript — bounded primary-source metadata & exact-support verification

- Date: 2026-10-07
- Owner: librarian (literature). Artifact path: `.research/literature/conference-sources-2026-10-07.md`
- Scope: English IACGN 2026 manuscript on **Write → next Read issue-time prediction / censored overwrite criteria from MSR Cambridge**.
- Budget actually consumed: **1 web search, 6 fetch attempts** (limit: 1 search / 6 fetches). No shell, no downloads, no execution.
- Write ownership honored: this file is the only artifact written. `papers.jsonl`, `claims/evidence-map.md`, `citation-audit.md` and the claim map were **not** modified. New IDs are **proposed** below for the orchestrator to merge.
- Max assigned S-ID checked: catalog `.research/literature/papers.jsonl` ends at **S026**; a project note (`.research/protocol/synthetic-temperature-demo-v0.1.md` line 72) explicitly states **S027 was not assigned**. Therefore proposed new IDs start at **S027**. S020/S023 are reserved leads in notes, not catalogued sources; they are below S026 and do not change the maximum.

## Acceptance summary

| # | Source | Identity metadata | Exact support retrieved | Access depth | Usable |
|---|---|---|---|---|---|
| S027 (proposed) | Narayanan, Donnelly, Rowstron, *Write Off-Loading*, FAST 2008 | Verified | Abstract only | Abstract + official landing/BibTeX | Yes (context/attribution; abstract level) |
| S028 (proposed) | Ke et al., *LightGBM*, NIPS 2017 | Verified | Abstract only | Abstract + official proceedings page | Yes (identity + generic boosting context) |
| S009 (update, not new) | Wang et al., *SepBIT*, FAST 2022 | Verified (now with pages/ISBN) | Abstract only (official); §2.3 passage is prior arXiv full-text record | Abstract + official landing/BibTeX | Yes |
| S016 (README, update blocked) | MSR Cambridge official README | **Retrieval failed** | None this pass | Endpoint unreachable | No — access limitation |

Three references (S027, S028, S009) meet the 2–3 usable-reference acceptance. The one dataset-schema task that mattered most (timestamps vs ResponseTime) **could not be verified** because the official IOTTA host was unreachable (see outage log).

## Search & fetch log (all attempts, including failures)

| ID | Tool | Target / query | Result |
|---|---|---|---|
| Q1 | websearch (Exa) | `LightGBM: A Highly Efficient Gradient Boosting Decision Tree NeurIPS 2017 official proceedings` (6 results) | Surfaced official `proceedings.neurips.cc` / `papers.nips.cc` pages; used to locate S028 landing page |
| F1 | webfetch | `https://iotta.snia.org/traces/block-io/386/download?type=readme` | **TIMEOUT** (120 s) — no bytes |
| F2 | webfetch | `https://www.usenix.org/conference/fast-08/write-loading-practical-power-management-enterprise-storage` | SUCCESS — S027 |
| F3 | webfetch | `https://iotta.snia.org/traces/block-io/386/download?type=readme` (retry) | **TIMEOUT** (120 s) — no bytes |
| F4 | webfetch | `https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html` | SUCCESS — S028 |
| F5 | webfetch | `https://www.usenix.org/conference/fast22/presentation/wang` | SUCCESS — S009 official version |
| F6 | webfetch | `https://iotta.snia.org/traces/block-io/386` | **TIMEOUT** (120 s) — no bytes |

Outage note: the entire `iotta.snia.org` host appeared unreachable from this environment (three independent paths, each 120 s timeout). This is **not** evidence the resource is unavailable globally; it is an access limitation of this session. No alternative mirror was substituted because the task named this URL as the official README and a mirror would not carry the same provenance. No retry remains within budget.

## Proposed new S-IDs (ready for orchestrator merge; do not auto-merge)

### S027 — Write Off-Loading (FAST 2008)
```json
{"id":"S027","title":"Write Off-Loading: Practical Power Management for Enterprise Storage","authors":["Dushyanth Narayanan","Austin Donnelly","Antony Rowstron"],"year":2008,"doi":null,"arxiv_id":null,"url":"https://www.usenix.org/conference/fast-08/write-loading-practical-power-management-enterprise-storage","version":"6th USENIX Conference on File and Storage Technologies (FAST 08), San Jose, CA, February 2008; official landing page and BibTeX; page numbers not shown on retrieved page","retrieved_at":"2026-10-07","access":"abstract","metadata_status":"title/authors/venue/year verified on official USENIX page and BibTeX 2026-10-07; abstract text read; no pages or DOI shown; source of the MSR Cambridge trace dataset by paper-level attribution only (README linkage NOT verified this pass)","note_path":".research/literature/conference-sources-2026-10-07.md#s027","source_type":"paper"}
```

### S028 — LightGBM (NIPS 2017)
```json
{"id":"S028","title":"LightGBM: A Highly Efficient Gradient Boosting Decision Tree","authors":["Guolin Ke","Qi Meng","Thomas Finley","Taifeng Wang","Wei Chen","Weidong Ma","Qiwei Ye","Tie-Yan Liu"],"year":2017,"doi":null,"arxiv_id":null,"url":"https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html","version":"Advances in Neural Information Processing Systems 30 (NIPS 2017), Long Beach, CA; official NeurIPS proceedings abstract page; no page numbers shown","retrieved_at":"2026-10-07","access":"abstract","metadata_status":"title/authors/venue verified on official NeurIPS proceedings page 2026-10-07; abstract text read; no DOI/pages shown on retrieved page","note_path":".research/literature/conference-sources-2026-10-07.md#s028","source_type":"paper"}
```

### S009 — metadata enrichment only (existing source, NOT a new ID)
Proposed fields to add to the existing S009 record (preprint/publication relationship retained): official FAST 22 venue string, `isbn: 978-1-939133-26-7`, `pages: 429-444`, `official_url: https://www.usenix.org/conference/fast22/presentation/wang`. Keep the existing arXiv ID `2104.12425` and the header-recorded FAST 22 relationship; do not discard the arXiv record.

### S016 — README sub-record (blocked)
No verified fields can be added this pass. If/when the orchestrator retries from a network where `iotta.snia.org` resolves, record the README schema as a sub-field of S016. Do not infer schema from the earlier 2026-09-30 internal note as if freshly verified.

## Per-source exact support and caveats

### S027 — Narayanan, Donnelly, Rowstron. *Write Off-Loading: Practical Power Management for Enterprise Storage*. FAST 08, 2008.
- Identity: verified directly from the official USENIX landing page. BibTeX visible on page: `@inproceedings {268334, author = {Dushyanth Narayanan and Austin Donnelly and Antony Rowstron}, title = {Write {Off-Loading}: Practical Power Management for Enterprise Storage}, booktitle = {6th USENIX Conference on File and Storage Technologies (FAST 08)}, year = {2008}, address = {San Jose, CA}, publisher = {USENIX Association}, month = feb }`. Byline affiliations all "Microsoft Research Ltd." No page numbers and no DOI were shown; **do not invent them**.
- Exact support (abstract, verbatim): "We analyzed block-level traces from 36 volumes in an enterprise data center for one week and concluded that significant idle periods exist, and that they can be further increased by modifying the read/write patterns using *write off-loading*." Also: "We evaluate it by replaying portions of our traces on a rack-based testbed."
- Support classification: **direct** for (a) paper identity and (b) the paper's own statement that its analysis used 36-volume, one-week enterprise block-level traces. **partial/context-only** for the specific claim that the public IOTTA "MSR Cambridge Traces" dataset *is* the same 36-volume collection, because the README that would confirm the linkage could not be retrieved.
- Caveat: **abstract-level access**; the full PDF was not read. The abstract also frames the workloads around "spinning disks" (HDD-era enterprise storage) — see HDD caveat below.

### S028 — Ke, Meng, Finley, Wang, Chen, Ma, Ye, Liu. *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NIPS 2017.
- Identity: verified directly from the official NeurIPS proceedings abstract page. Title and all eight authors visible; venue "Advances in Neural Information Processing Systems 30 (NIPS 2017)".
- Exact support (abstract, verbatim): "we propose two novel techniques: \emph{Gradient-based One-Side Sampling} (GOSS) and \emph{Exclusive Feature Bundling} (EFB)." And: "LightGBM speeds up the training process of conventional GBDT by up to over 20 times while achieving almost the same accuracy."
- Support classification: **direct** for method identity (introduces LightGBM as a GBDT implementation using GOSS/EFB). **context-only** for generic boosting/loss-objective background.
- Caveat: **abstract-level access**; no page numbers shown; no DOI shown. The "up to over 20 times" is an **author-reported abstract figure**, not independently verified here and **must not** be used to support any specific hyperparameter or training-speed claim in the manuscript. Use S028 only for identity and generic GBDT context. (The manuscript's actual `lightgbm.txt` model files and their provenance remain a separate local-artifact question.)

### S009 — Wang, Li, Lee, Ouyang, Shi, Huang. *Separating Data via Block Invalidation Time Inference for Write Amplification Reduction in Log-Structured Storage*. FAST 22, 2022.
- Identity: verified directly from the official USENIX FAST 22 page. Byline: "Qiuping Wang, Jinhong Li, and Patrick P. C. Lee, *The Chinese University of Hong Kong;* Tao Ouyang, Chao Shi, and Lilong Huang, *Alibaba Group*". BibTeX: `booktitle = {20th USENIX Conference on File and Storage Technologies (FAST 22)}, year = {2022}, isbn = {978-1-939133-26-7}, address = {Santa Clara, CA}, pages = {429--444}`.
- Exact support (abstract, verbatim): "We propose a novel data placement algorithm for reducing WA, SepBIT, that aims to infer the BITs of written blocks from storage workloads and separately place the blocks into groups with similar estimated BITs." And: "Trace analysis and prototype experiments show that SepBIT reduces WA and improves I/O throughput, respectively, compared with state-of-the-art data placement schemes."
- Write-invalidation vs read-time distinction: the official FAST 22 abstract concerns **write amplification and I/O throughput** and never makes a read-time prediction claim. The decisive write-only passage — "We only consider write requests as they are the only contributors of WA" — is recorded for **§2.3 of the arXiv full text (`2104.12425`)** in the existing `source-notes.md` S009 entry; it was **not re-fetched** in this pass and remains a prior full-text record, not a fresh verification. Classify: **direct** for "SepBIT targets block-invalidation-time inference for write amplification"; **partial** for the exact §2.3 quote (prior full-text record).
- Caveat: the USENIX page marks the PDF as gated ("This content is available to: Conference attendees"), so the official version was accessed at **abstract/metadata depth** only; the write-only §2.3 passage is supported by the previously inspected arXiv rendering, not the official PDF. The paper concerns cloud log-structured storage, not a device FTL, and its outcomes are WA/throughput, not read parallelism.

## Dataset-schema issue: timestamps vs ResponseTime (UNRESOLVED this pass)

The specific question — whether the MSR Cambridge trace schema exposes a request **issue Timestamp** and a separate **ResponseTime** (completion duration), which determines whether the manuscript's "Write → next Read **issue-time**" labels and censoring boundaries are well defined — **could not be verified** because all three attempts to reach the official IOTTA host timed out. Status: **UNKNOWN / access-blocked**.

- Earlier internal record `papers.jsonl` S016 (`retrieved_at: 2026-10-01`) and `source-notes.md` describe the README §3 as previously independently verified on 2026-09-30 and mention Read/Write bytes/time fields. That is a **prior, internal, unre-verified** record; it is **not** fresh evidence from this pass and should not be cited as verified in the manuscript without a successful README retrieval.
- Recommendation to the orchestrator: treat the schema as UNVERIFIED; do **not** assert the exact column set, whether ResponseTime is present, or which field is the issue time, until the README is retrieved. Provide the exact URL for retry: `https://iotta.snia.org/traces/block-io/386/download?type=readme` (and fallback landing `https://iotta.snia.org/traces/block-io/386`).

## Historical-HDD caveat (do not describe as SSD benchmark)

The MSR Cambridge traces are **2007–2008 enterprise hard-disk-drive (HDD) block-I/O traces**, not SSD traces. S027's abstract is framed explicitly around spinning disks ("enterprise workloads make spinning disks down ineffective…") and redirecting writes on spun-down disks; S016 records the dataset year as 2007. The manuscript must **not** present these traces as an SSD benchmark, SSD workload, or as evidence about flash/NAND behavior. Any SSD-parallelism discussion is a separate inference that these traces cannot directly support.

## Coverage and access limitations (honest)

- Only **2 of 3** sources were obtained at the level the task ideally wanted for the dataset; the **README (schema/attribution linchpin) was not obtained at all**.
- All three obtained sources were accessed at **abstract/metadata depth**, not full text. No PDF was parsed. Exact-support quotes are therefore limited to abstracts and official BibTeX/landing pages.
- Forward citation chaining was not performed (no citation-graph tooling used; out of budget and not required for acceptance). Backward chaining was not needed — the FAST 2008 paper is the primary attribution origin.
- No DOI was visible on any retrieved official page; none is proposed. Crossref was not queried (no tool call within the 1-search budget).
- The `iotta.snia.org` outage is session/environment-specific; it is **not** a global availability claim.

## Recommended next search / action (for the orchestrator, not executed here)

1. **Retry the official MSR Cambridge README** from a network where `iotta.snia.org` resolves (or via an authorized local download), then record: exact column schema (Timestamp vs ResponseTime and any issue/completion distinction), file naming/volumes, capture dates, and the explicit attribution sentence naming the FAST 2008 paper. This is the single highest-value follow-up for the manuscript's labeling validity.
2. Only after the README confirms the schema, decide whether the "Write → next Read issue-time" definition and censoring window are supported as written.
3. If a full-text check of S027 or S028 is later required, retrieve the official PDFs (FAST 08 `narayanan.pdf`; NeurIPS `...-Paper.pdf`) — but they are **not** needed for the identity/context support already established.
4. Do **not** promote the prior 2026-09-30 README note to verified status without a successful fresh retrieval.

## Handoff

- Artifact written (sole ownership): `.research/literature/conference-sources-2026-10-07.md`.
- New S-IDs proposed: **S027** (FAST 2008 Write Off-Loading), **S028** (LightGBM NIPS 2017). Existing **S009** proposed for metadata enrichment (pages 429–444, ISBN, official URL) — not a new ID. Existing **S016** README sub-record blocked by host outage.
- No catalog, claim-map, protocol or manuscript file was changed. Merge of S-IDs and any C-ID linkage is an orchestrator decision.
- Blockers/limitations: MSR README schema unverifiable this session (IOTTA host timeouts); all retrieved sources abstract-level; HDD-not-SSD caveat must be preserved.
