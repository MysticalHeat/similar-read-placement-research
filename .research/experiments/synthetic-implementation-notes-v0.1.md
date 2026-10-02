# Synthetic implementation v0.1 — только подготовка
2026-10-01. First-party stdlib; никаких execution/import/compile/tests/probes/network.
Прочитаны plan все76строк, approval, reviewR004/R005, README/brief/C037.
Исторические draft-PENDING в C037/README superseded только preparation approval;
техническая корректность C037 остаётся UNVERIFIED. Протокол/state не редактировались.

## Владение и статическая схема R005
- scripts/synthetic_temperature_demo.py: Event, validate/parse_csv/generate_csv,
  pages/past_features/future_counts/count_label, mask_reason/grid, feature_table,
  label_table/truth_and_audit, metrics/score_release. Только чистые in-memory функции.
- scripts/synthetic_expectations.py: EXPECTED_GRIDS/MASKS, recipe_expectations;
  отдельная формула цикла/Random42 replay и собственная классификация counts.
  Нет imports production/model, shared label/window/reset/count helpers отсутствуют.
- scripts/synthetic_models.py: exact Fraction CART, BudgetGuard, train_case,
  prediction_payload. Нет imports generator/trace/oracle/config/filesystem.
- scripts/test_synthetic_temperature_demo.py: ручные F0/F1–4/Fcross/Faligned/
  Fties/Funseen/FboundaryU/Fcensor/Fmutation/Freset, threshold2, STOP domains,
  recipe per-page/bin и decision keys/labels, split/gap, CART toys, metrics/guards.
- configs/synthetic-temperature-demo-v0.1.json: versioned prospective recipe,
  empty third-party lock, stdlib/runtime exact version UNKNOWN, hashes null.
  Notes — этот файл. Все файлы новые; никаких иных write ownership нет.

Generator возвращает целый CSV до parse/count. Production scans issue timestamps
и byte overlaps, а oracle получает только имя recipe, не events/CSV/features.
Fixtures содержат literal expected feature/count tables. Expected grids перечислены,
mask expectations ручные; oracle не вызывает и не копирует production mask algorithm.
Ни oracle, ни IDs/time/phase не входят в bare matrix Cart.fit/predict.
Модель хранит frozen Node; повторный успешный fit запрещён. Mutation/reorder toy checks
используют те же деревья, без refit. Toy fits не входят в четыре benchmark fits.

## Будущий data access / artifact contract — НЕ реализованный runner
E004 после G1: сначала exclusive raw directory и bounded write CSV; потом parse,
validate, causal feature files ОТДЕЛЬНО от label/oracle/check files. Проверить полную
recipe/fixture agreement, masks, shared keys, mutation/reorder до разрешения G2.
E005 сначала проверить complete immutable E004 manifest/input hashes, отдельное G2
и свежую containment/ledger receipt; затем load ТОЛЬКО past features/train labels.
Два train_case (cycle,negative), по A/X, итого четыре fits. Stable train rows decision,page.
prediction_payload без truth; exclusive durable commit обеих val/test predictions
для всех cases ДО открытия любых val/test truth. После commit scoring val→test,
Z,D,A,X; no refit/tuning. E005 никогда не открывает expectation tables.
score_release требует одинаковые keys и один case/split; unseen/coverage отдельным
truth_and_audit, no future union. All cases/negative/failed outcomes retain.
Эти интерфейсы уменьшают coupling, но не доказывают disk access separation.

## R004: точные незакрытые gates
Entrypoint БЕЗУСЛОВНО STOP; flags/receipt сами по себе не user approval.
Не существует готового launcher/artifact adapter; runnable freeze UNKNOWN.
Нужен независимо согласованный новый runtime contract methodologist, затем:
1. Проверенная containment ДО Python startup/inventory, fresh dedicated cgroupv2
   per stage, memory.max≤1GiB, swap0, Threads1/no children; launcher scope/accounting.
2. External watchdog и remaining cumulative active-wall/aggregate-CPU ledger
   E004+E005, startup/overhead/finalization included, human G2 wait excluded по contract.
3. 15/35/40/15/15 phase caps, четыре≤10s fits и global120s приоритет; BudgetGuard
   лишь injected prospective checks before/after/in loops, НЕ watchdog/measurement.
4. Whole-domain memory.current/peak/cpu.stat, phase attribution, полный external
   post-exit accounting; pre-exit snapshots НЕ final certification. Нет RLIMIT_AS/
   ru_maxrss замены, root/cgroup writes/spawn/systemd/секретов.
5. Logical И allocated newdisk≤5MiB включая подготовленный код/config/tests,
   все trials/partials/enforcement; bounded writer/reservefailure/ledger UNKNOWN.
6. Freeze executable/runtime/stdlib, inspected hashes/protocol/config/revision,
   exact approved commands, G1 отдельно и G2 после E004 review. Bootstrap UNKNOWN
   требует своего permission/containment; никаких auto retries/extensions/fallbacks.

Не реализованы stage I/O, exclusive dirs/writes/final manifest/checksums, logging,
permission/receipt authentication, cgroup native checks, disk enforcement, durable
prediction-before-truth release и автоматический four-fit/event-total ledger.
Приоритет дан inspectable pure functions + tests и безопасному безусловному STOP,
как разрешено заданием; это implementation gap, НЕ выполненный pipeline/изменение метода.
Никаких E004/E005 dirs/data/results/hashes сейчас нет; E002/E003 reserved, E001 immutable.

## Воспроизведение / handoff
Команд исполнено: НОЛЬ; exit codes/run IDs/manifests/checksums измерений отсутствуют.
Тесты НЕ запускались; даже syntax/importability и количественная feasibility unverified.
После отдельного разрешения review/freeze/runtime test gate предложенная команда
из scripts/: `<frozen-python> -B -m unittest test_synthetic_temperature_demo`;
НЕ runnable-approved command сейчас, trials тоже требуют caps/новых immutable artifacts.
Stage commands отсутствуют намеренно: direct entrypoint только блокирует запуск.
Reviewer проверяет R005 separation и toys; orchestrator согласует R004/gates,
затем versioned implementation дополнение до ANY run. Интерпретация — analyst.
