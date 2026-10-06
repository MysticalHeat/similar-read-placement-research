# Исходные данные

- `msr-cambridge1.tar` содержит 13 исходных трасс `hm`, `mds`, `prn`, `proj`, `prxy`, включая `prxy_0` и `prxy_1`.
- `msr-cambridge2.tar` содержит 23 исходные трассы `rsrch`, `src1`, `src2`, `stg`, `ts`, `usr`, `wdev`, `web`, включая `usr_1`.
- `hm_0.csv` и `prxy_0.csv` — отдельные ранее полученные преобразованные файлы; они не используются для текущего read-прогноза.

Текущий pipeline читает gzip напрямую из tar, без полной распаковки. Схема исходных MSR CSV: Timestamp, Hostname, DiskNumber, Type, Offset, Size, ResponseTime. Offset и Size указаны в байтах; временные метки — Windows FILETIME.

В Git входит этот README. Сами трассы исключены через `.gitignore`; размеры и SHA256 записаны в `../artifacts/manifest.json`. При переносе проекта восстановите их в dataset текущего checkout. Официальная страница MSR Cambridge traces: https://iotta.snia.org/traces/block-io/388. Подробнее: `../docs/git-storage.md`.

Точная схема и требуемая атрибуция находятся в `MSR-Cambridge/README.txt` внутри архивов. Модели обучались отдельно для usr_1, prxy_1, prxy_0, proj_1 и prn_1; namespaces разных logical volumes не объединяются. Скрининг всех 36 трасс до обучения новых моделей: `../reports/data-sufficiency.ru.md`. Новые будущие оценки: `../reports/new-workloads.ru.md`.
