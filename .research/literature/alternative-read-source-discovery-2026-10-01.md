# Alternative small block-I/O source discovery (bounded)

2026-10-01. DOCUMENTATION/METADATA-ONLY. Только docs-only поиск после source-pivot («да»): ровно
**3/3** public query, **5/5** public-text fetch, **3** candidate family. Никакие trace/archive/sample
байты, `.csv`, `.gz`, скрипты, shell, download, install, terms acceptance не выполнялись. Все fetch —
README/HTML-listing/license/metadata. Ни один существующий файл не менялся; создан только этот note.
S020/C028–C029 (архивные лиды) не затрагивались; новые ID с S021/C030. Snippet = lead, не support.

## Budget / факт использования
| Инструмент | Использовано | Итог |
|---|---|---|
| websearch (Exa, numResults8) | 3/3 | исчерпан |
| public-text webfetch | 5/5 | исчерпан (2 отказа/пусто) |
| candidate families | 3/3 | Alibaba-official; Tencent-official; IOTTA general+curated |

Запросы: (Q1) `Alibaba Cloud block storage trace dataset official release README block size LBA units`;
(Q2) `SNIA IOTTA block I/O trace small dataset documented block size sector units timestamp`;
(Q3) `Tencent cloud block storage trace dataset official release github read write offset length timestamp`.
Фильтры: без доменных; inspected — 8 сниппетов/query (titles/highlights), не 8 прочитанных документов.

## Retrieval trail
| # | URL | Outcome | Что реально видно |
|---|---|---|---|
| 1 | https://github.com/alibaba/block-traces | 200 | первичный README целиком: schema, units, license, checksums, размер tarball |
| 2 | https://iotta.snia.org/traces/block-io?historical=true&n=100&page=1 | 200 | официальный listing 14 строк: name/timespan/records/size/actions |
| 3 | https://github.com/cacheMon/cache_dataset/blob/main/README.md | 200 | сторонний curated README: форматы/units и license по нескольким наборам |
| 4 | https://s3.amazonaws.com/cache-datasets/index.html | 200 | **JS-only**, список объектов не отрендерился (текст недоступен) → UNKNOWN |
| 5 | https://s3.amazonaws.com/cache-datasets?list-type=2&prefix=cache_dataset_txt/2015_cloudphysics/ | 200 | S3 XML metadata: `<KeyCount>0</KeyCount>` для угаданного prefix; per-file размеры не получены |

Fetch #4/#5 не давали trace-байтов; это metadata/listing. Повторов/обхода бюджета не было.

## Кандидаты и gate-статус
| S-ID | Источник (тип) | Byte/sector unit | Размер ≤100MiB | ≥6h | Rights | Вердикт |
|---|---|---|---|---|---|---|
| S021 | Alibaba Block Traces, official GitHub | **да, offset/length в bytes; timestamp µs** | **нет: tarball 181GB gzip / 751GB** | да (месяц Jan-2020) | CC BY 4.0 (README) | blocked by size/access |
| S023 | Tencent Block Storage, SNIA IOTTA 27917 | заявлен сектор (в snippet); primary README не читан | нет: parts ~0.9–1.14GB | нет: part ≈1h | SNIA License (distributor) | нe проходит 6h и size |
| S024 | cacheMon curated block traces (CloudPhysics/Tencent CBS/Alibaba) | **да, документированы** (sectors/µs/cmd) | UNKNOWN (S3 listing не читается) | CloudPhysics 7 дней; Tencent 10 дней | CC BY 4.0 | derivative-provenance + size UNKNOWN |
| — | HP LAJW (IOTTA 3379) | нет dataset README (unit UNKNOWN) | да: 8.08MB | да: 2 мес | SNIA License | fails unit-doc (SRT, 1992 HDD) |

## Точная первичная поддержка
**S021 Alibaba** (README, fetched 2026-10-01): «`offset` … Offset of this operation, in bytes»;
«`length` … Length of this operation, in bytes»; «`timestamp` … in microseconds»; «`opcode` … 'R' or 'W'»;
«`device_id` … ID of the virtual disk»; «recorded over the month of January 2020», 1000 ultra disks;
«the tarball is very large, 181GB gzip-compressed and 751GB uncompressed»; license section:
«The trace data and document are licensed under CC-4.0». Repo file tree: only `README.md`.
**C030** (EVIDENCE/S021): units/rights/coverage полностью документированы первично; **но отдельного
маленького файла нет** — весь `io_traces.csv` внутри 181GB tarball. **C031** (EVIDENCE/S021): официальный
download route = OSS + короткий survey (`yida.alibaba-inc.com/o/alibaba_block_traces_2020_survey`),
не прямой URL файла; байты/terms не трогались.

