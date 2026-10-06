"""Render the verified fixed-mixture development report."""

import json

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT


def main():
    folder = PROJECT_ROOT / "results/mixture/prn_1"
    verification = json.loads((folder / "verification.json").read_text())
    assert verification["passed"] and verification["metrics_fingerprint"] == fingerprint(folder / "metrics.json")
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    frozen = json.loads((folder / "frozen.json").read_text())
    metrics = json.loads((folder / "metrics.json").read_text())
    lines = ["# prn_1: смеси log-L2/raw-L1", "",
             "**Компромисс не устранён: смеси снижают MAE, но уменьшают долю проходов относительно log-L2.** "
             "Ни одна из трёх смесей не прошла заранее заданное validation условие. "
             "Frozen метод остался log-L2 в обеих постановках; веса постфактум не менялись.", "",
             "Новые модели не обучались. Смешивали сохранённые прогнозы в секундах: "
             "75/25, 50/50, 25/75 (log-L2/raw-L1). Validation — день 4, development оценка — дни 5–7. "
             "Все методы на идентичных observed строках; это уже просмотренные дни, не новый holdout.", "",
             "Правило: выбрать минимальную validation MAE среди смесей, которые строго улучшают MAE "
             "log-L2 и не снижают confirmed pass count. Если таких нет — log-L2. "
             "Отдельно фиксируется MAE-best mixture как диагностика, не primary замена. "
             "90% не достигнуты.", ""]
    for rule in ("same_start", "range"):
        data = metrics[rule]["pooled"]
        baseline = data["log_l2"]
        lines.extend([f"## {rule}", "", f"Frozen: **{frozen[rule]['selected']}**. "
                      f"Допустимых смесей: {len(frozen[rule]['eligible_mixtures'])}. "
                      f"MAE-best смесь: {frozen[rule]['mae_best_mixture']}.", "",
                      "### Validation: день 4", "", "| Метод | MAE, s | Pass lower |",
                      "|---|---:|---:|"])
        for method, value in frozen[rule]["validation"].items():
            lines.append(f"| {method} | {value['metrics']['mae_seconds']:,.2f} | {value['pass_lower']*100:.2f}% |")
        lines.extend(["", f"### Дни 5–7: N={baseline['observed_reads']:,}, "
                      f"все Write={baseline['all_writes']:,}, coverage={baseline['coverage']*100:.2f}%", "",
                      "| Метод | MAE, s | ΔMAE vs log-L2 | P90, s | Pass lower–upper | Δpass, п.п. |",
                      "|---|---:|---:|---:|---:|---:|"])
        for method, value in data.items():
            lines.append(f"| {method} | {value['metrics']['mae_seconds']:,.2f} | "
                         f"{(value['metrics']['mae_seconds']/baseline['metrics']['mae_seconds']-1)*100:+.2f}% | "
                         f"{value['metrics']['p90_absolute_error_seconds']:,.2f} | "
                         f"{value['pass_lower']*100:.2f}–{value['pass_upper']*100:.2f}% | "
                         f"{(value['pass_lower']-baseline['pass_lower'])*100:+.2f} |")
        lines.extend(["", "### Target-срезы (oracle, не gate)", "",
                      "| Метод | <6h: N / MAE, s / pass | >=6h: N / MAE, s / pass |",
                      "|---|---:|---:|"])
        for method, value in data.items():
            short, long = [value["target_slices"][key] for key in ("under_6h", "at_least_6h")]
            lines.append(f"| {method} | {short['n']:,} / {short['mae_seconds']:,.2f} / {short['pass_lower']*100:.2f}% | "
                         f"{long['n']:,} / {long['mae_seconds']:,.2f} / {long['pass_lower']*100:.2f}% |")
        lines.extend(["", "### Все дни", "", "| День | Метод | MAE, s | Pass lower |", "|---|---|---:|---:|"])
        for day in range(5, 8):
            for method, value in metrics[rule][str(day)].items():
                lines.append(f"| {day} | {method} | {value['metrics']['mae_seconds']:,.2f} | {value['pass_lower']*100:.2f}% |")
        lines.append("")
    lines.extend(["## Вывод", "",
                  "Простое постоянное смешивание не даёт нужного одновременного выигрыша. "
                  "В этих трёх кандидатах больший вес raw-L1 снижает MAE ценой основного критерия. "
                  "По pooled MAE чистая raw-L1 лучше всех трёх смесей; смеси остаются промежуточным "
                  "компромиссом, а не новым лучшим решением. Это не доказательство невозможности "
                  "любых смесей или адаптивного выбора; здесь проверены только три заранее заданных веса.", "",
                  "Проверки: 8 окон × 5 методов; смеси восстановлены из parent forecasts, "
                  "selection/metrics/bounds/slices/pooled и hashes независимо проверены. "
                  "86 unit-тестов прошли. Протокол: `docs/protocols/mixture-protocol.md`. "
                  "Артефакты: `results/mixture/prn_1/`.", "",
                  "```bash", ".venv/bin/python -m read_prediction.experiments.mixture",
                  ".venv/bin/python -m read_prediction.checks.mixture",
                  ".venv/bin/python -m read_prediction.mixture_reporting", "```"])
    report = PROJECT_ROOT / "reports/mixture.ru.md"
    report.write_text("\n".join(lines) + "\n")
    print(report)


if __name__ == "__main__":
    main()
