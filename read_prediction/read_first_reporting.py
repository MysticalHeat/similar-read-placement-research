"""Render selective and full-population results without mixing denominators."""

import json

from read_prediction.paths import PROJECT_ROOT


def percent(value):
    return "—" if value is None else f"{value:.2%}"


def main():
    lines = ["# Двухэтапный прогноз: Read до повторной Write", "",
             "Модель сначала оценивает вероятность Read-first, затем выдаёт прогноз времени для выбранной группы. Порог выбирается на дне 6 до повторной диагностики дня 7. Все дни уже просмотрены: нового независимого holdout нет.", "",
             "## Выборочный режим на дне 7", "",
             "Покрытие здесь — доля прежних **оценённых завершённых примеров**, не всех Write трассы. Точность класса — доля истинных Read-first среди выбранных моделью. Ошибка относительно перезаписи включает все выбранные примеры, в том числе ошибочно выбранные Write-first. Неизвестные перезаписи учтены консервативной нижней границей.", "",
             "| Нагрузка | Выбрано / оценено | Покрытие | Точность Read-first | Ошибка меньше перезаписи в выбранной группе | MAE выбранной группы, с | Диагностическое условие |",
             "|---|---:|---:|---:|---:|---:|---|"]
    records = {}
    details = []
    for workload in ("usr_1", "prxy_1"):
        folder = PROJECT_ROOT / "results/read-first" / workload
        if not (folder / "verification.json").exists():
            raise ValueError(f"Verify {workload} first")
        result = json.loads((folder / "diagnostic.json").read_text())
        selection = json.loads((folder / "selection.json").read_text())
        records[workload] = result
        gate = result["selective"]
        metric = gate["selected"]
        error_rate = percent(metric["pass_lower_bound"]) if metric else "—"
        mae = f"{metric['mae_seconds']:.3f}" if metric else "—"
        lines.append(f"| {workload} | {gate['selected_n']:,}/{result['routed_all']['n']:,} | {percent(gate['coverage'])} | {percent(gate['read_first_precision'])} | {error_rate} | {mae} | {'выполнено' if gate['qualifies_selective'] else 'не выполнено'} |")
        val = selection["validation"][selection["chosen"]]
        details += [f"### {workload}", "", f"Выбран `{selection['chosen']}` из {len(selection['validation'])} комбинаций.", "",
                    f"На validation выбранных {val['selected_n']:,}, coverage {percent(val['coverage'])}, precision {percent(val['read_first_precision'])}; условие выборочного режима {'выполнено' if val['qualifies_selective'] else 'не выполнено'}.", "",
                    f"На дне 7 отобрано {gate['selected_n']:,}, recall Read-first {percent(gate['read_first_recall'])}. Порог после refit не перенастраивался.", ""]
        if workload == "usr_1":
            details += ["Ни одна validation-комбинация не выполнила одновременно precision >=90%, долю проходящих >=90% и диагностическое coverage >=10%. Fallback выбрал лишь несколько validation-примеров при высоком пороге; после refit на дне 7 выборка пуста. Это не рабочий результат и не достижение 90%.", ""]
        details += ["Лучшие validation-комбинации с coverage >=10% (описательная таблица, не новый выбор):", "",
                    "| Комбинация | Покрытие | Precision Read-first | Проходят | MAE, с |",
                    "|---|---:|---:|---:|---:|"]
        broad = [(name, value) for name, value in selection["validation"].items() if value["coverage"] >= .1]
        broad.sort(key=lambda item: (-min(item[1]["read_first_precision"], item[1]["selected"]["pass_lower_bound"]), -item[1]["coverage"]))
        for name, metric in broad[:6]:
            details.append(f"| {name} | {percent(metric['coverage'])} | {percent(metric['read_first_precision'])} | {percent(metric['selected']['pass_lower_bound'])} | {metric['selected']['mae_seconds']:.3f} |")
        details.append("")
    lines += ["", "Диагностическое условие выборочного режима: обе доли >=90% при coverage >=10%. Ограничение 10% использовано для поиска, а не согласовано как допустимое рабочее покрытие.", "",
              "## Общий исходный критерий на всех оценённых примерах", "",
              "На невыбранных записях используется current. Ни одна запись не исключается из общего знаменателя.", "",
              "| Нагрузка | Прежняя модель: проходят | Routed: проходят | Routed MAE, с | Общие 90% |",
              "|---|---:|---:|---:|---|"]
    for workload, result in records.items():
        metric = result["routed_all"]
        lines.append(f"| {workload} | {percent(result['current_all']['pass_lower_bound'])} | {percent(metric['pass_lower_bound'])} | {metric['mae_seconds']:.3f} | {'достигнуты' if metric['meets_90_percent'] else 'не достигнуты'} |")
    lines += ["", "В обоих случаях для времени выбран current. Поэтому routed-прогноз совпадает с прежней моделью. На prxy_1 улучшился отбор группы, а не точечный прогноз времени на всём наборе.", "",
              "Прежний отдельный overwrite90-кандидат usr_1 проходил критерий на том же дне в 50.18% случаев; переход на текущий routed не улучшает его. Этот эксперимент не рекомендуется как замена лучшему предыдущему прогнозу usr_1.", "",
              "## Детали выбора", "", *details,
              "## Область применимости и следующий эксперимент", "",
              "- Отбор сделан по причинным признакам до будущего Read/Write, а не по известной после события правильной подгруппе. История исходов обновляется только после завершённого Read; это исключает будущее условие попадания пары в сохранённый набор.",
              "- Сохранённая выборка содержит только Read, завершившиеся до конца дневного окна. Незавершённые Write не входили в обучение/оценку gate; precision и coverage на всех Write не измерены. Обучение на этой условной выборке может не перенестись на все Write.",
              "- Перезапись — тот же начальный Offset. Физические блоки, перекрытия диапазонов и completion time I/O не моделируются.",
              "- Высокая доля error<overwrite в выбранной группе не доказывает точную группировку по времени: MAE и ширина временных групп остаются отдельными критериями.",
              "- Следующее направление: построить выборку всех Write с исходами Read-first/Write-first/цензурирование, добавить причинные признаки текущего burst (число Write после Read, интервалы между Write, размер и соседние адреса), затем проверять точность и покрытие на новых данных. Одного повышения порога вероятности недостаточно для расширения покрытия.", "",
              "## Проверка", "",
              "Пересчитаны независимо 36 validation-комбинаций каждой нагрузки, все строки дня 7, precision/recall/coverage, выборочный и общий error<overwrite. Для 64 примеров каждой нагрузки прямым поиском прошлых завершённых пар восстановлены признаки, вероятности gate и прогнозы времени. Проверены hashes входов, кода, validation-моделей и frozen-моделей. Новых fits в checker нет.", "",
              "```bash", "uv run python -m read_prediction.experiments.read_first usr_1",
              "uv run python -m read_prediction.experiments.read_first prxy_1",
              "uv run python -m read_prediction.checks.read_first usr_1",
              "uv run python -m read_prediction.checks.read_first prxy_1",
              "uv run python -m read_prediction.read_first_reporting", "```", "",
              "Эксперимент отказывается перезаписывать существующие папки. Протокол: `docs/protocols/read-first-protocol.md`.", ""]
    path = PROJECT_ROOT / "reports/read-first.ru.md"
    path.write_text("\n".join(lines))
    print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
