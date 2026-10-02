# B001: bootstrap stopped before artifact creation
2026-10-02 · Immutable outcome record, not a classifier run or resource certificate.

## Authorisation and one attempt
User explicitly answered «да» to the exact bootstrap-only command/scope.
Tool: functions.bash; workdir `/home/nomli/workspace/bdss_lab/research1`; timeout15000ms.
```text
/usr/bin/python3 -B -S /home/nomli/workspace/bdss_lab/research1/.research/experiments/scripts/synthetic_practical_caller_v0.1.py --stage bootstrap --approval-ref B001
```
One invocation; no retry, fallback, additional shell, tests, generator or fits.

## Exact visible tool output
```json
{"created":[],"durable_failure_pointer":null,"full_reason_location":"UNKNOWN","local_return_intended":2,"outputs":{},"owned_directory":null,"primary":{"reason":"worker RSS concern","reason_omitted":false,"type":"RuntimeError","type_truncated":false},"secondary":null,"tail":"UNKNOWN; pre-exit only; missing receipt forbids next stage"}
```
Tool exposed no separate OS exit code, elapsed/CPU/RSS numbers or timestamps; these are UNKNOWN, not zero. `local_return_intended=2` is caller output, not independently observed OS exit.

## Native post-attempt observations
- Read `experiments/control` returned File not found.
- Read `experiments/raw` returned E001 only; no E004/E005.
- No freeze/receipt/ledger/failure file was available to inspect.

## Exact code support and limits
Caller `Budget.check` compares Linux SELF `ru_maxrss*1024` with1GiB; the failed predicate emits `worker RSS concern`. No numeric sample was exported. Do not infer measured current RSS, source of the peak, OOM, successful budget compliance or remaining120s from this message.
Interpreter/script and stdlib code ran; computational code was not loaded or tested. B001 is spent. C037/H005 remain UNVERIFIED; historical R002 OPEN. Missing accounting blocks silent budget reset; further diagnostics/retry require a new explicit checkpoint. This record/state additions remain in prospective5MiB scope; total footprint UNKNOWN.
