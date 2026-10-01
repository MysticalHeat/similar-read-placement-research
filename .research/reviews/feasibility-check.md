# Независимая быстрая sanity-рецензия — 2026-09-30
Один короткий проход; объект — условная feasibility, не статья, исследование или approval. Записан только этот файл; прежние reviews сохранены.
Scope: question-feasibility.md, hypotheses-feasibility.md, claims/evidence-map.md, experiments/dataset-profile-summary.md и raw/E001/{profile,manifest}.json; simulator-audit.md §§3–6.
Контекст прочитан: README/brief, условный protocol, предыдущий R001, literature/papers.jsonl и public-data-options.md; analysis/draft — пустые шаблоны, не результаты.
Независимо сверены сохранённые числовые поля E001 с таблицей summary: rows/first_tokens W = 515114 и 2427089, field_counts=3, blank/comment=0, eof/stable=true, status=complete; manifest exit_code=0.
Это сверка артефакта, не повторный подсчёт: dataset/ не читался, hashes не пересчитывались, исполнение/пиковая RAM не проверялись. Сети, shell, scans, training и новых runs нет.
S013: осмотрены локальные цитаты кода в audit, не полный первичный исходник; S003/S016 — локальные записи поддержки, не независимое открытие первоисточников. Архивы S016 не доступны для проверки здесь.
Итог: в текущих feasibility-формулировках не выявлено подмены условного механизма наблюдаемой эффективностью; отсутствие finding не устанавливает валидность.
Findings: новых R002+ нет; major/minor дефект формулировок в этом scope не установлен. R001 остаётся open для возможного будущего pooling/split, не проверялся заново и не разрешён.
Механизм ≠ efficacy: question:5–8,13–16 и hypotheses:2–9,12–14 явно отделяют INFERENCE/H004 от измеренного gain и учитывают migration/GC/inference.
Next-write ≠ read: question:11; C006/C007/S013; audit:64–78,109–117 — allocation block/offset против l2p read mapping; улучшение next-read не следует из writing pointer.
Ready concurrency/resources: question:6–7; hypotheses:5–6; audit:139–152 — прогноз не создаёт готовый demand; независимость ресурсов ограничена шинами/командами, serial elapsed не тестирует overlap.
Literal ≠ semantic: question:9–10; summary:5–10; C014/E001 — весь профиль W, но смысл/units/preprocessing UNKNOWN; вывод «нет read labels под схемой R/W» не равен доказанному write-only исходнику.
Toy ≠ benchmark: question:16 и hypotheses:14 прямо ограничивают synthetic sanity; логический пример или заранее заданный паттерн не свидетельствует о реальном SSD gain.
Docs ≠ downloads: question:12; C015/S016; public-data-options:55–68,94–105 — задокументированная схема, не проверенные архивы, read fraction, predictability или provenance локальных CSV.
Сильнейший контраргумент: точный прогноз может ничего не дать при последовательной зависимости reads; при overlap миграция/общая шина могут съесть всю экономию. Выгоду также может дать простой layout/scheduler без learned predictor.
Различающая будущая проверка через оркестратора, не запуск: одинаковые arrivals/cache/scheduler и caps; обычный layout, forecast без migration, простая causal migration и learned migration в проверенной concurrent model; считать useful demand MiB/s, overlap и все затраты за один горизонт.
Отрицательный контроль — строго зависимые reads без overlap; эффект без дополнительного overlap не поддержит именно заявленный механизм. Сейчас reanalysis не требуется: performance результатов нет.
Блокеры эмпирического вывода: подтверждённая read/mixed trace с units/order/access; physical control и concurrent completion correctness; заданные cost horizon/caps. Остаточные риски: переносимость, простые baselines, causal history и novelty не установлены.
Безопасно новичку: «Идея условно возможна: если несколько чтений уже готовы, их размещение позволяет реальное перекрытие, а выигрыш больше затрат переноса. Здесь ускорение не измерено; прогноз сам по себе параллелизма не создаёт».
