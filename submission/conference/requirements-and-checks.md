# IACGN 2026: requirements and final checks

## Current deliverables

**Current delivery after literature expansion:**
`Elmanov_IACGN_2026_expanded.docx` and `.pdf` (3 pages, six references), with
their `.md`, `.build.json`, and `.quality-check.json`. These supersede all
earlier delivery versions listed below. Source comparison confirms only
Related Work/References differ from the prior full-university-name article;
all empirical sections, tables, negative findings and conclusions unchanged.
All three actual expanded-page previews inspected by orchestrator; independent
review checked the six-reference layout before the final one-paragraph wording
correction. Final correction independently read and accepted as R033 resolved.
Final automated checks verify source/DOCX identity, references count, copied
table values, font/geometry and three-page PDF. No research runs performed.

Sources: canonical S006 (neural SSD prefetching), S007 (SGDP arXivv2), S031
(forward reuse distance arXivv1); C053–C055 support in current claim map.
Independent report: `.research/reviews/conference-related-work-citation-review-2026-10-07.md`.
Publication2021 versus conference2020 for S006 explicitly verified; no citation
uses unverified pages/year or imports prior-work performance. Two arXiv entries
explicitly distinguish their version/source status. Bounded discovery is not a
systematic or exhaustive novelty review. R031 residual gap still disclosed.

**Latest author-field revision:** full name supplied by user:
`Don State Technical University, Rostov-on-Don, Russia`. Use
`Elmanov_IACGN_2026_Don_State.docx` and `.pdf` (3 pages), with their
`.quality-check.json`. Source comparison confirms the affiliation is the only
text change from the `_DSTU` version. First-page layout checked after export.
The older `_DSTU` and `_final` records below are historical snapshots.

**Updated author affiliation:** user supplied `DSTU, Rostov-on-Don, Russia`.
Use `Elmanov_IACGN_2026_DSTU.docx` and `.pdf`, with their `.md`, `.build.json`
and `.quality-check.json`. Three pages retained; first page inspected after
re-export. Scientific text/tables unchanged. Earlier `_final` files listed
below are preserved snapshots containing the old placeholder.

**View the template:**
`submission/conference/c2feffd4-7038-4707-ac0c-180520464337.docx`.
Original local legacy Word file:
`/home/nomli/Downloads/c2feffd4-7038-4707-ac0c-180520464337.doc`.

- `Elmanov_IACGN_2026_final.docx` — editable working conference article.
- `Elmanov_IACGN_2026_final.pdf` — rendered three-page article.
- `Elmanov_IACGN_2026_final.md` — exact source-text copy.
- `Elmanov_IACGN_2026_final.build.json` — build/source/template hashes.
- `final-quality-check.json` — document-only automated checks (when completed).

Earlier `article` and `article_v2` documents/previews are layout iterations,
not the delivery copies. The first layout produced a short fourth-page tail;
editorial tightening eliminated it without removing the negative findings.
Three pages satisfies the actual CFP range of 3–6; no filler was added merely
to reach the initially suggested 4–5-page target.

## Requirements actually inspected

Source: user's `Call_for_Papers(3).docx`; its hyperlink targets
`c2feffd4-7038-4707-ac0c-180520464337.doc` on graduate.nuaa.edu.cn.
The matching local Downloads file was converted by installed LibreOffice;
its body identifies “Preparation of Papers for the Proceedings of the IACGN”.
No independent remote-to-local template checksum comparison was performed.

| Requirement | Implementation / check |
|---|---|
| English; 3–6 pages; Word and PDF | English draft; final pdfinfo reports 3 pages, both formats provided |
| Letter 8.5×11in; top .75in/bottom1in/left-right .625in | Explicit OOXML geometry; rendered 612×792pt |
| Title18pt; authors/affiliations12pt; Times allowed | Named template styles normalized to Times, Nimbus Roman in PDF |
| Body10pt, exactly12pt lines; .125in paragraph indent | Explicit OOXML body style |
| Two3.5in columns, .25in gap, except title/author block | Continuous section boundary, two-column body |
| Abstract9pt bold, exactly10pt; ≤100words recommended | 87words; Abstract label bold italic |
| 2–4alphabetical keywords | Censoring; Next-read prediction; Storage traces |
| Major Roman-numbered headings; refs unnumbered | SectionsI–VIII; References |
| References9pt,10pt line,hanging .25in | Explicit reference style; three primary citations |
| No headers/footers/page numbers | Clean document package has none |

Math is editable native Word equation with a numbered lower-bound formula.
Three compact tables are kept within single columns; final PNGs inspected
for clipping, row splits and readability. Equations/special symbols may use
embedded fallback fonts in PDF; body/headings use Times-compatible Nimbus Roman.
Changing affiliation or opening in another Word renderer may alter pagination;
re-export and check PDF after any edit.

## Scientific and source checking

The paper uses current `submission/` empirical results, not the old synthetic
draft. Traceability: `.research/claims/conference-evidence-map-2026-10-07.md`
C042–C052/S029 and `.research/writing/conference-open-issues-2026-10-07.md`.
Independent report: `.research/reviews/conference-manuscript-review-2026-10-07.md`.
Three reference identities and narrow contextual statements independently checked
on official abstract/metadata pages; full-paper reading/independent experiment
replication not claimed. Dataset schema/required attribution also checked in
local archive README §§3–4 after public endpoint timeouts.

Preserved limitations: already-used days5–7 (development), dependent records,
observed-Read-only MAE, censoring identification bounds not confidence intervals,
partial overlap not complete overwrite, issue-time not service latency, no
general ML superiority or measured SSD benefit. R031 full per-record pass-array
audit remains disclosed. R032 citation reauthentication resolved.

## Author actions before submission

1. Affiliation filled as requested: `DSTU, Rostov-on-Don, Russia`. Confirm it
   matches the venue's affiliation convention; no unsupported expansion added.
2. Confirm author order/eligibility, originality/nonpublication,
   nonconfidentiality and lawful use/release of materials. No raw traces included.
3. Check venue-required funding/conflicts/AI-use declarations; no statements invented.
4. Read and approve final scientific text; recheck Word/PDF after author edits.
5. Ask university academic mobility office for the application link/late-submission
   arrangements. CFP deadline is **2026-10-07 12:00 Beijing**; correspondence
   email is explicitly NOT a paper submission address. Nothing was submitted.

## Reproduce document assembly only

From project root, choose a NEW stem (existing outputs are never overwritten):

```bash
/usr/bin/python3 submission/conference/build_article.py --stem Elmanov_IACGN_2026_rebuild
libreoffice -env:UserInstallation=file:///tmp/opencode/iacgn-lo-profile --headless --convert-to pdf --outdir submission/conference submission/conference/Elmanov_IACGN_2026_rebuild.docx
pdfinfo submission/conference/Elmanov_IACGN_2026_rebuild.pdf
```

No dependencies installed or experimental code executed. Existing experiment
commands are documented separately in the writing ledger and must not be
rerun automatically or overwrite saved results.
