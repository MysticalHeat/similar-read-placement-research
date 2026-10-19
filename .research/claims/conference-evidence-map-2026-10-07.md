# Conference claim map (current empirical submission)

2026-10-07. Historical synthetic IDs remain unchanged; no new experimental
run is created by document preparation. S029 denotes existing saved empirical
artifacts, NOT a fabricated execution ID. Exact source paths below relative to
project root. Review: reviews/submission-conference-evidence-review-2026-10-07.md.
User approved this bounded content/interpretation and affiliation placeholder.

| C-ID | Bounded claim | Evidence and exact support | Status / confidence / caveat |
|---|---|---|---|
| C042 | Labels are next-Read issue timestamp minus Write issue timestamp, in seconds; ResponseTime excluded. Same-start equal Offset, range any byte intersection; intervening Writes do not cancel address Read target. | S016 local MSR-Cambridge/README.txt §§3–4; S029 read_prediction/pipeline.py:68–82,92–132; range_label.py:165–198; methods-static-audit §§14–41 | Direct static implementation and primary README. High in definitions; not physical latency or consumption of same data version |
| C043 | Seven earlier-row same-start history inputs, missing history NaN; current Write excluded; source-row ties. | S029 submission/models.json:2–14; pipeline.py:95–116; methods-static-audit §§43–60 | Direct static support, high in inspected path; even range labels use same-start features, not strict timestamp precedence/universal leakage freedom |
| C044 | Final package uses train days1–3, day4 min observed-Read MAE choice; proj_1 address median, prn_1 .25logL2+.75rawL1 in seconds; 150trees/31leaves/lr.05/minchild50/lambda1/seed42/2threads, no early stopping. | S029 submission/models.json:15–47; protocols/mean-overwrite:7–12, long-history:22–33, mixture:7–8; static audit:95–103 | Direct protocol/config/code support, high in recorded recipe; not proof of bitwise reproducibility or fresh holdout |
| C045 | Three of four pooled observed-Read comparisons satisfy MAE<mean overwrite via lower bound; proj_1/range undetermined. | S029 submission/overwrite-results.json selected_results filter window=pooled observed_read; results/mean-overwrite/metrics.json $.{workload}.{rule}.windows.pooled.methods.{selected}.observed_read; reports/mean-overwrite:48,53,58,63 | Direct stored metrics and independent consistency review; high in reported finite results, no recomputed joins. Exact values in reviewer table |
| C046 | Selected-method pass bounds on observed-Read cohort: proj same_start51.35–52.72%, range45.79–47.17%; prn same_start50.03–50.36%, range46.19–46.51%; all upper bounds<90%. | S029 overwrite-results.json pooled pass_lower/pass_upper/ninety_percent_status; README main table | Direct export-level support; high in copied values, parent raw pass arrays not audited. Censoring identification bounds, NOT confidence intervals; no all-Write claim |
| C047 | Paired Read+known overwrite subset gives MAE above exact mean overwrite for all selected methods (and all saved compared methods). | S029 reports/mean-overwrite:11–36; primary metrics pooled methods.*.paired, paired_n. Selected table in submission/README:29–34 | Direct stored metrics, high consistency; different cohort from C045, no contradiction or generalization |
| C048 | Days5–7 pooled coverage: proj same_start211844/1022738=20.71%, range236034/1022738=23.08%; prn same_start633316/1299820=48.72%, range684054/1299820=52.63%. | S029 submission/README:91–96; overwrite-results pooled observed_reads/all_writes; primary metrics pooled | Direct reported denominators/coverage; dependent Writes, not IID replicates; MAE undefined for censored Read records |
| C049 | Same-start screen records36traces/eight eligible (two earlier controls,six new), range confirmation of six new; inspected code ranks support on initial19.2h, not future errors. | S029 dataset-comparison.json traces/eligible_new_workloads/range_confirmation/selected; docs/protocols/data-sufficiency:9–15,42–44; static-audit:62–76 | Direct export/static support; historical access chronology not certified, one excluded-row lookahead; not all36 range-screened |
| C050 | Days5–7 already inspected: development/exploratory evaluation, not independent confirmatory holdout; records/pages/days dependent. No SSD speedup measured. | S029 protocols/long-history:3–4, mean-overwrite:26–28; reviewer R027/R029; scope of submission metrics only | Direct disclosure/design interpretation; high in documented limits. No novel/general superiority claim |
| C051 | Source metadata records approximately7days, EOF; proj23639742 events and prn11233411; requested168h not exact coverage certificate. | S029 results/new-workloads/{proj_1,prn_1}/source.json:8–19; methods-static-audit:78–93; S027 abstract one-week enterprise block traces | Direct metadata/coarse interpretation; no rehash/raw recount, not measured SSD workloads |
| C052 | Related-work context: SepBIT infers block-invalidation times to group data for WA reduction; LightGBM is GBDT implementation. | S009 official FAST22 abstract and verified2026-10-07 metadata; S028 official NIPS2017 abstract; literature/conference-sources §§55–71 | Abstract-level direct context; not evidence for present predictor performance, no comprehensive novelty survey |
| C053 | Chakraborttii and Litz propose neural-network-based prediction of future block accesses for SSD prefetching, addressing sparse address spaces and predicting sufficiently ahead for timely prefetching. | S006 canonical previously reserved lead; NSF PAR10187652 abstract at https://par.nsf.gov/biblio/10187652-learning-access-patterns-improve-prefetching-ssds independently fetched2026-10-07: “Prefetching predicts future block accesses ... preloads them into main memory ahead of time”; “neural network based prefetching approach”; “very large sparse address spaces ... timely manner by predicting ahead of time” | Direct abstract-level support, high for narrow purpose, no architecture/next-request-size claim from provider-extracted body and no reported performance numbers imported. Not a result of our predictor |
| C054 | SGDP models logical-block-address delta streams with a weighted directed graph and extracts features with graph neural networks for data prefetching. | S007 arXiv2304.03864v2 abstract, https://arxiv.org/abs/2304.03864 fetched2026-10-07: “models LBA delta streams using a weighted directed graph ... extracts hybrid features by graph neural networks for data prefetching” | Direct primary abstract support, high for stated task/mechanism. Cite arXivv2/2023, IJCNN acceptance reported not fresh publisher authentication. Address-stream prefetching, not present Write-conditioned elapsed-time/error-vs-overwrite result |
| C055 | Li and Gu's preprint predicts forward reuse distance with LSTM-based networks for cache replacement; its target uses access-count distance, not elapsed seconds. | S031 arXiv2007.15859v1 full HTML https://arxiv.org/html/2007.15859v1,2026-10-07: §I definition “number of accesses between two consecutive accesses to the same datum”; §III logical time increments1peraccess; §IV Multi-LSTM; §V pOPT uses current index+predicted forward distance; §VI-C MSR storage traces, TableII includes proj/prn trace families | Direct full-text section support, high in definition/context, no independent reproduction. Preprint not peer-reviewed venue. TableII aggregates server/volume families: do NOT assert identical proj_1/prn_1 files/splits/provenance. Context is prediction for cache replacement, not proof of present 90% reliability/SSD benefit |

