# Conference draft: traceability and author checkpoints

## Latest Related Work handoff — 2026-10-07

Use submission/conference/Elmanov_IACGN_2026_expanded.{docx,pdf}: three pages,
six sources, full university name. Only SectionII/References changed from the
_Don_State version; all empirical sections unchanged by document-only comparison.
Current detailed literature ledger: conference-related-work-ledger-2026-10-07.md;
independent review: ../reviews/conference-related-work-citation-review-2026-10-07.md.
Numbering now[1]S027,[2]S006,[3]S007,[4]S031,[5]S009,[6]S028.
R033 absence claim introduced in compression removed and reviewer closed;
R031 remains disclosed/R032resolved. Older reference-number/file/affiliation
statements below are retained stage history, not current delivery directions.

## Later author-field update — 2026-10-07

Latest instruction supersedes abbreviation: **Don State Technical University,
Rostov-on-Don, Russia**. Latest delivery is
submission/conference/Elmanov_IACGN_2026_Don_State.{docx,pdf}; checks confirm
affiliation-only text change from preserved _DSTU.md, three pages retained.
Affiliation resolved; remaining scientific/declaration caveats unchanged.

User supplied `DSTU, Rostov-on-Don, Russia` and requested replacing the
placeholder. Current source contains that exact affiliation; deliverables are
submission/conference/Elmanov_IACGN_2026_DSTU.{docx,pdf}. Earlier _final copies
preserve the reviewed pre-update text. No scientific prose/tables changed;
document-only verification passed and3pages retained. Historical affiliation
pending statements below describe the earlier checkpoint; this field is now
resolved by user instruction, not inferred from other documents.

Date: 2026-10-07. Writer owns this file, `conference-article-2026-10-07.md` and the subsequently approved `conference-article-layout-v1-2026-10-07.md` snapshot. Current empirical scope approved in `.research/README.md` October 7 decision rows 30–31; historical synthetic draft and evidence are not used. No new runs, searches, shell execution or source/result edits. Initial evidence review used twelve targeted reads; layout revision inspected only the two local writing files. S029 is the existing local artifact bundle, not a new E-ID or independent replication.

## Evidence-first outline / completed manuscript claim ledger

| Manuscript section | Purpose / claim IDs | Support | Required qualification |
|---|---|---|---|
| Abstract; I. Introduction | Distinguish aggregate mean and record reliability; C045–C048, C050 | S029 pooled saved results | Observed-Read cohort; development only |
| II. Related Work | Dataset attribution and modest context; C051–C052 | S016 local README §4; S027/S009/S028 official abstract notes | HDD-era source; no novelty or transferred performance |
| III. Methods | Labels, features, splits, selection and censoring math; C042–C044, C048–C051 | S029 code/config/protocol locators in current claim map and static audit | Issue-to-issue, partial overlap, source-row ties, unequal horizons, changed selection, dependent records |
| IV. Results | Three compact numeric tables and counterevidence; C045–C048 | S029 `submission/overwrite-results.json` pooled selected entries and reviewer | Bounds are identification bounds; paired denominator differs; range mean undetermined, not failed |
| V. Interpretation | Explain non-equivalence of criteria; C045–C047, C050 | S029 metrics plus reviewer counterevidence | Possible tail/cohort explanations are hypotheses, not established causes |
| VI. Limitations | Coverage, dependence, development and reproduction gaps; C042–C043, C048–C051 | S029 protocols, review R026–R030, static audit | No IID inference, chronology certificate, independent rerun or SSD benefit |
| VII. Future Work; VIII. Conclusion | Untouched-data design and bounded summary; C045–C050 | Existing evidence and disclosed limits | Recommendations only; no promised gain |
| References | Exactly three verified identities | S027 [1], S009 [2], S028 [3] | Abstract-level support for cited contextual claims |

## Exact support index

Paths below are relative to the project root. Claims retain the current evidence-map wording; this ledger does not create stronger shared claims or new run IDs.

