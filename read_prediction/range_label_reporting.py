"""Render the range-label day-7 diagnostic report."""

import json

from read_prediction.paths import PROJECT_ROOT

CAT_NAMES = {
    0: "то же начало и тот же размер",
    1: "то же начало, Read меньше",
    2: "то же начало, Read больше",
    3: "Read начинается раньше, частично покрывает",
    4: "Read начинается внутри диапазона",
    5: "Read покрывает весь диапазон Write",
}


def gib(value):
    return f"{value / 2**30:.2f} GiB"


def load(workload):
    folder = PROJECT_ROOT / "results/range-label" / workload
    if not (folder / "verification.json").exists():
        raise ValueError(f"Verify range-label/{workload} first")
    return json.loads((folder / "labeling.json").read_text())


def main():
    lines = [
        "# Разметка по диапазонам байтов против точного начального Offset",
        "",
        "Диагностика единицы данных: прежняя разметка сопоставляла Read и Write по точному начальному Offset и игнорировала Size. Новая разметка использует полуинтервалы байтов на сетке 512 Б: любое пересечение диапазонов означает чтение или перезапись записанной версии, первое событие по порядку строк решает исход. Протокол зафиксирован до расчёта метрик: `docs/protocols/range-label-protocol.md`. День 7 повторно просмотрен: это development-диагностика, нового holdout нет. Модели не переобучаются, frozen selections не изменяются.",
        "",
        "## Проверенные факты о данных",
        "",
        "Во всех 45 283 980 (usr_1) и 168 638 964 (prxy_1) событиях загруженных префиксов Offset и Size делятся на 512 без остатка, поэтому байтовые диапазоны — объединения полных 512-байтовых блоков и разметка по блокам 512 Б совпадает с байтовой точно. Сетка 4 KiB невозможна: у usr_1 45 283 936 событий имеют Offset % 4096 = 3584. Характерные размеры: usr_1 — 74,09% запросов по 64 KiB; prxy_1 — 57,43% по 8 KiB. Поля источника: Timestamp — время поступления (FILETIME), ResponseTime — длительность выполнения в тех же единицах (SNIA IOTTA README §3, проверено 2026-09-30); основная разметка, как и все прежние этапы, использует issue-to-issue, ResponseTime в кэшах не сохраняется.",
        "",
        "## Воспроизведение прежней разметки",
        "",
        "Переопределённое в новом модуле правило «точный начальный Offset» воспроизвело опубликованные счётчики дня 7 точно, а подтверждённая доля `|pred − target| < budget` на прежнем наблюдаемом наборе совпала с опубликованной до 10⁻⁹.",
        "",
        "| Нагрузка | Все Write | Read-first (прежняя) | Write-first (прежняя) | Цензурированные (прежняя) | Опубликованная доля | Воспроизведённая |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        record = load(workload)
        old, n = record["old_outcomes"], record["old_outcomes"]["all_writes"]
        criteria = record["criteria"]
        lines.append(f"| {workload} | {n:,} | {old['read_first']:,} ({old['read_first']/n:.2%}) | {old['write_first']:,} ({old['write_first']/n:.2%}) | {old['censored']:,} ({old['censored']/n:.2%}) | {criteria['published_old_pass_lower_bound']:.4%} | {criteria['old_observed_current_pass']:.4%} |")
    lines += [
        "",
        "## Исходы дня 7 по диапазонам",
        "",
        "| Нагрузка | Read-first (диапазоны) | Write-first (диапазоны) | Цензурированные (диапазоны) |",
        "|---|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        record = load(workload)
        new, n = record["range_outcomes"], record["range_outcomes"]["all_writes"]
        lines.append(f"| {workload} | {new['read_first']:,} ({new['read_first']/n:.2%}) | {new['write_first']:,} ({new['write_first']/n:.2%}) | {new['censored']:,} ({new['censored']/n:.2%}) |")
    lines += [
        "",
        "Диапазонная разметка находит первые события, которых правило точного начала не видело: частичные чтения и частичные перезаписи внутри записанного диапазона.",
        "",
        "## Критерий «ошибка меньше перезаписи» без переобучения",
        "",
        "Используются сохранённые per-Write прогнозы `current` из `results/all-write` (модель обучалась на прежних targets). Сравнение на идентичных наборах публикуется отдельно от сравнения знаменателей; каждый знаменатель указан явно.",
        "",
        "| Нагрузка | Набор | N | current: подтверждённая доля | Нулевой прогноз: доля |",
        "|---|---|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        c = load(workload)["criteria"]
        rows = [
            ("прежняя разметка, наблюдённые", c["old_observed_n"], c["old_observed_current_pass"], c["old_observed_zero_pass"]),
            ("диапазоны, наблюдённые", c["range_observed_n"], c["range_observed_current_pass"], c["range_observed_zero_pass"]),
            ("наблюдённые в обеих, старые targets", c["both_observed_n"], c["both_current_pass_old_target"], c["both_zero_pass_old_target"]),
            ("наблюдённые в обеих, новые targets", c["both_observed_n"], c["both_current_pass_new_target"], c["both_zero_pass_new_target"]),
        ]
        for label, count, current_pass, zero_pass in rows:
            lines.append(f"| {workload} | {label} | {count:,} | {current_pass:.4%} | {zero_pass:.4%} |")
    lines += [
        "",
        "Отдельно — подмножество Write с изменившимся совпавшим Read (знаменатель = число таких Write):",
        "",
        "| Нагрузка | N | current по старым targets | current по новым targets |",
        "|---|---:|---:|---:|",
    ]
    for workload in ("usr_1", "prxy_1"):
        c = load(workload)["criteria"]
        lines.append(f"| {workload} | {c['changed_read_n']:,} | {c['changed_current_pass_old_target']:.4%} | {c['changed_current_pass_new_target']:.4%} |")
    lines += ["", "## Интерпретация", ""]
    for workload in ("usr_1", "prxy_1"):
        record = load(workload)
        n = record["range_outcomes"]["all_writes"]
        changed, partial = record["changed"], record["partiality"]
        categories = partial["matched_read_categories"]
        matched = partial["matched_reads"]
        details = [f"{CAT_NAMES[int(key)]}: {value:,} ({value/matched:.2%})" for key, value in sorted(categories.items(), key=lambda kv: int(kv[0]))]
        lines += [
            f"### {workload}",
            "",
            f"Переходы состояний (старая → новая разметка): цензурированные → Read-first {record['state_transitions']['old-1_new1']:,}; Read-first → Write-first {record['state_transitions']['old1_new0']:,}; Write-first → Read-first {record['state_transitions']['old0_new1']:,}.",
            "",
            f"У {changed['read_match_changed']:,} Write ({changed['read_match_changed']/n:.2%} всех, {changed['read_match_changed_bytes']/changed['total_write_request_bytes']:.2%} суммы размеров Write-запросов, {gib(changed['read_match_changed_bytes'])}) совпавший Read изменился; у {changed['overwrite_match_changed']:,} ({gib(changed['overwrite_match_changed_bytes'])}) изменилась совпавшая перезапись. Повторные записи считаются повторно, это не объём уникальных данных.",
            "",
            f"Среди {matched:,} совпавших первых Read по диапазонам: " + "; ".join(details) + ".",
            "",
            f"Из Read-first с последующей пересекающей перезаписью ({partial['read_first_with_intersecting_overwrite']:,}) у {partial['partial_overwrite_of_read_first']:,} перезапись лишь частична и консервативно уничтожает версию целиком (вариант A протокола).",
            "",
        ]
    lines += [
        "### Что это означает",
        "",
        "- На prxy_1 запросы малы и совпадения почти всегда полного диапазона: диапазонная разметка меняет исход лишь у 10 206 из 8,46 млн Write, а критерии почти не двигаются (68.7978% → 68.7975% на идентичных строках). Прежние выводы для prxy_1 устойчивы к определению пересечения.",
        "- На usr_1 эффект большой: 64 KiB записи читаются частями. Подтверждённых Read-first стало 198 864 вместо 127 352 (+56%), цензурированных 183 203 вместо 264 043, а доля проходящих на идентичных строках выросла с 47.49% до 52.62% (55.60% на новом наблюдённом наборе). Нулевой прогноз на идентичных строках: 46.76% → 50.86%. Достичь 90% по-прежнему не удалось ни на одном наборе.",
        "- У 7 951 Write прежняя разметка считала исход Read-first, хотя по диапазонам раньше наступает пересекающая перезапись: прежние targets для них соответствовали чтению уже перезаписанных байтов. Одновременно 50 916 бывших цензурированных получили наблюдённый Read через частичные чтения. «Время чтения записанной версии» требует диапазонной разметки; правило точного начала искажает и наблюдаемость, и порядок событий на usr_1.",
        "- Изменившийся совпавший Read у usr_1 проходит критерий в 62.45% против 18.93% по старым targets. Это чувствительность разметки, а не улучшение модели: текущая модель обучалась на прежних targets, и до переобучения прямое сравнение невозможно.",
        "- Консерватизм варианта A заметен только на usr_1: 10 788 из 137 942 Read-first с перезаписью (7.82%) перезаписаны частично. Поблочное выживание версий (вариант B) может вернуть часть таких случаев в Read-first, но его влияние ограничено.",
        "",
        "## Ограничения",
        "",
        "- Все дни 5–7 уже просмотрены; результаты диагностические и не заменяют независимой проверки.",
        "- Прогнозы current получены из моделей, обученных на прежней разметке; критерии на новых targets показывают чувствительность, а не качество переобученной модели.",
        "- Read-first не гарантирует полезный прогноз времени: нулевой прогноз проходит почти так же хорошо, поэтому рядом с 90% нужны MAE/P90 и качество временных групп.",
        "- Равные timestamps разрешаются порядком строк, момент прогноза — поступление запроса; чувствительность к временам завершения (Timestamp + ResponseTime) по протоколу проверяется отдельно ограниченной выборкой.",
        "- Вариант B (поблочное выживание версий), время чтения именно записанной версии и работа с Write-first — следующие решения после этого этапа.",
        "",
        "## Проверка и воспроизведение",
        "",
        "Прежняя разметка воспроизвела опубликованные счётчики и подтверждённую долю точно. Независимая медленная реализация совпала с быстрой на 64 случайных Write каждой нагрузки (RNG42) по всем четырём правилам; счётчики исходов и критерии пересчитаны из сохранённых массивов; hashes данных и кода зафиксированы в `labeling.json`; checker не обучает модели.",
        "",
        "```bash",
        "uv run python -m read_prediction.experiments.range_label usr_1",
        "uv run python -m read_prediction.experiments.range_label prxy_1",
        "uv run python -m read_prediction.checks.range_label usr_1",
        "uv run python -m read_prediction.checks.range_label prxy_1",
        "uv run python -m read_prediction.range_label_reporting",
        "```",
        "",
        "Эксперимент отказывается перезаписывать готовый каталог. Протокол: `docs/protocols/range-label-protocol.md`.",
        "",
    ]
    path = PROJECT_ROOT / "reports/range-label.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