## Primary local documentation recovery and citation check
Official S016 README web endpoint timed out in librarian's three attempts.
Orchestrator read the1815-byte README member in existing dataset/msr-cambridge1.tar
on2026-10-07, no extraction or trace modification. UTF8 decode first failed;
cp1252 decode succeeded. §2:36volumes/13servers and filenames; §3 explicitly
"Timestamp is the time the I/O was issued in Windows filetime", Offset/Size
bytes, ResponseTime time taken to complete; §4 requests citation to Narayanan,
Donnelly, Rowstron FAST08. This resolves schema/attribution support locally,
not remote checksum authentication or archive license certificate. The outage
does not invalidate the historical schema evidence; fresh local primary text
now independently inspected. Exact excerpt and access distinction retained.

Orchestrator independently re-fetched S027/S028 official landing pages on
2026-10-07, spot-checking all bylines/title/year and precise abstract support.
S009 official-source enrichment is librarian verification, to recheck against
the eventual manuscript; no official full-paper access claimed.

## Related-work expansion — 2026-10-07

Librarian note: literature/conference-related-work-expansion-2026-10-07.md;
4search attempts(1rate-limited),10fetch attempts with blocked publisher/PDF
routes. Bounded exploratory, not comprehensive/systematic. Orchestrator added
four exact-URL checks: Crossref S006, NSF abstract S006, arXiv S007, fullHTML S031.
Selected3additions (total6refs): S006/S007/S031. S008 refreshed but omitted to
prioritize storage rather than CPU memory. Zhou/Maas time-to-next-access lead
not promoted without readable supporting text; no absence/novelty claim follows.

ID deduplication: librarian proposed S030 for a source already reserved as S006.
Use canonical S006 and promote that lead, never duplicate as S030. S030 remains
unassigned proposal alias in historical note; S031 is new and distinct.

S006 metadata conflict resolved with publisher-deposited Crossref record:
https://api.crossref.org/works/10.1007%2F978-3-030-67667-4_26 . Retrieved2026-10-07.
Title/byline match NSF; page427–443, DOI10.1007/978-3-030-67667-4_26,
container “Machine Learning and Knowledge Discovery in Databases: Applied Data
Science Track”, conference assertions ECML PKDD/2020, published-online2021-02-25,
published-print2021. Bibliography publication year2021, conference2020 retained
in catalog. NSF repository lists2020-07-01/ICML-PKDD; do not silently choose that
abbreviation/date as publication venue/year. Crossref is metadata verification,
not source-claim verification; narrow C053 separately supported by NSF abstract.

Writer may expand only contextual C053–C055 and renumber existing references;
methods/tables/conclusions unchanged. Preserve no novelty or general superiority
claims and mark S031 as preprint. Independent exact support check follows.
