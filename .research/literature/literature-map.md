# Карта литературы: предварительный скопинг SSD

Status: INITIAL BOUNDED DISCOVERY COMPLETE WITH ACCESS LIMITATIONS, 2026-09-30. НЕ систематический обзор, НЕ завершённая проверка новизны. Семь записей источников; два полных HTML-текста доступны библиотекарю, три pivotal support passages независимо проверены оркестратором в S003/S009/S010. Нет воспроизведённых результатов.

| Направление | Источники | Значение для идеи | Ограничение |
|---|---|---|---|
| SSD layout and scheduling | S001/S002 metadata; S003 full-text | C001: пространственные и временные условия операций, FTL и планирование | S003 — контроллерное scheduling, не предсказание будущих чтений; архитектура из старой работы |
| Storage read prediction/prefetch | S007 abstract; S006 unresolved lead | Возможный вариант: предсказание будущих блоков и префетч | Нет проверенной end-to-end latency оценки для нашего контекста |
| Memory-prefetch methods | S008 abstract | Концептуальные методы и baselines | Не SSD, не доказательство переносимости |
| Predicted placement for invalidation/GC | S009 full-text; S010 abstract | C002/C003: размещение по ожидаемой инвалидизации для WA/write throughput | Цель отличается от read-page prediction; нельзя переносить результаты |
| Direct near prior work | S005/S012 unresolved leads | read-driven allocation / backend-aware prefetch worth checking | Первичные тексты и метаданные не подтверждены, novelty check неполон |

## Механизмы — не смешивать
1. Prefetch: раньше прочитать ожидаемые данные в кэш; меняет момент чтения, не обязательно физическое размещение.
2. Placement: при первоначальной записи или переносе выбирать размещение будущих совместно читаемых страниц; требует определённых возможностей FTL/эмулятора/интерфейса. Реально доступные пользователю возможности UNKNOWN.
3. Scheduling/grouped transaction: одновременно предъявлять подходящие запросы контроллеру. S003 §§2.1–2.2 и 4.2 показывают, почему имеет значение не только адрес, но и время поступления.

Writing point остаётся пользовательским неопределённым термином. Page может означать логический блок либо NAND page; размер UNKNOWN. Не утверждаем, что термин не существует или имеет единственное определение.

## Что поддержано и что нет
- C001/C004: в описанной Sprinkler архитектуре физические координаты и своевременное предъявление запросов важны; plane sharing имеет конкретные ограничения. Совместная группа по нескольким planes/dies не равна концентрации всех страниц на одном последовательном ресурсе.
- C002/C003: SepBIT и DOGI — близкие по идее прогнозирования размещения, но прогнозируют инвалидизацию; их цели WA/WAF и запись, не наша read latency.
- Пользовательская причинная цепочка «next read prediction → writing point → ускорение чтения» остаётся HYPOTHESIS, без прямой проверки для заданной нагрузки.
- Точность предсказания сама по себе не является доказательством ускорения: это методологический риск, требующий end-to-end оценки, а не отдельный результат найденных статей.

## Метрики и сравнители для обсуждения (предложения, не протокол)
Prediction precision/coverage and timeliness; demand-read latency and throughput; CPU/RAM prediction cost; extra reads/writes and WA. Для placement: обычная политика, одинаковая политика без прогнозов, oracle только как недостижимый upper-bound diagnostic. Для prefetch: без prefetch и простые последовательные/корреляционные методы. Определения и независимые единицы не выбраны.

## Пределы покрытия и следующий шаг
8 запросов библиотекаря (1 HTTP 429), 12 fetches (4 unreadable PDFs, 1 HTTP 403), затем 3 независимые проверки оркестратора. Не выполнен запрошенный минимум трёх полнотекстовых первоисточников. Не проверены доступность/лицензии traces, ZNS/FDP semantics, современная NAND и точные близкие работы S005/S012. Нет основания утверждать «такого ещё не делали». Выбор вопроса должен учитывать эти пробелы и ресурсы пользователя. Следующий шаг — методологические альтернативы и human checkpoint, не запуск.

## Уточнение после выбора throughput и конкретного репозитория
2026-09-30: добавлен S013, первичный исходный код FTLSim-MiDA commit a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21. Не научная публикация и не validation report; восемь retained source records теперь включают repository source. Статическая source evaluation — experiments/simulator-audit.md; точные claims C006–C010. Writing points означают next-write allocation; reading uses l2p. Есть read/migration time accounting, но последовательное, без требуемого concurrent timeline. Это ограничивает пригодность кода для выбранной цели parallel read throughput, не опровергает гипотезу на реальном SSD. Novelty evidence не добавилось. Dataset audit/learning-task design — отдельный следующий milestone; extension/replacement timing model требует решения пользователя.

2026-09-30: S014/S015 — локальные CSV, provenance/schema/version/license ещё неизвестны, только sample/metadata access. Claims C011/C012: первые 120 строк каждого имеют W; C013: native R/r line-start search без совпадений. Source evaluation в experiments/dataset-audit.md и claims/dataset-screening.md. Не установлены полный op mix или отсутствие чтений; пригодность next-read labels — обязательный data gate в draft protocol v0.1. Это данные аудита, не новые научные findings/novelty evidence. Если документация/full profile подтверждает отсутствие reads, запросить исходные read/mixed traces вместо подмены вопроса.
