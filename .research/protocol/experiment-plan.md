# Условный план: проверка данных и будущий пилот предиктора

Version: v0.1, 2026-09-30. Status: CONDITIONAL DRAFT — NOT APPROVED / NOT EXECUTABLE.
Разрешена подготовка аудита/дизайна на локальной машине; shell/Python full profile, обучение, installs, network и simulator execution НЕ разрешены. Ни один этап ниже сам по себе не даёт permission.
Связь: question.md v0.2 Q-C/H001 — будущий exploratory development pilot; Q-A/H002/H003 — только дальнейшая перспектива. Это НЕ confirmatory системный эксперимент и НЕ публичная регистрация.
README/brief фиксируют делегированный выбор useful demand-read MiB/s primary и IOPS secondary; question/hypotheses ещё содержат неутверждённые альтернативы. Этот план предлагает уточнения, не изменяет H-ID или их статус; согласовать операционализацию до обучения.

## Основание и текущие блокеры
C011/S014 и C012/S015: в строках 1–120 dataset/hm_0.csv и dataset/prxy_0.csv виден начальный W; это sample only (experiments/dataset-audit.md §§2–3).
C013/S014,S015: native поиск ^[Rr][ \t]+ не вернул совпадений (claims/dataset-screening.md, строки 7–15). Это НЕ полный row validation и НЕ доказательство all-write; labels/encoding/whitespace/семантика UNKNOWN.
C010/S013: FTLSim-MiDA, commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21, проверенное serial timing не устанавливает parallel-throughput gain (experiments/simulator-audit.md §§4–6; claims/evidence-map.md).
Происхождение, preprocessing, единицы адреса/длины, chronology, license/access, hashes, hardware и точный deadline UNKNOWN. «Короткий срок» не является численным бюджетом. Runs/E-ID/обученных моделей/измеренного throughput нет.

## Gate 1 — пригодность данных, без обучения
До разрешённого profiling запросить source/version и схему: значения operation tokens, адрес и длина с отдельными единицами, sector/page size, device/queue namespace, preprocessing/фильтрация и сохранение исходного порядка.
Подтвердить право локального использования/лицензию, ограничения приватности и доступ; traces/адреса не отправлять в сеть. Имена файлов не устанавливают происхождение или независимость.
Условный локальный streaming profile обоих файлов: validate encoding/разделитель/число полей/op codes/числовые поля, op mix, malformed/missing rows, bytes/EOF row counts и SHA256; только агрегаты, без выгрузки raw строк/адресов.
Бюджет profile ПРЕДЛОЖЕН, не разрешён: max 120 s суммарного wall-clock на оба файла и inventory, RAM max 512 MiB; Python stdlib only, no network/install, no writes в dataset/, без неограниченных словарей уникальных адресов.
После отдельного permission проверить код и доступность enforcement лимитов; собрать CPU/доступную RAM/OS/Python inventory без secrets. Скрипт, команды и механизм лимитов сейчас отсутствуют; разрешение shell отдельно от scientific approval.
Hash/profile должны охватывать целые неизменившиеся файлы; если EOF не достигнут, timeout/RAM limit/ошибка/изменение входа — сохранить partial/failed status, не объявлять полный профиль или окончательный op mix. Лимит автоматически не увеличивать.
Проверить наличие реальных read events по документированной schema, не только буквальному R. Подтвердить chronology из источника/времени; если доступен лишь порядок событий — явно ограничить задачу event-order prediction, без physical timeliness/parallelism выводов.
Gate проходит только после документированных units/schema/provenance/access/read labels/order, полной проверяемой профильной записи/hashes и inventory; несовместимый/частичный профиль остаётся блокером.
Если подтверждено отсутствие reads — STOP next-read study на этих файлах, запросить original read/mixed traces. Не менять target на next-write, не реконструировать/фабриковать read labels и не выбирать удобный фрагмент как обход.

