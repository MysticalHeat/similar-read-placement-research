# Independent post-writing review: conference manuscript

Дата: 2026-10-07. Объект: `.research/writing/conference-article-2026-10-07.md`, 144 строки, после удаления duplicate tail paragraphs и ненумерованного References. Не submission endorsement.

## Scope и access
- 10 native reads/searches и 3 webfetch attempts с timeout30s; shell/import/compute/rerun/raw modifications/search web — 0. Единственная предполагаемая запись — этот review.
- Полностью прочитаны manuscript, conference-open-issues, CURRENT conference-evidence-map C042–C052, saved submission review, conference-methods-static-audit и conference-sources note. Два glob ничего не вернули; native directory read обнаружил open-issues. Поиск R031–R039 в `.research/*.md` не нашёл занятых IDs.
- Числа сопоставлены с текущим ledger и первичными metrics/export, самостоятельно прочитанными в предшествующем аудите этого же дня (review L21–27). В этом post-writing проходе metrics/export повторно не открывались: отсутствие изменений байтов не переаутентифицировано. Полные raw joins, hashes, parent pass arrays и code execution не проверены.
- Exact methods проверены на соответствие current static-audit/protocol/config support, НЕ новым прямым чтением production code. Local tar README первичный текст записан в CURRENT claimmap L23–33; это снимает прежний schema blocker на уровне поддерживающей записи. Сам tar member reviewer здесь не открывал. Не переносить старый remote-outage статус из source note на текущую schema.
- Author/email/student status и affiliation placeholder соответствуют supplied/approved данным. CFP English3–6pages/Times/two columns принят из запроса; DOCX/PDF, actual page count/font/columns здесь отсутствуют и не проверены. Все внешние запросы — только публичные URLs; unpublished content не отправлялся.

## Summary и readiness
Рукопись не усиливает C042–C052 до general learned-model superiority, novelty, leakage freedom или SSD benefit. Разные cohorts, dependent records, development reuse, partial overlap, unequal horizons и negative findings раскрыты. Нового установленного major scientific defect нет; это НЕ установление validity.
**READY FOR AUTHOR REVIEW WITH DISCLOSED LIMITATIONS.** Обязательной правки чисел/научного вывода по прочитанному тексту не выявлено. Независимая свежая проверка reference[3] осталась незавершённой; R031/R032 ниже — questions/evidence gates, не обнаруженные ошибки эксперимента. Для submission отдельно нужны human declarations и rendered-format check.

## Methods/logic audit
- Manuscript L35/C051 сохраняет approximately7days и не выдаёт requested168h/EOF за exact duration; event counts23639742/11233411 соответствуют static-audit L80–92, source.json:9 pointers. Source bytes не проверены повторно.
- L37/C049 — support-based19.2h screening, boundary-row lookahead и отсутствие historical no-access certificate соответствуют static-audit L66–76; все36 range-screened не заявлены.
- L39–41/C042 — issue-to-issue, ResponseTime excluded, independently found next Read/Write, half-open overlap, data-version caveat и row ties согласуются со static-audit L16–41 и local README record claimmap L23–33. Runtime identity остаётся unknown.
- L45–53/C043–C044 — семь inputs/current-Write exclusion/NaN/same-start history даже для range;72h train/day4 validation/24h future windows;3/6 selection versus5/8 evaluated; median и .25/.75 mixtures;150trees/31leaves/.05/minchild50/lambda1/seed42/2threads согласуются со static-audit L47–60,97–103 и ранее прочитанными models/protocols. Mixture arithmetic не была прямо проверена этим reviewer.
- L57–63: denominator C одинаков у MAE и overwrite mean; known B плюс censored remaining L даёт lower bound. MAE<M_L достаточно; MAE≥M_L при неизвестном upper mean не доказывает failure. Pooling records, не average daily means. Математика корректна при заявленных lower-bound semantics; конечность реального будущего overwrite interval не установлена.
- L65: strict known equality failure; e<L confirmed, unresolved contributions дают q/N…(q+r)/N. Conservative treatment e=L логически допустим, но связь с конкретным export/checker equality implementation не проверена (R031). Bounds не CI; upper<.90 исключает порог только в C.

