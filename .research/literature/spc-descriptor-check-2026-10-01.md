# SPC per-file descriptor / dataset-rights check (bounded)

2026-10-01. DOCUMENTATION DISCOVERY ONLY. Оркестратор выдал bounded task; агент выполнил ровно 2 public generic query и 4 public-text webfetch. Данные/архивы/сэмплы, `.bz2`, `.csv`, `.doc`, PDF-binary, скрипты и shell НЕ загружались и не запускались. Никакие существующие файлы (papers.jsonl, search-log, evidence-map, README, raw/manifests) не менялись. Создан только этот note. Source policy: exact visible primary support; search snippets и сторонние docs — только lead.

## Budget и факт использования
- Queries (provider Exa, auto, numResults8): ровно **2/2**.
- Public-text fetches: ровно **4/4** (в т.ч. 1 отказ). Больше нет; на gate остановлено по бюджету.
- Запросы: (Q1) `SPC trace Financial WebSearch LBA block size description Storage Performance Council trace documentation`; (Q2) `UMass Trace Repository SPC traces Financial WebSearch license terms of use documentation block size description README`.
- Фильтры: без доменных фильтров; inspected — 8 сниппетов на каждый query (titles/highlights), не 8 прочитанных документов.

## Retrieval trail
| # | Tool / URL | Outcome | Что реально видно |
|---|---|---|---|
| 1 | https://skulddata.cs.umass.edu/traces/storage/ | **FAIL 403** | hosting directory index заблокирован; файл-листинг не получен |
| 2 | https://traces.cs.umass.edu/docs/traces/storage/ (HTML) | 200 | только `.doc`/`.pdf` Docs + 5×`.spc.bz2`; per-file descriptor отсутствует |
| 3 | https://traces.cs.umass.edu/ (text) | 200 | primary distributor license statement (см. ниже) |
| 4 | https://web.archive.org/cdx/search/cdx?url=skulddata.cs.umass.edu/traces/storage/*&output=text&fl=original,timestamp,statuscode,mimetype&collapse=urlkey&limit=300 | 200 | archived listing: ровно 7 объектов, только `.bz2` + `.doc` + `.pdf` |

Fetch #1 403 и не читался; fetch #4 — public Wayback listing, без auth/обхода; он вернул только метаданные объектов, не содержимое данных.

## License / dataset terms — verified (primary distributor)
Fetch #3, домашняя страница репозитория, дословно:
- «Unless otherwise specified, data on this repository is provided under a CC BY 4.0 license.»
- footer: «UMass Trace Repository © 2025 by University of Massachusetts Amherst is licensed under CC BY 4.0».

