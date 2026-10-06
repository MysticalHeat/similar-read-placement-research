# Исход до плановой границы окна

Протокол `../../docs/protocols/window-outcome-protocol.md`; общий отчёт `../../reports/all-write.ru.md`.

Переиспользуются неизменённые и проверенные features/meta/source из `../all-write/`. Classifier: Write-first до окна (0), Read-first до окна (1), нет первого события до окна (2). Класс 2 не означает «никогда не прочитают». Training 5–6 полностью наблюден до собственных deadlines; test 7 может быть частичным и оценивается консервативно.

Дополнительный признак — оставшееся время до плановой границы, доступное в момент Write; будущий EOF не используется. День 5 обучает, 6 выбирает, после заморозки 7 повторно диагностирует. Нового независимого holdout нет.

`selection.json`, `validation.predictions.npz`, `validation-*.lightgbm.txt`, `gate.lightgbm.txt`, optional `time.lightgbm.txt`, `frozen.json`, `day7.predictions.npz`, `diagnostic.json`, `verification.json`, `report-metrics.json`.

`report-metrics.json` содержит дополнительные описательные recall/byte coverage и zero-baseline на выбранном наборе; они не использовались для выбора.