## Numerical table audit
Ключи: P-S/P-R proj_1 same_start/range; N-S/N-R prn_1 same_start/range.
| Key | Table I: N/all Write; coverage | Table II: MAE / M_L seconds; status | Table III: pass bounds; paired N; ratio |
|---|---|---|---|
| P-S |211844/1022738;20.71%|18162.30/18974.56;Satisfied|51.35–52.72%;188375;1.3939|
| P-R |236034/1022738;23.08%|17146.95/16275.23;Undetermined|45.79–47.17%;212376;1.6227|
| N-S |633316/1299820;48.72%|13715.20/19184.55;Satisfied|50.03–50.36%;522581;1.3581|
| N-R |684054/1299820;52.63%|13741.74/16475.83;Satisfied|46.19–46.51%;591037;1.4644|
- Manuscript locators: TableI L75–84; TableII L86–95; TableIII L97–106. Rounding/copying agrees with prior independently inspected saved fields, no arithmetic rerun claimed.
- Mean/count/paired support S029: `results/mean-overwrite/metrics.json` `$.{workload}.{rule}.windows.pooled`, `methods.{selected}.{observed_read,paired}`; P-S L394–455; P-R L884–945; N-S L1568–1580/1695–1709; N-R L2298–2310/2425–2439. Ratios correspond to recorded1.3939040719/1.6226549393/1.3580924127/1.4643639615.
- Pass support S029: `submission/overwrite-results.json` selected_results window=pooled L123–149,268–294,413–439,558–584. Export-level support only; no independent parent-array check. Manuscript L124 acknowledges this distinction.
- Daily prn mean successes L95 supported by prior metrics selected day5–7 blocks; all saved compared paired failures L106 supported by pooled methods.*.paired.passed=false. They are descriptive, not significance/generalization claims.
- Counterexamples L108 match S029 export pooled_candidates: raw_l1 N-S13545.950922374297 (L917), median N-R13606.783035254508 (L1178), versus selected13715.195621932955/13741.737575063507. No retrospective reselection.
- Abstract L11 range45.79–52.72% is the envelope of selected bounds, not pooled across workloads; three mean successes/four selected paired failures match TablesII/III. Conclusion L136 is cohort-contextualized and does not import synthetic scores.

## Independent citation audit (retrieved2026-10-07)
### [1] S027 (+ local attribution S016)
- URL: https://www.usenix.org/conference/fast-08/write-loading-practical-power-management-enterprise-storage
- SUCCESS: official landing abstract/bylines/BibTeX read; title, Narayanan/Donnelly/Rowstron, FAST08/year2008 match manuscript L140. No pages/DOI invented.
- Exact abstract support for L25: “block-level traces from36 volumes ... for one week”; spinning disks/power management context. **DIRECT** for paper context, abstract-level only, not full text.
- Dataset attribution sentence L25 separately supported by local README §4 recorded in claimmap L27–33; web abstract alone does not establish archive identity. No archive reauthentication claimed.
### [2] S009
- URL: https://www.usenix.org/conference/fast22/presentation/wang
- SUCCESS: official abstract/byline/BibTeX read. All6authors/title/FAST22/year2022/pages429–444 match manuscript L142. No DOI asserted.
- Exact support for L27: abstract says SepBIT “infer[s] the BITs of written blocks” and places groups with “similar estimated BITs” for reducing WA. **DIRECT** narrow mechanism/context support; differentiation from this study is bounded comparison, not borrowed performance evidence.
- Access depth: official abstract/metadata only; official PDF not read, previous arXiv§2.3 not reauthenticated or needed for current sentence.
### [3] S028
- Exact official URL from note: https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html
- Reviewer inadvertently requested `https://www.proceedings.neurips.cc/...` instead; Transport error. This is a reviewer URL transcription failure, NOT established outage of the exact official URL. Third fetch allowance spent; no retry/search.
- Manuscript L29/L144 metadata and generic GBDT sentence match saved source note L44,61–65 and writer ledger L41; **SAVED ABSTRACT-LEVEL SUPPORT, FRESH INDEPENDENT REAUTHENTICATION INCOMPLETE**. No fresh text/metadata retrieved by this reviewer, no full-paper reading.
- Manuscript appropriately supports actual hyperparameters by local artifacts, not[3], and imports no LightGBM speedup figure.

