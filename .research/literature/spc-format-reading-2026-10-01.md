# S018: прочитанная спецификация формата SPC

2026-10-01. DOC-ONLY SOURCE AUDIT; generic format verified, DATA SUITABILITY NOT ESTABLISHED. Оркестратор прочитал все191строки извлечения и сверил exact support; независимая reviews/spc-document-audit-2026-10-01.md. Не загружали трассы/сэмплы, не обучали, не принимали dataset terms, raw/E001 сохранён.

## Первичный источник и сохранённые артефакты
URL: https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf
Название: **SPC TRACE FILE FORMAT SPECIFICATION**; организация на обложке **Storage Performance Council(SPC)**. Personal authors/отдельная дата выпуска UNKNOWN. Cover Revision1.0.1; DOCUMENT HISTORY содержит17-Jul-02/Version1.01. Нотация версий сохранена, copyright1999,2002 не принят за publication date.
Сохранённый PDF: experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0/source.pdf (127256bytes; recordedSHA256442b3c6c64fec10ebcc7221b088640925f0ca3cc3f6e2c6e9f30acf7e9c9ae06).
Текст: тот же каталог/extracted.txt (10383bytes; recordedSHA25646f6ce13476746a7d753b7bdd365310f56e8e1dac49f0406ebd7881b7cba9ddf).
Provenance/commands/code/config hashes/status: manifest.json, audit.log, READOUT.md в том же каталоге. Hashes прочитаны в manifest, НЕ пересчитаны оркестратором. Это не E-ID/модельный эксперимент.

## Exact support и пределы
Page numbers ниже: physical PDF index по6form-feed-разделителям; printed numbering отличается.
| Claim | Exact primary support | Что не устанавливает |
|---|---|---|
| C023 generic schema | §§1.1–1.2, physical4/printed3, extractedL75–89; §§1.2.1–1.2.5 L91–133: one I/O command per comma/newline record; ASU,LBA,Size,Opcode,Timestamp + optional fields | Соответствие конкретного Financial/WebSearch файла, реальные reads/число классов |
| C023 bytes/op/time | §1.2.3 physical4/printed3 L109–113 Size=bytes; §1.2.4 physical4–5/printed3–4 L115–125 R/r=read,W/w=write; §1.2.5 physical5/printed4 L127–133 timestamps seconds from trace start,nondecreasing | Exact issue-versus-completion capture convention, continuous6h одного файла |
| C024 LBA units | §1.2.2 physical4/printed3 L101–103: ASU block offset; “the size of a block is contained in the description of the trace file” | Конкретные512/4096bytes per LBA block; request Size modulo512 не определяет address unit |
| C025 legal zero size | §1.2.3 physical4/printed3 L109–111 “A value of zero is legal”, subsystem-dependent; modulo512 expected but not required | Как интерпретировать zero-size event для нашего target; текущий plan STOP приSize≤0 сохранён до checkpoint |
| C026 ASU | §1.2.1 physical4/printed3 L91–97 Application specific unit, numbering0..n−1, several units possible | ASU=physical disk/volume, singleASU конкретного файла; нельзя silently filter/pool |

Optional fields: §1.2.6 physical5/printed4 L135–151 не стандартизованы, могут отсутствовать/меняться в количестве. §1.3 L153–185 — исключительно пример формата, не просмотр actual trace rows.
Весь текст191строки прочитан; dataset-specific license/use terms не найдено. Cover copyright — не usage grant. Rights/source descriptor/time capture/actual reads/one namespace/full6h/cardinality/class support всё ещё UNKNOWN.

## Исполнение и оговорки
Первый scriptv1 не запускался: обнаружен defect hard-limit inheritance, сохранён blocked manifest в experiments/documentation/S018-2026-10-01-docaudit-a91c7e/. V2 новая подготовительная версия, old artifacts неизменны, scientific design/caps не менялись; доv2sourceattempts0. Единственный source download/extractionv2 exit0, HTTP200,networkattempts1/runtime retries0, около3.4s scriptwall, reportedprocessCPU≈0.093s. Previous inventory≤5s, exactcombinedwall отдельно не измерен.
AS soft64MiB parent+192MiB child выставлены/записаны; RLIMIT_AS не whole-treeRSS. Parent ru_maxrss1111816KiB аномален относительно256MiB cap, происхождение не установлено; child20068KiB. Нельзя ни заявить соблюдение RAM≤256MiB, ни приписать actualpeak именно PDF операции. **R002 major открыт: RAM compliance не сертифицировано.** Источник и текст прочитаны, но statuscomplete означает conversion success, не полное budget compliance.
Установка/дополнительные runtime investigations не выполнялись; признакиseccomp/minimalenv записаны, полноценной sandbox/cgroup verification не заявляем. Применялся существующий pdftotext; dependency lock/versionpackage UNKNOWN. Новые маленькие output artifacts<5MiB по сохранённым bounded records.

## Воспроизводимость и следующий gate
Actual shell command: `ls -ld ".research/experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0" && exec /home/linuxbrew/.linuxbrew/bin/python3 -I -S -B ".research/experiments/scripts/inspect_spc_doc_v2.py"` (tooltimeout55s).
Actual extractor: `/usr/bin/pdftotext -layout -enc UTF-8 -eol unix - -`, PDFstdin. Это историческая команда, не разрешение нового запуска; exclusiveoutputs намеренно не допускают reuse каталога.
Дальнейшее исполнение STOP. Нужны source-specific description(blocksize/rights/capture/namespace/coverage), explicit parser/version adaptation cR003, deterministicfile selection, freeze/env/defensiblelimits и отдельноеE002/E003permission. Target4KiB/historyH600s/labels0,1–2,≥3 и caps сохранены. Ни F1, ни SSD throughput, ни efficacy H005 не измерены.
