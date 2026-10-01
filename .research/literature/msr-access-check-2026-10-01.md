# MSR Cambridge Traces — official access check (single-volume gzip availability)

Status: BOUNDED PUBLIC-TEXT ACCESS CHECK, 2026-10-01. Retrieval only; no archive
bytes retrieved, no terms/cookies accepted, no shell/network client/code run.
Ownership: this is the only file written by this check. papers.jsonl,
search-log.md, README, protocol, claims/evidence-map were NOT modified. Proposed
S016 updates and C-ID entries are returned to the orchestrator below as text.

Purpose: determine from publicly listed official text whether an official
*separately downloadable single-volume* `*.csv.gz` exists (with exact listed
URL/name/volume and any publicly stated size), or whether only a bulk archive is
offered. This does not evaluate dataset suitability, read mix or predictability.

## Retrieval trail (exact attempts, 2026-10-01)

All fetches used the `webfetch` tool against official `iotta.snia.org` text/HTML.
Budget: 3 of 3 webfetches used; optional 1 generic websearch NOT used (primary
evidence was decisive and the task barred unbounded mirror search).

1. FETCH OK, markdown — https://iotta.snia.org/traces/block-io/388
   Locators: heading "MSR Cambridge Traces"; the results table with columns
   "Trace Name | Details | ... | Year Recorded | Timespan | Record Count |
   File Size | Actions"; the two row action lists; the note "cookies must be
   enabled within your browser in order to download traces".
   Observed: exactly 2 items (MSR Cambridge Traces 1, MSR Cambridge Traces 2).
   Per-item actions are trace-level, NOT file-level: Download Readme, Download
   Sample, Download via HTTPS, Download via Unix shell script, Download via
   Windows batch script, SHA-1 Checksum, Download Bibtex Citation.
   Displayed File Size column: Traces 1 = 3.06 GB; Traces 2 = 1.88 GB.
   No per-volume file list, no individual `*.csv.gz` names, no per-file URLs,
   no per-file sizes are present on this landing page.

2. FETCH OK, markdown — https://iotta.snia.org/traces/block-io/386
   (trace detail page, reached from the landing-page item).
   Locator: results region under the same table headers.
   Observed: "No items found for this query." No member/file listing, no sizes.

3. FETCH OK, text — https://iotta.snia.org/traces/block-io/386/download?type=checksum
   Locator: entire response body (one line, verbatim):
   `28ef578dcafa98b94ba9d9fd1205e7eec58f43d8  msr-cambridge1.tar`
   Observed: the Traces 1 downloadable artifact is a SINGLE bulk `.tar` named
   `msr-cambridge1.tar`; no size is shown at this endpoint. The archive is not
   itself gzip and is not a single-volume file.

No fetch failed. No terms/cookie gate was encountered on these three pages; the
"Download" action targets were not followed, because they would serve archive
bytes (forbidden).

## Answer to the objective

FACT (public listing, inspected): The official MSR Cambridge Traces listing
exposes only trace-level bulk download actions. A publicly listed, separately
downloadable single-volume `*.csv.gz` — with its own URL, filename/volume and
size — was NOT found on the pages inspected. Traces 1's official bulk artifact is
a single `.tar` (`msr-cambridge1.tar`, SHA-1 `28ef...f43d8`).

INFERENCE (from prior documented README + this checksum, not a byte inspection):
README §2 (retrieved 2026-09-30, recorded in
`.research/literature/public-data-options.md` "Exact read-field support") states
files are `<hostname>_<disknumber>.csv.gz` and that there are 36 traces from 36
volumes. Combined with the single-`.tar` checksum, the single-volume gz files are
most plausibly *members inside the bulk tar*, not separate official downloads.
This is an inference; it is not verified by opening the archive.

UNKNOWN (gaps):
- Traces 2 bulk archive filename/SHA-1 (endpoint not fetched; budget). Expected
  nomenclature must not be asserted.
- Any per-member manifest (member names, per-member sizes, whether members are
  `.csv.gz` in the tar) — not publicly listed here.