**S022 IOTTA historical listing** (fetched): строки включают Slacker 14 минут/3.37MB; Nexus 5
(коллекция 6 мес/31.2MB); FIU 3 мес/28.8GB; Microsoft Production 18.2GB (8 zip, «first seven … one for
each of the first seven timestamped hours»); MSR Cambridge 4.94GB; Cello 1992 603MB / 1996 4.94GB /
1999 30.7GB; SPC OLTP 248MB и SPC Search 71.9MB оба «hosted extern… UMass»; **HP LAJW 8.08MB/2 месяца**
(только Download Sample, без Readme). **C032**: в пределах listing ни одна официальная строка не даёт
одновременно ≥6h и ≤100MiB вместе с dataset-specific README о единицах; единственная малая
долгая запись (HP LAJW) без README.

**S023 Tencent SNIA** (snippet only, landing НЕ fetch): Parts 001… «about 1 hour», «192 Million»,
1.14GB … «174 Million», 1.02GB; источник — OSCA ATC’20. **C-предложение UNKNOWN**: units/schema и
per-file размеры не подтверждены первичным чтением; даже при 512-секторах parts нарушают 6h и 100MiB.

**S024 cacheMon curated README** (fetched): CloudPhysics — «timestamp … microseconds», «lbn … in
sectors», «len … in sectors», «cmd … SCSI command … read or write», 106 дисков, одна неделя; Tencent
CBS — «Offset … in sectors (1 sector = 512 bytes) … (converted to bytes in our open-sourced traces)»,
«Timestamp … Unix time (seconds)», `IOType` 0/1, 10 дней; Alibaba — bytes/µs. License: «This work is
licensed under … CC BY 4.0». **C033** (EVIDENCE/S024): в **стороннем curated** каталоге единицы
документированы, но это derivative-пере-release (не original distributor), и per-file размеры не
разрешены. **C034** (UNKNOWN): S3 per-file размеры/доступность остаются UNKNOWN (index JS-only;
угаданный prefix дал KeyCount=0; корректный layout не устанавливался, чтобы не изобретать URL).

## Scoped negative (bounded)
**C035 (EVIDENCE, scoped negative)**: в просмотренных 3 family / 5 public-text источниках **не найден
primary-distributor BLOCK-I/O trace, одновременно дающий** (a) документированный byte/sector unit,
(b) индивидуально listed файл ≤100MiB, (c) ≥6h непрерывной записи. Это отсутствие **в inspected
материалах**, не утверждение «не существует»; gated/bulk/неархивные маршруты не исключены.

## Recommended provisional candidate + selection rule (НЕ executable)
Единственный документированный primary BLOCK-I/O маршрут — **S021 Alibaba**; его блокер —
**size/access gate (181GB)**, а не единицы/права. Поэтому recommended рекомендован условно:
- **Single-trace preread selection rule (зафиксировать ДО contents, без future/class signal):** в
  будущем официальном per-volume списке упорядочить имена по bytewise-лексикографическому UTF-8,
  выбрать первое; взять первый непрерывный 6h префикс `[t0, t0+21600s)` по timestamp от первого
  события; границу freeze до labels. Не выбирать device/file по read-count, класс-балансу или
  будущему сигналу. Если выбранный файл >100MiB или units не подтверждены dataset-specific docs —
  STOP без перехода к «следующему лучшему».
- **Parser adaptations pending (отдельный freeze/checkpoint):** Alibaba — CSV `device_id,opcode,
  offset_bytes,length_bytes,timestamp_us`; нужен фильтр одного device_id и покрытие 6h; вместо
  gzip/MSR-Windows-filetime. Tencent (если брать) — sectors×512 и Unix seconds. cacheMon — derivative
  конверсия (Tencent уже переведён в bytes) — требует явного принятия provenance.
- **Unresolved runtime/data gates:** точный official URL/member+checksum; размер и доступность
  ≤100MiB; license acceptance уполномоченным человеком; timezone/специфика µs; непрерывность 6h;
  фактическая read-density/class support/ASU/namespace; R002 memory/R003 compatibility.

