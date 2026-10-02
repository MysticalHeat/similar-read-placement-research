# Practical caller v0.1 — PREPARATION ONLY / EXECUTION STOP
2026-10-02. Ownership: только этот NEW note и NEW scripts/synthetic_practical_caller_v0.1.py.
Режим practical принят; execution НЕ разрешено. Reference flag не permission token.
Основа: protocol/synthetic-practical-runtime-amendment-v0.2.md §§3–7, README decision58,
brief, claims/evidence-map.md C037, adapter483/fixes68/review46; старые файлы untouched.
README/amendment принимают режим; конец brief/C037 сохраняет историческое PENDING.
Здесь это раскрыто, не исправлено: integration принадлежит orchestrator.

## Реализован только будущий bootstrap
- Exact flags: --stage bootstrap --approval-ref <реальная ссылка на отдельное решение>.
- USER_BOOTSTRAP_PENDING/пустой/placeholder reference → STOP/return2 ДО Writer/записей.
- E004/E005 имеют отдельные stage values, но всегда BLOCKED до записи/загрузки.
- Exact sys.executable=/usr/bin/python3, -B/-S; отсутствующий executable — invocation error,
  NO FALLBACK. Существование/version сейчас UNKNOWN; эта команда НЕ выполнялась:
```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_practical_caller_v0.1.py --stage bootstrap --approval-ref USER_BOOTSTRAP_PENDING
```
- Один stdlib caller/worker, same process/thread, no children/threads/framework/supervisor.
- time→first monotonic marker/process_time→stdlib imports→soft main-thread SIGALRM.
  Imports/parse до установки alarm входят в observed interval, но не прерываются им.
- own sys.version/executable, os.uname, stdlib module origins; no env/auth/git/network/proc.
  CPU hardware/RAM hardware/revision/dirty state/thread count/compiler details unresolved.
- SCOPED в caller = adapter25–30; E004_EXTRA=oracle/tests; caller/amendment тоже hashes.
  Census prepared text/code hashes как DATA; config exact UTF-8 bytes в freeze.
  Никаких compile/exec/import production/adapter/models/oracle/tests/fixtures/generation/fits.
- dependency lock=[] (no third-party); environment spec в freeze + exact observed runtime.
  Это не hash-lock установленной stdlib и не защита от недоверенного runtime/import hook.

## Учёт и soft STOP
- CPU charge=absolute process_time: initial preclock CPU включён ОДИН раз; wall от FIRST_WALL.
- Bootstrap initial previous=null допустим только в pristine single-use practical namespace.
  Занятый/частичный namespace STOP; retries/budget reset запрещены, failed outputs остаются.
- inventory15/15 включает bootstrap finish; work12/12 + внутри него reserve3/3 до15.
  Phase/global checks кооперативные; soft alarm absolute wall12 затем absolute15, не renew.
- RAM=getrusage SELF ru_maxrss Linux KiB×1024; worker target1GiB, global wall/CPU120.
  Phase targets15/35/40(each10)/15/15 записаны; E004/E005/fit origins НЕ реализованы.
- Ledger current inventory, totals_at_entry=[0,0], prior_phase_used=[0,0], origin=[0,0].
  Будущая origin=totals_at_entry−prior_phase_used, не свежий cap; новый fit index только1..4.
  Через stages нужны linked cumulative snapshots без double charge/human live wait; BLOCKED.
- Pre-exit ledger/receipt НЕ self-complete; startup wall, final-write/own-exit/tool tail null.
  No whole RAM/time/disk certificate, remaining=null; R002/R004/R005/R014 не закрыты.

## Conservative disk scope / writer
- ЦЕЛИКОМ README/brief/claims; scripts synthetic*/test_synthetic* включая recursive snapshots;
  configs synthetic-*.json; protocol/reviews synthetic-*.md; experiments synthetic*/test_synthetic*.
- control synthetic*/test_synthetic* recursive (включая practical); raw/E004,E005 и
  processed/E005 только если существуют, включая будущие partial/failures. Ancestor dirs counted.
- E001/dataset/documentation/legacy raw/прочие unchanged files исключены; не читаются.
  Никаких фиктивных pre-CODEPREP дельт. Bounded enumeration≤256, total entries+future≤256,
  каждый regular file≤2MiB; missing prospective dirs допустимы, symlinks/unclear types STOP.
- logical и st_blocks×512 дедуплицированы по device/inode; metadata estimate512/entry.
  Directory allocation counted; future dir/each-file rounding estimate4096, НЕ hard bound.
- Normal aggregate64KiB/3files + failure8KiB/1file; future directories≤3; stdout≤2KiB
  резервируется как1 capture entry+4096 estimate; actual tool capture/metadata UNKNOWN.
- used+remaining future payload+rounding+metadata≤5MiB отдельно logical/allocated.
  Census preflight, перед/после каждого write batch; не на каждом loop sample; no quota.
- Только future control/synthetic-practical-v0.2/bootstrap-001/ exclusive; parent control
  при отсутствии создаётся, practical/bootstrap exclusive. Ownership сразу после mkdir до fsync.
- freeze.json→receipt.json→ledger.json, each xb/write/fsync once; failure.json best-effort.
  Full census/hash list or STOP (no truncated success); SHA256 links exclude self checksum.
  Primary/secondary + owned mkdir paths в bounded stdout; no delete/rewrite/retry.
  Preownership/crash/write/alarm failures могут не дать record: pointer UNKNOWN, nextstage STOP.

## BLOCKED / handoff
E004/E005 intentionally absent: captured adapter binding, stage reservations/linked ledger,
G1 review/G2 E004 manifest hash and prediction-before-truth path требуют limited future addition.
Никакого автоматического перехода/full negative suite. IDs E004/E005 remain PLANNED.
Этот проход: native reads/apply_patch only; команды/import/compile/tests/probes/gen/fits=0.
После единственного save — native read обоих resulting files, затем STOP; syntax UNVERIFIED.
