# Synthetic stage adapter corrections v0.2 — STATIC ONLY / launch STOP
2026-10-01. Один bounded author pass по review R014–R017; closure решает reviewer.
Прочитаны review64 строки и исходный adapter425; parent dirs проверены native read.
ДО edits сохранён полный snapshot425 в
`scripts/synthetic_preparation_versions/adapter-v0.1/synthetic_stage_adapter_v0.1.py`;
прочитан полностью и сопоставлен с исходным текстом, без вычисленных hashes.
Snapshot больше не редактируется. Original notes/reviews/state/claims/config/core unchanged.
Ownership: active adapter + этот NEW fixes note + NEW UNRUN test specification + snapshot.

## R014: proposed source binding correction
Session отвергает cache names P/M/O/T до callbacks и повторно после initial checkpoint.
Каждый scoped source читается один раз; hash и computational exec используют captured
bytes одного чтения. `bound_source` — маленький helper ModuleType/compile/exec, future
runtime ONLY; exact project-derived canonical path, no sys.path search/pyc/import loader.
Module регистрируется до exec для dataclasses; failure STOP с retained cache, no retry.
E004 loading order P/M/O/T; T aliases проверяются на те же bound P/M/O objects.
sample/guard/toy/stages используют bound references, no bare computational imports.
E005 читает/загружает ТОЛЬКО P/M, не O/T; pretruth inputs/release порядок не меняется.

## Обязательный exact caller loading contract — не реализованный launcher
Caller должен быть отдельно inspected/frozen/approved и contained до startup;
trusted exact stdlib/runtime/import policy и protected read-only frozen sources обязательны.
Caller читает approved adapter source из exact absolute project/SCRIPT path, сравнивает
SHA256 с внешним freeze, создаёт fresh ModuleType с __file__=этому path, регистрирует
под отдельным fresh именем, compile/exec ИМЕННО captured bytes, не import/pyc/sys.path.
Context adapter_loading={path: exact absolute path, sha256: frozen digest,
mode: 'captured-source-no-cache'}; Session проверяет path и совпадение с frozen file hash.
Это declaration/path check, НЕ proof того, как caller загрузил adapter, human approval,
authenticity или OS sandbox. Самостоятельный self-hash такого proof не даёт.
Не модифицировать source bytes/runtime code для freeze; disk sources protected externally.
Trusted callbacks не должны подменять globals/modules/source/cache или читать withheld truth;
защита от злонамеренного callback/stdlib import hook этой library НЕ предоставляется.

## R015/R016: proposed receipt/namespace corrections
record snapshots outputs/attempted ДО callbacks; принимает только новый успешно
persisted nonreserved файл текущей invocation. Point single-use включая failures;
point→filename links сохраняются в local manifest и failure payload.
Writer exact reserved name↔slot predicate двунаправлен ДО charge/attempt/open:
обычный put не может занять manifest.json/failure-001.json; mismatched slots STOP.
Explicit reserved slots нужны только internal finish/fail; trusted callback policy это сохраняет.
Freshness не подтверждает содержание receipt, telemetry completeness или permission.

## R017: proposed primary/partial retention correction
Writer constructor без I/O; Session публикует object ДО create(). Successful mkdir
ставит created=True ДО sync; exclusive mkdir failure не даёт ownership.
fail пишет только в свой newlycreated dir; existing чужой root никогда не используется.
Handlers best-effort report_failure, затем bare raise ПЕРВИЧНОГО exception.
Secondary error сохраняется на Session и primary.failure_reporting_error; add_note
если доступно, fallback attribute иначе, external_failure_pointer=None/UNKNOWN.
Если custom exception запрещает оба механизма, primary всё равно сохраняется;
outer trusted owner обязан сохранить primary/secondary из facility/session diagnostic scope.
I/O/hard crash могут исключить durable failure receipt: external pointer UNKNOWN,
не обещание успешной записи. No retry/delete/overwrite; COMPLETE-looking partial
manifest при outer exception не означает успешного run без external failure review.

## UNRUN specifications / unchanged scientific and resource gates
NEW scripts/test_synthetic_stage_adapter_v0.1.py: stale caches, callback preload,
wrong hash/path/loading contract, captured-vs-disk/provenance, E005 no O/T,
fresh/reused/no-write/failed receipts, reserved slots, primary/secondary/reserve,
mkdir-sync/occupied-root. Только small test stubs/mock I/O/temp fixtures, no generator/fits.
Это НЕ E004 TOYS; separate runtime/test/disk permission нужен, не включать незаметно.
E004 checklist11/8toy/0benchmark и E0054fits/no tuning остаются прежними.
Все prepared+NEW snapshot/tests/fixes входят в5MiB logical/allocated+metadata scope;
footprint/reserves/feasibility UNKNOWN. Guards soft, original hard accounting gates STOP.
Commands/imports/compile/tests/probes/gen/fits/network executed=0, hashes/results отсутствуют.
После save — полное native static read resulting files, затем STOP; dynamic UNVERIFIED.
Main безусловно STOP, shell/launcher отсутствуют; LOCAL_WORKER_COMPLETE не global certification.
C037 UNVERIFIED; R002/R004/R005/R008–R013 не закрываются этим author pass; H005 deferred.