## Предлагаемые JSONL (для orchestrator; НЕ записаны)
```
{"id":"S021","title":"Alibaba Block Traces","authors":null,"year":2020,"doi":null,"arxiv_id":null,"url":"https://github.com/alibaba/block-traces","version":"GitHub master README retrieved 2026-10-01; commit UNKNOWN; dataset Jan-2020, tarball MD5 95780fc531a60fd4ca0513ef88ef469c","retrieved_at":"2026-10-01","access":"full-text","metadata_status":"official distributor README independently fetched; schema/units/license/checksums read from primary; repo tree only README.md; tarball bytes not downloaded; size gate FAILS (181GB)","note_path":".research/literature/alternative-read-source-discovery-2026-10-01.md"}
{"id":"S022","title":"Block I/O Traces (IOTTA historical listing)","authors":null,"year":null,"doi":null,"arxiv_id":null,"url":"https://iotta.snia.org/traces/block-io?historical=true&n=100&page=1","version":"public listing retrieved 2026-10-01; page version UNKNOWN","retrieved_at":"2026-10-01","access":"full-text","metadata_status":"official distributor listing 14 rows with timespan/record count/file size/actions independently fetched; no trace bytes; no README for FIU/HP LAJW","note_path":".research/literature/alternative-read-source-discovery-2026-10-01.md"}
{"id":"S023","title":"Tencent Block Storage (SNIA IOTTA)","authors":null,"year":2018,"doi":null,"arxiv_id":null,"url":"https://iotta.snia.org/traces/block-io/27917","version":"landing seen via search snippet only; parts ~1h/0.9-1.14GB each; exact part list/version UNKNOWN","retrieved_at":"2026-10-01","access":"metadata","metadata_status":"SEARCH SNIPPET ONLY, landing/README not independently fetched; units/schema UNVERIFIED","note_path":".research/literature/alternative-read-source-discovery-2026-10-01.md"}
{"id":"S024","title":"Open-source Cache Dataset (cacheMon/cache_dataset)","authors":["Juncheng Yang"],"year":2024,"doi":null,"arxiv_id":null,"url":"https://github.com/cacheMon/cache_dataset/blob/main/README.md","version":"main README retrieved 2026-10-01, 556 lines/31.2KB; changelog first version 2024-12-01; commit UNKNOWN","retrieved_at":"2026-10-01","access":"full-text","metadata_status":"third-party curated catalog README independently fetched; documents units for CloudPhysics/Tencent CBS/Alibaba and CC BY 4.0; per-file S3 sizes NOT resolved (index JS-only; guessed prefix KeyCount=0); derivative provenance, not original distributor","note_path":".research/literature/alternative-read-source-discovery-2026-10-01.md"}
```

## Предлагаемые claims (для integration; НЕ записаны)
- **C030 (EVIDENCE, S021)** — официальный Alibaba README документирует BLOCK-I/O: `offset`/`length` в
  bytes, `timestamp` в µs, `opcode` R/W, `device_id`; месяц Jan-2020; CC BY 4.0. Caveat: это
  документация источника, не проверка содержимого/read-density.
- **C031 (EVIDENCE, S021)** — доступ к данным идёт через Alibaba OSS после survey; отдельного маленького
  файла/подфайла официально не перечислено; tarball 181GB gzip / 751GB uncompressed.
- **C032 (EVIDENCE, S022)** — в IOTTA historical listing нет официальной строки, дающей одновременно
  ≥6h и ≤100MiB с dataset-specific README единиц; HP LAJW (8.08MB/2мес) идёт без Readme.
- **C033 (EVIDENCE, S024)** — сторонний curated каталог документирует sector/µs единицы и CC BY 4.0,
  но является derivative-пере-release; его per-file размеры не разрешены.
- **C034 (UNKNOWN)** — per-file размеры/доступность curated S3 block-наборов остаются UNKNOWN;
  JS-only index и KeyCount=0 не позволяют судить.
- **C035 (EVIDENCE, scoped negative)** — в inspected 3 family / 5 источниках не найден
  primary-distributor BLOCK-I/O trace с единицами + ≤100MiB + ≥6h одновременно; не «не существует».

