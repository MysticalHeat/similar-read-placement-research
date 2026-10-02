# Один контролируемый synthetic launch: минимальный план v0.1
2026-10-01 · **DRAFT / EXECUTION STOP / human approval отсутствует** · Один статический design-pass.
Все пути ниже относительно `/home/nomli/workspace/bdss_lab/research1`, если не указано иное. Это предложение, не сертификат, runner или разрешение.

## 1. Основание и неизменный эксперимент
Прочитаны README, brief, question/hypotheses, literature-map, evidence-map C037; synthetic-temperature-demo-v0.1, preparation-approval-2026-10-01, runtime-contract-v0.1; обе code reviews и implementation notes/fixes, config и три pure modules. Только локальные источники.
Approval принимает recipe/caps и подготовку, НЕ shell/bootstrap/E004/E005. Старые draft-PENDING чисел — история; runtime-domain approval по-прежнему pending.
Опора для gaps: implementation-notes §§Future contract/R004; runtime-contract §§1–4; code-review-v0.1 §§Existing findings и fixes-v0.2 §§Remaining gates.
C037 — UNVERIFIED техническая гипотеза: causal features/READ labels, независимые expectations и общие masks/keys совпадут; любое нарушение опровергает корректность этой реализации.
Два фиксированных case: phase_cycle, independent_negative(seed42); 96 страниц, 4KiB, 6h, history/H/step600s, cold0/warm1–2/hot≥3; train/gaps/val/test/reset без изменений.
Z frequency, D cold, A count-only CART, X four-feature CART; depth3/minleaf50, четыре benchmark fits, tuning0. Нет обязательного X>Z или practical gain threshold.
Единица — целый искусственный case; страницы/окна не независимые реплики. Два case для inspectability, не power; confusion/F1/support/coverage/paired deltas описательные, без p-values/CI.
Цикл специально кодирует переходы, negative конечен; plausible mechanism не proof. H005/реальные reads/SSD throughput/новизна не проверяются; нового поиска нет.
**R002 historical major OPEN; R004 partial; R005 static addressed, dynamic pending.** Этот документ их не закрывает.

## 2. Единственный рекомендованный route и необходимые будущие компоненты
Route: заранее предоставленный managed cgroup-v2 control boundary → один native single-thread supervisor → один single-thread Python worker, E004/E005 последовательно; никаких research children/параллельных workers.
Будущие компоненты, сейчас ОТСУТСТВУЮТ: `experiments/scripts/synthetic_controlled_launch_v0.1` (native supervisor) и `synthetic_artifact_adapter_v0.1.py` (stage I/O adapter), оба под `.research/`.
Supervisor: authenticated approval/stage dispatch, ledger/phase clocks, наблюдение/termination, bounded exclusive writer, post-worker receipts; adapter: E004 preparation или E005 train→predict→commit→release→score.
Это две узкие программы, не framework; реализации/сборки здесь нет. Нынешний `synthetic_temperature_demo.py` main безусловно STOP; запускать его как runner нельзя.
Managed facility должна ДО supervisor exec настроить родительский domain: memory.max=1073741824, memory.swap.max=0, pids.max=2 (tasks/threads), без выхода/дочерних cgroups, worker forks запрещены отдельно.
1GiB — весь согласованный supervisor+worker charge, НЕ дополнительный 1GiB каждому; worker domain также не может превысить 1GiB. Bootstrap использует лишь supervisor, pids.max=1.
Предсуществующий manager/kernel/shared tool server не объявляются RAM машины внутри domain; research-specific control requests/receipt writer входят в wall/CPU/disk и отдельно объявленный RAM/process scope.
Нужен **явный process-count amendment**: вместо exact1 process — максимум2 research processes/2 threads внутри runtime domain, worker1/thread1; transient control scope отдельно в §3.
Нельзя создать containment из уже запущенного неучтённого research wrapper и назвать его pre-start. Создание/quota/service activation выполняет заранее согласованный control facility, с отдельным bootstrap approval и учётом.
Terminal owner — этот предсуществующий facility, НЕ новый третий research observer. Если его собственный хвост нельзя охватить внешней измеряемой/ограниченной границей, STOP, а не рекурсия supervisors.