## Numbered concerns
### R031 — question / useful evidence improvement: equality-case linkage not independently audited
- Location: manuscript L65 and TableIII L101–104; open-issues L25,55; C046.
- Observation/criterion: conservative formula is valid, but export q/r counts and underlying handling e=L, clipped final boundary and zero intervals have not been matched to a checker branch/fixture. No observed numeric discrepancy or defective bound established.
- Consequence: a claim of independently verified exact per-record bound implementation would exceed this audit. Existing L124 correctly discloses parent-pass audit gap.
- Requested action: retain limitation; if stronger verification is wanted, orchestrator obtains existing checker code/equality fixture pointers and static consistency check before considering separately authorized reanalysis. No new run required merely for author review.
- Confidence: high in stated access gap, implementation behavior UNKNOWN. Status: OPEN, nonblocking for bounded descriptive author review.
### R032 — question / citation-verification follow-up: reference[3] fresh authentication incomplete
- Location: manuscript L29,L144; citation audit above; S028/C052.
- Observation/evidence: reviewer used wrong `www.` hostname; no primary response retrieved. Saved verification exists, but is not this reviewer's fresh independent check.
- Consequence: cannot describe this pass as independently reauthenticating all3references. Not evidence the source/reference is false or unsupported.
- Requested action: orchestrator commissions one separately permitted fetch of the exact bare-host URL, checks all8authors/year/venue and narrow GBDT sentence. Do not alter bibliography by conjecture or blame an untested official endpoint outage.
- Confidence: high in failed retrieval; saved source support positive but not freshly authenticated. Status: OPEN; no current manuscript correction established.

## Previous concerns, counterargument and residual risks
- R026 wording addressed for this manuscript by issue-to-issue and recovered local schema support; not full runtime closure. R027 dependence and R028 coverage/90% wording addressed at L84,106,120. R029 development/changed selection disclosed L49–53,124; R030 approximate duration/lookahead/no historical certificate disclosed L35–37,124. Old submission README remains outside writer ownership and inconsistent in places.
- Strongest rival explanation remains overwrite tails/cohort selection plus repeated target events, rather than general useful prediction. L108,112–124 preserve counterevidence and avoid causal resolution; manuscript does not need new experiments to report this contrast.
- A resolving stronger study would freeze endpoint/recipe/criteria on untouched data and assess dependency-aware/stratified record-versus-event contrasts. Any recomputation/new run requires orchestrator/user approval; no repository commands executed here.
- Remaining risks: code-to-artifact identity, complete boundary handling, mixture execution, screening chronology, raw hashes/joins, model/data licenses, hardware/runtime environment, all-Write outcomes/generalization. Citation metadata is not claim verification; primary abstracts support only narrow current context. No comprehensive novelty search, inferential tests or SSD outcome evidence.
- Required before submission, not scientific defects of the draft: affiliation/city/country, declarations/AI policy/funding/conflicts/rights, author approval, Word+PDF Times two-column3–6-page rendering and final-reference check. Markdown does not establish layout compliance.
- Handoff: author-review ready with R031 residual and R032 verification follow-up. No required scientific prose/table fixes identified within inspected scope; no submission endorsement. No other file/state/claimmap/manuscript edited. Earlier reviews retained.