- Whether an authenticated/license-gated page (after accepting terms/cookies)
  exposes per-file URLs or a file table — not checked, by explicit constraint.
- Any actual bytes, decompressed content, archive size on the wire, or checksum
  verification — not checked.

## Public metadata vs not-checked (required separation)

Publicly displayed metadata (observed): trace names; years (2007); timespans
(7/8 days); record counts (271M / 163M); File Size column (3.06 GB / 1.88 GB);
the set of trace-level download actions; SHA-1 of `msr-cambridge1.tar`.

NOT checked / NOT verified: archive bytes; that the `.tar` exists at a stable
URL with a stable size today; gzip membership or member names; any per-file
size; the SHA-1's applicability to any current download beyond the text
returned; licensing acceptance (agent did not accept SNIA terms); integrity.

## Constraint and STOP

Per protocol `temperature-poc-v0.1.md` §3: the blocking unknown was the exact
official single `*.csv.gz` URL / filename / single (Hostname,DiskNumber). Public
text does not provide a separately downloadable single-volume gzip. Under §3's
stated rule ("If official single gzip absent and all-traces/multi-GB archive is
proposed — STOP before a new decision; do not download the whole archive for a
member"), this access check STOPS without any download.

## Decision alternative (one, for the human)

Recommended: **a separate, explicit expanded-access plan** — authorize (a) human
acceptance of SNIA Trace Data Files Download License v2.0, then (b) download the
bulk `msr-cambridge1.tar` and extract exactly one pre-selected member under a new
written budget/cap, preserving the §3 selection-before-contents rule and
recording member provenance/hashes. This keeps the official source and the
protocol's anti-selection rules, and requires a new approval because it changes
the access granularity the protocol assumed.
(If that is undesirable, the remaining branch is: the user supplies a legal,
separately available read-containing trace as the input, and S016 is not used.)

No mirror, third-party rehost, or unofficial per-file endpoint was searched and
none should be assumed.

## Proposed records for the orchestrator (NOT written)

Proposed S016 metadata update (keep existing record; do not overwrite history):
- `url`: unchanged `https://iotta.snia.org/traces/block-io/388`
- `version`: add — "Traces 1 bulk archive filename `msr-cambridge1.tar`,
  SHA-1 28ef578dcafa98b94ba9d9fd1205e7eec58f43d8 (bulk, not per-volume);
  Traces 2 archive name/checksum UNKNOWN; no separately listed single-volume
  `.csv.gz`"
- `retrieved_at`: `2026-10-01`
- `access`: `metadata + documentation (public text/HTML only)`
- `metadata_status`: add — "official listing inspected 2026-10-01: trace-level
  bulk download only; checksum endpoint shows single .tar; per-member manifest
  and bytes NOT inspected"
- NEW `data_access`: `none`; NEW `documentation_access`: `landing page, trace
  detail page, checksum text`

Proposed C-ID evidence entries (orchestrator assigns numbers):
- C-XXXa: "SNIA IOTTA officially lists MSR Cambridge Traces only with trace-level
  bulk download actions; no separately downloadable single-volume .csv.gz with
  its own URL/name/size is publicly listed on the inspected pages."
  support: S016 + URLs above + locators (landing table; detail "No items found";
  checksum body). verification: direct public-text inspection 2026-10-01.
  confidence: high for inspected pages; caveat: license-gated/member manifests
  and Traces 2 checksum not inspected.
- C-XXXb: "The Traces 1 official downloadable artifact is a single tar
  `msr-cambridge1.tar` (SHA-1 28ef...f43d8); no public size shown."
  support: checksum endpoint text. verification: public text 2026-10-01;
  metadata only, no byte/download verification.

Proposed search-log entry: 1 line recording the 3 webfetches above, budget used
3/3 fetches + 0/1 search, no failures, STOP per §3.

## Coverage limits

- Only 3 official pages inspected; not a survey; not exhaustive.
- License-gated pages, per-member manifests, Traces 2 checksum and actual bytes
  were not examined; "not found publicly listed" does not mean "does not exist."
- Prestigious/official host status is not evidence of suitability; no claim about
  read content, size, page size or predictability is made or implied here.
