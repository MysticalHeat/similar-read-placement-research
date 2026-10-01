# Public block-I/O data options (bounded discovery)

Status: BOUNDED FEASIBILITY SNAPSHOT, 2026-09-30. FAST discovery, not a survey or
novelty check. One credible candidate found and its primary documentation
inspected. No data downloaded, no shell, no decompression. Local files were NOT
used to identify provenance; filenames are not provenance.

Scope: find ONE primary public block-I/O dataset source documented to include
reads with operation/address/size and ideally time, as a public fallback while
the local op mix (S014/S015) is unconfirmed. This file is the only artifact
written; papers.jsonl / search-log.md / README were not modified. S016 below is
a proposed record for the orchestrator to integrate.

## Chosen candidate (proposed S016)

| Field | Value |
|---|---|
| id | S016 (proposed) |
| title | MSR Cambridge Traces |
| authors | null — dataset; attribution in readme §4 is the FAST 2008 paper (Narayanan, Donnelly, Rowstron). Trace contributors not listed as a dataset byline. |
| year | 2007 (year recorded, per IOTTA landing page) |
| doi | null |
| arxiv_id | null |
| url | https://iotta.snia.org/traces/block-io/388 |
| version | MSR Cambridge Traces 1 (IOTTA trace 386) + Traces 2 (IOTTA trace 387); recorded 2007; archive byte-version/checksum UNKNOWN |
| retrieved_at | 2026-09-30 |
| access | metadata + dataset documentation (landing page, readme full text, license page); NO trace data downloaded |
| metadata_status | primary host inspected (SNIA IOTTA official repository); readme text read in full; does not verify archive contents or actual sample rows |
| note_path | .research/literature/public-data-options.md (this file) |
| source_type | public-dataset |
| license | SNIA Trace Data Files Download License v2.0 |

Proposed JSONL line (do not duplicate if orchestrator assigns a different S-ID):

```
{"id":"S016","title":"MSR Cambridge Traces","authors":null,"year":2007,"doi":null,"arxiv_id":null,"url":"https://iotta.snia.org/traces/block-io/388","version":"IOTTA trace ids 386 (Traces 1) and 387 (Traces 2); recorded 2007; archive checksum UNKNOWN","retrieved_at":"2026-09-30","access":"metadata","metadata_status":"verified on primary host (SNIA IOTTA official repository); readme full text and license page inspected; no trace downloaded","note_path":".research/literature/public-data-options.md","source_type":"public-dataset","license":"SNIA Trace Data Files Download License v2.0"}
```

## Is this primary documentation or a mirror?

- SNIA IOTTA (`iotta.snia.org`) is the repository that distributes and licenses the
  traces; the landing page and README are the dataset's own distribution
  documentation, not a third-party mirror.
- The underlying data originate at Microsoft Research Cambridge; the README points
  to the original FAST 2008 paper for more information (attribution, not the data
  host). The canonical citable paper is:
  "Write Off-Loading: Practical Power Management for Enterprise Storage",
  Dushyanth Narayanan, Austin Donnelly, Antony Rowstron, FAST '08,
  http://www.usenix.org/event/fast08/tech/narayanan.html (not fetched; only the
  URL as written in README §4 was visible).
- Version relationship to be preserved: two IOTTA trace records (386, 387) form
  the "MSR Cambridge Traces" set; do not collapse their record counts/sizes into
  one number without stating the sum.

## Exact read-field support (locator + faithful excerpt)

Source: README retrieved from
https://iotta.snia.org/traces/block-io/386/download?type=readme (text, 2026-09-30).

- README §3 "I/O trace file format" lists the CSV fields exactly as:
  `Timestamp,Hostname,DiskNumber,Type,Offset,Size,ResponseTime`
- Definitions (paraphrase, README §3):
  - `Type` is "Read" or "Write" → operation is present; reads explicitly supported.
  - `Offset` is "the starting offset of the I/O in bytes from the start of the
    logical disk" → address is present.
  - `Size` is "the transfer size of the I/O request in bytes" → size is present.
   - `Timestamp` is the issue time in Windows filetime; `ResponseTime` is
     the DURATION taken to complete in Windows filetime units, not an absolute
     completion timestamp. Orchestrator independently checked README §3 on
     2026-09-30 and corrected this shorthand → time is present (issue + response duration).
