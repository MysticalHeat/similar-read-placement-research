# Ограниченный эксперимент по снижению MAE

Протокол: `../../docs/protocols/mae-improvement-protocol.md`. Готовый отчёт: `../../reports/mae-improvement.ru.md`.

На новых днях 5–7 pooled MAE `usr_1` снизилась с 264,22 до 214,68 минуты (−18,7%); преимущество над адресной медианой — 1,2%. Кандидат `prxy_1` ухудшил MAE с 12,99 до 13,85 секунды (+6,6%), поэтому его замена прежней модели не рекомендуется. На пятом дне `usr_1` кандидат также хуже прежней модели; публикуются все результаты.

Для каждой нагрузки `usr_1/` и `prxy_1/`:

- `selection.json` — рецепты моделей, число деревьев после early stopping, пять validation/development метрик, pooled MAE и выбранный метод;
- `baselines.json` — глобальная и адресные медианы только из исходных завершённых train labels;
- `frozen.json` — зафиксированный до новых будущих данных метод, вес смеси, признаки и SHA256 моделей/кода/протокола;
- `*.lightgbm.txt` — модели, сохранённые с best_iteration, а не со всеми пробными деревьями;
- `validation.predictions.npz`, `day{2,3,4}.predictions.npz` — прогнозы всех кандидатов на данных разработки;
- `holdout.json`, `holdout-day{5,6,7}.predictions.npz` — новая будущая оценка current/address_median/selected без fits;
- `verification.json` — независимый пересчёт метрик, проверка выбора, временных границ, baseline и смесей;
- `source-verification.json` — независимый проход по сырой трассе: hash полного префикса, граница EOF и выборочные истории/прогнозы выбранного метода.

Дни 2–4 ранее опубликованы и теперь являются development. Новый тест — дни 5–7. Метрика условна на чтениях до конца каждого окна; coverage обязательно читать вместе с MAE. Последнее окно может закончиться у EOF немного раньше 168 часов. Разные нагрузки не усредняются вместе.

Target остаётся обращением к точному начальному Offset: перезапись не отменяет предыдущую запись. Время до перезаписи и пригодность для размещения данных здесь не измеряются.

Модель без истории принимает прежние log1p-признаки в порядке `read_prediction.pipeline.FEATURE_NAMES`; точные столбцы перечислены в `frozen.json`. Модель с историей дополнительно использует log1p последней завершённой write→read задержки, log1p медианы последних максимум пяти завершённых задержек, sin/cos времени суток. История формируется только после фактического чтения. Обратное преобразование прогноза: `max(0, expm1(model.predict(features)))`. Для смеси затем применяется `model_weight * model_prediction + (1-model_weight) * address_median`. Версии Python и библиотек текущего запуска — в `environment.json`.

Проверка уже созданных артефактов (без обучения):

```bash
uv run python -m read_prediction.checks.mae_improvement --workload usr_1
uv run python -m read_prediction.checks.mae_improvement --workload prxy_1
uv run python -m read_prediction.checks.mae_source_audit --workload usr_1
uv run python -m read_prediction.checks.mae_source_audit --workload prxy_1
uv run python -m read_prediction.mae_reporting
```

Источник и полные прогнозы хранятся локально вне Git; размеры и SHA256 перечислены в `../../artifacts/manifest.json`. В Git сохраняются модели, JSON и Markdown. Для повторного эксперимента требуется новый каталог результатов; существующие selection/holdout не используются как свежий тест.
