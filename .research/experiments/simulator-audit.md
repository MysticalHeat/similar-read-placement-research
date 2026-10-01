# FTLSim-MiDA: статический аудит пригодности для read throughput

Дата получения источников: **2026-09-30**. Статус: **SOURCE AUDIT ONLY**, не эксперимент, не реализация и не утверждённый дизайн.

## 1. Границы и краткий ответ

Проверены локальные README/decision log, brief, question, hypotheses, protocol/experiment-plan, claims/evidence-map и reviews/peer-review. Вопрос и H-ID не утверждены; протокол — неутверждённый шаблон; бюджет, доступ к конкретному датасету и независимая единица не установлены. Локальные question/hypotheses ещё содержат кандидаты с latency, тогда как brief/decision log фиксируют новое предпочтение throughput. Это несогласованность для будущего версионированного уточнения, не разрешение самостоятельно исправлять протокол.

**EVIDENCE:** `MiDaFTL.writing_pointers` хранит активные блоки назначения для записи по separation group. Это не адрес следующего demand-read и не обучаемый predictor.

**EVIDENCE:** репозиторий не ограничивается WAF: в проверенном пути есть demand-read, счётчики физических операций и простая модель длительностей NAND, включая GC read/write/erase и LSB backup. Но время накапливается последовательно в одном `Statistics.elapsed`, без моделирования перекрытия операций.

**INFERENCE:** можно было бы вывести показатель чтения для явно оговорённой последовательной модели из её корректных счётчиков и времени. Это не готовый throughput-report и не измерение реального SSD. Существующая модель не позволяет проверить заявленный механизм ускорения через channel/die/plane parallelism и конкуренцию с предсказательной миграцией. Обучение predictor само по себе этот пробел не закрывает.

Никаких чисел производительности не получено. Числа длительностей ниже — параметры исходного кода, не наблюдения и не benchmark.

## 2. Источник S013 и неизменяемая версия

- Репозиторий: `MysticalHeat/FTLSim-MiDA-implementation`.
- API реально вернул commit **`a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21`**, commit message `fix`, дату commit author/committer `2026-09-16T07:24:23Z`. Это дата версии, не установленный год публикации/создания проекта.
- Tree: **`aa815719e0bb8b6f1016f6fd6cd9fa531681066d`**, `truncated: false`, 16 файлов, без показанных подкаталогов или submodule entries.
- Неизменяемая версия: https://github.com/MysticalHeat/FTLSim-MiDA-implementation/commit/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21
- Tree API: https://api.github.com/repos/MysticalHeat/FTLSim-MiDA-implementation/git/trees/aa815719e0bb8b6f1016f6fd6cd9fa531681066d?recursive=1
- Первый запрос `commits?per_page=1` — mutable discovery endpoint. Все последующие тексты получены через raw URL с полным commit hash; выводы привязаны к нему, не к будущей default branch.
- Глубина: полный текст девяти Python-файлов и LICENSE, плюс метаданные commit/tree; **без исполнения, независимой репликации и проверки физической точности модели**.
- Commit API сообщает автора данного commit, но это не устанавливает авторский состав всего проекта. Библиографические title/authors/year оставлены null в предложенной записи ниже.

### Реестр инспекции и retrieval budget

Всего **12 webfetch**, все успешны; websearch — 0. Запросы 1–2: commit discovery и tree. Запросы 3–12: перечисленные десять текстов. Порядок ответов внутри параллельных пакетов не означает последовательность исполнения кода.

| Файл | Глубина и назначение | Git blob SHA из API tree (не независимо вычисленный checksum) |
|---|---|---|
| ftlsim.py | Полностью: CLI, parser, initialization, replay, завершение | `8cddb61739a5afc047e79de1abcb31ce1413590c` |
| FTL.py | Полностью: dispatch, mapping, allocation, victim selection, backup, physical operations | `fbbf9ff6854028b143cd08df526dfd36e5fa08de` |
| MiDaFTL.py | Полностью: writing pointers, migration groups, reads/writes/GC | `7a323b202ab5540fcb243008cbb32b5bf23dfc58` |
| DAC.py | Полностью: альтернативная policy, regions, reads/writes/GC | `9719d104a005beaba788a07f17384d1c4c04f742` |
| PageFTL.py | Полностью: альтернативная policy, single update block, reads/writes/GC | `5589317f531a342a47cd26b2111a34b18c72ab96` |
| Block.py | Полностью: состояния блока, offset, mapping slots, migration counts | `40cbe1a49de1d70bff5cfea85e2ee690ef79777a` |
| NAND.py | Полностью: размеры, PPN conversion, paired-page classification, durations | `2a90b7f559ca4266304b7264bb1fc3eb98ad6916` |
| Statistics.py | Полностью: counters, elapsed, reset, output, add_time | `98bfe51cf0dc26db8b194184c2a81417f5439acd` |
| Trace.py | Полностью: функция текстового логирования, НЕ parser входной нагрузки | `ed3d093dbbe551db5cd85dec4cd2b4354817d848` |
| LICENSE | Полный текст GPL version 3 | `9cecc1d4669ee8af2ca727a5d8cde10cd8b2d7cc` |