- **C042, III.A and VI:** S016, existing `dataset/msr-cambridge1.tar` README member, §3 (issued Timestamp, separate ResponseTime), §4 (FAST08 attribution). Local text was inspected by the orchestrator on 2026-10-07; writer checked its recorded excerpt in the current claim map, lines 23–33. S029 `read_prediction/pipeline.py:68–82,92–132`; `read_prediction/range_label.py:165–198`; static-audit lines 14–41 cover issue subtraction, matching, partial intersection, independent targets and row ties. Confidence high for the inspected definitions, not runtime completeness or archive authentication.
- **C043, III.B and VI:** S029 `submission/models.json:2–14`, static-audit lines 43–60; underlying `pipeline.py:100–116` and `extended.py:90–140` describe seven inputs, current-Write exclusion, same-start history, NaN and transforms. Earlier-row semantics do not establish universal leakage freedom or range-aware history.
- **C044, III.B–D:** S029 `submission/models.json:15–47,49–85`; `docs/protocols/long-history-protocol.md:10–33,37–48`; `mixture-protocol.md:7–17,27`; `mean-overwrite-protocol.md:7–12`. Current selection has 3/6 candidates; evaluated comparison pools have 5/8 methods (`submission/README.md:36–43`, `overwrite-results.json` pooled_candidates). Actual hyperparameters and transforms also have static-audit lines 95–103 / underlying `long_history.py:96–106` support. Configuration/protocol evidence is not a fresh execution or bitwise reproducibility certificate. Dependency pointers were located in the static audit, not inspected for runtime correspondence by this writer.
- **C045–C046, abstract, III.C, IV Tables II–III, V and VIII:** S029 `submission/overwrite-results.json`, selected_results entries filtered by `window="pooled"`, respectively `proj_1/same_start` lines 122–150, `proj_1/range` 267–295, `prn_1/same_start` 412–440 and `prn_1/range` 557–585. Fields: `observed_read.{mae_seconds,mean_overwrite_lower_seconds,status}`, `confirmed_pass_count`, `unknown_pass_count`, `pass_lower`, `pass_upper`, `ninety_percent_status`. Current protocol lines 14–28 supports the finite-cohort mean lower bound and pooling. Strict pass semantics are supported by long-history lines 42–48 and static-audit lines 35,48–50. The manuscript conservatively leaves e=L unresolved unless strict boundary exclusion is established; it does not claim an independent equality-case array audit. Bounds are descriptive censoring bounds, not inferential confidence intervals.
- **C047, IV Table III and V/VIII:** Same four pooled entries, `paired_n` and `paired.{mae_seconds,mean_overwrite_seconds,ratio,passed}`; `submission/README.md:25–34`; reviewer lines 38–40 supports all saved methods' pooled paired failures. Confidence high in stored consistency, with no independent raw joins. Paired records are a different cohort.
- **C048, IV Table I and VI:** Same pooled entries, `observed_reads` and `all_writes`; `submission/README.md:91–96`. Coverage percentages were cross-checked against these saved rows, not newly recomputed. Repeated Writes/target Reads are dependent. Counts are not IID replicates.
- **C049, III.A:** Current claim map row C049 and static-audit lines 62–76: `docs/protocols/data-sufficiency-protocol.md:9–15,42–44`, `data_sufficiency.py:59–77,102–127,165–172`; saved dataset-comparison fields `traces/eligible_new_workloads/range_confirmation/selected`. Prefix support selection and one excluded-row lookahead are statically supported; historical access chronology is not certified. Dataset-comparison was inspected by the reviewer, not directly re-read within this writer's 12-read budget.
- **C050, abstract, III.B, V–VIII:** `long-history-protocol.md:3–4`, `mean-overwrite-protocol.md:26–28`, reviewer R027/R029 and lines 41–49. Specific mixture counterexamples in IV are reviewer lines 41–43, independently matched to S029 `overwrite-results.json` pooled_candidates: N-S/raw_l1 `observed_read.mae_seconds` line 917, N-R/address_median line 1178. No universal superiority, novelty or SSD benefit claimed. Possible tail/cohort mechanisms and future designs are qualified hypotheses/recommendations, not new findings.
- **C051, II and III.A:** S029 `results/new-workloads/{proj_1,prn_1}/source.json:8–19`, endpoints/event counts reproduced in static-audit lines 78–93; S027 abstract context. Exact elapsed duration, uninterrupted capture and independent rehash were not established.
- **C052, II:** S009/S028 official abstract support and exact metadata in `literature/conference-sources-2026-10-07.md:61–71`. No paper performance figure or full-text-specific claim is imported. S027 primary abstract and attribution support are in lines 55–59 plus the locally resolved S016 §4.

## Citation checks performed

Writer checked reference order, complete bylines, titles, years, venues and permissible page fields against the catalog and October 7 primary-source verification notes. This was a **saved-record support/identity check**, not fresh network retrieval or independent full-paper reading. Official source retrieval dates below are those recorded by the librarian/orchestrator.

