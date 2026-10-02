# Synthetic code preparation fixes v0.2
2026-10-01 · CODEPREP ONLY / EXECUTION STOP. Один локальный fix pass.
Прочитаны synthetic-code-review-v0.1.md целиком (52строки), текущие P/M/T,
config/notes v0.1 и runtime contract v0.1. Review/contract не изменялись.

## Сохранение v0.1 ДО активных правок
Native read каталога scripts подтвердил отсутствие synthetic_preparation_versions;
native read experiments подтвердил отсутствие этого нового fixes-документа.
Затем apply_patch создал точные read-content copies в новый каталог:
`scripts/synthetic_preparation_versions/v0.1/`:
- synthetic_temperature_demo.py (236строк);
- synthetic_models.py (146строк);
- test_synthetic_temperature_demo.py (193строки).
Все три snapshots целиком прочитаны ДО следующего apply_patch активных файлов.
Snapshots больше не редактировались. Это сохранение текста, не computed hash audit.
Config72/notes79/expectation-module v0.1 оставлены на прежних путях без изменений;
вместе со snapshots они сохраняют исходную подготовительную версию.
Snapshots — тоже новые prepared artifacts для будущего disk ledger, не baseline.

## R006 — предложенное исправление реализации
P.validate теперь явно отвергает timestamp<0, сохраняя int-only (не bool),
chronology/ties, distinct IDs, endpoint-exclusive и прежний ValueError message.
Новый literal test_R006_direct_Event_recording_bounds: -1/-2/endpoint/endpoint+1,
bool/non-int, empty ID, malformed endpoint; 0 и distinct-ID ties legal;
CSV literal acceptance0/rejections согласованы с direct Event domain.
Никаких generator/window/model/recipe изменений.

## R007 — предложенное исправление реализации
BudgetGuard._coordinates проверяет tuple/list exactlen2, built-in int/float,
не bool, finite/nonnegative/[0,120); копирует coords в tuple без caller mutation.
__init__ проверяет callable sample, fixed integer phase caps15/35/40,
phase/optional fit origins и fit>=phase coordinatewise, НЕ вызывает sampler.
check проверяет current тем же domain predicate, current>=phase/fit origins,
nondecreasing current, затем phase/perfit caps по ОБЕИМ coords через range(2).
Нет zip truncation/negative elapsed escape. Global120 и perfit10 неизменны;
прежние cap/error strings сохранены, новые origin errors явно отделены.
UNRUN literal tests: len1/len3/empty/nonfinite/negative/bool/non-numeric/outsidecap,
fitbeforephase/futurefit, callable/cap predicates, wall-only и CPU-only breaches,
nonmonotonic samples, valid near-cap/origin equality и mutable-origin detachment.
Все добавленные проверки — спецификации, НЕ наблюдённые результаты.

## Статический handoff / оставшиеся gates
После правок native READ активного source/tests и notes; без Python/import/tests.
Безусловный fail-closed entrypoint сохранён; runner/launcher/OS probes не добавлялись.
BudgetGuard остаётся injected application check, НЕ watchdog/cgroup/RAM/disk limit.
R004 domain acceptance, pre-start containment, observer tail, disk quota/reserve,
runtime/code/config/hash freeze, immutable I/O и durable truth release ещё pending.
Snapshots/новые tests/notes учитываются будущим logical+allocated5MiB ledger;
расход и feasibility UNKNOWN. Никаких cleaning/limit extensions/fallbacks.
Команд исполнено0; exit codes/hashes/manifest/run results отсутствуют, tests UNRUN.
R006/R007 formal closure — independent reviewer/orchestrator, не автор fixes.
C037 остаётся UNVERIFIED; raw/manifests/state/claims/protocol/reviews unchanged,
E004/E005 не создавались и не разрешены. Метод/caps/генератор не менялись.