## Gate 2 — выбор learning task и design approval
Только при Gate 1: кандидат target — start address СЛЕДУЮЩЕГО READ REQUEST либо его start-page при документированной гранулярности. Это один target на request, не искусственный порядок развёрнутых страниц внутри multi-page запроса.
Зафиксировать единицы/namespace, общий поток или queue/device, момент прогноза, допустимую историю reads/writes, горизонт и связь request IDs; прогноз использует только доступное к решению прошлое. Target ещё не выбран.
Предложение split: chronological 60/20/20 train/validation/test по каждому подтверждённому stream; все доли awaiting approval. При недоказанной chronology — только отдельно согласованный event-order split/ограничение, не выдуманное время.
Labels и input windows никогда не пересекают split boundaries; граничные примеры маскировать, количество/причину сохранять. Предлагается одинаковый reset history на начале split для всех методов; window length и cold-start/evaluation mask зафиксировать заранее.
Не разделять файлы на train/test по именам: проверить общее происхождение/namespace/дубликаты. Два файла НЕ доказаны независимыми. Fit vocabulary, нормализации, feature statistics и frequency/transition tables — только train.
Unseen/OOV targets в validation/test не удалять ради accuracy: заранее определить representation, fallback/abstention и оценивать по истинному адресу; ошибочный/отсутствующий top1 считается ошибкой. Не сводить все unseen адреса к одному «правильному UNK».
Если cardinality/labels/representation не помещаются в caps либо unsupported OOV мешает задаче — отложить архитектуру, запросить решение; не объявлять viable classifier до профиля и не менять target молча.
Baselines: last-read-address, causal last-stride, frequency и transition; одинаковые доступные features/history, target/masks/splits. Определить stride/fallback и ограничения таблиц до pilot; tuning только validation, сопоставимые заранее распределённые budgets, без test-lookahead.
Small learned model рассматривается после profile/inventory; architecture/framework пока deferred. Зафиксировать модель, features, representation, loss, hyperparameters/search space, config count, seeds/RNG и stopping rule; совместимость с существующим локальным окружением проверить, installations не разрешены.
До training нужны: выбранные target/units/data rules/splits/masks/OOV, архитектура/параметры/зависимости, baseline parity, run matrix/seeds, enforceable caps, finite budget/точный срок и записанное human approval. Этот draft не готовая команда запуска.

## Gate 3 — будущий validation-only exploratory pilot
Бюджет ПРЕДЛОЖЕН, approval/feasibility PENDING: local CPU, max 10 min cumulative wall-clock для всех pilot preprocessing/training/tuning/baseline/evaluation attempts, RAM max 2 GiB, max 2 threads; no GPU/paid services/network/install.
После inventory caps могут быть снижены до исполнения; не обещаем, что хотя бы один fit завершится. Число конфигураций/повторов и распределение общего времени ещё не заданы; никакого запуска до отдельного approval.
Pilot: train только train, development scoring только validation; test не расходовать для выбора модели/параметров/architecture. Профиль пригодности не должен подгонять модельные statistics/vocabulary по test.
Test никогда не используется для model selection; scoring возможен только после финального выбора модели/параметров и отдельного frozen approved protocol. Ни этот draft, ни validation pilot не разрешают test evaluation. Validation results exploratory, не подтверждение H001.
Synthetic checks, если отдельно разрешены, — только exploratory проверки pipeline, не реальные read labels и не способ пройти data gate; их успех не подтверждает предсказуемость пользовательских traces.
Primary prediction metric ПРЕДЛОЖЕНА: top1 exact NEXT-READ accuracy = correct predicted target / все eligible next-read examples, с согласованными masks и OOV/abstention как ошибками. Optional hit@k — отдельно, только после fixed k; не неоднозначные precision/recall для одного target.
Это уточнение single-request pilot относительно неутверждённого precision@k кандидата H001; принятие согласовать до training, не менять hypotheses.md здесь. δP/action thresholds/cost caps ещё PENDING, эффект не предполагается.
Показывать per-stream/file numerator/denominator, paired validation accuracy differences learned−baseline, OOV/mask/missing counts и CPU/RAM/cost; не скрывать отрицательные результаты. Inference speed — стоимость, НЕ throughput SSD.
Кандидат unit of inference — подтверждённый workload/trace; events/windows зависимы, два файла не «n=2 независимых реплики». Pilot описательный, без mechanical p-values/гарантий power; uncertainty/generalization ограничить доступными traces и validation reuse.
Контроль: одинаковые target/eligible rows/history/cold start, train-only fit и budgets; признаки не используют future labels. Seeds/порядок запуска/background load/dependency versions до исполнения фиксируются; без shuffle chronology, retries не выбирать по успеху.