| Reference / S-ID | Verified identity and exact claim support | Access depth / status / caveat |
|---|---|---|
| [1] S027 (+ S016 attribution) | D. Narayanan, A. Donnelly, A. Rowstron; *Write Off-Loading: Practical Power Management for Enterprise Storage*; FAST08, 2008. Official abstract: one-week block-level traces from 36 enterprise volumes; spinning-disk context. S016 local README §4 directs this attribution. | Official landing/BibTeX and abstract recorded 2026-10-07; direct for paper context, local README direct for dataset attribution. No full-paper claim; no DOI/pages added. |
| [2] S009 | Q. Wang, J. Li, P. P. C. Lee, T. Ouyang, C. Shi, L. Huang; full SepBIT title retained; FAST22, 2022, pp. 429–444. Official abstract: infer block-invalidation times and separately place blocks with similar estimates for write-amplification reduction. | Official abstract/metadata recorded 2026-10-07; direct for the narrow context. Official PDF not read. Catalog retains prior arXiv full-text relationship; writer does not rely on its §2.3 quotation or imply official full-text access. |
| [3] S028 | G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, T.-Y. Liu; *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*; *Advances in Neural Information Processing Systems 30*, 2017. Official abstract supports GBDT method identity. | Official abstract/metadata recorded 2026-10-07; direct identity/context only. Hyperparameters supported by S029, not [3]. No training-speed figure, DOI or unverified pages used. |

Verified public identity URLs retained here rather than lengthening the manuscript references:

1. https://www.usenix.org/conference/fast-08/write-loading-practical-power-management-enterprise-storage
2. https://www.usenix.org/conference/fast22/presentation/wang
3. https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html

**Resolved source-note conflict:** the librarian's timeout/“no schema support” statements in its October 7 note are superseded by the orchestrator's local tar README inspection in the current claim map. Schema/attribution are supported locally, not freshly remote-authenticated. Also, submission/README retains overstrong statements about independent events, exact 168-hour coverage, historical non-access and not declaring 90% failure (lines 51,82,85,98). These were not edited. The manuscript follows the newer reviewed C042–C052 scope; the discrepancies are explicitly reported here for orchestrator integration, not silently altered in evidence artifacts.

## Numerical and presentation checks

- Three tables, each with four data rows and respectively 4/5/4 columns; separate `TABLE I/II/III.` captions. All durations/errors use seconds; paired ratios, coverage and counts are clearly dimensionless. Column-width/page-fit remains compositor work, not a verified four-page layout.
- P-S/P-R/N-S/N-R defined before the tables. Table I denominators match saved pooled entries; coverage is explicitly workload-specific. Table II method/MAE/lower-bound/status values match both export and reviewed source rows. P-R remains **undetermined**, never classified as a failed observed-Read mean comparison.
- Table III endpoints match the saved pass bounds to two percentage decimals: 51.35–52.72%, 45.79–47.17%, 50.03–50.36%, 46.19–46.51%. Paired N and ratios match the export, including 1.3939/1.6227/1.3581/1.4644. All four 90% failures explicitly apply to the observed-Read cohort only. No raw-array or equality-boundary recomputation was performed.
- Mean lower-bound equation sums known B and remaining-window lower bounds L over the **same** observed-Read denominator; pooling uses records, not unweighted day means. Strict inequalities and paired-cohort distinction retained. No p-values or inferential confidence intervals.
- Abstract unchanged at **87 words**, excluding the `Abstract —` prefix. Three alphabetical keywords. Main text has no internal claim IDs; numbered references are [1] dataset attribution, [2] SepBIT, [3] LightGBM in first-citation order. The approved name/status now share one paragraph; affiliation placeholder and email remain separate and unchanged.
- Orchestrator/user supplied an automated pre-trim count of **2,266 words including Markdown** and reported four pages with poor last-page balance. This supersedes the original writer's rough 2,500-word estimate. Layout revision removes approximately **200 words**, aiming at **2,050–2,080** (about **2,060** estimated); no automated count, computation or render was performed by this writer. Exact revised count and page balance remain compositor checks.

## Reviewer concerns and remaining UNVERIFIED items

