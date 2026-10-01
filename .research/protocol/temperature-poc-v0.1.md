# Малый PoC: прогноз будущей read-temperature, только классификация
Версия v0.1, 2026-10-01. **CONDITIONAL EXPLORATORY DRAFT — НЕ APPROVED, НЕ READY TO RUN.**
Все числа, алгоритмы, пороги и gates ниже — предложения помощника, не evidence/решение пользователя. Ничего не исполнено.
Ownership: создан только этот документ; legacy next-read experiment-plan.md, question/hypotheses/state/evidence/reviews/literature и existing/raw сохранены.
Это отдельная операционализация предпосылки C017/H005, НЕ фиксация/изменение H005 и НЕ тест её throughput efficacy; новый H-ID не вводится.

## 1. Основание, вопрос и граница вывода
- Из existing evidence-map: C014/E001 — локальные два CSV all-W по literal tokens, read-label gate под R/W схемой не проходят; происхождение неизвестно.
- C015/S016 — MSR Cambridge README §3 документирует Read/Write, byte Offset/Size, issue Timestamp и ResponseTime как длительность; документация проверена 2026-09-30, данные НЕ скачаны.
- Точные сохранённые указатели: claims/evidence-map.md C014–C017; literature/public-data-options.md §§Exact read-field support, Access and license caveats. Это чтение локальных записей проверки, не повторная первичная retrieval/репликация.
- C010/S013 — проверенный serial simulator не позволяет вывести throughput gain от overlap; source audit, не новый запуск. Классификация этот блокер не устраняет.
- **Предлагаемый вопрос:** на одном заранее выбранном read-containing volume улучшает ли fixed depth-3 tree X прогноз read-класса следующего 10-min окна относительно past-frequency Z на тех же причинно доступных страницах, по test macro-F1 хотя бы на 0.05 абсолютных пунктов?
- Целевая популяция/estimand: только выбранный 6-hour prefix одного volume, парная разница macro-F1 по всем eligible test (page, decision) примерам. Условия: полная документированная запись запросов, границы/лимиты ниже.
- Проверяемое предположение: Δmacro-F1 ≥ 0.05 при hot precision и recall не хуже Z более чем на 0.05 каждое; предсказание направления — X лучше Z; величина UNKNOWN.
- Предложенный механизм: прошлые read-count/recency/write-count могут кодировать повторяемость и смену активности. Это HYPOTHESIS, не доказательство; stationarity может полностью объяснить успех Z.
- Независимая единица — workload/volume, здесь n=1; окна/страницы зависимы. Ни p-values, ни pseudo-independent CIs, ни power guarantees; sample size задаёт workload cap, не статистическую мощность.
- Не проверяем placement, physical NAND page size, migration, MiB/s, SSD speedup, co-access или novelty. Это не systematic/novelty study; нового поиска нет, bounded evidence до 2026-09-30 не устанавливает новизну.