## R032 follow-up — independent resolution, 2026-10-07
- Orchestrator extended verification budget by exactly one additional webfetch, timeout30s, to the exact official bare-host URL; no other retrieval/search/execution. URL: https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html . Result: SUCCESS; official landing metadata and complete visible abstract independently read by this reviewer.
- Title matches manuscript reference[3]: “LightGBM: A Highly Efficient Gradient Boosting Decision Tree”. Byline contains all8authors in matching order: Guolin Ke; Qi Meng; Thomas Finley; Taifeng Wang; Wei Chen; Weidong Ma; Qiwei Ye; Tie-Yan Liu. Venue/year visible: “Advances in Neural Information Processing Systems 30 (NIPS 2017)”. Reference[3] initials/title/year/venue agree.
- Exact support locator: Abstract, sentence “We call our new GBDT implementation with GOSS and EFB \\emph{LightGBM}.” This directly supports manuscript L29's narrow GBDT-implementation identity claim (C052/S028); it does not verify this study's hyperparameters, package execution, accuracy or training speed.
- Access depth: official abstract plus landing metadata, not full paper. BibTeX/Metadata/Paper links were visible but not fetched; no DOI/pages inferred. No additional performance claim imported.
- **R032 status: RESOLVED for fresh independent reference[3] identity and exact narrow-sentence support.** Earlier wrong-www Transport error and the initial incomplete verdict above are retained as historical provenance, not deleted or reattributed to an official-host outage. All3references now have independently inspected official abstract/metadata support for their narrow contextual sentences; local dataset attribution still rests on the separately recorded README recovery.
- Current handoff supersedes only the R032 follow-up requirement: READY FOR AUTHOR REVIEW WITH DISCLOSED LIMITATIONS; R031 and other stated residual risks unchanged. No manuscript/claimmap edits, numerical reanalysis, new experiments or submission endorsement.

## Final editorial/layout follow-up — 2026-10-07
- Scope: exactly5native reads: current manuscript142lines, `submission/conference/final-preview-{1,2,3}.png`, and `submission/conference/final-rendered.txt`174lines. No web/shell/compute; no document/result edits except this append. Earlier v1 review and failed-fetch provenance retained. Pre-edit `conference-article-layout-v1-2026-10-07.md` not newly opened; comparison uses the earlier144-line manuscript independently read in this review, not a new bytewise diff of archived versions.
- Current text versus earlier reviewed content: no strengthened scientific claim or consequential caveat loss identified. Issue-to-issue/partial overlap/row ties, same-start histories, unequal horizons, changed3/6candidate selection versus5/8comparisons, already-inspected development days, cohort-specific90%failures, P-R undetermined, dependence, non-replication, historical-access/leakage gaps and no measured SSD benefit remain explicit (current L33–67,82–106,118–134). Shortened reproducibility paragraph is qualified further at L122; it does not certify independent replication.
- All12table data rows and their numeric fields in current text and visible render agree with the earlier reviewed table values/rounding. No new metric calculation, raw-array check, fingerprint verification or rehash; artifact integrity limits unchanged.
- Visual page2 right column: TableI and TableII each have readable headers and all4rows, with captions and explanatory text; neither table splits across columns/pages. Visual page3 left column: TableIII likewise shows all4rows intact with readable percent ranges, paired counts and ratios. No table clipping, text/table overlap or lost row identified at the supplied preview resolution. Equation(1), strict inequalities and bound explanation remain legible on page2; pass paragraph continuation across columns is present, not missing.
- Visual page3 right column: References[1],[2],[3] all present, readable and complete in the displayed page; author/title/year/venue/page fields remain consistent with the independently authenticated narrow citations. References heading is unnumbered; no duplicate tail section observed. R032 remains RESOLVED; no new source retrieval.
- Rendered text corroborates TablesI/II L78–109, TableIII L117–137, qualifications L159–173 and all3references L151–163. Side-by-side column interleaving in text extraction is not a layout defect; PNGs supply spatial evidence.
- Three supplied page images visibly show a two-column body and the final references on page3. User-reported pdfinfo3pages,2046words and Times10/exact12 metadata were NOT independently read/recomputed. Final `.docx`/`.pdf` bytes, page count, font family/size, line spacing and Word geometry were not inspected; PNG appearance cannot certify these or establish identity between previews and final binaries. Three-preview layout is consistent with the stated3–6page range, not an independent PDF-metadata certificate.
- **Required fixes from this bounded follow-up: none identified.** Approved affiliation placeholder remains visible on page1 and still requires human completion before submission, not removal merely for author review. R031 parent-array/equality-case gap and the existing scientific/provenance/declaration limitations remain unchanged. No new R-ID warranted by an observed defect.
- **Narrow readiness: current text and supplied three-page visual render are ready for author review.** This is not submission endorsement, full layout/Wordfont compliance certification, fresh numerical validation or a guarantee that the final binaries reproduce these previews. Reviewer owns only this appended review; no additional tools or runs.