| Review item | Manuscript treatment | Remaining limit |
|---|---|---|
| R026 | III.A says issue-to-issue, separate ResponseTime, partial intersection and source-row ties. Local primary schema recovery acknowledged internally. | Full runtime/byte-integrity audit not established. |
| R027 (major in source review) | VI and III.C disclose dependence and use no IID tests/binomial or inferential intervals. | Dependence-aware confirmation absent; obsolete source README wording remains outside writer ownership. |
| R028 | IV gives workload-specific coverage and definite 90% failure on observed-Read records. | All-Write prediction reliability not identified. |
| R029 | III.B distinguishes current MAE selection from earlier rules, 3/6 candidates from 5/8 evaluated methods, and development from untouched holdout. | Historical chronology and fresh prospective confirmation remain unverified. |
| R030 | III.A says approximately seven days and explains prefix-based code with boundary-row lookahead. | Historical no-access certificate, capture continuity and complete independent screening verification absent. |

The review explicitly permits this bounded descriptive article without new computation; these concerns are narrowed/disclosed, not universally closed by writing. Stronger causal, predictive-generalization or SSD-performance conclusions remain **UNVERIFIED** and are omitted.

The layout instruction also requires retention of R031 limits. All existing methodological and verification caveats remain; this wording-only edit does not resolve R031 or any other review finding. R031's finding text was not separately retrieved for this edit, so no new interpretation or closure status is assigned here.

Author must verify before submission: **affiliation/city/country; funding or no-funding statement; conflicts; originality and prior-publication/submission status; applicable AI-use disclosure; any required author declarations; permission/terms for data and code redistribution; venue/session eligibility and final submission approval.** No declarations or acknowledgments have been invented. No unresolved bibliographic identity is used in the three references, but independent citation verification against the eventual final wording remains required.

## Reproduction supplement: existing commands, not executed

The following commands are transcribed verbatim from `docs/protocols/mean-overwrite-protocol.md:35–38`, not invented or run:

```text
.venv/bin/python -m read_prediction.experiments.mean_overwrite
.venv/bin/python -m read_prediction.checks.mean_overwrite
```

They reference existing saved inputs and write/read existing result paths; **do not rerun automatically or overwrite artifacts**. A future authorized reproduction needs inspected code, a suitable locked environment, lawful trace access, preserved input provenance and separately approved new output paths. Their presence is not a claim of successful fresh replication. Earlier fits and package execution were not performed by this writer.

## Handoff

- Draft: `.research/writing/conference-article-2026-10-07.md`.
- Reviewed pre-trim text, preserved **before editing**: `.research/writing/conference-article-layout-v1-2026-10-07.md`. This is the current reviewed text with the duplicate trailing paragraphs already removed and References unnumbered, not the historical synthetic draft.
- Claim/source ledger, citation-check record and pending fields: this file.
- No `.research/writing/draft.md`, evidence-map, protocol, literature, results or raw artifact was edited; no new findings/runs/searches/shell commands.
- Writing is complete for the bounded approved scope. Final text requires **human checkpoint and independent citation verification**. Exact word count and four-page fit should be checked by the authorized compositor; polished wording is not scientific validation.

## Layout tightening record

- Shortened repetitive Introduction, contextual method attribution, event/feature/window descriptions, reproducibility audit wording, Interpretation, Limitations, Future Work and Conclusion. No results or citations were added, removed or strengthened. Evidence remains C042–C052 with the same support index above.
- TABLE II caption now reads exactly: “TABLE II. MAE and lower bound on mean overwrite delay (seconds).” M_L and “Satisfied” remain defined in Results prose and the methods equation. TABLE III caption now reads exactly: “TABLE III. Pass bounds and paired-cohort control.” The paired-ratio definition remains in Results prose.
- All three tables and every numerical entry are unchanged, including coverage denominators, mean lower bounds, four pass ranges and paired ratios. Three mean successes, P-R's undetermined status, all four observed-Read 90% failures, all saved methods' pooled paired failures and mixture counterexamples remain explicit.
- Retained seven inputs (Read/Write counts and recencies are paired inputs), same-start history for range labels, NaN/log transforms, source-row ties, issue-time/ResponseTime distinction, partial intersection/version qualification, censoring equation/equality caution, unequal windows, clipped endpoint, frozen fits/updating history, all hyperparameters and mixture weights. Retained 3/6 selection candidates versus 5/8 evaluated methods, changed objectives, already-inspected development days, approximate duration, prefix-lookahead/history limits, dependence/no inferential CI, all-Write restriction and incomplete replication/integrity/runtime provenance. No measured SSD benefit is claimed.