## 2. Предлагаемые параметры и причинный target
| Параметр | Fixed proposal | Причина выбора, не эмпирический факт |
|---|---|---|
| Logical page | 4096 bytes (4 KiB) | Простая программная единица; не утверждение о physical NAND |
| History / future H / decision step | 600 / 600 / 600 s | Одинаковые 10 min: простая frequency baseline и неперекрывающиеся future окна |
| Абсолютные labels | cold=0 reads; warm=1..2; hot≥3 (k=2) | Прозрачный счёт, не тертили/квантили и не гарантия баланса |
| Universe U(t) | Все logical pages, наблюдавшиеся в R ИЛИ W с issue time <t после reset сегмента | Causal seen-universe; writers-only/never-read страницы остаются |
- Для запроса с Offset=o≥0, Size=s>0 учитывать pages floor(o/4096)..floor((o+s−1)/4096). Каждая overlapping page получает +1 ровно один раз на исходный read request, не по байтам/сектору.
- Истинный label для p∈U(t): число исходных READ requests, перекрывающих p, с issue time в [t,t+600). Не создавать искусственный read order между страницами одного запроса.
- Features используют только issue times в [t−600,t), universe — события от reset до t. События ровно в t не входят в history/U(t), входят в future; все одновременные события обрабатываются batch, порядок строк не даёт знания будущего.
- Issuance ≠ completion: это offline host-observer прогноз *поступивших* reads. Предполагается, что issue-событие известно к следующему decision; ResponseTime/completion не используются как feature. Нельзя перенести это без проверки на FTL видимость/готовность/успех reads.
- Writes расширяют наблюдаемый universe при issuance, НЕ подтверждают mapped/valid/available physical data; read of previously unseen page тоже расширяет его только для последующих решений. Write-hot не становится read-hot.
- Для p∉U(t) default category=cold, никаких lookups по будущему. Primary confusion/F1 только U(t), с полной cold mass. Нельзя выбирать U из future readers или из global full-file address vocabulary.
- Отдельный audit coverage на каждом future окне: доля read page-request incidences, где p∈U(t); denominator=все read page-request incidences; при 0 reads coverage=NA. Также число уникальных future unseen pages и их cold-default ошибки/истинные warm/hot counts.
- Future unseen set допустим ТОЛЬКО для этого coverage audit, не для eligibility/features/обучения; у действительно unseen future readers count>0, cold-default ошибочен. Unseen hot recall=0 при hot support>0, иначе NA; hot precision=NA без hot predictions. Полностью ненаблюдавшиеся и нечитавшиеся в будущем pages не перечислимы из trace, полной device coverage не заявлять.
- Complete окно требует доступных записей всего history и future внутри сегмента и документированной trace coverage. Начало после reset — warmup; конец/gap/EOF — censored, исключение с reason/count, никогда truncation-as-cold.

## 3. G0 → E002: bounded доступ/подготовка ДО любого fit
- Кандидат источник — S016, official landing https://iotta.snia.org/traces/block-io/388 ; документация https://iotta.snia.org/traces/block-io/386/download?type=readme . Это НЕ URL файла данных.
- **BLOCKING UNKNOWN:** точный official single *.csv.gz URL, имя файла/member и документированный единственный (Hostname,DiskNumber). Их нужно предъявить и зафиксировать до разрешения загрузки, не угадывать. Expected version/checksum фиксировать, если опубликованы; иначе null, actual byte-version/SHA256 устанавливает E002 при stable EOF и фиксирует до E003.
- Предлагаемое правило выбора ДО просмотра contents/labels: первый по bytewise-лексикографическому имени из official list отдельно доступных single-volume *.csv.gz; сохранить список/выбранное имя. Если выбранный файл непригоден/слишком велик — STOP, не переходить к следующему по качеству.
- Если official single gzip отсутствует и предлагается all-traces/multi-GB archive — STOP до нового решения. Не скачивать весь архив ради member; не применять скрытую синтетическую замену, локальные all-W не переименовывать в read trace.
- Человек должен принять условия SNIA Trace Data Files Download License v2.0 (текст/актуальность проверить до доступа) и подтвердить право локального использования/сохранения. Агент не принимает terms от его имени.
- G0 также требует inventory OS/CPU/свободных RAM/disk/Python/packages и проверку cap enforcement, inspected first-party code, secret-free exact dependency/config freeze и отдельное execution permission. Сейчас hardware/dependencies/code/enforcement UNKNOWN.
- Предпочтительно streaming download без automatic retry: HTTP размер/тип проверить, runtime byte counter обязателен даже без Content-Length; gzip должен быть одним CSV, не tar/zip/HTML, без исполнения third-party code.
- Полностью проверить gzip integrity, compressed SHA256 и decompressed SHA256 при EOF под caps; не считать partial gzip успешным. Stream decompression/parse, не держать файл в RAM; запрет записи в existing dataset/raw.
- Выбранный member должен содержать только один подтверждённый volume; неожиданное смешение volumes — STOP без фильтрации/pooled fit. Schema/units/time conversion, Read/Write tokens и полноту записи сверить с документацией и содержимым.
- Timestamp переводить в elapsed seconds от первого issue event t0 по документированной Windows filetime scale; точную реализацию конвертации проверить и заморозить, timezone не изобретать. Nonmonotonic timestamps — STOP, не сортировать задним числом.
- Prefix фиксирован ДО labels: первые [t0,t0+21600 s), т.е. 6 часов. Нужен первый event на/после правой границы либо документированное recording end≥границы; не растягивать prefix до появления hot/reads.
- Caps: ≤250000 исходных prefix requests; ≤1000000 page-request incidences (R+W); ≤10000 различных pages во всём prefix; ≤1024 pages/request; line≤4096 bytes. Превышение — STOP, не выбирать subset pages и не делать более короткое окно complete.
- Prefix может быть короче cap по requests, но обязан покрывать все 6 часов; немой tail без подтверждённого recording coverage — censored/STOP. Corrupt/malformed/missing/неизвестный op/Size≤0/отрицательные поля — STOP, не silently drop rows.
- Сохранить исходные row/request IDs; точные одинаковые строки без документированного duplicate ID НЕ дедуплицировать (могут быть реальные requests). Доказанная дублированная экспортная запись/неясный порядок — STOP для разбирательства.
- E002 создаёт split/mask manifest, past-only features и offline labels раздельно; val/test labels не предъявлять человеку/модельному подбору на suitability gate. Read existence/schema/coverage/caps — только пригодность, не quality-driven selection.
- Train-only gate: ≥1000 selected train examples и все 3 класса представлены; counts сохранить. Если отсутствуют reads/класс/coverage или нарушены caps — negative suitability/inconclusive forecast, без другого trace/threshold/модели и без fit.