## 3. Permission D: единственный discovery probe — amendment, не bootstrap
Сейчас рекомендуется запросить ТОЛЬКО D: один read-only shell probe вне неподтверждённой containment; разрешить временно timeout+sh+stat (максимум3 concurrent processes, по одному thread; env exec не добавляет постоянный process).
Amendment D явно исключает для этого probe утверждение hard whole-tree RAM/pre-start cgroup guarantee; наблюдение доступного outer harness ≠ исходная1GiB compliance. Пределы120/120/5MiB не повышаются, всё списывается в общий ledger.
Если человек не принимает такую узкую исключённую из RAM-certification область — STOP без probe. Нет автоматического второго probe, cgroup writes, systemctl, Python/model imports, generator/fixtures/fits, tests, installs/network.
Exact prospective argv: `/usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C /usr/bin/timeout --signal=TERM --kill-after=1s 8s /bin/sh -c BODY`; BODY ниже, **НЕ исполнялся**. Нет login shell, env/auth files или secrets.
```sh
set -eu
ulimit -c 0
cd /home/nomli/workspace/bdss_lab/research1
printf 'READ_ONLY_DISCOVERY_v0.1\n'
for f in /proc/self/cgroup /sys/fs/cgroup/cgroup.controllers /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.swap.max; do
  printf 'FILE %s\n' "$f"
  if [ -r "$f" ]; then n=0; while IFS= read -r line; do printf '%s\n' "$line"; n=$((n+1)); [ "$n" -lt 8 ] || break; done < "$f"; else printf 'UNKNOWN\n'; fi
done
n=0
while IFS= read -r line; do
  n=$((n+1)); [ "$n" -le 512 ] || { printf 'MOUNT_SCAN_TRUNCATED\n'; break; }
  case "$line" in *' - cgroup2 '*) printf 'CGROUP_MOUNT %s\n' "$line";; esac
done < /proc/self/mountinfo
for x in /usr/bin/python3 /usr/bin/systemctl; do if [ -x "$x" ]; then printf 'EXECUTABLE_PRESENT %s\n' "$x"; else printf 'UNKNOWN %s\n' "$x"; fi; done
set -- .research/experiments/scripts/synthetic_*.py .research/experiments/scripts/test_synthetic_temperature_demo.py
set -- "$@" .research/experiments/scripts/synthetic_preparation_versions/v0.1/*.py .research/experiments/configs/synthetic-temperature-demo-v0.1.json
set -- "$@" .research/experiments/synthetic-implementation-*.md .research/protocol/synthetic-*.md .research/reviews/synthetic-*.md
[ "$#" -le 32 ] || { printf 'FILE_COUNT_STOP\n'; exit 2; }
/usr/bin/stat --printf='%n|logical=%s|blocks=%b|block_bytes=%B|mode=%a\n' -- "$@"
```
Paths/utility availability unknown: missing/read/stat error is retained failure→STOP, не установка/fallback. cgroup mount/controllers/root settings и executable presence НЕ доказывают delegation/current membership/runtime version/quota.
Shell/globs читают только scoped metadata, не содержимое scripts/секретов; фиксированный список ещё не полный disk census (§5). Нет проверки writable через попытку записи.
Планировать до9s wall/CPU для D и ≥6s остатка inventory на bootstrap/repeated startups; общий inventory15/15. Timeout8+kill1 — **best-effort**, не aggregate CPU/RAM/15s hard accounting и не предел startup/blocked I/O/observer tail.
Existing outer harness должен начать monotonic interval ДО env/timeout startup, сохранить stdout/stderr≤16KiB суммарно, exit/signal, все task CPU и own receipt/exit tail; writer output — единственная разрешаемая запись, без нового helper process. Overflow→явный truncated/failure record+STOP, не silent truncation.
Предложенный новый receipt path: `.research/experiments/control/synthetic-launch-v0.1/discovery-001/`, exclusive; status/failure и raw streams неизменяемы. Путь сейчас не создан; до D нужен storage-owner и предварительная оценка prepared footprint/reserve.
Если hard outer accounting неизвестен, D разрешим ТОЛЬКО как явно best-effort exception с actual/unknown ledger fields, без caps certificate. Невосстановимый CPU/tail или storage bound блокирует subsequent bootstrap/E004/E005.

