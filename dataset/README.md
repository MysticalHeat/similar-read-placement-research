# Исходные данные

- `msr-cambridge1.tar` содержит `MSR-Cambridge/prxy_1.csv.gz`.
- `msr-cambridge2.tar` содержит `MSR-Cambridge/usr_1.csv.gz`.
- `hm_0.csv` и `prxy_0.csv` — отдельные ранее полученные преобразованные файлы; они не используются для текущего read-прогноза.

Текущий pipeline читает gzip напрямую из tar, без полной распаковки. Схема исходных MSR CSV: Timestamp, Hostname, DiskNumber, Type, Offset, Size, ResponseTime. Offset и Size указаны в байтах; временные метки — Windows FILETIME.

В Git входит этот README. Сами трассы исключены через `.gitignore`; размеры и SHA256 записаны в `../artifacts/manifest.json`. При переносе проекта восстановите их в dataset текущего checkout. Официальная страница MSR Cambridge traces: https://iotta.snia.org/traces/block-io/388. Подробнее: `../docs/git-storage.md`.

Точная схема и требуемая атрибуция находятся в `MSR-Cambridge/README.txt` внутри архивов. Данные использованы для независимых моделей usr_1 и prxy_1; namespaces разных logical volumes не объединяются.