Страница Storage (fetch #2) не содержит иных/более строгих условий; отдельного SPC-specific grant там нет. Вывод **scoped**: UMass как дистрибьютор заявляет CC BY 4.0 на данные репозитория «unless otherwise specified», и для этих 5 файлов списка других условий не указано. Остаётся неизвестным grant исходного контрибьютора (Storage Performance Council / Ken Bates HP / Bruce McNutt IBM); страница говорит «made available courtesy of», а не «licensed by». Т.е. права подтверждены на уровне дистрибьютора, не оригинального автора, и зависят от оговорки «unless otherwise specified». Footer/огонь CC BY — не то же самое, что доказанный grant контрибьютора.

## Per-file LBA block size — UNKNOWN, с точным объяснением
- Единственная per-trace документация в листинге: `SPC-Traces.doc` и `SPC-Traces.pdf`. Оба — не HTML/txt, `.doc`/PDF binary сюда не тянулись.
- Ранее прочитанный S018 (тот же `SPC-Traces.pdf`) §1.2.2 прямо отсылает: «the size of a block is contained in the description of the trace file». Эта «description» в разрешённых первоисточниках **отсутствует**: страница Storage и Wayback-листинг не содержат README/txt/отдельного описания.
- Q1 поднял SPC-1 benchmark spec (`storageperformance.org/.../SPC1_v3_10_final_0.pdf`): «For SPC-1, a LOGICAL BLOCK is assumed to be 512 bytes in size.» Это (а) search highlight, не инспектированный primary текст; (б) другой документ — спецификация бенчмарка SPC-1, а не «description of the trace file»; (в) не относится явно к Financial/WebSearch 1999. Поэтому 512 **не промоутируется**. Нельзя выводить unit из модулей Size, размера сэмплов или сторонних gist/статей.
- Итог: actual per-file LBA unit (512 vs 4096 и т.п.) — **UNKNOWN** в рамках позволенных источников. Scoped negative: в архивированном листинге этого пути нет non-binary descriptor; это не утверждение «нигде не существует».

## Remaining gates
| Requirement | Status на 2026-10-01 |
|---|---|
| Per-file LBA unit / block size | UNKNOWN; нет HTML/txt описания в разрешённых источниках |
| ASU: один ли physical volume на файл | UNKNOWN (generic ASU см. C026) |
| Capture convention (issue vs completion) | UNKNOWN |
| Continuous 6h в одном файле | UNKNOWN; только collection-level «1 day» (C021) |
| Namespace/ASU count | UNKNOWN |
| Distributor license | CC BY 4.0 «unless otherwise specified» подтверждён (primary) |
| Original contributor (SPC/HP/IBM) grant | UNKNOWN |
| Actual read rows / class support | UNKNOWN; данные не скачивались |

## Предлагаемые записи для orchestrator (НЕ записаны в papers.jsonl/evidence-map)
- **S019** — UMass Trace Repository home page. URL https://traces.cs.umass.edu/ . Type: dataset-distribution-documentation (license statement). Retrieved 2026-10-01, access full-text. Identity verified (title/org/copyright видимы). Exact quote/date: «Unless otherwise specified, data on this repository is provided under a CC BY 4.0 license.» (2026-10-01). Null gaps: авторство, дата публикации страницы, применимость к SPC-контрибьюции — UNKNOWN.
- **S020** — Wayback CDX archived directory listing of `skulddata.cs.umass.edu/traces/storage/*`. Type: archive-listing (evidence of absence of descriptor). Snapshot timestamps 2021-04-21; retrieved 2026-10-01. Identity verified by response. Null gaps: полнота архива, более старые/иные дистрибуции — UNKNOWN.
- S019/S020 — subordinate documentation/listing, НЕ независимые датасеты; S017/S018 остаются основными.

## Предлагаемые claims (для integration, не записаны)
- **C027 (EVIDENCE, S019)** — UMass repo заявляет CC BY 4.0 «unless otherwise specified», и storage-страница иных условий не указывает. Caveat: дистрибьюторский grant, не доказательство контрибьюторского grant; «unless otherwise specified» остаётся оговоркой.
- **C028 (EVIDENCE, S020, scoped)** — В archived listing пути storage только 5×`.spc.bz2` + `SPC-Traces.doc` + `SPC-Traces.pdf`; non-binary per-file descriptor не найден. Scoped negative в пределах listing, не «не существует».
- **C029 (UNKNOWN)** — Actual per-file LBA unit остаётся UNKNOWN; не инферировать 512. Дополняет C024/C026, не отменяет их.

## Stop / next choice (рекомендация, не execution permission)
- Дальнейший public doc поиск STOP: бюджет исчерпан, а единственный недостающий per-trace descriptor в разрешённых источниках отсутствует. Расширять запросы/тянуть `.doc`/SPC-1 PDF/Trace bytes — нельзя без нового решения.
- Рекомендуемый минимальный PoC-route (не ещё 3 обзора): (1) попросить у advisor/пользователя lawful read-trace с **явно документированным** LBA unit и лицензией (README/dataset card), либо (2) изменить план под источник, где единица адреса указана документально. Использование Financial/WebSearch без разрешённого per-file unit оставляет target 4KiB логически не обеспеченным.
- Если пользователь захочет всё же эти трассы: нужен отдельный, явно одобренный источник/канал для per-trace «description» (у UMass его нет; возможно, у исходного SPC-релиза) — это новый шаг с новым разрешением, не авто-расширение.

## Coverage limits
Bounded exploratory проверка, не systematic review; 2 query / 4 fetch, n=1 distributor family. Отсутствие per-file descriptor установлено только для страницы Storage и для archived листинга этого пути. Класс-поддержка, read-content и H005 efficacy не проверялись и не выводятся. R002/R003 не затрагивались.

## Orchestrator verification / narrowing
2026-10-01: independently fetched UMass home https://traces.cs.umass.edu/ (markdown) and checked exact data-license statement in welcome section: **“Unless otherwise specified, data on this repository is provided under a CC BY 4.0 license.”** Это заявление явно о DATA, не только website footer; новая поддержка C027. Надёжность указана как primary-distributor statement with exception clause, не юридическая гарантия всей цепочки прав. Нельзя продолжать писать «только footer / никаких dataset terms» без этого уточнения. Original contributor-specific grant не найден, но его отдельная недоступность сама по себе не опровергает явные опубликованные условия дистрибьютора.
Independent re-fetch exact Wayback CDX URL from trail failed HTTP503; no retry. Therefore archived7object list/time metadata remain librarian-reported only, NOT independently verified/preserved content. ProposedS020/C028 archival-absence claim not promoted to verified evidence. Existing CurrentStorage listing + genericS018 suffice for scoped statement: per-file blocksize not established in documentation actually inspected; UNKNOWN не «проверенное отсутствие везде».
The task budget exhausted. No data/shell/model activity. Recommendation: do not spend an unbounded search on missing SPC descriptor; retain numeric PoC task/budget and ask user whether to switch the candidate source. Earlier phrases «единственная per-trace documentation»/«уUMassего нет» are narrowed here to **not found in inspected materials**; unseen/gated/unarchived descriptions may exist.