## 4. Раздельные permissions и конкретная prospective последовательность
Все следующие argv — спецификация будущих, отсутствующих компонентов, **не runnable commands сейчас**; control facility вызывает binary непосредственно без research shell/timeout/systemctl процесса.
1. D approval (точный BODY, exceptions/process scope/receipt writer) → один probe → сохранить полный исход и остановиться для человеческого review; никакого auto-bootstrap.
2. B approval отдельно: принять runtime/process/domain amendment, inspected future code+exact binary/runtime hashes, accounting boundary, quota/path census/reserves и immutable ledger root.
3. Facility под внешним accounting создаёт dedicated parent cgroup+budget quota, effective controls/permissions; затем contained exec: `.research/experiments/scripts/synthetic_controlled_launch_v0.1 --stage bootstrap --config .research/experiments/configs/synthetic-temperature-demo-v0.1.json --ledger-root .research/experiments/control/synthetic-launch-v0.1 --approval-stage B`.
Bootstrap только проверяет effective controls/membership/counters/quota/read-only provenance/runtime metadata и exclusive receipt readiness; никакого полного unittest, production imports/generator/toy fits. Missing authenticated approval или null freeze blocker → STOP.
Bootstrap/repeated startup используют ОСТАТОК15/15 после D, не новые15s. В worker startup E004 проверить `sys.version` против frozen provenance ДО generation; mismatch→immutable failure, без substitution Python.
4. После terminal B receipt и review — отдельный G1/E004: тот же binary/config/ledger, `--stage E004 --approval-stage G1`; facility containment ДО startup, child argv: frozen absolute Python executable, `-B`, `-S`, `.research/experiments/scripts/synthetic_artifact_adapter_v0.1.py`, `--stage`, `E004`; config/approval/ledger передаются ограниченными supervisor descriptors, не inherited secrets.
5. E004 exclusive raw/E004: trace двух cases → validate/event-total≤30000 → fixtures/recipe comparisons → separate features/train labels/eval truth/masks/audits; no benchmark fits. Все schema/causal/reset/ties/unseen/mutation checks сохраняются.
E004 fixture/model-prediction invariance toy checks требуют ЯВНОГО G1 scope: конечный список/count≤8 toy fits по существующим tests, внутри35/35, не четыре benchmark fits; полный suite не разрешается. Если список нельзя freeze — STOP, не скрытые дополнительные fits.
6. После worker exit, observer+terminal accounting завершены, E004 COMPLETE input hashes/review → все research процессы exit → human G2 wait; это ожидание не active wall. Incomplete E004 блокирует E005.
7. Отдельный G2/E005: тот же binary/config/ledger, `--stage E005 --approval-stage G2`; новый contained supervisor/worker с тем же child argv, только stage `E005`; immutable raw/E005, вход frozen E004 и cumulative ledger, case cycle→negative, A→X четыре fits, каждый≤10/10.
8. Predict Z,D,A,X на всех val И test keys обоих cases → exclusive bounded prediction files+hashes+fsync(files/directories)+immutable commit receipt; только ПОСЛЕ commit открыть val/test truth, score val→test; refit/tuning0.
До commit E005 adapter не открывает eval truth/raw trace/expectations и не получает их дескрипторы; features и train labels доступны. Reviewed access log/call-path guards — не OS sandbox; supervisor открывает truth лишь после проверенного commit и передаёт read-only дескрипторы.
9. Сохранить models/mutation invariance/shared keys/confusions/support/strata/unseen/coverage/censor/failures и derived processed/E005 отдельно; ссылки на raw/script hashes. No automatic restart/release/retry при любом сбое.
E004/E005 IDs проверить перед exclusive mkdir: заняты→STOP, не overwrite/reuse E002/E003/E001. Каждый command/approval действителен только для frozen hashes; receipt flag сам не является approval.

## 5. Один ledger, disk и termination reserve
Новый ledger root из §3 содержит numbered append-only receipts с previous hash, authorization, phase/process scope, monotonic intervals, cumulative CPU/wall, cgroup IDs/limits/events/peak, disk/reserve, exit/status/reason; unknown=null, не0.
Active wall — сумма непересекающихся operation intervals, параллельный overhead не удваивается; CPU — весь user+system domain плюс controls/terminal facility attribution, без double-count parent/child cpu.stat. D+B+E004+E005+startup+failures+all tail ≤120/120.
Subcaps остаются inventory15/15, E00435/35, E005 fits40/40 (each10/10), prediction/metrics15/15, finalization15/15; все commands/startups имеют phase attribution, total приоритетнее суммы.
D/B/repeated inventory startup-through-own-tail целиком списываются в inventory15/15; E004/E005 post-exit records — в finalization15/15, без двойного CPU счёта. В finalization заранее резервировать ≥5/5 для terminal emergency; dispatch только при достаточном остатке для работы+tail, иначе STOP.
Supervisor reads memory.current/peak/events/cpu.stat и phase boundaries; worker guards — cooperative soft checks. Предложенный poll≤10ms лишь target cadence, не guaranteed scheduling deadline.
memory.max/swap0/pids bound — условные kernel bounds в указанном charge scope; cpu.max — rate, НЕ cumulative CPU cap. timeout/poll/watchdog сами НЕ hard wall/CPU guarantee.
Для hard120/120/per-fit нужно согласованное facility-bound termination latency+accounting tail и conservative CPU/wall headroom; dispatch пороги ниже caps на эту величину. Если bound неизвестен/необеспечен — STOP, не «измерили polling и сертифицировали».
Disk одновременно logical+metadata reserve≤5242880 И allocated(st_blocks×512)+metadata reserve≤5242880, peak+partials+reserved future; не два суммируемых allowance. Directories/inodes/quota rounding тоже входят.
Scope начинается с codeprep: active P/M/O/T, config, v0.1 snapshots, все новые synthetic notes/protocols/reviews, ЭТОТ план, будущий supervisor/adapter/receipts/raw/processed/logs/temp/failed и control overhead, даже вне одного каталога.
До B полный frozen path census и unchanged pre-codeprep baseline; D stat — только кандидаты, не baseline/compliance. Не считать prepared files старым baseline; copies/moves не исключают originals и не уменьшают measured peak задним числом.
Предлагаемый disk reserve: failure/terminal512KiB logical И allocated плюс отдельно ≥128KiB metadata (или больше по filesystem bound), общий file-count≤96 включая prepared/dirs; измерить возможность, не факт наличия места.
Managed aggregate quota для всех новых writable namespaces с filesystem metadata bound плюс writer logical guard; immutable prepared copies учитываются дополнительно, не дважды одна и та же allocation. Peak copy cost учитывается. Без защищённого пути/квоты/metadata bound — STOP.
Materialized reserve заменяет reserved amount, не прибавляется второй раз; заранее ограничить сериализацию/логи, запретить temp spill/pycache/core dumps и произвольные writes. Оценка worst-case outputs может не поместиться5MiB: STOP, без cleanup failed ради места.

