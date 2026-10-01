# Hot/warm/cold: прогноз будущей read-категории
PROVISIONAL v0.2, 2026-09-30; TARGET INTENT CONFIRMED / OPERATIONALIZATION PENDING; few-minute conceptual scope.
Пользователь подтвердил: категории ПО ЧТЕНИЯМ, прогноз БУДУЩЕЙ категории, группировка для использования параллелизма SSD. Это approval направления, НЕ H/thresholds/model/layout/protocol/budget или efficacy.
Концептуальный вопрос: повышает ли прогноз будущей read-категории hot/warm/cold с ресурсно-осведомлённым размещением/переносом страниц useful demand-read MiB/s относительно обычного размещения и той же политики с простой исторической частотной эвристикой при одинаковой нагрузке и полном учёте затрат?

## Target и pipeline — предложения для операционализации
Кандидат label: число/частота чтений страницы в будущем окне H → hot/warm/cold по количественному правилу; H (время/события), page unit, thresholds, момент решения/переклассификации UNKNOWN. Частота не равна времени до следующего чтения или co-access.
Pipeline: доступная история каждой страницы → future-class predictor → resource-aware placement/migration decision layer → scheduler готовых запросов → оценка net throughput. Классификация и физические действия — отдельные компоненты; модель/архитектура/код не выбираются.
Features — только прошлые read counts/recency и иная разрешённая история; future labels доступны только offline при подготовке/оценке, не deployment predictor или scheduler. Описательные past-frequency labels не выбранный future target; write-hot не proxy read-hot без evidence.
Правило labels/H фиксировать до оценки; thresholds fit только train, выбор модели/параметров на validation, test не для настройки. Temporal history/label windows не пересекают splits; chronology/overlap streams проверить. Тертили/равные thresholds/balanced classes автоматически не задавать.
Задать page universe из доступного на момент решения состояния, например mapped pages или исторически наблюдавшихся страниц; не выбирать только страницы, прочитанные в будущем. Для ещё не наблюдавшихся страниц нужна отдельная causal/default policy и отчёт покрытия.
Never-read/cold страницы возможны; исключение их исказит class support. Нулевые reads в полном H могут задавать cold по согласованному правилу; неполное окно на конце trace — censored, не автоматически cold. Размер universe и masks ещё не выбраны.
Три класса сокращают output representation, но predictive difficulty/качество UNKNOWN; ANN не необходима и преимущество обучения не предполагается.

## Logical groups ≠ independent hardware resources
Три логические class groups/write frontiers не означают три независимых канала. Нельзя назначить весь hot одному ресурсу и объявить параллелизм; физическая policy должна учитывать суммарную ожидаемую request load, capacity и баланс ресурсов, соблюдая NAND command/shared-bus constraints.
Hotness не определяет совместно запрашиваемые страницы и temporal overlap. Для parallel service нужны уже готовые outstanding reads и scheduler; прогноз категории не делает будущий demand-запрос готовым и не разрешает подать его раньше зависимости.
Нужно отдельно формализовать class→destination, causal migration triggers/caps и mapping correctness; полезность требует своевременности, reuse и амортизации source-read/destination-write/GC/inference за согласованный горизонт.
C006/S013, MiDaFTL.py L19,58–72,78; simulator-audit.md §3: next-write pointers и четыре migration-count groups не являются готовой новой трёхклассовой read-policy.

## H005 — retained, PROPOSED; efficacy UNVERIFIED
Гипотеза: на нагрузке с предсказуемой будущей read-temperature causal hot/warm/cold predictor и своевременная resource-aware placement/migration policy повысит useful demand-read MiB/s относительно ОБОИХ сравнителей — обычного размещения и той же resource-aware policy с простой past-frequency threshold heuristic — при сопоставимых budgets и полном учёте затрат.
Mechanism (INFERENCE): class-driven decisions могут уменьшить конфликты готовых reads и позволить overlap. C001/C004/S003 §§2.2,4.2 поддерживают лишь пространственные/временные условия описанной архитектуры, не результат H005.
Comparators/controls: обычный layout той же модели; simple heuristic при той же policy/action caps. Фиксировать workload/arrivals/concurrency, scheduler/cache, occupancy/GC, mapping и tuning budgets; gain от изменения scheduler не приписывать predictor. Прогноз без миграции — возможное разделяющее сравнение.
Null: net throughput не выше хотя бы одного comparator; useful δ/cost caps ещё PENDING. Свидетельство против — достаточно точная оценка исключает useful gain, нет заявленного overlap либо затраты убирают gain; неточная оценка оставляет неопределённость.
Контрпримеры: зависимые serial reads, hot pages на одном busy resource, drift/ошибки labels или migration/GC/inference доминируют. Категории сами не доказывают causal mechanism; universal speedup/novelty не заявляем.
Classification отдельно: candidate macro-F1, per-class confusion matrix/support, masks/coverage/cold/unseen counts; actual class balance UNKNOWN. System endpoint отдельно: успешно завершённые полезные demand bytes / 2^20 / completion makespan(s) = MiB/s; IOPS вторичная, internal copies не числитель. Accuracy/F1/inference speed/WAF не throughput.

## Evidence, ограничения и следующий маленький шаг
C014/E001: 515114/2427089 строк локальных CSV все с token W; по R/W schema read-label blocker сохраняется. Source/units/preprocessing/order/license UNKNOWN, новых reads не создавали.
C015/S016: первичная MSR Cambridge документация описывает Read/Write bytes/time; это будущий public candidate, архивы не скачаны и локальное происхождение не установлено. C010/S013: serial timing текущего simulator не проверяет parallel throughput; нужна отдельно проверяемая concurrent model.
C017 остаётся efficacy-UNVERIFIED; прежняя пометка pending read/write intent историческая — направление подтверждено текущим checkpoint README/brief, но quantitative target/layout не утверждены. Обученных моделей, classification/throughput результатов и evidence новизны нет.
Следующий полезный шаг без запуска: формализовать H и численное правило labels вместе с page universe, затем набросать class→resource design с балансом нагрузки/ограничениями и costs. Уже подтверждённые read/future/parallelism вопросы повторно не задаются.
v0.1 дословно сохранена до ревизии в temperature-scoping-v0.1.md; H005 retained, H004/hypotheses/protocol/raw/state/evidence не изменены. Ревизия по conceptual checkpoint до efficacy results; training plan отложен, новых searches/runs/approvals нет.
