# Полная выборка всех Write

Протокол `../../docs/protocols/all-write-protocol.md`, общий отчёт `../../reports/all-write.ru.md`.

Каждый Write дней 5–7 получает 17 причинных признаков из полного прошлого потока, next Read/Write и состояние к границе окна. Отсутствующие события и незавершённые Read не удаляются из all-Write метрик. Day 5 train, day 6 выбор, day 7 повторная диагностика; нового holdout нет.

Файлы: `source.json`, `features.npy`, `meta.npy`, source audit cache `events.bin`; `selection.json`, `validation.predictions.npz`, `validation-*.lightgbm.txt`; `gate.lightgbm.txt`, опциональный `time.lightgbm.txt`, `frozen.json`; `day7.predictions.npz`, `diagnostic.json`, `verification.json`, `source-audit.json`.

NPY/NPZ/BIN остаются внешними артефактами. Bucket-кэши удаляются после подготовки; events.bin сохраняется для независимого source audit. Разметка — точный начальный Offset, не физические диапазоны. Дополнительный finite-window gate — в `../window-outcome/`.