## 4. Численный бюджет, все попытки включены
| Предлагаемый этап | Wall / aggregate CPU time | RAM / threads | Data/storage |
|---|---|---|---|
| E002 inventory + single access + decompress + prep + unit checks | ≤600 s wall, ≤300 s CPU; сеть внутри него ≤120 s | ≤1 GiB whole process tree, ≤2 threads | Download≤100 MiB; decoded bytes≤1 GiB |
| E003 fixed classifier comparison, checks, scoring, reports | ≤300 s wall, ≤300 s CPU | ≤1 GiB whole process tree, ≤2 threads | Новых downloads=0 |
- Итого ≤15 min wall, ≤10 CPU-min; суммарный новый disk footprint E002+E003 ≤1536 MiB, включая partial files, gzip, decoded/derived, logs/models; existing artifacts не входят и не изменяются.
- E002 sublimits: access≤120 s wall, decode/integrity≤180 s, inventory+parse/prep/tests≤300 s; общий CPU cap имеет приоритет. E003: full tree fit≤90 s, ablation fit≤90 s, predict/baselines≤75 s, checks/metrics≤45 s.
- Local CPU only, no GPU, paid services, training APIs, installs или remote compute. Download разрешается только E002 после G0; E003 offline. Это рекомендованный потолок, не известная feasibility.
- До запусков проверить watchdog wall/aggregate CPU, process-tree memory/thread и disk/byte counters (например поддерживаемая локальная isolation/cgroup + application counters); RLIMIT_AS не выдавать за whole-tree RAM cap. Если enforcement недоступен — STOP.
- Timeout/crash/cap/no disk/неполный manifest → failure/partial и STOP, не сравнивать unfinished model по F1, не autoextend/retry/redesign. Сохранить уже полученные negatives/failures в новом E-ID после permission; не удалять их ради storage cap, остановиться заранее.

