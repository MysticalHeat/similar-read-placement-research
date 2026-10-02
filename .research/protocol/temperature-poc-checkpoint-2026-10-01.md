# Human checkpoint: temperature classification PoC

2026-10-01. Дополнение статуса, НЕ новая методика/запуск. Исходный temperature-poc-v0.1.md и рецензия сохранены неизменными; их исторические PENDING действовали до данного ответа.

## Ответ и область согласия
На вопрос «Принимаем 4 KiB / история10мин / горизонт10мин / метки0,1–2,≥3 и указанный поэтапный бюджет?» пользователь ответил «1. да».
На предложение ограниченного поиска небольшого публичного файла БЕЗ скачивания (если нет нового файла с чтениями) ответил «2. ок». Это принято как выбор public-source discovery; наличие нового локального read-containing файла не заявлено.

- Согласованы logical4KiB, history/future/step600s, cold0/warm1–2/hot≥3 и представленный малый classification design: частотная эвристика против fixed depth3 tree, count-only ablation/always-cold controls, temporal splits и однократная оценка без tuning.
- Принят поэтапный потолок: подготовка≤10min wall, сравнение≤5min, суммарно≤10CPU-min; RAM≤1GiB, ≤2threads; download≤100MiB, decoded≤1GiB, newdisk≤1536MiB; noGPU/paid/install. Это согласование лимитов, не подтверждение feasibility или permission на команды.
- Первоначальная v0.1 остаётся conditional design: exact source/schema/license, hardware/dependencies, inspected implementation/config и enforcement неизвестны. Freeze окончательного executable protocol/config позже, без молчаливой смены согласованных чисел.
- НЕ разрешены сейчас download/принятие лицензии от имени пользователя/shell/inventory execution/профилирование нового файла/fit/test release/симуляция. Перед E002 показать exact input/commands/limits и получить отдельное разрешение; E003 отдельный checkpoint после suitability.
- H005 SSD efficacy не проверяется этим PoC. Prediction quality не throughput.

## Текущий обратимый шаг
Библиотекарю: max3 generic public queries + max6 public-text fetches, ≤3 candidate sources, stop at first well-supported candidate or budget exhaustion. Только documentation/metadata, НЕ trace/archive/sample bytes, no shell/download/run/install/license acceptance. Новые source IDs начиная S017 при достаточной identity verification; UNKNOWN не заполнять догадками.
Искать actual block/page I/O READ events с timestamp, byte/sector address и request length, single namespace, documented schema/rights и separately listed small file≤100MiB. ≥6h recording необходимо для текущего split; decompressed size/cardinality/class support могут остаться UNKNOWN до отдельно разрешённой проверки. Не заменять на filesystem API events/cache hits/synthetic stream без нового решения.

Если найденный source не соответствует gzip/MSR-specific assumptions v0.1, подготовить отдельную версию адаптации parser/provenance/license до E002; это не разрешение изменить page/H/labels/splits/caps. При отсутствии источника сохранить ограниченный отрицательный результат поиска, не объявлять данные несуществующими и не расширять доступ автоматически.

## Следующий предлагаемый doc-only checkpoint — НЕ разрешён
Discovery вернул UMass/SPC S017 и ссылку S018 https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf ; webfetch не извлёк читаемый PDF text. Предлагается отдельно разрешить загрузку ТОЛЬКО этой публичной документации и local text extraction для schema/units/rights, не данных.
Предлагаемые отдельные потолки: ≤60s wall суммарно/≤30CPU-s, ≤256MiB RAM, ≤1MiB downloaded bytes, ≤5MiB new documentation outputs; ≤1network attempt, no automatic retry/installs. Только first-party bounded downloader после инспекции + уже установленный PDF extractor (если отсутствует/limits не обеспечены — STOP); не исполнять содержимое PDF и не открывать trace links. Новые local doc artifacts с provenance/hashes, no overwrite; никаких E002/E003/raw/model действий. Согласование этих дополнительных лимитов/локальной shell обработки PENDING; не входит автоматически в уже одобренное metadata-only discovery.

## Последующее разрешение doc-only
Пользователь после объяснения назначения документа ответил «окей, давай». Это разрешает описанный выше bounded download/extraction ТОЛЬКО S018 PDF и локальные команды проверки доступности/запуска существующего extractor под теми же лимитами. Предыдущий PENDING — исторический. По-прежнему запрещены trace/archive/sample downloads, installs, принятие terms, E002/E003 и обучение.
Артефакты этой проверки: новый уникальный каталог под experiments/documentation/ (не experiments/raw/), inspected first-party script под experiments/scripts/; source URL/time/hash, extracted text, command/status/limits сохранять без overwrite. Это аудит источника S018, не эксперимент качества/SSD и не новый E-ID. Если нет инструмента/не удалось обеспечить caps/ошибка/timeout — сохранить failure и STOP без retry или расширения бюджета.

## Смена кандидата источника после SPC doc gate
После genericS018check и bounded per-file search фактическийSPCLBAblocksize остаётсяUNKNOWN; явноеdefaultDATA license UMassCC BY4.0(unlessotherwise specified) провереноC027. Пользователь «да» соглашается переключиться на другой небольшой публичный источник без скачивания. Разрешён новый docs-onlysearch≤3queries/5fetches/3families, stopatfirstplausiblecandidate/budget; no newexecution/SPClookup/raw changes. Прежние page/H/labels/splits/caps не меняются; каждый source-specificparser adaptation под отдельнымfreeze/checkpoint. Не выбирать источник по testlabels или предполагаемому learnedgain; record metadata-basedselection beforecontents. R002memory/R003compatibility сохраняются, E002/E003неapproved.

## Отдельная синтетическая демонстрация: design approval only
После boundedsourcefailureC035 пользователь «давай» выбирает подготовку planA из data-route-options-v0.1.md. Это новая иллюстративная популяция/цель, НЕ замена realSSD efficacy на syntheticF1. Realtraceprotocolv0.1/E002/E003 deferred; их plannedIDs не переиспользовать для другой цели. Новый syntheticprotocol будет отдельно создан/reviewed/presented; generator/model/numericalbudget/executionpending. Page4KiB/historyHstep600s/labels0,1–2,≥3 сохраняются как одобренные conventions. R002major остаётсяbefore-executiongate; no installs/network/shell/generation/fit allowed now.

Новыйdraft synthetic-temperature-demo-v0.1.md и review synthetic-temperature-demo-review-v0.1.md сохранены, orphanplaceholdercommands НЕreadytorun. Следующийcheckpoint — approve/revise96pages/6h/cycle+independentnegative/customstdlibCART4fits/total120sCPUwall1GiB1thread5MiB дляcode/configpreparationONLY. До исполнения уточнитьR004(totalactiveledger E004+E005 includingstartup/cleanup,nohumanwaiting charged, processscope/bootstrap/disk) иR005(independentrecipeexpectations vs eventcounter no sharedlabel/window/resetcompute, modelnotfedrecipe/testexpectations). Эти уточнения обязательные будущие acceptancecriteria, ещё не выполнены и не закрываютR002. Bootstrap/environmentexecution иE004/E005 требуют scopedpermissions отдельно; ни один новыйrun не разрешён этим checkpoint.
