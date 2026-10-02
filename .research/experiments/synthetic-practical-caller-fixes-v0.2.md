# Practical caller fixes v0.2 — STATIC ONLY / EXECUTION STOP
2026-10-02. Один author pass по reviews/synthetic-practical-caller-review-v0.1.md R018/R019.
Ownership: active caller + NEW immutable snapshot + этот NEW note; closure решает reviewer.
Сначала полностью прочитаны review55/caller348, native проверены scripts/versions/experiments.
ДО active edits сохранён полный caller348 в
`scripts/synthetic_preparation_versions/caller-v0.1/synthetic_practical_caller_v0.1.py`;
snapshot полностью прочитан, сопоставлен с исходным текстом; byte hash НЕ вычислялся.
Snapshot сохраняет старые defects; больше не редактируется, не является runtime evidence.

## R018: предложенная correction
- checked требует существующий directory PROJECT без symlink, запрещает lexical `..` escape.
- Только root и ancestors/leaf ниже PROJECT: ни PROJECT.parent, ни follow-first exists.
- FileNotFoundError любого below-root component → None при missing=True; root missing STOP.
- Каждый existing intermediate symlink/non-dir STOP; leaf symlink тоже STOP.
- census.add опирается только на checked; base/control/practical predicates тоже checked/stat.
- Обычный CONTROL missing при existing experiments работал раньше; обратного не заявляем.
- Это не OS sandbox/race immunity; существование текущих prospective paths не измерено.

## R019: предложенная correction
- error_record сохраняет FULL primary reason для единственной failure.json write; failed
  str(error) явно UNAVAILABLE. Никакого silent character truncation durable reason.
- failure slot всё ещё8KiB: слишком большой полный payload → reporting failure, no retry;
  detailed durable pointer тогда UNKNOWN. Secondary хранится в памяти/summary, не дописывается.
- stdout reason preview≤64characters, type≤24, явные reason_omitted/type_truncated flags.
- encoded bytes проверяются против2048 ВНУТРИ formatter handler; overflow → explicit OMITTED
  fallback с fixed fields, owned/durable pointer и primary/secondary types≤24characters.
- Два type strings worst-case non-BMP: 2×24×12=576 escaped bytes плюс fixed ASCII fields/paths;
  fallback encodedlen тоже проверяется. Последний fixed emergency literal<256bytes с UNKNOWN.
- Formatter failure не выходит traceback; первичная ошибка не заменяется success (return2).
- Единственный unbuffered os.write(stdout): short/error→return2, no second write/flush/stderr.
  Primary retained; actual external delivery/persistence UNKNOWN, не certificate.
- Alarm cancellation защищена handler; при ошибке nonzero, имеющийся primary сохраняется.

## Неизменное / handoff
Normal64KiB + failure8KiB + stdout2KiB, disk5MiB/census/phase/RSS targets не расширены.
NEW snapshot/note входят в прежний recursive synthetic disk scope; footprint UNKNOWN.
Original notes/reviews/state/protocol/config/adapter/core/raw untouched; no control/raw dirs.
Placeholder по-прежнему отвергается ДО writes; B001 proposed, real dated human approval absent.
E004/E005 BLOCKED, no automatic transition/tests/gen/fits; remaining/tail UNKNOWN.
Commands/import/compile/tests/probes/network/agents/hash computations executed=0.
После edits — полный native read active caller/этого note, затем STOP; syntax/dynamic UNVERIFIED.
R018/R019 author correction ≠ independent closure; R002/R004/R005/R014 не закрываем.