## 5. Fixed temporal splits, causality и минимальная модель
- Elapsed minutes: train [0,180); gap [180,200); validation [200,260); gap [260,280); test [280,360). Gap events не используются вообще; reset U/history в 0/200/280 min одинаков для всех методов.
- Warmup первые 10 min каждого сегмента, затем decision grid от start+10 до end−10 включительно с шагом10: train 17, validation5, test7 decisions. History/future целиком внутри своего сегмента; split metadata фиксируются до labels.
- U растёт только внутри данного сегмента; test не наследует train pages/tables. Learned tree frozen после train, без online fitting. Val/test feature history естественно обновляется прошлыми issue events своего сегмента, но не чужими labels.
- Ни vocabulary/global normalization по полному trace, ни pooled streams. R001 локально исключён дизайном: один volume/one pipeline/common time cuts, no other inputs; проверить split manifest и непересечение исходных events между сегментами. Исторический R001 остаётся open; формальное закрытие review не делается.
- Features (4 scalar): read-count last600s, read-count last300s, write-count last600s, min(time since last read,600)/600; отсутствующий прошлый read →1. Counts доступны только прошлым issuance; recency clipped, no future completion.
- LPN/Hostname/row ID/timestamp-as-ID/адресные embeddings не входят в model. Namespace/page используются только для счёта, join и audit; это не physical mapped universe.
- Proposed implementation: sklearn DecisionTreeClassifier(max_depth=3, min_samples_leaf=50, criterion='gini', splitter='best', max_features=None, class_weight=None, random_state=42); остальные default параметры явно записать после inventory/version freeze.
- X: один fit по 4 features. Ablation A: один такой же tree по read-count last600s, чтобы отделить дополнительную историю от learned count thresholds. Никаких NN, grid search/early stopping/validation fishing; tuning budget=0 configs сверх этих 2 fixed fits.
- Z: cold/warm/hot по прошлому read-count last600s с ТЕМИ ЖЕ 0 / 1..2 / ≥3 thresholds; равные H, U, masks и splits. Diagnostic D: always-cold на том же U. Baselines не учатся, не получают меньшего покрытия или lookahead.
- Train cap=50000: выбрать min(50000,Ntrain) минимальных SHA256 ключей canonical UTF-8 `train|decision_tick|hostname|disk|page`, tie-break по tuple; выбор без labels/stratification/class balancing, алгоритм/encoding frozen. Не заменять seed, если cold доминирует.
- Eval — ВСЕ U(t), без subsampling/class filtering: ≤100000 примеров отдельно val/test; ≤300000 generated examples суммарно до train cap. При caps выше ожидаемые максимумы 170000/50000/70000; фактические support UNKNOWN.
- Ограниченная training выборка экономит память/CPU; полной evaluation cold mass и unseen coverage сохраняются. Записать train count до/после cap, class support выбранного train и всех eval, universe sizes/never-read/zero-history strata.
- Один seed42, 2 fits, 1 evaluation pass validation и test для всех 4 методов; test не переиспользовать. Порядок predict фиксирован Z,D,A,X, shared cached features; runtime только diagnostic, не SSD outcome и не speed competition.
- Validation — sanity report, НЕ выбор победителя/threshold; после его качества не менять запуск test. Для causal/implementation failure STOP (не «плохой F1»); poor validation остаётся результатом, без redesign. Test release входит только в отдельное G2 approval.

## 6. Controls, анализ и критерии исхода
- После permission нужны unit tests на маленьких handwritten fixtures (не synthetic benchmark/substitute): aligned/cross-boundary pages, один multi-page request, повторный request, tie timestamps, t-boundary, write-only seen page, unseen default, censored tail/reset/gaps.
- Инварианты: ни feature event≥t; count600≥count300; U из past R/W; labels только [t,t+H); zero future count=cold только complete; все future/read IDs учтены ровно по overlaps; методы оцениваются на идентичных keys.
- Leakage control: изменение future ops/addresses в fixture не меняет U/features/predictions при t; изменение label files не меняет train sample keys. Проверить отсутствие features с LPN-ID и overlap train/val/test input events.
- Main report: 3×3 confusion (true rows, predicted columns cold/warm/hot), per-class support/predicted counts/F1, macro-F1=(F1cold+F1warm+F1hot)/3 для Z,D,A,X; ΔX−Z первичная, ΔX−A дополнительная ablation.
- Если 2TP+FP+FN=0, computational F1=0 для fixed 3-class macro; явно пометить absent class. Recall без true support и precision без predicted support — NA, не молчаливый perfect/zero; missing-class macro не интерпретировать как полноценное трёхклассовое качество.
- Отдельно hot precision/recall, coverage/unseen и cold counts (§2), per-decision confusion/support, zero-history/never-read seen strata, masked/censored counts, train sample fractions, runtime/peak resources/failures. Не взвешивать основной macro-F1 по поддержке классов.
- Supportive exploratory signal: completed valid run, ≥1000 eval examples в каждом val/test, ≥20 true examples каждого класса в каждом из них, test ΔX−Z≥0.05 и обе hot метрики X≥Z−0.05 (NA не проходит). Это предложенный practical screen, не significance/доказательство H005.
- Negative для этого screen: при тех же valid/support условиях Δ<0.05 или hot guardrail нарушен; если X≤Z — отдельно нет observed learned advantage. Даже positive против Z не означает преимущество дополнительных features, если X≈A.
- Inconclusive: недостаточный/missing support, NA hot comparison, censored/непригодные данные, cap/failure/leakage. Всё наблюдённое сохранить; отсутствие класса — не универсальная непредсказуемость. Не «чинить» thresholds/splits/trace для красивого баланса.
- Internal validity: утечки, unequal masks, issuance visibility, недоказанные duplicate records; construct: logical counts≠co-access/mapped reads/SSD gain; external: один старый enterprise volume и short prefix; conclusion: n=1, dependence, missing classes, deterministic subsample/temporal drift.
- Альтернативы успеху: stationarity, train/test похожие phases, простое learned count thresholding; абляция и Z различают часть объяснений, но не доказывают causal mechanism или переносимость.