## Human choice (одна, исполнимая)
Рекомендуется **отдельно разрешить только metadata-only проверку** курированного BLOCK-маршрута
(cacheMon S3: CloudPhysics / Tencent CBS): получить корректный object listing (имена + размеры) и
подтвердить, есть ли **один per-disk файл ≤100MiB** с документированными секторами/µs и ≥6h, приняв
derivative-provenance (CC BY 4.0). Primary-distributor Alibaba в текущем 100MiB cap неисполним;
расширение download-бюджета до 181GB не рекомендуется и требует отдельного решения. Данные/байты в
рамках этого note не загружались и не будут без нового approval.

## Coverage limits
Bounded exploratory, не systematic review; 3 query / 5 fetch, n=1 distributor catalog family
(IOTTA) + 2 cloud-vendor repos. Per-file размеры и полные списки частей не проверялись; gated/bulk,
неархивные и неиндексированные маршруты не исключены. Класс-поддержка, read-content, H005 efficacy
и R002/R003 не проверялись и не выводятся. Stop: бюджет исчерпан, дальнейший public-doc поиск требует
нового решения.

## Orchestrator verification and narrowing, same date
Four additional metadata/docs verification fetches, distinct from librarian's3queries/5fetches: AlibabaREADME, cacheMonREADME, and two S3 ListObjectsV2 XML responses for exact prefixes linked by cacheMon. No trace/object data fetched. Budget/scope counted explicitly; no claim these four were included in agent's five.
- Independently read https://github.com/alibaba/block-traces sectionsSchema/Download/License: offsets/lengthbytes, received-by-server timestampµs, RW/deviceID;181GBcompressed/751GBuncompressed stated; survey route; CC-4.0 link points to CC BY4.0. Original exactfiledata/version/independentperdisk route unknown. No181GBdownload proposed/executed.
- Independently read https://github.com/cacheMon/cache_dataset/blob/main/README.md: **Open-source Cache Dataset**, TencentCloudEBSTraces section says TimestampUnixseconds issued, originalOffsetsectors(1sector512bytes) converted tobytes in curatedtext; Size statedsectors, IOType0Read/1Write, VolumeID. ExactSize conversion in curatedfiles not inferred. LicenseCC BY4.0; Acknowledgements attributes collection/convertedtraces toJunchengYang. This is a converted distribution, not originalsourcevalidation. CloudPhysics only says sectors; **sectorbytes not established**. OracleGeneral has timestamp,obj_id,obj_size,next_access_vtime and noRW; cannot replace full causalblock-request data or provide future feature.
- S025 XML metadata URL: https://cache-datasets.s3.amazonaws.com/?list-type=2&prefix=cache_dataset_txt%2F2008_msr%2F&max-keys=50 . Response2026-10-01: KeyCount3, IsTruncatedfalse. Keys/sizes: `cache_dataset_txt/2008_msr/msr-cambridge1.tar`3282677760bytes; `.../msr-cambridge2.tar`2022451200bytes; `.../msr.zip`5441159985bytes. Allabove100MiB; ETagsmultipart not adopted as inputchecksum. No tar/zipbytes fetched. This curatedMSRroute therefore not a smallfile solution.
- S026 XML metadata URL: https://cache-datasets.s3.amazonaws.com/?list-type=2&prefix=cache_dataset_txt%2F2020_tencentBlock%2F&max-keys=20 . Response2026-10-01: KeyCount2, IsTruncatedfalse. Keys/sizes: `cache_dataset_txt/2020_tencentBlock/README`2052bytes and `.../tencentBlock.zst`137224724902bytes. SmallREADME is documentation, notdata; dataobjectabove100MiB. Neitherobjectcontents fetched. These exactprefixmetadata resolve a subset of earlierC034unknown, not allcuratedfiles.
Librarian's TencentSNIApartsize/duration fromsnippets remains UNVERIFIED leadS023, notcatalogedverifiedclaim; no primaryperparteligibility conclusion fromit. ProposedC032globalcatalogabsence narrowed: listingcollectionsize/duration cannotruleout unseenindividualsubfiles. Familygrouping3in agentnote is exploratory grouping(IOTTA+curator grouped), not systematic screeningdenominator. No exhaustiveabsenceclaim.
Outcome: no candidate has established a usable≤100MiB fullblock-request file in inspectedmaterials. Preserve negatives/gaps rather than redrawnumericcaps or substituteOracleGeneral. protocol/data-route-options-v0.1.md proposes syntheticillustration / documentedusertrace / separatelyexpandedMSRaccess; noneapproved, no classifieroutcomes. Source-searchstopped, no datadownload/shell/modelrun, R002/R003stillopen.