## 6. Post-exit и immutable failure/result records
Worker pre-exit manifest — промежуточный. Supervisor wait/reap → final worker domain snapshot → append own observation; его CPU/wall/final writes/exit ещё НЕ закрыты этим snapshot.
Facility после supervisor exit/empty cgroup читает final counters/events, attribution own control work, disk peak/final/reserves; пишет NEW terminal receipt и сохраняет final managed-operation usage/exit под своим заранее определённым outer boundary.
Все own-tail writes/CPU/wall/storage, включая terminal export, списываются в ledger. Последняя локальная запись не может самосертифицировать собственный будущий exit: external facility event/accounting нужен как artifact pointer и расход, а не бесконечный observer.
Если facility может дать только pre-exit snapshot либо unbounded/unmetered receipt tail — mark INCOMPLETE/limits UNKNOWN и STOP; этот route не позволяет честно certify исходный all-process hard claim.
Каждый исход сохраняется: launch rejection, exit0/nonzero, signal, timeout/OOM/quota/cap/schema/causal/hash/commit failure, killed supervisor, missing final telemetry; заранее prepared failure slot, facility fallback receipt в ТОЙ ЖЕ disk quota/reserve.
Never overwrite/delete raw/partials/old receipt/failure; final status отдельный новый файл. При невозможности записать receipt retain partials+facility failure pointer, evidence incomplete; никаких fabricated results или quality scores для incomplete models.
Provenance: exact approved argv/body, protocol/code/config/input/output hashes, repo revision/dirty (без git diff/секретов), Python/stdlib/OS/kernel/CPU/RAM/filesystem/quota, seed/order/splits, starts/ends/exit, observations/deviations; compiler only для будущего native binary.
Hash/runtime values сейчас UNKNOWN; local freeze не public time-stamped registration. Любая revision — новая версия+dated rationale+approval ДО новой execution, старые docs/results сохранить; post-outcome changes exploratory.

## 7. Checkpoint / неизвестные / stop recommendation
Что известно: computational core существует, main blocked; launcher/adapter отсутствуют; tests UNRUN. Что неизвестно: delegation/pre-start facility, complete terminal accounting, bounds termination, quota/metadata/prepared footprint, runtime/hash freeze и permissions.
Internal threats: wrong access/order/reset/common-mode counters/unchecked guard sample; controls — manual+recipe+trace paths, shared keys, frozen mutation checks, durable commit. External/construct: artificial cycle≠real workload, READ issuance≠SSD throughput.
Conclusion threats: dependent examples/engineered bad Z/count-only transform/finite negative correlation; никакого победного pooled score, effect proof/power guarantee. Runtime success отдельно от C037 correctness и отдельно от budget compliance.
**Запрос сейчас:** разрешить ровно один D probe с argv/BODY выше, best-effort8+1 timeout внутри15/15 и total120/120, максимум3 transient processes, explicit uncontained RAM/pre-start exception и bounded receipt capture, без tests/Python/cgroup writes; approval пока PENDING.
Process amendment runtime2 и boundary/quota acceptance — отдельный B checkpoint ПОСЛЕ D, не часть минимального разрешения сейчас. Если D не устанавливает правдоподобный managed route или остаются blocking unknowns — STOP/report, не повторные probes/инфраструктурный проект.
Ничего не исполнялось/импортировалось/компилировалось/тестировалось/измерялось; network/agents нет. Единственный новый authored artifact — этот план; исходные state/claims/code/config/protocol/raw сохранены. Новых outcomes/limit claims нет.