## Stopping, failures и будущая воспроизводимость
При истечении общего времени/RAM/thread cap, malformed input, inconsistent units, missing read labels, file change или невозможности обеспечить лимиты — STOP; failed/partial/negative attempts сохранить, не заменять скрыто и не считать завершёнными.
Не удалять rows/OOV/outliers по качеству прогноза. Правила malformed/missing/duplicate/boundary/cold-start exclusions утвердить заранее, публиковать aggregate masks/completeness; если данных недостаточно — отложить обучение, не invent sample size.
Только после execution approval каждый запуск получает новый E-ID и отдельный experiments/raw/<E-ID>/ без overwrite: timestamps/command/exit/status/logs, input hashes, code commit/dirty state, config/model/RNG/dependency hashes, environment/caps и измеренные затраты. Здесь E-ID не создаются.
Сырые dataset/ неизменны; logs/outputs локально в новых разрешённых artifacts, адреса/идентификаторы/credentials не публиковать. Processed outputs отдельно с input/run/script pointers; сохранение агрегатов не означает запись в dataset/.
Dataset/config/model/RNG/dependency hashes, runtime и run commands сейчас UNKNOWN; утверждённого protocol checksum/frozen plan нет. Повторяемость по seed не равна независимой репликации.

## Будущий системный endpoint — отдельный, заблокированный этап
Выбор оркестратора по делегированию пользователя: primary useful demand-read MiB/s = успешно завершённые полезные demand bytes / 2^20 / simulated completion makespan(s); secondary demand IOPS = успешно завершённые исходные read requests / тот же makespan. Ничего не измерено.
Не включать internal NAND/GC/copy reads в числитель, skips считать неуспехом; частичные host requests не равны full-page payload. Inference throughput, accuracy и WAF не замена этому endpoint.
C010 блокирует parallel-throughput вывод: требуется отдельно выбрать/проверить concurrent timing model (расширение текущей либо другой проверяемый simulator), ресурсы/общие шины/команды, arrivals/dependencies/load/concurrency и одинаковый scheduler/cache/warmup.
Дальнейший comparator — обычный layout без proactive migration; разделить forecast без миграции и простую causal migration с равными action/tuning budgets. Учесть source read+destination write, inference, mapping correctness, GC/free space и migration tail в согласованном timeline/horizon.
Migration tentative; useful δT, confidence/action thresholds, write/WA/CPU/RAM caps, workload/repetitions/independent units и cost horizon PENDING. Predictor pilot не проверяет H002/H003 и не доказывает SSD gain; prefetch/next-write не подменяют placement/next-read.

## Validity, approvals и версии
Internal: unequal tuning/budgets/cache/history/selection; construct: неверные units/labels/artificial page order и accuracy≠throughput; external: неизвестное происхождение и узкие traces/модель; conclusion: зависимые events, OOV/exclusion bias и validation overfitting. Возможный learned gain может быть только sequentiality/memorization; baselines нужны для различения.
Смысловой сигнал/параллелизм и эффект UNKNOWN; механизм C005 не доказательство. Novelty unresolved S005/S012. Ни отсутствие буквального R, ни незначимый/неточный pilot result не доказывают универсальную непредсказуемость.
Approval: preparation only; profiling permission/budget, Gate 1 acceptance, task/protocol/training budget, test release и systemic timing route — PENDING отдельными решениями. Все numerical splits/caps здесь предложения помощника, не выбор пользователя.
Следующий checkpoint: источник/schema/preprocessing/license, подтверждение reads/order и отдельное permission на ограниченный read-only Python profile; уточнить точную дату deadline. До этого STOP, без shell/обучения.
v0.1 заменяет пустой неутверждённый шаблон; question/hypotheses и их архивы не изменены. Перед изменением approved/frozen версии сохранить её и deviation/date/rationale до новых runs; post-hoc изменения exploratory. Ни frozen checksum, ни публичной регистрации сейчас нет.