## 7. Reproducibility, approval и runnable gaps
- При native read 2026-10-01 raw/ содержал только E001: **planned E002=access/preparation, E003=classifier comparison**, пока свободны; перед созданием recheck, при занятости STOP/reassign явно. Никакие run directories сейчас не создаются.
- После permission новые raw/<E-ID>/: manifest/config/logs/status/exit code/timestamps/commands, source URL/license receipt, compressed/decoded hashes, prefix endpoint/IDs, split/mask manifest, support/coverage/confusions; сохранить negative/failed/partial. Адреса локально, не публиковать raw.
- Manifest: protocol/config/code hashes, repository commit/dirty state, CPU/RAM/OS/Python/exact package versions/dependency lock, seed/thread environment, resource enforcement/usage, input provenance/schema/conversion, output checksums; unknown поля не выдумывать.
- Proposed scripts/config paths для будущего разрешённого implementation: experiments/scripts/temperature_prepare.py, temperature_compare.py; experiments/configs/temperature-poc-v0.1.json; derived outputs отдельно experiments/processed/<E-ID>/ с input/script hashes. Сейчас этих новых artifacts/inspected scripts нет.
- НЕКОМАНДЫ ЗАПУСКА, лишь placeholders интерфейса: `python3 -B <inspected_prepare_script> --config <frozen_config> --run-id E002`; затем `python3 -B <inspected_compare_script> --config <frozen_config> --run-id E003`. URL/лимиты/lock/enforcement входят в config/wrapper; эти строки сейчас не executable instructions.
- G0: human selection numerical design + official exact single URL/volume/list + license acceptance + inventory/code/config/limits freeze и execution permission; можно отдельно разрешить bounded inventory без сети. Dependencies UNKNOWN; missing packages или changed deps → дополнительный checkpoint, не install автоматически.
- G1: approval ТОЛЬКО E002 budget/access/prep, с точными source/командой/wrapper. По его завершении предъявить suitability, masks, train support, hashes и расход; suitability pass НЕ approval training.
- G2: отдельное human approval frozen numerical protocol/config, E003 budget/2 fits и single validation+test release, с inventory/dependency/code gates пройденными. Затем только разрешённое исполнение; никаких auto-transitions.
- Перед любым пересмотром сохранить versioned copy и dated deviation/rationale/approval ДО новых runs; существующий документ/raw не переписывать. После увиденных outcomes новая гипотеза/анализ exploratory, не confirmatory. Local freeze не public time-stamped preregistration.
- Для выбора человеком: рекомендуемый H/history/step10min, k2, tree3; альтернатива — сначала только E002 suitability и отказаться от fit; иные H/labels/linear model требуют новой заранее согласованной версии, не подбора после результатов.
- Рекомендация checkpoint сейчас: принять/изменить числа и бюджет, разрешать поэтапно **только подготовку после закрытия точного доступа/лицензии/inventory/code gates**. E003/H005 efficacy/system experiment не approved; approvals и findings в этом документе отсутствуют.
