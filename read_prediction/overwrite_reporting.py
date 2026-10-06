"""Add population-wide censoring bounds to the paired overwrite comparison."""

import hashlib
import json
from pathlib import Path

import numpy as np

from read_prediction.experiments.overwrite_comparison import OUTPUT, report
from read_prediction.paths import PROJECT_ROOT


def lifetime_bounds(overwrite, censor_lower_bound):
    known = np.isfinite(overwrite)
    if not len(overwrite):
        raise ValueError("Empty comparison cohort")
    minimum = np.where(known, overwrite, censor_lower_bound)
    observed = np.sort(overwrite[known])
    left, right = (len(overwrite) - 1) // 2, len(overwrite) // 2
    # Maximal possible median places unknown lifetimes after the observed ones.
    median_upper = (float((observed[left] + observed[right]) / 2)
                    if right < len(observed) else None)
    return {"n": len(overwrite), "censored_n": int((~known).sum()),
            "mean_lower_bound_seconds": float(minimum.mean()),
            "mean_upper_bound_seconds": float(observed.mean()) if known.all() else None,
            "median_lower_bound_seconds": float(np.median(minimum)),
            "median_upper_bound_seconds": median_upper}


def criterion(mae, lower, upper):
    if mae < lower:
        return "выполняется даже по нижней границе"
    if upper is not None and mae >= upper:
        return "не выполняется даже по верхней границе"
    return "не определено из-за неизвестных интервалов"


def main():
    report()
    path = PROJECT_ROOT / "reports/overwrite-comparison.ru.md"
    text = path.read_text()
    table_start = text.index("| Нагрузка / метод |")
    table_end = text.index("## Дневные показатели")
    section = text[table_start:table_end].splitlines()
    rows = [line for line in section if line.startswith("|")]
    notes = [line for line in section if line.startswith("**")]
    text = text[:table_start] + "\n".join(rows) + "\n\n" + "\n\n".join(notes) + "\n\n" + text[table_end:]
    path.write_text(text)
    lines = ["", "## Вся исходная выборка: неизвестные перезаписи не исключаем", "",
             "Предыдущие таблицы сравнивают совпадающие записи с известной следующей Write. Исключение неизвестных интервалов меняет выборку. Ниже используем все исходные записи и наблюдаемые нижние пределы неизвестных интервалов. Среднее время жизни может быть сильно увеличено редкими долгими интервалами; отдельно проверяем медиану и долю проходящих записей.", "",
             "| Нагрузка / метод | MAE всех записей, с | Средний интервал не меньше, с | Медианный интервал: нижняя–верхняя границы, с | Общая доля error < overwrite: границы |",
             "|---|---:|---:|---|---:|"]
    explanations = []
    for workload in ("usr_1", "prxy_1"):
        folder = OUTPUT / workload
        record = json.loads((folder / "summary.json").read_text())
        duration_parts, lower_parts = [], []
        for day in (5, 6, 7):
            with np.load(folder / f"day{day}.comparison.npz") as data:
                duration_parts.append(data["overwrite_seconds"])
                lower_parts.append(data["overwrite_censor_lower_bound_seconds"])
        bounds = lifetime_bounds(np.concatenate(duration_parts), np.concatenate(lower_parts))
        assert bounds["n"] == record["pooled"]["n"]
        method = "selected" if workload == "usr_1" else "current"
        metric = record["pooled"]["methods"][method]
        mae = metric["all_mae_seconds"]
        high = bounds["median_upper_bound_seconds"]
        high_text = f"{high:.3f}" if high is not None else "не ограничена"
        lines.append(f"| {workload} / {method} | {mae:.3f} | {bounds['mean_lower_bound_seconds']:.3f} | {bounds['median_lower_bound_seconds']:.3f}–{high_text} | {metric['fraction_error_lt_overwrite_lower_bound']:.2%}–{metric['fraction_error_lt_overwrite_upper_bound']:.2%} |")
        mean_test = criterion(mae, bounds["mean_lower_bound_seconds"], bounds["mean_upper_bound_seconds"])
        median_test = criterion(mae, bounds["median_lower_bound_seconds"], high)
        explanations.append(f"- **{workload}:** сравнение MAE со средним интервалом — {mean_test}; с медианным интервалом — {median_test}. Неизвестных интервалов {bounds['censored_n']:,}/{bounds['n']:,}.")
        bounds["reporter_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (folder / "censoring-bounds.json").write_text(json.dumps(bounds, indent=2) + "\n")
    lines += ["", *explanations, "",
              "Условие на средние не означает, что ошибка мала для большинства записей. Оценка на наблюдённых перезаписях и границы для всей исходной выборки отвечают на разные вопросы; нельзя смешивать MAE одного набора со средним интервалом другого.", "",
              "Полный отчёт с границами для всей выборки воспроизводится командой `uv run python -m read_prediction.overwrite_reporting`.", ""]
    with path.open("a") as output:
        output.write("\n".join(lines))
    print("Added full-cohort censoring bounds", flush=True)


if __name__ == "__main__":
    main()
