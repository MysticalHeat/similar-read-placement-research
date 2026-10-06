"""Render the completed bounded MAE-improvement experiment as a Russian report."""

import argparse
import json
import math
from pathlib import Path

from read_prediction.paths import PROJECT_ROOT, REPORTS

WORKLOADS = ("usr_1", "prxy_1")
ARTIFACTS = ("selection", "holdout", "verification")
DEVELOPMENT_DAYS = ("2", "3", "4")
HOLDOUT_DAYS = ("5", "6", "7")
METHOD_KINDS = {
    "model": "модель",
    "blend": "смесь модели и адресной медианы",
    "address_median": "медиана по адресу",
}
WINDOW_HOURS = {"2": (24, 48), "3": (48, 72), "4": (72, 96),
                "5": (96, 120), "6": (120, 144), "7": (144, 168)}


def _load_artifacts(root=PROJECT_ROOT):
    artifacts = {}
    missing = []
    for workload in WORKLOADS:
        artifacts[workload] = {}
        for name in ARTIFACTS:
            path = root / "results/mae-improvement" / workload / f"{name}.json"
            if not path.is_file():
                missing.append(path.relative_to(root).as_posix())
                continue
            artifacts[workload][name] = json.loads(path.read_text())

    if missing:
        paths = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "Отчёт не создан: сначала завершите runner и независимую проверку. "
            f"Не найдены артефакты:\n{paths}"
        )
    return artifacts


def _validate_artifacts(artifacts):
    for workload in WORKLOADS:
        run = artifacts.get(workload)
        if not isinstance(run, dict):
            raise ValueError(f"{workload}: комплект артефактов отсутствует или имеет неверный формат")
        for name in ARTIFACTS:
            if not isinstance(run.get(name), dict):
                raise ValueError(f"{workload}: {name}.json должен содержать JSON-объект")
        selection = run["selection"]
        holdout = run["holdout"]
        verification = run["verification"]
        for artifact, value in (("selection", selection), ("holdout", holdout),
                                ("verification", verification)):
            recorded_workload = value.get("workload")
            if recorded_workload is not None and recorded_workload != workload:
                raise ValueError(f"{workload}: workload в {artifact}.json не совпадает")
        definitions = selection.get("definitions")
        selected = selection.get("selected_method")
        if not isinstance(definitions, dict) or selected not in definitions:
            raise ValueError(f"{workload}: selection.json не содержит выбранный метод и его определение")
        development = selection.get("development")
        if not isinstance(development, dict):
            raise ValueError(f"{workload}: selection.json не содержит development")
        for name in ("current", "address_median", selected):
            if name not in development:
                raise ValueError(f"{workload}: нет development-метрик для {name}")
        holdout_days = holdout.get("days")
        if not isinstance(holdout_days, dict):
            raise ValueError(f"{workload}: holdout.json не содержит days")
        for day in HOLDOUT_DAYS:
            entry = holdout_days.get(day)
            if not isinstance(entry, dict) or not isinstance(entry.get("metrics"), dict):
                raise ValueError(f"{workload}: нет holdout-метрик за день {day}")
            for method in ("current", "address_median", "selected"):
                if method not in entry["metrics"]:
                    raise ValueError(f"{workload}: нет holdout-метрики {method} за день {day}")


def _get(record, *keys, default=None):
    value = record
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _format_number(value, digits=3):
    number = _finite_number(value)
    return "—" if number is None else f"{number:,.{digits}f}"