- README §2: "36 I/O traces from 36 different volumes on 13 servers"; files are
  `<hostname>_<disknumber>.csv.gz`; disk 0 is generally the boot disk.
- README §4 attribution as above.

Conclusion for the request: this dataset is documented to contain read events with
operation, byte address, transfer size, and time. That is direct documentation
support, from the primary distributing host.

## Size / counts directly visible (do not extrapolate)

From the IOTTA landing page
(https://iotta.snia.org/traces/block-io/388, retrieved 2026-09-30):
- MSR Cambridge Traces 1 (trace 386): 271 Million records; 3.06 GB; 7 days.
- MSR Cambridge Traces 2 (trace 387): 163 Million records; 1.88 GB; 8 days.
- Combined row on `/traces/block-io`: 434 Million records; 4.94 GB; 8 days.
These are displayed metadata, not checksummed/measured archive sizes.

## Access and license caveats

- License page: https://iotta.snia.org/repository/download_license (retrieved
  2026-09-30) shows "SNIA Trace Data Files Download License", Version 2.0,
  Copyright (c) 2008 SNIA. For non-OSI materials the text grants use, copy,
  modify, merge, publish, distribute, sublicense and sell, provided the notice
  and disclaimers are included; provided "AS IS" with no warranty. Download
  requires accepting the terms (cookies enabled).
- I did NOT download or accept the license; I did NOT obtain the files, so
  acceptance and archive access are unverified.
- Files are gzipped CSV (`*.csv.gz`) and require decompression; not performed.
- No SHA-1/MD5 checked; the archive as served today is not byte-fixed here.
- `Offset` is in bytes with no page-size stated in the README → logical page
  granularity for a "page" target is UNKNOWN.
- Timestamps are Windows filetime; epoch/timezone conversion is a downstream
  task, not verified here.
- Record mix (actual read fraction per trace) was not measured, because no data
  was downloaded. Schema-only, both Read and Write labels are documented.
- Workloads are 2007 enterprise servers; fit to the user's SSD/FTL question and
  to the local dataset is a separate determination, not established here.

## Relationship to local files — explicit non-inference

Filename `hm_0.csv` / `prxy_0.csv` is NOT treated as evidence of origin, format,
schema or source. The MSR Cambridge candidate is offered only as an independent
public option, not as an identified provenance for the local samples. No local
raw addresses were submitted to any web service; searches used generic terms.

## Reproducible search log (this discovery only)

No failures. Dates are 2026-09-30.

1. websearch (Exa), type auto, numResults 8:
   `MSR Cambridge block I/O traces SNIA IOTTA repository read LBA size timestamp`
   → identified iotta.snia.org/traces/block-io/388 and block-io list.
2. webfetch markdown: https://iotta.snia.org/traces/block-io/388
   → landing page: title, year, record counts, sizes, license name, readme/sample
   links (386/387).
3. webfetch text: https://iotta.snia.org/traces/block-io/386/download?type=readme
   → README full text: file format fields, read/write semantics, 36 traces,
   FAST 2008 attribution.
4. webfetch markdown: https://iotta.snia.org/repository/download_license
   → SNIA Trace Data Files Download License v2.0 terms.

Budget used: 1 of 2 websearches, 3 of 3 webfetches. Bounded discovery stopped at a
credible candidate as instructed.

## Bounded recommendation

- Recommend S016 (MSR Cambridge Traces via SNIA IOTTA) as the single public
  fallback candidate: its own primary documentation specifies Read/Write type,
  byte Offset, byte Size, and Timestamp/ResponseTime, under a permissive SNIA
  license.
- Do not treat this as validation that the local dataset has reads, nor as
  evidence that next-read prediction is achievable, nor that any simulator's
  timing is suitable. Metadata/documentation presence is not download or claim
  verification.
- If a data sample is later authorized, the concrete next check (outside this
  budget) is to open one `*.csv.gz` sample and confirm actual Read rows and page
  size; licensing acceptance would be required first.
- Alternative public block-I/O sources that appeared but were NOT inspected
  (Microsoft Production Server Traces, and others on /traces/block-io) remain
  unassessed; if enterprise-2007 read mix is unsuitable, a fresh bounded search
  should target those.

## Coverage limits

- One dataset inspected; not a survey, not exhaustive.
- Landing page and README are metadata/documentation, not archive verification.
- No alternative dataset compared; no novelty or predictability claim made.
- Exact archive version/date/checksum and original sample rows remain UNKNOWN.
