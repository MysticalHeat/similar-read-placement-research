# Быстрый полный literal-profile, не SSD benchmark

2026-09-30. E001: оба файла достигли EOF, stat identity до/после совпала. Выполнение заняло около 4.5 s при internal115/tool120 s и RLIMIT_AS512MiB. Нет сети, установок или записи в dataset/. Script inspected before execution; exact command, timestamps, script/data hashes and environment in raw/E001/manifest.json and profile.json. Статистики — буквальная структура файлов, не подтверждённые physical units/provenance/chronology.

| Input | Rows | Literal first token W | R/Read/r/read | Fields |
|---|---:|---:|---:|---|
| dataset/hm_0.csv | 515114 | 515114 | 0 | 3 in every row |
| dataset/prxy_0.csv | 2427089 | 2427089 | 0 | 3 in every row |

Все остальные literal labels отсутствуют, blank/comments=0. Значения после первого token проходят int(token,10); это не подтверждает смысл/единицы чисел. Под схемой R/W предложенного симулятора эти файлы не содержат read events. Происхождение от руководителя сообщает пользователь; исходная трасса, preprocessing и лицензия остаются UNKNOWN. Никаких reads не восстановлено/сгенерировано и model accuracy/throughput не измерялись.

Воспроизведение разрешённой проверки: python3 -B .research/experiments/scripts/profile_tokens.py dataset/hm_0.csv dataset/prxy_0.csv . Повторный stdout сохранить в НОВЫЙ run ID, не overwrite E001; совпадение input hashes проверять отдельно. Это не команда обучения.
