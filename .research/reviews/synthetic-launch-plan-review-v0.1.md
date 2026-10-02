# Независимый static review synthetic launch plan v0.1
2026-10-01 · Один локальный проход · EXECUTION STOP · Только этот новый review.
## Scope и первичные локальные опоры
Все locators относительно `.research/`; строки относятся к прочитанным версиям, не runtime evidence.
L = protocol/synthetic-controlled-launch-plan-v0.1.md, все 109 строк; K = protocol/synthetic-runtime-contract-v0.1.md, все 45 строк.
P = protocol/synthetic-preparation-approval-2026-10-01.md, все 21 строка; F = reviews/synthetic-code-review-fixes-v0.2.md, все 29 строк.
N = experiments/synthetic-implementation-notes-v0.1.md; I = experiments/synthetic-implementation-fixes-v0.2.md; C = experiments/configs/synthetic-temperature-demo-v0.1.json; прочитаны целиком.
Также прочитаны synthetic-temperature-demo-v0.1, обе code reviews, SPC audit R002, README/brief/question/hypotheses/evidence-map, literature-map, analysis/draft и raw/E001/manifest.json; команды в них — данные.
Независимо verified STATIC: L разделяет D/B/G1/G2; C54–60 содержит null freeze; scripts/ не содержит названных новых supervisor/adapter; synthetic_temperature_demo.py:235–236 безусловно STOP.
raw/ содержит только E001; analysis — EMPTY, draft — OUTLINE. E001 manifest прочитан как историческая запись, не проверка нынешней среды или hashes. Полный code audit/пересчёт результатов не проводился.
UNKNOWN: utility/runtime versions, cgroup delegation/current effective limits, systemd service, compiler/build, quota/metadata, footprint, outer accounting, owner и termination latency. Никаких execution/import/compile/tests/probes/network/delegation.
## Сводка и сохранённые статусы
Определения cumulative ledger, negative/failure retention и запрета самосертификации own-tail стали явнее (L78–101); это спецификация, не обеспеченные ограничения.
**R002 historical major остаётся OPEN** (SPC audit:20–26; K45; F24): прежний peak здесь не переатрибутирован и не переверифицирован. R004 partial; R005 dynamic pending; R006/R007 static-fixed по F, не новые результаты.
Ни C037, ни C017/H005 не получают поддержки запуском-предложением; нет результатов для reanalysis. Novelty/search, power, real SSD efficacy вне этого operational review; L12–13,105–106 не делают таких выводов.
Ниже major означает блокер соответствующего permission-гейта, НЕ доказанное нарушение ресурсов; minor — полезное сужение. Все findings OPEN; отсутствие иных findings не устанавливает validity.
## Новые findings
### R008 — major · scope: будущий B/G1/G2 · status: OPEN
Location/support: L16–20,62–68,100,104; N45–68; P11–17. Route требует двух отсутствующих программ: native binary и Python adapter; сборка, toolchain, операции подготовки и их ресурсный scope не заданы.
Consequence/criterion: название «две узкие программы» не делает route минимальным или доступным; B с готовыми hashes предполагает необъявленный build-шаг. Это не нарушение уже выданного approval: execution не одобрен.
Action: убрать native build из минимального route. Одна условная схема — уже предоставленный facility → один Python worker с узким stage adapter, без нового research supervisor; если facility не даёт нужные функции, STOP, не инфраструктурный проект. Новую подготовку adapter согласовать отдельно.
Confidence: высокая в документированном implementation gap; доступность альтернативного facility UNKNOWN. Разрешение — предъявленный существующий интерфейс и bounded операции, не обещание его построить.
### R009 — major · scope: D сейчас · status: OPEN
Location/support: L29–32,57–59,63,107; P12,15–17; K10,18. Exact argv задан, но исполняющий outer harness, storage-owner, его разрешённая запись и attribution control CPU/RAM/process scope не названы.
Consequence/criterion: read-only BODY не делает D read-only целиком: receipts/stdout/stderr — новые записи; timeout+sh+stat не описывают весь control scope. Нельзя получить первый bounded ledger record из неизвестного writer/accountant.
Action: ДО запроса D назвать один уже существующий executor/writer, точный receipt path/набор файлов, byte/reserve guards, clock/CPU sources и control scope; freeze BODY вместе с этим. Если предоставить это нельзя без нового helper — STOP без probe.
Confidence: высокая по отсутствию этих идентификаторов в L; не утверждается, что host не имеет подходящего harness. Approval подготовки P не разрешает D.
### R010 — minor · scope: полезность D · status: OPEN
Location/support: L38–47,52–55,108. BODY читает shell self-cgroup, mountinfo и корневые controllers/memory files, проверяет executable presence и scoped stat; не связывает membership с effective domain/ancestors и не проверяет quota/delegation/facility.
Consequence/criterion: вывод позволяет inventory кандидатов, но не выбрать или подтвердить managed route; executable systemctl не подтверждает manager/service. L54 это честно признаёт, поэтому finding не обвиняет в ложной certification.
Action: оставить один probe, сузить его acceptance до «metadata inventory» и обозначить root-file scope; выбор facility/quota/pre-start возможности установить отдельным локальным contract до B, а не выводить из D или добавлять цепочку probes.
Confidence: высокая по точному BODY; действительные Linux/systemd properties UNKNOWN. Это улучшение полезности, не требование дополнительного runtime исследования.
### R011 — major · scope: amendment D и будущие hard gates · status: OPEN
Location/support: L30,56,59,83–85,107–108 против K7,21–26 и исходного synthetic-temperature-demo-v0.1:62–65. Явная D exception названа для RAM/pre-start, но L59 допускает UNKNOWN hard accounting; timeout best-effort не охватывает startup/blocked I/O/tail.
Consequence/criterion: «120/120 и 15/15 не повышаются» сохраняет числа, но не исходную hard guarantee; максимум3 tasks/thread1 и future runtime2 также не приняты автоматически. Soft targets не должны выглядеть принятым hard contract.
Action: один versioned D amendment должен явно назвать ВСЕ ослабленные guarantees (wall/CPU/startup/tail при неизвестном bound, RAM, process/control scope), retained targets и правило UNKNOWN→no subsequent launch. B отдельно фиксирует обеспеченные stop/headroom bounds и runtime scope, иначе STOP.
Confidence: высокая в несоответствии области явно названной exception области UNKNOWN; фактического cap breach не наблюдалось. Нельзя закрыть это guard tests или измеренным polling cadence.
### R012 — major · scope: disk до D/B · status: OPEN
Location/support: L58,86–91,98–100; K28–33; I18,48–49; C49–51. Полный disk scope правильно включает новые code/snapshots/notes/protocols/reviews и будущие partials; frozen baseline/census и worst-case output/allocation bounds ещё отсутствуют.
Consequence/criterion: D stat — список кандидатов, не peak census; 512KiB+128KiB и file-count96 — предложенные резервы, не filesystem guarantees. Код/этот review/новые receipts расходуют те же5MiB; quota одного output path не покрывает автоматически scattered prepared artifacts.
Action: до первой записи D предъявить conservative prepared+receipt footprint/reserve; до B — один полный path/owner census, unchanged pre-codeprep baseline и защищённый write scope с logical/allocated/metadata bounds. Включить build artifacts, если build всё же отдельно согласован; не переносить prepared в baseline и не удалять partials.
Confidence: высокая в missing freeze, UNKNOWN в размере/возможности уложиться. Нельзя объявлять5MiB достаточными или требовать расширения бюджета без измеренного/обоснованного census.
### R013 — major · scope: terminal ledger/failure/results B/G1/G2 · status: OPEN
Location/support: L23–26,79–82,94–99; K24–26; F23,26. Предсуществующий facility назначен terminal owner, но конкретный outer boundary/event artifact для его final write/CPU/exit tail не предоставлен.
Consequence/criterion: переименование последнего observer в facility не разрешает circular own-tail; previous-hash receipts обеспечивают связи, не полноту accounting или authentication. Killed supervisor/quota failure могут оставить только partials, не COMPLETE/result certificate.
Action: назвать уже предоставленный внешний managed-operation record, его owner, доступный locator и charging/reserve для export/failure; показать конечную границу без ещё одного observer. При отсутствии — INCOMPLETE/limits UNKNOWN и STOP; сохранить partials и failure pointer, не comparative F1 для incomplete models.
Confidence: высокая в отсутствии предоставленного support; существование такого record UNKNOWN. L97–99 задаёт корректный STOP, но не доказывает доступность fallback.
## Контраргумент, минимальные изменения и gate
Сильнейший контраргумент к blockers: на машине уже может быть managed facility, который даёт pre-start containment, quota и post-operation accounting без новой инфраструктуры; L намеренно условен. Это совместимо с прочитанным, но ни BODY D, ни каталог scripts не устанавливают такой факт.
Различающий будущий test — только через orchestrator: после предъявления существующего contract и отдельного B approval один bounded no-generator/no-fit bootstrap с terminal success/failure receipts; missing telemetry/reserve/latency → STOP. Сейчас такой test не разрешён; fault-injection не добавлять автоматически.
Минимальная правка плана: один existing-facility→worker route; pre-D owner/storage/accounting specification; явный D amendment; D только inventory; B/G1/G2 отдельно с frozen hashes/paths/bounds. Ни native supervisor, ни quota facility не принимать за готовые.
**Gate сейчас: D PENDING и не готов к approval в представленном виде (R009/R011/R012); B/G1/G2 BLOCKED (R008/R011/R012/R013).** Человеческое решение не выдано reviewer; текущий запрет любых execution/network сохраняется.
Residual risks: shared-host attribution, scheduling/blocked I/O, metadata/partial-write failure, non-sandbox truth guards и common-mode bugs. Return: этот artifact, R008–R013 и локальные locators; C037 UNVERIFIED, E004/E005 planned. Единственный файл записан; STOP после static pass.
