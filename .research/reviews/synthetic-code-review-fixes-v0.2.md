# Узкая STATIC review исправлений v0.2
2026-10-01 · Один проход · CODEPREP ONLY / EXECUTION STOP.
Locators относительно `.research/`: P/M/T = experiments/scripts/synthetic_temperature_demo.py / synthetic_models.py / test_synthetic_temperature_demo.py; F=experiments/synthetic-implementation-fixes-v0.2.md; V=experiments/scripts/synthetic_preparation_versions/v0.1/.

## Scope и проверяемость
- Прочитаны active P31–48/235–236, M1–55, T94–112/200–269, F53 строки, предыдущая code review52 строки и README1–12; сравнены V/P31–48 и V/M10–35. Эти snapshot predicates соответствуют прежним R006/R007; полная идентичность snapshots/hashes не проверялась.
- O/config/old notes/runtime contract и остальные функции повторно не аудировались: для них сохраняется прежний ограниченный scope, неизменность принята по заданию. README latest-review pointer исторически отстаёт от доступной code review; state не исправлялся.
- Никаких execution/import/compile/tests/probes/web/delegation, вычисления hashes или runtime/source verification. Test specifications не являются результатами; syntax/importability и budget compliance не установлены. Записан только этот новый review, предыдущий не изменён.

## Disposition прежних findings
### R006 — minor: STATIC FIXED; dynamic verification UNVERIFIED
- Support/location: P41–44 теперь требует built-in int и timestamp≥0 вместе с nondecreasing time и timestamp<endpoint. Прежний контрпример первого Event(-1) отвергается predicate; 0 и distinct-ID ties остаются допустимыми по P37–48.
- T94–112 буквально задаёт acceptance0/ties, rejection -1/-2/endpoint/endpoint+1, bool/non-int/empty ID/malformed endpoint, CSV acceptance0 и boundary rejections. Это достаточная статическая реализация запрошенного исправления, не «tests passed».
- Consequence/action/status: прежнее расхождение lower-bound domains устранено в прочитанном коде; дополнительной code correction по R006 не требуется. Confidence высокая по явному predicate; статус закрыт ТОЛЬКО для static defect, проверку поведения запросить через orchestrator после отдельного разрешения.
### R007 — minor: STATIC FIXED; dynamic verification UNVERIFIED
- Support/location: M20–26 проверяет tuple/list len=2, built-in int/float, не bool, finite и [0,120); преобразование в tuple отделяет mutable origins. M28–39 требует callable sampler, integer caps15/35/40 и fit_origin≥phase_origin по обеим координатам; constructor sampler НЕ вызывает.
- M41–55 вызывает sampler только в check, тем же predicate проверяет current, требует current≥phase/fit origins и monotonic current; phase delta≥cap и fit delta≥10 отвергаются через range(2), без zip truncation. previous обновляется только после успешных checks; старые len1/future-origin bypass устранены чтением.
- T210–251 задаёт malformed shapes/domains, origin order, invalid sampler/caps, no-constructor-sample, future origins и monotonic failures; T253–269 задаёт wall-only/CPU-only phase и fit boundaries, valid near-caps/equality и detachment mutable origins. Ни один test не исполнялся.
- Consequence/action/status: дополнительной code correction по R007 не выявлено; Confidence высокая по двум explicit-coordinate paths. Статический дефект закрыт, dynamic verification pending; injected guard НЕ authenticates ledger и НЕ external watchdog/RAM/disk enforcement.

## Оставшиеся gates и самый малый следующий шаг
- R005: static paths ADDRESSED по предыдущей review; dynamic comparisons/receipts pending. C037 остаётся UNVERIFIED; нет новых source/result claims или выполненных models/runs, E004/E005 остаются planned.
- R004: PARTIALLY ADDRESSED, без нового closure. Human domain acceptance, containment ДО bootstrap startup, observer own-exit/final-write tail, process scope и logical+allocated disk/reserve/enforcement всё ещё UNKNOWN. Дополнительный research process требует versioned human-approved amendment, не тихого расширения.
- R002 historical major OPEN, не понижен/не cleared; будущая compliance не ретроспективная сертификация. P235–236 остаётся безусловно fail-closed; runnable adapter/launcher не подтверждён этим follow-up.
- F18,48–49 правильно относит новые snapshots/tests/notes к будущему5MiB ledger, не baseline; ни их объём/allocated footprint, ни возможность уложиться здесь не измерены.
- Сильнейший остающийся контраргумент к «готово к запуску»: корректные pure predicates могут получать неверные accounting samples и не охватывают OS/observer tail. Разрешить его может только отдельно согласованный bounded containment/accounting bootstrap с receipts, не успешные guard tests.
- Минимальный следующий шаг без исполнения: orchestrator предъявляет ОДИН inspected bounded launcher/bootstrap design со scope/reserves/pre-start containment; при несовместимости — STOP/human amendment. После отдельного approval и review receipts можно отдельно разрешить narrow Event/BudgetGuard test subset, без generator/toy fits; новое run approval этой review НЕ даётся.
- Полный unittest suite вызывает generator и toy fits: это НЕ bootstrap/doc-only operation. G1/E004 и последующий G2/E005 остаются отдельными permissions; существующих classifier results для reanalysis нет. Прежние external-validity/engineered-baseline риски не пересматривались.
STOP после одного узкого прохода; integration статусов в state/общий review — orchestrator.
