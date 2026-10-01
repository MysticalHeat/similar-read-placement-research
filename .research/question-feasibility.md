# Быстрая оценка принципиальной возможности
PROVISIONAL v0.1, 2026-09-30; scope — несколько минут, не обучение или большой эксперимент; approval вопроса/эффекта PENDING.
Вопрос: на выбранной нагрузке с повторяемыми reads может ли обучаемый causal next-read predictor с предварительным размещением/переносом страниц повысить useful demand-read MiB/s против обычного размещения с простым causal predictor, при одинаковых workload/concurrency и полном учёте затрат?
Система/популяция пока не выбраны; предполагаемое вмешательство — physical placement/migration, НЕ prefetch и НЕ next-write prediction. ANN не обязательна; класс модели не выбран.
Цепочка (INFERENCE): прогноз → своевременное размещение → меньше конфликтов между готовыми чтениями → concurrent service → net throughput; каждое звено может не сработать.
Необходимые условия: предсказуемые повторения; физический контроль layout по независимым ресурсам с допустимыми командами/общими шинами; несколько одновременно готовых outstanding reads. Предсказание само по себе не делает будущий demand-запрос готовым.
Выгода требует амортизации переноса за согласованный горизонт: extra writes, GC, inference и конкуренция могут превысить экономию. Ни co-location, ни spreading не гарантируют ускорения.
Endpoint: полезные bytes успешно завершённых demand-read / 2^20 / согласованный completion makespan(s); IOPS вторичная. Internal copies не числитель, accuracy/WAF/inference speed не throughput; unit вывода — workload/trace, не отдельные запросы.
EVIDENCE C014/E001, experiments/dataset-profile-summary.md: стабильный полный EOF; hm_0.csv — 515114 строк, prxy_0.csv — 2427089, каждая с первым token W. По R/W схеме симулятора reads нет; semantic provenance/preprocessing/units/license UNKNOWN.
Эти файлы не дают next-read labels под указанной схемой. Это не доказательство, что исходная трасса до preprocessing была write-only; ничего не восстановлено или обучено.
C006/S013: writing_pointers — next-write allocation blocks, не next-read targets. C010/S013: текущий serial timing не проверяет parallel-throughput gain (simulator-audit.md §§4–6).
C015/S016: первичная документация MSR Cambridge описывает Type Read/Write, bytes и issue/completion timing (README §3); архивы не скачаны. Это возможный будущий источник, НЕ provenance локальных файлов и НЕ evidence эффективности.
Контрпримеры: строго последовательные зависимые reads не дают overlap; независимый случайный доступ не даёт полезного прогноза; частая миграция может уменьшить throughput даже при верных прогнозах.
Вердикт: условный механизм логически возможен, реальный gain UNVERIFIED; novelty не установлена (S005/S012 unresolved), универсального ускорения не заявляем.
Рекомендация сейчас: сформулировать механизм и условия; позже при отдельном решении взять реальную read/mixed trace и проверенную concurrent timing model. Предыдущий training plan отложен по сокращённому scope пользователя.
Синтетический повторяемый паттерн — только sanity check заранее заданных предпосылок, не эмпирическая правдоподобность для реального SSD. Новых runs/поисков/approvals здесь нет; актуальный C014 заменяет прежний неполный screening, несмотря на устаревшие blockers в README.