Содержимое **README.md, Makefile, FTLFactory.py, SSD.py, Page.py, .gitignore не получено**: известны только пути/размеры/blob IDs из tree. Их нельзя считать прочитанными. В частности, factory dispatch, SSD capacity/provision constants, sentinel Page.INVALID, build recipes и дополнительные указания README остаются непроверенными. Бюджет исчерпан; дальнейших запросов не было.

Raw URL любого прочитанного файла: `https://raw.githubusercontent.com/MysticalHeat/FTLSim-MiDA-implementation/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/<path>`. Точные clickable source locations приведены ниже. Номера строк соответствуют полученному raw-тексту; GitHub fragment служит адресуемым указателем, не отдельной проверкой rendered GitHub page.

## 3. Что именно означает writing pointer

### Структура и выбор группы

[MiDaFTL.py L7–34](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/MiDaFTL.py#L7-L34):

```python
SEPARATION_GROUPS = 4;
self.writing_pointers = [None for i in range(self.SEPARATION_GROUPS)]
```

`find_group(migration_count)` возвращает migration count, ограниченный сверху `SEPARATION_GROUPS - 1`. По реализации это группировка по количеству пережитых GC migrations, не по будущим чтениям. Хранимое значение pointer — объект `Block` либо `None`; offset хранится внутри блока. [Block.py L12–25](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/Block.py#L12-L25) сбрасывает `offset`, `lpns`, `migration_counts`, `valid_pages`, `last_accessed`, `region` при erase.

### Назначение, использование и продвижение

[MiDaFTL.py L58–72](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/MiDaFTL.py#L58-L72):

```python
update_block = self.writing_pointers[group]
if update_block  == None:
    update_block = self.writing_pointers[group] = self.allocate_block()
(block, offset) = (update_block, update_block.offset);
update_block.offset += 1;
if update_block.offset == NAND.PAGES_PER_BLOCK:
    update_block.status = Block.USED;
    self.writing_pointers[group] = None;
return (block, offset);
```

`FTL.allocate_block` берёт `self.free_blocks.pop()` и ставит `Block.INUSE` ([FTL.py L103–107](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L103-L107)). Таким образом pointer задаёт следующий свободный слот **записи** в активном блоке группы. Он продвигается при allocation, а не при чтении. Несколько страниц одной группы последовательно занимают один блок; это не представление нескольких независимых NAND resources.

### Host write и GC migration

- [MiDaFTL.py L76–89](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/MiDaFTL.py#L76-L89): host write вызывает `self.get_update_ppn(0)`, backup при необходимости, `write_page`, `update_mapping`, затем `block.migration_counts[offset] = 0`. При `len(self.free_blocks) <= self.SYNC_GC_THRESHOLD` синхронно запускается `reclaim_block()`; threshold в этой версии равен 1.
- [MiDaFTL.py L36–56](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/MiDaFTL.py#L36-L56): GC перебирает valid LPN victim, увеличивает `victim.migration_counts[index] + 1`, выбирает группу через `find_group`, выполняет backup/migrate/update_mapping, сохраняет новый count, стирает victim и возвращает его в free list.
- [FTL.py L110–147](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L110-L147): victim selection только из `Block.USED`, cost-benefit score использует age по `Statistics.clock` и valid fraction. `update_mapping` инвалидирует прежний слот и обновляет `l2p`/`block.lpns`.
- `last_accessed` обновляется в `write_page`, а `read_page` его не меняет: название не означает recency demand-read ([FTL.py L36–48](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L36-L48)).
- Полностью прочитанные PageFTL и DAC используют соответственно `update_block` и `update_blocks[region]` с аналогичным next-write allocation. В DAC regions меняются по host overwrite / reclamation, не по next-read prediction.

Уже существует перенос valid pages **внутри GC**. Это не готовая политика proactive read-driven migration. Перенос данных без GC потребовал бы отдельного causal decision path, mapping correctness и учёта затрат; здесь он не реализовывался и не проверялся.

## 4. Parser и путь demand-read

Вход разбирается не в Trace.py, а в [ftlsim.py L112–163](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/ftlsim.py#L112-L163), функция `process_workload`:

```python
e = l.strip().lstrip().split();
RW = e[0].upper();
sector_start = long(e[1]);
sector_count = long(e[2]);
```

- Ожидаемые первые три поля: operation, starting sector/LBA, sector count. Пустые строки и строки с первым token, начинающимся с `#`, пропускаются. Обычные `R` **не отфильтровываются**: поступают в `ftl.process`.
- Дополнительные поля не используются: timestamps, queue ID, completion/dependencies не извлекаются. Из этого нельзя заключать, что пользовательский датасет содержит/не содержит такие поля.
- Адреса >= `SSD.SECTOR_MAX` берутся по модулю. Пересекающий конец адресного пространства запрос разбивается на два вызова `ftl.process`. Это может исказить workload locality и request count относительно исходной нагрузки.
- Есть assert верхней границы sector_count, но нет явной валидации допустимого operation, отрицательных значений или полного формата. В `FTL.process` всё, что не `R`, увеличивает write counters, но реальные операции вызываются только для точных `W`/`R`. Неизвестный token может поэтому увеличить статистику без соответствующего I/O.
- `Statistics.clock += 1` после обработанной строки — индекс запроса в trace, не время. Для split-at-wrap clock увеличивается один раз, а request counters — за каждый `process`.

[FTL.py L70–100](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L70-L100) переводит sector range в покрывающий его диапазон LPN, последовательно обходит `lpns`, считает request/page counters и вызывает `process_read`/`process_write`.

[MiDaFTL.py L21–28](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/MiDaFTL.py#L21-L28):

```python
if self.l2p[lpn] == Page.INVALID: return False;
ppn = self.l2p[lpn];
self.read_page(ppn);
```

Чтение использует **существующий** LPN→PPN mapping, не writing pointer. То же поведение видно в DAC/PageFTL. Unmapped page возвращает False без физического read; вызывающий `FTL.process` этот результат не проверяет, хотя request/pages counters уже увеличены. Поэтому эти counters нельзя без проверки называть числом успешно завершённых чтений. Payload/проверка прочитанных байтов в проверенном пути не представлены; mapping asserts не заменяют end-to-end data validation.

Default initialization предварительно записывает usable space и вызывает `Statistics.reset()` ([ftlsim.py L188–195](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/ftlsim.py#L188-L195)). `-init_empty` отменяет заполнение. Заполнение не является trace-based warmup или replay исторического layout; его время исключается из summary, но состояние FTL сохраняется. Per-page/request streams могут получить записи заполнения, поскольку они не отключаются перед fill — ещё одна граница окна измерения, которую надо проверить до будущих запусков.

## 5. Время, параллелизм и накладные расходы

[NAND.py L3–14](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/NAND.py#L3-L14) задаёт 128 pages/block, 16 sectors/page, 512 bytes/sector, то есть 8192 bytes/page. Параметры `US_READ_LSB/MSB` — 80/120 μs, `US_WRITE_LSB/MSB` — 500/1500 μs, `US_ERASE_BLOCK` — 1500 μs. Это предположения версии кода, не подтверждённые характеристики пользовательского устройства.

[Statistics.py L111–124](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/Statistics.py#L111-L124):

```python
def add_time(rw, target):
    global elapsed;
    if rw == 'R':
        if NAND.is_lsb(target):
            elapsed += NAND.US_READ_LSB;
        else:
            elapsed += NAND.US_READ_MSB;
```

Для W/E эта же функция прибавляет write/erase duration. Проверена цепочка `process_workload → FTL.process → process_read/process_write/reclaim_block → read_page/write_page/erase_block → Statistics.add_time`. Вывод о последовательном времени основан на этой полной inspected chain, а не на отсутствии keyword hits.

| Компонент | Что поддерживает проверенный measured path |
|---|---|
| Simulated time | Один cumulative elapsed в μs; нет событий start/completion для нескольких операций |
| Arrival/idle time | Parser не читает timestamps; нет межзапросного idle time |
| Queue/concurrency | Вложенные последовательные циклы запросов/страниц; queue depth и scheduler не задаются |
| Address/resource topology | PPN = block.id × pages/block + offset; обратно только block/page. Channel/die/plane IDs и busy intervals в проверенных NAND/Block/FTL/Statistics не представлены |
| Bus/controller/command constraints | Transfer time, channel contention, multi-plane commands, controller occupancy в проверенном accounting не представлены |
| GC/backup | Read/write/erase durations суммируются синхронно в elapsed |
| Predictor overhead | Predictor не участвует; CPU/inference cost в elapsed не добавляется |
| Utilization | Resource utilization/overlap не выводятся |

[FTL.py L63–67](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L63-L67): `migrate_page` делает `self.read_page(ppn); self.write_page(block, offset);`, затем увеличивает `pages_migrated`. Backup тоже делает физические read/write и иногда erase ([FTL.py L150–179](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L150-L179)). Поэтому **существующие GC/backup затраты не нулевые** в serial time/WAF. Но нельзя утверждать, что посчитаны будущие proactive migration, predictor, ресурсная конкуренция или net end-to-end throughput предлагаемого метода.

INFERENCE: в read-only interval без новых записей эта версия не инициирует GC или read-driven relocation из `process_read`. Перекладывание страниц может изменить LSB/MSB service cost в этой абстракции, но это другой механизм, не доказательство parallelism.

### Риск классификации LSB/MSB — обнаружен статически, не воспроизведён

[NAND.py L18–23](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/NAND.py#L18-L23) содержит special cases `ppn == 0x7f` и `ppn == 0`, а Statistics передаёт абсолютный PPN, не offset modulo 128. Например, offset 0 и absolute PPN 128 классифицируются этой функцией различно, хотя оба соответствуют offset 0 в своих блоках. Backup проверяет offset через `NAND.is_msb(offset)`. **INFERENCE:** возможна несогласованность timing и paired-page модели для блоков после первого. До будущих измерений требуется отдельная проверка и согласованная версия исправления; никакого исправления или теста здесь не было.

## 6. Outputs, единицы и допустимость throughput

[Statistics.py L25–55](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/Statistics.py#L25-L55) выводит Clock, Elapsed, host request/page counters, physical pages read/written/migrated/backup/skipped, erased blocks и WAF:

```python
WAF = (float(pages_written) / float(requests_pages_write));
[1, 3, 1, "Elapsed", elapsed / 1000000],
```

- WAF — physical page writes / pages covered by host writes; при нулевом знаменателе печатается 0.0, а не математически определённый WAF read-only workload. Extra copies/backup входят в numerator.
- `elapsed` внутри — μs; printed Elapsed предположительно секунды. В видимом Python-2 коде деление целых отбрасывает дробную часть, поэтому printed summary недостаточно точен для последующего throughput calculation.
- `Clock` — trace request index. `Pages.Read` — **все физические read**, включая GC/backup, а не только demand-read payload.
- `-statistics_page` и `-statistics_request` пишут `"%s %d\n" % (RW, end - start)` в μs ([FTL.py L87–100](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/FTL.py#L87-L100)). Это serial simulated operation/request cost, не arrival-to-completion latency с очередью; у unmapped read может быть ноль. Запись W включает синхронные GC/backup внутри вызова. Request ID, LBA, timestamps и status в этих строках отсутствуют.
- `- Run for` в ftlsim — wall-clock разность `datetime.now()` для работы Python replay ([ftlsim.py L197–212](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/ftlsim.py#L197-L212)). Это не simulated SSD elapsed и не read throughput устройства.
- Прямого IOPS/bytes-per-second поля в полностью прочитанных outputs нет. Корректный будущий числитель — успешно завершённые demand-read requests либо их фактические bytes, не `pages_read` с internal copies. Частичный sector request нельзя автоматически считать full-page payload.

**Условно осуществимо, но не выполнено:** после проверки completeness/status можно вычислять `completed demand reads / (unrounded simulated elapsed μs / 10^6)` для согласованного serial busy-time window. Для mixed workload denominator включал бы учтённые write/GC/erase costs. Нужно назвать это throughput **последовательной идеализированной модели**, а не наблюдаемой SSD throughput; исходные counters пока не гарантируют completion correctness.

**Не поддержано текущим accounting:** throughput от channel/die/plane parallel layout при реальных arrivals/concurrency и migration contention. Просто добавить формулу деления или обучить модель недостаточно: отсутствует механизм, которым параллелизм может изменить completion timeline.

## 7. Лицензия, зависимости, failure handling и воспроизводимость

- [LICENSE](https://github.com/MysticalHeat/FTLSim-MiDA-implementation/blob/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21/LICENSE): получен текст **GNU GPL Version 3, 29 June 2007**. Не устанавливались отдельно copyright provenance всех файлов, GPL-only versus or-later grant и совместимость будущего распространения с иными компонентами. Лицензия пользовательского датасета UNKNOWN.
- В прочитанных imports — Python standard library `os`, `sys`, `argparse`, `datetime` и project modules. В полученном полном tree нет requirements/lock/environment spec; это проверка инвентаря, не доказательство отсутствия любых внешних требований. Makefile/README и три вспомогательных Python-файла не прочитаны.
- `print` statement, `long`, `xreadlines` и integer division показывают Python-2-era source; версия interpreter не pinned, Python-3 compatibility без изменения кода не поддержана видимым синтаксисом. Сборка/установка/портирование не проводились.
- В read/write loops и counters нет RNG; это не доказательство bitwise determinism всего запуска с непрочитанной factory/runtime. Никакие seed, OS/hardware/runtime/compiler/version или utilization для запуска не фиксировались, потому что запуска не было.
- `KeyboardInterrupt` перехватывается с `pass`, после чего печатается summary; прочие exceptions/assertions не обрабатываются централизованно. Это риск принятия частичного replay за завершённый. Status/completed trace checksum/run manifest здесь не генерируются.
- CLI открывает output в режиме `w`; это не безопасная система write-once raw artifacts. В будущем внешняя согласованная harness должна исключать overwrite и сохранять failed/negative runs. В этом аудите output CLI не открывался.
- Git commit/tree/blob hashes выше — идентификаторы, реально полученные от GitHub API, **не независимо вычисленные SHA256 checksums**. Локальная копия репозитория не создавалась, raw snapshots не сохранялись; воспроизводимость аудита зависит от доступности immutable GitHub objects. Проверка криптографической целостности не выполнялась.

## 8. Минимально необходимая будущая работа — только предложение

Это **не изменения кода, не согласованный протокол и не инструкция к запуску**.

1. Для корректного serial baseline: проверить runtime/factory/SSD constants и license provenance, operation validation, missing mappings/completions, wraparound/request IDs, prefill versus measurement window, unrounded time и LSB/MSB classification. Зарегистрировать изменения до будущих runs.
2. Для исходного parallelism question: выбрать другую проверяемую timing model либо существенно расширить эту — resource topology, event completions, shared channel/bus occupancy, command restrictions, arrivals/dependencies, queue depth и scheduling. Это не маленькая правка WAF report. Без этих элементов механизм placement → concurrent service не проверяется.
3. Для migration: добавить отдельно causal relocation policy с source read, destination write, mapping invalidation/update, free-space/GC effects, scheduling и resource contention. Учесть inference/preprocessing/CPU delay по согласованной модели, не вычитать μs NAND и CPU-cost без определения совместного timeline.
4. Для trained predictor: сначала предложить интерфейс `доступная история read/write + время/состояние → ranked future LPNs + horizon/confidence`, а затем отдельный decision layer `forecast → permitted placement/migration action`. Конкретная neural architecture не требуется по умолчанию. Temporal train/validation/test, причинные features, простые baselines и cost caps надо определить до training; future test data недоступны online policy.
5. Будущая проверка harness должна быть на явно помеченных synthetic/pilot traces: известных read durations, no-overlap/allowed-overlap cases, GC/backup, correctness, incomplete/invalid requests. Здесь таких тестов не было; pilot не будет confirmatory evidence.

Статусы: allocation/mapping/GC scaffold — **проверен в исходнике**; serial read timing — **проверен в исходнике, correctness требует проверки**; learned prediction/proactive migration — **только предложение**; parallel read throughput/net benefit — **не поддержано проверенным accounting, эффект UNKNOWN**; suitability пользовательского dataset — **UNKNOWN**.

## 9. Что запросить о датасете и нагрузке

- Место хранения/безопасный доступ, provenance/version/checksum, лицензия и ограничения приватности. Для начала достаточно schema и обезличенного примера, не передачи всего private trace внешнему сервису.
- Значение operation codes (R/W/TRIM/flush и т. п.), address namespace/device ID, LBA units, sector size, request size; timestamps и их units, порядок при ties.
- Submission/arrival и completion time, request/thread/queue IDs, queue depth или зависимости между запросами; если их нет, throughput assumptions нужно выбирать отдельно.
- Read/write mix, число независимых traces/workloads/devices, длительность/объём, missing requests, prehistory/initial valid pages, sequentiality и рабочий диапазон адресов.
- Что считать next page: LPN 8 KiB этой модели либо granularity датасета; следующий read во всём потоке или в конкретной queue/thread; k и prediction horizon.
- Temporal split и workload separation, возможность adaptation, data/version drift, запрет train/test leakage.
- Primary throughput units (demand IOPS или useful bytes/s), load/concurrency, useful improvement threshold, migration/write amplification/CPU/RAM caps и горизонт амортизации затрат.
- Hardware/CPU/RAM/GPU при необходимости, runtime portability requirements, срок, finite training/tuning/run budget и независимая единица. Количество requests само по себе не число независимых реплик.

## 10. Handoff: предлагаемые S/C записи, НЕ внесённые в literature/claims

Proposed S013 record (не запись публикации; null-поля не заполняются догадками):

```json
{"id":"S013","title":null,"authors":null,"year":null,"doi":null,"arxiv_id":null,"url":"https://github.com/MysticalHeat/FTLSim-MiDA-implementation/commit/a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21","version":"a8cf9b70823b9f500d4f3b7ac6e18a574f6e8e21","retrieved_at":"2026-09-30","access":"full-text","metadata_status":"commit/tree verified via GitHub API; repository bibliographic metadata incomplete","note_path":".research/experiments/simulator-audit.md"}
```

Четыре **кандидатных атомарных claims** для интеграции оркестратором; C006–C009 не объявляются зарезервированными/подтверждёнными вне этого handoff:

| Candidate | Bounded claim | S-ID / exact support | Verification / confidence / caveat |
|---|---|---|---|
| C006 | В указанном commit `MiDaFTL.writing_pointers` задаёт next-write allocation в активных блоках separation groups. | S013; MiDaFTL.py L19, L58–72, L78 | Direct source inspection; высокая уверенность в семантике данной версии, не predictor/аппаратный pointer |
| C007 | В указанном commit mapped demand-read MiDa обрабатывается через `l2p` и `read_page`, а не writing pointer. | S013; MiDaFTL.py L21–28; FTL.py L36–38, L87–92 | Direct; высокая уверенность в code path, unmapped read пропускается, execution не проверено |
| C008 | В проверенном timing path длительности NAND операций последовательно суммируются в одном `Statistics.elapsed`. | S013; Statistics.py L111–124; FTL.py L36–67 | Direct; высокая уверенность в inspected accounting, не доказательство физической точности или parallel throughput |
| C009 | В указанном commit `migrate_page` включает source read и destination write в существующий time accounting. | S013; FTL.py L63–67, L36–48; Statistics.py L111–122 | Direct; высокая уверенность в учёте этих операций, не полный overhead будущей learned proactive migration |

Рекомендуемый следующий шаг: **сначала schema/units/arrival-concurrency данных и выбор проверяемой модели времени**, затем versioned refined question с throughput. Если цель остаётся ускорением через параллелизм, не начинать training/benchmark на предположении, что текущие writing pointers и elapsed уже моделируют этот механизм. Разрешение использовать репозиторий не является scientific design approval.

## 11. Выполнение и сохранённые артефакты

- Сохранён только `.research/experiments/simulator-audit.md`. README, hypotheses, protocol, literature и evidence-map не менялись.
- Shell commands: **нет**. Build/install/clone/train/replay: **нет**. Exit codes: **N/A**, процессов эксперимента не запускалось.
- E-ID/raw directories/experiment manifests: **не создавались**. Новые эксперименты не разрешены и не проводились. Отсутствие manifest здесь не пропуск результата: результатов нет.
- Web retrieval: два API URL из §2 (discovery endpoint: `https://api.github.com/repos/MysticalHeat/FTLSim-MiDA-implementation/commits?per_page=1`) и десять raw URLs по шаблону §2 для файлов таблицы; без broad search, confidential inputs или исполнения source instructions.
- Reproduction **аудита**: открыть тот же commit/tree и десять raw файлов, пройти paths/symbols из §§3–7; это повторение source inspection, не rerun benchmark. Запускные команды не предлагаются, так как execution/design/budget не утверждены.
- Дизайн не изменялся; deviations эксперимента N/A. Блокеры будущих runs: approval, protocol/version, workload access/units/concurrency, independent unit, budget, timing suitability и correctness risks. Это handoff, не интерпретация статистической значимости.
