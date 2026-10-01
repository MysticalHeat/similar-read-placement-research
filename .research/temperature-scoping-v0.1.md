# Hot/warm/cold: отдельный кандидат задачи
PROVISIONAL v0.1, 2026-09-30; few-minute scoping only. H005 PROPOSED / candidate, approval PENDING, efficacy UNVERIFIED; H004 и прежние документы сохранены без изменений.
Воспоминание пользователя о предложении руководителя — контекст, не определение labels и не доказательство ускорения. Разделить две задачи: «какой класс у страницы?» и «что placement policy делает с этим классом?».

## Кандидат target, не утверждённые labels
Для цели read throughput рекомендуется обсуждать FUTURE READ FREQUENCY: сколько чтений страницы ожидается в фиксированном будущем горизонте H; hot/warm/cold — согласованные диапазоны этой величины.
Это предложение помощника, не установленный смысл hot. Page/granularity, population страниц, H (время или события), границы классов и treatment отсутствующих данных UNKNOWN; cold может означать отсутствие чтений в H, не требуется делать все страницы hot когда-либо.
Признаки — только доступное прошлое: read counts/recency/переходы и иные заранее выбранные causal features; labels — чтения в будущем окне. Время до следующего read/reuse — другой target: одинаковая частота не задаёт одинаковый момент следующего чтения.
Если labels вычисляются из той же прошлой частоты, это descriptive heuristic; модель может лишь воспроизводить правило, а не прогнозировать будущее. Write-hot не означает read-hot без проверенной связи.
До будущего теста заранее зафиксировать правило H/labels; численные thresholds fitting — только train, модель/настройки — validation, test не использовать для выбора. Окна labels/history не пересекают split boundaries; связность streams и chronology требуют проверки.
Не назначать автоматически равные thresholds/тертили и не предполагать balanced classes. Три выхода сокращают representation относительно адреса, но difficulty/accuracy/throughput UNKNOWN; архитектура модели не выбрана, нейросеть не обязательна.

## Placement — отдельная политика
Варианты для выбора: три логических write frontiers по классам либо распределение классов/страниц по независимым ресурсам. Это разные конструкции; три frontiers не означают три независимых канала или параллельную службу.
C006/S013, MiDaFTL.py L19,58–72,78; simulator-audit.md §3: существующие next-write pointers и четыре группы по migration count — НЕ готовые read-temperature классы/политика.
Нужно отдельно задать class → destination mapping, допустимые команды/общие шины, causal migration triggers, caps и обновление l2p. Сам hotness не показывает, какие страницы будут запрошены вместе и есть ли несколько готовых outstanding reads.
Сосредоточение hot pages на одном занятом ресурсе может усилить contention; простое spreading тоже не гарантирует выигрыш. Прогноз класса не делает будущий demand-запрос готовым.

## H005 — полезность class-driven placement
Гипотеза: на нагрузке с предсказуемой будущей read-temperature causal классификация hot/warm/cold и своевременная class-driven placement/migration policy повысит useful demand-read MiB/s относительно ОБОИХ сравнителей — обычного размещения и той же policy с простой исторической frequency-threshold heuristic — при сопоставимых budgets и полном учёте затрат.
Mechanism (INFERENCE): классы могут помочь allocation/migration уменьшить конфликты и улучшить обслуживание готовых reads; категории сами по себе этого не гарантируют. Для заявленного parallelism нужны независимые ресурсы, допустимые mappings и concurrent ready requests.
Контролировать workload/arrivals/concurrency, mapping correctness, cache/scheduler, occupancy/GC, action/tuning budgets и inference/source-read/destination-write costs; перенос должен амортизироваться за согласованный горизонт. При возможности разделить классификацию без migration и policy с простой heuristic.
Null: net throughput не выше хотя бы одного сравнения; practically useful δ и cost caps ещё PENDING. Свидетельство против — достаточно точная оценка исключает useful gain либо эффект исчезает после учёта затрат; неопределённая оценка оставляет вопрос открытым.
Контрпримеры: все hot pages на одном busy channel, строго зависимые serial demands, неверные/описательные labels или migration/GC/inference доминируют. Никакого универсального выигрыша или novelty не заявляем.
Classification metrics-кандидаты: macro-F1 и per-class confusion matrix, class counts/support; accuracy может скрыть majority-class prediction, но actual balance UNKNOWN. MiB/s полезных завершённых demand bytes / 2^20 / completion makespan(s) — отдельный systemic endpoint, не F1/accuracy/inference speed/WAF.

## Блокеры и минимальный checkpoint
C014/E001: все 515114/2427089 строк локальных файлов имеют token W; по R/W schema read labels нет. Переименование классов не создаёт reads; source/units/preprocessing/order/license остаются UNKNOWN.
C015/S016: публичная MSR Cambridge documentation описывает read/mixed schema, архивы не скачаны. C010/S013: нынешний serial timing не проверяет parallel-throughput. Нет trained model/classification/throughput результатов; synthetic sanity check не evidence реального gain.
Три уточнения: (1) hot означает чтения или записи, frequency/recency/reuse? (2) класс — прогноз будущего H или описание истории, как задать H/границы? (3) классы идут в три логических writing points или управляют независимыми ресурсами; какое действие для hot/warm/cold?
Рекомендация сейчас: уточнить target и class→policy, не обучать. Следующий возможный этап — реальные read traces и проверенная timing model только по отдельному решению; search/runs/protocol authorization/approvals здесь нет, прежний training plan отложен.