def _format_count(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{int(value):,}" if math.isfinite(value) else "—"


def _format_fraction(value):
    number = _finite_number(value)
    return "—" if number is None else f"{number:.1%}"


def _kind_name(kind):
    if kind in METHOD_KINDS:
        return METHOD_KINDS[kind]
    return f"тип не указан ({kind})" if kind else "тип не указан"


def _method_text(name):
    return str(name).replace("|", "\\|").replace("`", "\\`")


def _metric(record, method, day=None, split="development"):
    if split == "development":
        return _get(record, "selection", "development", method, day)
    return _get(record, "holdout", "days", day, "metrics", method)


def _coverage(record, day, split):
    if split == "development":
        coverage = _get(record, "selection", "development_coverage", day, default={})
    else:
        coverage = _get(record, "holdout", "days", day, "coverage", default={})
    return coverage if isinstance(coverage, dict) else {}


def _coverage_text(coverage):
    observed = coverage.get("observed_targets")
    eligible = coverage.get("writes")
    censored = coverage.get("right_censored")
    fraction = _finite_number(coverage.get("observed_fraction"))
    if fraction is None:
        observed_number = _finite_number(observed)
        eligible_number = _finite_number(eligible)
        if observed_number is not None and eligible_number:
            fraction = observed_number / eligible_number
    if censored is None:
        observed_number = _finite_number(observed)
        eligible_number = _finite_number(eligible)
        if observed_number is not None and eligible_number is not None:
            censored = max(0, int(eligible_number - observed_number))
    return (
        _format_count(observed), _format_count(eligible),
        _format_count(censored), _format_fraction(fraction),
    )


def _day_title(day):
    start, end = WINDOW_HOURS[day]
    return f"{day} ({start}–{end} ч)"


def _day_table(record, workload, split):
    selection = record["selection"]
    selected = selection["selected_method"] if split == "development" else "selected"
    methods = ("current", "address_median", selected)
    title = "Разработка, уже просмотренные дни 2–4" if split == "development" else "Новый holdout, дни 5–7"
    lines = [
        f"### {workload}: {title}",
        "",
        "| День (окно от начала трассы) | Завершённые N | Подходящие записи | Незавершённые | Покрытие | MAE current, с | MAE address_median, с | MAE selected, с | Конец окна / статус |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    days = DEVELOPMENT_DAYS if split == "development" else HOLDOUT_DAYS
    for day in days:
        coverage = _coverage(record, day, split)
        observed, eligible, censored, fraction = _coverage_text(coverage)
        metrics = [_metric(record, method, day, split) for method in methods]
        scores = [
            _format_number(_get(metric, "mae_seconds")) if isinstance(metric, dict) else "—"
            for metric in metrics
        ]
        end_status = "—"
        if split == "holdout":
            entry = _get(record, "holdout", "days", day, default={}) or {}
            end_seconds = _finite_number(entry.get("end_seconds"))
            partial = entry.get("partial_day")
            if partial is None and end_seconds is not None:
                partial = end_seconds < int(day) * 86400
            if end_seconds is not None:
                end_status = f"{end_seconds / 3600:.2f} ч"
            if partial:
                end_status += ", частичный"
        lines.append(
            f"| {_day_title(day)} | {observed} | {eligible} | {censored} | {fraction} | "
            f"{scores[0]} | {scores[1]} | {scores[2]} | {end_status} |"
        )
    lines.append("")
    return lines


def _pooled_mae(record, method, split):
    days = DEVELOPMENT_DAYS if split == "development" else HOLDOUT_DAYS
    weighted_error = 0.0
    total = 0
    for day in days:
        metric = _metric(record, method, day, split)
        mae = _finite_number(_get(metric, "mae_seconds"))
        count = _finite_number(_get(metric, "n"))
        if count is None:
            count = _finite_number(_coverage(record, day, split).get("observed_targets"))
        if mae is None or count is None or count <= 0:
            continue
        weighted_error += mae * count
        total += int(count)

    if total:
        return weighted_error / total, total

    if split == "development":
        fallback = _finite_number(_get(record, "selection", "pooled_development_mae", method))
        if fallback is not None:
            return fallback, None
    return None, None


def _improvement_percent(reference, selected):
    base = _finite_number(reference)
    chosen = _finite_number(selected)
    if base is None or chosen is None or base == 0:
        return None
    return 100 * (base - chosen) / base


def _format_improvement(reference, selected):
    change = _improvement_percent(reference, selected)
    return "н/д" if change is None else f"{change:+.1f}%"


def _pooled_table(record, workload, split):
    methods = ("current", "address_median", "selected" if split == "holdout"
               else record["selection"]["selected_method"])
    values = {method: _pooled_mae(record, method, split) for method in methods}
    current, median, selected = (values[method][0] for method in methods)
    total = values[methods[2]][1]
    split_name = "development" if split == "development" else "holdout"
    lines = [
        f"| {workload} | {split_name} | {_format_count(total)} | {_format_number(current)} | "
        f"{_format_number(median)} | {_format_number(selected)} | "
        f"{_format_improvement(current, selected)} | {_format_improvement(median, selected)} |"
    ]
    return lines


def _model_definition(definition, definitions):
    if definition.get("kind") == "model":
        return definition
    if definition.get("kind") != "blend":
        return {}
    source = definition.get("model_method")
    if source in definitions:
        return definitions[source]
    model_path = definition.get("model_path")
    matches = [
        item for item in definitions.values()
        if item.get("kind") == "model" and model_path is not None
        and item.get("model_path") == model_path
    ]
    return matches[0] if len(matches) == 1 else {}


def _fit_details(method, definitions):
    definition = definitions.get(method, {})
    model = _model_definition(definition, definitions)
    profile = model.get("profile", "—")
    iteration = model.get("best_iteration", "—")
    return str(profile), _format_count(iteration)


def _validation_section(record, workload):
    selection = record["selection"]
    definitions = selection.get("definitions", {})
    validation = selection.get("validation", {})
    if not isinstance(validation, dict):
        validation = {}
    candidates = []
    for method, metric in validation.items():
        mae = _finite_number(_get(metric, "mae_seconds"))
        if mae is not None:
            candidates.append((mae, method))
    candidates.sort(key=lambda item: (item[0], str(item[1])))
    shown = [method for _, method in candidates[:5]]
    selected = selection["selected_method"]
    if selected not in shown and selected in validation:
        shown.append(selected)

    lines = [
        f"### {workload}: validation и выбор по development",
        "",
        f"Выбран по pooled MAE дней 2–4: `{_method_text(selected)}` "
        f"({_kind_name(_get(definitions, selected, 'kind'))}), "
        f"{_format_number(_pooled_mae(record, selected, 'development')[0])} с.",
        "",
        "Показаны пять лучших кандидатов по validation MAE; выбранный development-кандидат добавлен, если его нет в этих пяти.",
        "",
        "| Кандидат | Вид | Validation MAE, с | Pooled development MAE, с | Профиль | best_iteration | Выбран по development |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for method in shown:
        definition = definitions.get(method, {})
        profile, iteration = _fit_details(method, definitions)
        validation_mae = _get(validation.get(method), "mae_seconds")
        pooled, _ = _pooled_mae(record, method, "development")
        is_selected = "да" if method == selected else "нет"
        lines.append(
            f"| `{_method_text(method)}` | {_kind_name(definition.get('kind'))} | "
            f"{_format_number(validation_mae)} | {_format_number(pooled)} | "
            f"{profile} | {iteration} | {is_selected} |"
        )
    if not shown:
        lines.append("| Validation-метрики не записаны | — | — | — | — | — | — |")

    history_triggered = selection.get("history_round_triggered")
    round_one = selection.get("round_one_pooled_mae", {})
    if not isinstance(round_one, dict):
        round_one = {}
    round_one_scores = [
        (_finite_number(value), method)
        for method, value in round_one.items()
        if _finite_number(value) is not None
    ]
    if round_one_scores:
        first_score, first_method = min(round_one_scores)
        final_score = _pooled_mae(record, selected, "development")[0]
        if history_triggered is True:
            lines += [
                "",
                f"Дополнительный раунд с признаками истории был запущен. Лучший метод первого раунда: "
                f"`{_method_text(first_method)}` — {_format_number(first_score)} с; "
                f"итоговый выбранный метод: `{_method_text(selected)}` — {_format_number(final_score)} с.",
            ]
        elif history_triggered is False:
            lines += [
                "",
                f"Дополнительный раунд с признаками истории не запускался. Лучший метод первого раунда: "
                f"`{_method_text(first_method)}` — {_format_number(first_score)} с; "
                f"итоговый выбранный метод: `{_method_text(selected)}` — {_format_number(final_score)} с.",
            ]
    elif history_triggered is not None:
        lines += ["", f"Раунд с признаками истории: {_yes_no(history_triggered)}."]

    new_fits = selection.get("new_fits")
    lines += ["", f"Новых model fits при выборе: {_format_count(new_fits)}.", ""]
    return lines


def _yes_no(value):
    if value is True:
        return "да"
    if value is False:
        return "нет"
    return "не записано"


def _stop_reason(source):
    reason = source.get("stop_reason")
    labels = {
        "duration_reached": "достигнут лимит длительности",
        "end_of_trace": "конец исходной трассы (EOF)",
        "event_cap_reached": "достигнут лимит событий",
    }
    return labels.get(reason, str(reason) if reason is not None else "не записана")


def _verification_section(records):
    lines = [
        "## Независимая проверка",
        "",
        "| Нагрузка | Замороженные hash-файлы | Проверенный выбор | Validation rows | Development rows | Holdout rows 5 / 6 / 7 | Holdout-метрики | Смеси проверены | Выбранный прогноз восстановлен | Новых fits в проверке |",
        "|---|---:|---|---:|---:|---|---|---|---|---:|",
    ]
    for workload in WORKLOADS:
        verification = records[workload]["verification"]
        holdout_rows = verification.get("holdout_rows_by_day", {}) or {}
        holdout_counts = " / ".join(_format_count(holdout_rows.get(day)) for day in HOLDOUT_DAYS)
        lines.append(
            f"| {workload} | {_format_count(verification.get('frozen_hashes_verified'))} | "
            f"{_method_text(verification.get('selection_verified', 'не записано'))} | "
            f"{_format_count(verification.get('first_day_validation_rows_verified'))} | "
            f"{_format_count(verification.get('development_rows_verified'))} | {holdout_counts} | "
            f"{_yes_no(verification.get('holdout_metrics_verified'))} | "
            f"development: {_yes_no(verification.get('blend_reconstruction_verified'))}; "
            f"holdout: {_yes_no(verification.get('holdout_blend_reconstruction_verified'))} | "
            f"{_yes_no(verification.get('selected_prediction_reconstruction_verified'))} | "
            f"{_format_count(verification.get('new_fits'))} |"
        )

    lines += [
        "",
        "Независимый checker сверяет пять сохранённых метрик (MAE, median absolute error, P90 absolute error, RMSE и MAE log1p) с сохранёнными прогнозами; также проверяет daily coverage, минимум pooled development MAE и замороженные hash-файлы. Значения выше показывают только поля, записанные checker-ом.",
        "",
    ]
    for workload in WORKLOADS:
        verification = records[workload]["verification"]
        audited = verification.get("source_samples_audited")
        skipped = verification.get("source_audit_skipped_reason")
        if isinstance(audited, (int, float)) and not isinstance(audited, bool):
            note = (
                f"{workload}: исходный префикс трассы просканирован; проверено {int(audited):,} "
                "выборочных историй и прогнозов. Это не повторная разметка всех интервалов."
            )
        elif skipped:
            note = f"{workload}: аудит сырых событий пропущен — {skipped}. Сохранённые метрики и hash-файлы проверены отдельно."
        else:
            note = f"{workload}: в verification.json нет подтверждения аудита сырых событий; полный независимый проход по трассе не заявляется."
        lines.append(f"- {note}")
    lines.append("")
    return lines


def _holdout_summary(records):
    lines = ["## Описательный итог holdout", ""]
    for workload in WORKLOADS:
        record = records[workload]
        wins = {"current": 0, "address_median": 0}
        valid_days = 0
        for day in HOLDOUT_DAYS:
            selected = _get(_metric(record, "selected", day, "holdout"), "mae_seconds")
            current = _get(_metric(record, "current", day, "holdout"), "mae_seconds")
            median = _get(_metric(record, "address_median", day, "holdout"), "mae_seconds")
            selected_number = _finite_number(selected)
            current_number = _finite_number(current)
            median_number = _finite_number(median)
            if selected_number is not None:
                valid_days += 1
            if selected_number is not None and current_number is not None and selected_number < current_number:
                wins["current"] += 1
            if selected_number is not None and median_number is not None and selected_number < median_number:
                wins["address_median"] += 1

        selected_mae, _ = _pooled_mae(record, "selected", "holdout")
        current_mae, _ = _pooled_mae(record, "current", "holdout")
        median_mae, _ = _pooled_mae(record, "address_median", "holdout")
        lines.append(
            f"- **{workload}:** pooled selected MAE {_format_number(selected_mae)} с; "
            f"изменение относительно current {_format_improvement(current_mae, selected_mae)}, "
            f"относительно address_median {_format_improvement(median_mae, selected_mae)}. "
            f"По дневным окнам selected лучше current в {wins['current']}/{valid_days} "
            f"и address_median в {wins['address_median']}/{valid_days}."
        )
    lines += [
        "",
        "Счёт дневных окон и pooled MAE — описательные сравнения этих нагрузок и периодов. Статистическую значимость не проверяли; это не гарантия результата на других трассах или нагрузках.",
        "",
    ]
    return lines


def render_report(records):
    """Build Markdown from already-completed runner and checker artifacts."""
    _validate_artifacts(records)
    lines = [
        "# Улучшение MAE прогноза следующего чтения",
        "",
        "Отчёт сформирован только из `selection.json`, `holdout.json` и `verification.json`; обучение здесь не запускается.",
        "",
        "Target — время от записи до первого последующего чтения того же точного начального Offset. Промежуточная перезапись не отменяет пример: прогноз касается адреса, а не версии данных, созданной конкретной записью. Время до перезаписи в этом эксперименте не измерялось, поэтому нельзя утверждать, что MAE ниже этого времени.",
        "",
        "Дни 2–4 уже были просмотрены и использованы как development для выбора одного метода отдельно на каждой нагрузке; их нельзя считать новым независимым тестом. После фиксации выбора проверяются отдельные будущие дни 5–7. В метрику входят только интервалы, завершившиеся чтением до конца соответствующего окна.",
        "",
        "## Короткий ответ: новые дни 5–7",
        "",
    ]
    for workload in WORKLOADS:
        record = records[workload]
        current = _pooled_mae(record, "current", "holdout")[0]
        selected = _pooled_mae(record, "selected", "holdout")[0]
        baseline = _pooled_mae(record, "address_median", "holdout")[0]
        scale, unit = (60, "мин") if workload == "usr_1" else (1, "с")
        current_text = _format_number(current / scale, 2) if current is not None else "—"
        selected_text = _format_number(selected / scale, 2) if selected is not None else "—"
        change = _improvement_percent(current, selected)
        if change is None:
            comparison = "Изменение к прежней модели не определено."
        elif change >= 0:
            comparison = f"Ошибка ниже прежней на {change:.1f}%."
        else:
            comparison = f"Ошибка выше прежней на {-change:.1f}%; этот кандидат не рекомендуется вместо прежней модели."
        lines.append(
            f"- **{workload}:** средняя абсолютная ошибка по всем завершённым записям новых дней: "
            f"**{current_text} → {selected_text} {unit}**. "
            f"{comparison} Снижение к простой медиане адреса {_format_improvement(baseline, selected)}."
        )
    lines += [
        "",
        "Числа относятся к одним и тем же записям внутри каждого окна. Положительный процент — улучшение, отрицательный — ухудшение. Отбор направлен на перенос на следующие дни, а не только на минимум ошибки короткого validation первого дня.",
        "",
        "## Выбранный метод по нагрузке",
        "",
        "| Нагрузка | Метод | Вид | Pooled development MAE, с |",
        "|---|---|---|---:|",
    ]
    for workload in WORKLOADS:
        record = records[workload]
        selection = record["selection"]
        method = selection["selected_method"]
        definition = _get(selection, "definitions", method, default={}) or {}
        pooled = _pooled_mae(record, method, "development")[0]
        lines.append(
            f"| {workload} | `{_method_text(method)}` | {_kind_name(definition.get('kind'))} | "
            f"{_format_number(pooled)} |"
        )

    lines += ["", "## Дневные результаты: MAE в секундах", ""]
    for workload in WORKLOADS:
        lines.extend(_day_table(records[workload], workload, "development"))
    for workload in WORKLOADS:
        lines.extend(_day_table(records[workload], workload, "holdout"))

    lines += [
        "## Count-weighted pooled MAE по каждой нагрузке",
        "",
        "Pooled MAE — сумма дневных MAE, взвешенных числом завершённых интервалов, делённая на общее число таких интервалов в split. Нагрузки не объединяются в общий средний результат. Изменение считается как `(MAE reference − MAE selected) / MAE reference`; плюс означает снижение ошибки, минус — ухудшение. Процент относительно current использует current в знаменателе, а относительно baseline — address_median.",
        "",
        "| Нагрузка | Split | N | Pooled current, с | Pooled address_median, с | Pooled selected, с | Улучшение к current | Улучшение к address_median |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for workload in WORKLOADS:
        for split in ("development", "holdout"):
            lines.extend(_pooled_table(records[workload], workload, split))

    lines += ["", "## Validation и детали выбора", ""]
    for workload in WORKLOADS:
        lines.extend(_validation_section(records[workload], workload))

    lines += ["## Покрытие holdout и граница трассы", ""]
    for workload in WORKLOADS:
        holdout = records[workload]["holdout"]
        source = holdout.get("source", {})
        if not isinstance(source, dict):
            source = {}
        requested_hours = source.get("requested_hours", 168)
        cap = source.get("max_events", 200_000_000)
        lines.append(
            f"- **{workload}:** остановка чтения источника — {_stop_reason(source)} "
            f"(запрошено {_format_count(requested_hours)} ч, лимит {_format_count(cap)} событий); "
            f"new_fits holdout: {_format_count(holdout.get('new_fits'))}."
        )
        if (source.get("stop_reason") == "end_of_trace"
                or ("first_excluded_timestamp" in source
                    and source["first_excluded_timestamp"] is None)):
            lines.append(
                "  EOF: конец трассы наступил без следующего исключённого события; последний день может быть частичным."
            )
        for day in HOLDOUT_DAYS:
            coverage = _coverage(records[workload], day, "holdout")
            observed, eligible, censored, fraction = _coverage_text(coverage)
            entry = _get(holdout, "days", day, default={}) or {}
            end_seconds = _finite_number(entry.get("end_seconds"))
            end_text = "конец не записан" if end_seconds is None else f"до {end_seconds / 3600:.2f} ч"
            partial = entry.get("partial_day")
            if partial is None and end_seconds is not None:
                partial = end_seconds < int(day) * 86400
            partial_text = ", частичный день" if partial else ""
            lines.append(
                f"  - День {day}: {observed} из {eligible} подходящих записей, "
                f"{censored} незавершённых, покрытие {fraction}; "
                f"{end_text}{partial_text}."
            )
    lines += [
        "",
        "`EOF`/частичный день не превращается в полноценное 24-часовое окно. Незавершённые к концу окна интервалы не включены в MAE, их число отражено в coverage как right-censored.",
        "",
    ]
    lines.extend(_holdout_summary(records))
    lines.extend(_verification_section(records))

    lines += [
        "## Ограничения интерпретации",
        "",
        "- MAE условна на наблюдаемых чтениях: долгие и незавершённые интервалы могут быть исключены; сверяйте N и coverage рядом с метриками.",
        "- Сравнение использует один и тот же набор завершённых примеров внутри каждого дня. Точный начальный Offset не описывает пересекающиеся диапазоны.",
        "- Development уже был просмотрен; holdout — отдельные временные окна, но не независимая выборка из генеральной совокупности. Выбор по development и последующая проверка не дают гарантии переноса.",
        "- MAE со временем до перезаписи не сравнивалась. Эксперимент не различает судьбу версий данных и не оценивает производительность SSD.",
        "",
        "## Воспроизведение",
        "",
        "Команды select/evaluate предназначены для чистого каталога results/mae-improvement и отказываются перезаписывать завершённый эксперимент. Запускайте выбор для обеих нагрузок до открытия holdout; затем завершите обе оценки и checker. Команда отчёта только читает готовые JSON и не обучает модели.",
        "",
        "```bash",
        "python -m read_prediction.experiments.mae_improvement select usr_1",
        "python -m read_prediction.experiments.mae_improvement select prxy_1",
        "python -m read_prediction.experiments.mae_improvement evaluate usr_1",
        "python -m read_prediction.experiments.mae_improvement evaluate prxy_1",
        "python -m read_prediction.checks.mae_improvement --workload usr_1",
        "python -m read_prediction.checks.mae_improvement --workload prxy_1",
        "python -m read_prediction.checks.mae_source_audit --workload usr_1",
        "python -m read_prediction.checks.mae_source_audit --workload prxy_1",
        "python -m read_prediction.mae_reporting",
        "```",
        "",
        "Поиск ограничен максимумом 1000 деревьев на fit и early stopping после 50 итераций без улучшения validation MAE. Если срабатывает условие history-раунда, дополнительно проверяются четыре фиксированных кандидата; никакой fit не выполняется на holdout. Сохраняются пять метрик: MAE, median absolute error, P90 absolute error, RMSE и MAE log1p.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        records = _load_artifacts()
        report = render_report(records)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    output = REPORTS / "mae-improvement.ru.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report)
    print(f"Сохранён отчёт: {output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
