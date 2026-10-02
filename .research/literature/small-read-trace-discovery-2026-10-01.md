# Small public block-I/O trace: bounded discovery

2026-10-01. DOCUMENTATION/METADATA ONLY; candidate found, data-suitability gate NOT passed. Orchestrator integrates librarian return after write denial; exact support independently narrowed below. No trace/archive/sample bytes, license acceptance, shell, installs, preprocessing or training.

## Fixed objective and limits
Small real block-I/O trace with reads, documented time/address/size/namespace, lawful local use, separately available download≤100MiB and recording≥6h. Approved task definition remains logical4KiB; history/H/step600s; labels0/1–2/≥3. Limits and split not changed to match sources. Metadata size≠actual bytes, schema≠actual reads or predictive signal.
Discovery budget: librarian≤3queries/6fetches/3candidate families; actual2queries/4fetches. Orchestrator verification3public HTML fetches. Search not systematic/novelty search.

## Retrieval trail and failures
| Who | Tool / query or URL | Access / outcome |
|---|---|---|
| Librarian | Exa auto numResults8: `UMass Trace Repository disk traces block I/O offset size read write timestamp download` | Reports8leads inspected, not8papers read; UMass/IOTTA leads |
| Librarian | https://iotta.snia.org/traces/block-io | Public list and historical candidates |
| Librarian | https://traces.cs.umass.edu/docs/traces/storage/ | Five individual SPC file links and displayed sizes |
| Librarian | Exa auto numResults6: `SPC trace file format specification OLTP host disk type offset size timestamp sectors` | SPC PDF extraction appeared in search results; inspected count not reported, do not infer6 |
| Librarian | https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf , format=text | Retrieved raw PDF bytes; FAILED readable text extraction |
| Librarian | Same PDF, format=markdown | Same readable-text FAILURE; not full-text reading |
| Orchestrator | https://traces.cs.umass.edu/docs/traces/storage/ | Independently checked file names, URLs, sizes, courtesy attribution and footer |
| Orchestrator | https://iotta.snia.org/traces/block-io | Independently checked SPC rows: recorded1999, Timespan1day, external UMass link |
| Orchestrator | https://traces.cs.umass.edu/docs/about/ | FAQ directs content questions to source contacts; no SPC-specific use conditions located |

Librarian reports3denied file-write attempts; no permission bypass used. Orchestrator saves this narrowed note via authorized file editor. Claims based only on search extraction are NOT promoted to verified schema.

## Candidate screening (three families considered in detail)
| Candidate | Evidence actually available | Decision |
|---|---|---|
| UMass-distributed SPC OLTP / Search Engine | Individual listed files7.6–34MB; IOTTA collection metadata1day; separate format-doc link | Plausible small candidate S017, conditional only |
| Slacker | IOTTA metadata14minutes,3.37MB | Excluded: duration incompatible with6h protocol; no data examined |
| Nexus5 | IOTTA metadata25application traces, collection6months,31.2MB | Not selected: collection span does not establish continuous6h in one trace; no per-trace docs read |

Other entries visible in aggregate IOTTA listing not independently evaluated. No exhaustive absence claim. S017/S018 do not duplicate existing DOI/arXiv/title records; S018 is a documentation link subordinate to S017, not a second independent dataset.

## S017: primary distributor listing
Title actually visible: **Storage | UMass Trace Repository**.
URL: https://traces.cs.umass.edu/docs/traces/storage/
Locator: sections **OLTP Application I/O** and **Search Engine I/O**.
Page says traces are made available courtesy of Ken Bates(HP), Bruce McNutt(IBM), Storage Performance Council. This is attribution, not an inferred dataset author list.

| Listed file | Displayed compressed-file size | Exact listed URL (not fetched) |
|---|---|---|
| Financial1.spc.bz2 | 27MB | https://skulddata.cs.umass.edu/traces/storage/Financial1.spc.bz2 |
| Financial2.spc.bz2 | 19MB | https://skulddata.cs.umass.edu/traces/storage/Financial2.spc.bz2 |
| WebSearch1.spc.bz2 | 7.6MB | https://skulddata.cs.umass.edu/traces/storage/WebSearch1.spc.bz2 |
| WebSearch2.spc.bz2 | 34MB | https://skulddata.cs.umass.edu/traces/storage/WebSearch2.spc.bz2 |
| WebSearch3.spc.bz2 | 32MB | https://skulddata.cs.umass.edu/traces/storage/WebSearch3.spc.bz2 |

Published MB values are not measured wire sizes; exact checksums/current versions UNKNOWN. WebSearch1 is smallest displayed file, not automatically selected. Choosing search-engine family or size-first rather than v0.1 lexicographic selection must be stated before download/contents; do not silently choose it on expected class quality.

IOTTA locator: historical rows **SPC OLTP Application Traces** and **SPC Search Engine Traces**, recorded1999, Timespan1day, links to this UMass page. Displayed collection sizes248MB/71.9MB. These are differently scoped collection metadata, not per-file uncompressed-size verification. Per-file continuous6h/endpoints UNKNOWN.

## S018: linked format documentation, readable text unavailable
URL: https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf . Linked from both UMass sections as **PDF Docs**. Title/byline/revision/date inside PDF UNKNOWN in this session. Retrieval of bytes is not full-text reading.
Search-provider extraction suggests fields `ASU,LBA,Size,Opcode,Timestamp`, R/W opcodes, seconds timestamps and byte sizes. **UNVERIFIED exact schema/units**: no readable primary passage independently checked. Do not infer512-byte LBA from request lengths or example values; block size must come from documentation. No example trace rows from search are adopted as actual-file evidence.

## Rights and missing gates
UMass footer actually says repository is licensed under **CC BY4.0**; it does NOT contain the librarian-reported phrase “unless otherwise specified” in orchestrator-visible text. Footer alone is not treated as conclusive license for separately contributed SPC data. FAQ does not resolve SPC-specific terms. IOTTA says these traces are externally hosted due to access restrictions. Dataset rights remain UNKNOWN pending source-specific documentation/human confirmation; no terms accepted.

| Requirement | Current status |
|---|---|
| Individually listed file below100MiB | Direct metadata support; actual size/hash not checked |
| Block-I/O provenance | IOTTA classification + UMass I/O descriptions; not modern SSD trace evidence |
| Real Read rows and documented units | Schema lead only; actual data not fetched; primary schema verification pending |
| One ASU/volume per file | UNKNOWN; do not filter/pool namespaces to pass gate |
| Complete chronological6h | Collection metadata1day only; per-file coverage UNKNOWN |
| Decode≤1GiB, prefix≤250krequests/10kpages | UNKNOWN; caps not expanded |
| Dataset license/rights | UNKNOWN; website footer insufficient |
| Class support/predictability | UNKNOWN; no inspection/evaluation performed |

## Next reversible step, not execution permission
Recommend resolve format/rights from the linked small documentation PDF before any data download. A separate authorized document-text extraction may be needed; no shell/parser run currently allowed. This stage can fail without changing task/budget.
If source passes docs gate: methodologist prepares source-specific protocol version (.bz2 instead of.gz, SPC schema/time/address instead of MSR Windows-filetime) retaining numerical target/splits/caps; exact file selection/source rights/commands/enforcement shown before E002 approval. Handing over legal local read trace is alternative. Do not approve E002 based only on listing size. No E-ID/model/results created.

## Coverage and interpretation
Historical dataset1999, n=1 intended, finite discovery, schema access failure and unverified rights/namespace/coverage. A small listed file is not yet a usable learning dataset. Even later positive F1 would not establish placement benefit, SSD parallelism or throughput.
