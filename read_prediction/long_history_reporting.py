"""Render frozen long-history development comparisons."""

import json

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT


def main():
    lines = ["# Трёхдневный train и суточный validation: результаты", "",
             "**Частичный эффект: MAE prn_1 улучшилась, proj_1 — нет. Общие 90% не достигнуты.** "
             "Это development: будущие дни этих нагрузок уже были просмотрены. "
             "Все сравнения ниже — на одинаковых observed Write дней 5–7, не с прежним pooled дней 2–7.", "",
             "## Постановка", "",
             "Train [0,72h), validation [72h,96h), оценка дни 5–7, по 24h окнам. "
             "Модели и baseline заморожены после train. Признаки прежние, веса моделей/медианы "
             "на validation не дообучались. Два фиксированных LightGBM all-features: log-L2 и raw-L1; "
             "третья кандидатура — адресная training median с global fallback. "
             "Выбор по validation lower pass; MAE-best фиксируется отдельно. "
             "Старые модель и адресная медиана — benchmarks, не кандидаты выбора.", "",
             "Train truth может длиться до 72h, validation/future truth — до 24h. "
             "Длинный train расширяет observed label distribution, а не только количество строк. "
             "Write-first не отменяет target. Наблюдаемое Read ограничено своим окном; неизвестные "
             "перезаписи дают pass bounds, не считаются failures.", "",
             "## Главные выводы", "",
             "- prn_1: новый log-L2 снижает pooled MAE примерно на 15–17%, raw-L1 — на 25–28% "
             "относительно прежней модели. Raw-L1 заметно лучше на >=6h ожиданиях, "
             "но хуже на коротких; поэтому общий pass ниже, чем у log-L2.",
             "- proj_1: новая log-L2 повышает pass, но MAE немного хуже. Raw-L1 и новая медиана "
             "по pooled MAE также хуже прежних. Расширение train не является универсальным исправлением.",
             "- Основной frozen выбор proj_1 same-start — адресная медиана, она проиграла в будущем. "
             "Не заменяем её постфактум на более удачный кандидат. Для proj_1 range и обеих "
             "постановок prn_1 основной выбор — log-L2.",
             "- На prn_1 MAE-best validation выбрал raw-L1. Эта альтернативная политика была "
             "зафиксирована до оценок, не выбрана по будущим результатам. "
             "Raw-L1 same-start немного лучше новой медианы по MAE, range — немного хуже неё.",
             "- 90% нет: улучшение ошибки времени и доли error<overwrite — разные цели. "
             "Общего одновременного выигрыша по обеим метрикам пока не получено.", "",
             "## Как читать", "",
             "MAE/P90 — секунды; pass — подтверждённый lower bound на всех Write с observed Read "
             "внутри дня. Верхний bound добавляет случаи неизвестной следующей Write. "
             "Under — доля занижений. ΔMAE — относительное изменение против прежней модели "
             "на тех же строках (отрицательное — улучшение). Target-срезы oracle, "
             "не используются для выбора прогноза в момент Write.", ""]
    for workload in ("proj_1", "prn_1"):
        folder = PROJECT_ROOT / "results/long-history" / workload
        verified = json.loads((folder / "verification.json").read_text())
        assert verified["passed"] and verified["metrics_fingerprint"] == fingerprint(folder / "metrics.json")
        provenance = json.loads((folder / "provenance.json").read_text())
        for path, expected in provenance["hashes"].items():
            assert fingerprint(PROJECT_ROOT / path) == expected, path
        frozen = json.loads((folder / "frozen.json").read_text())
        metrics = json.loads((folder / "metrics.json").read_text())
        for rule in ("same_start", "range"):
            choice = frozen[rule]
            pooled = metrics[rule]["pooled"]
            old_mae = pooled["previous_model"]["metrics"]["mae_seconds"]
            total = pooled["previous_model"]
            lines.extend([f"## {workload} / {rule}", "",
                          f"Train labels: **{choice['train_n']:,}**; train target median "
                          f"{choice['train_target_distribution']['q50']:,.2f} s, P90 "
                          f"{choice['train_target_distribution']['q90']:,.2f} s.", "",
                          f"Frozen primary: **{choice['selected']}**; frozen MAE policy: **{choice['mae_selected']}**.", "",
                          "### Validation: день 4", "",
                          "| Метод | N | MAE, s | Pass lower |", "|---|---:|---:|---:|"])
            for method, value in choice["validation"].items():
                lines.append(f"| {method} | {value['observed_reads']:,} | {value['metrics']['mae_seconds']:,.2f} | {value['pass_lower']*100:.2f}% |")
            lines.extend(["", f"### Дни 5–7: N={total['observed_reads']:,}, все Write={total['all_writes']:,}, "
                          f"coverage={total['coverage']*100:.2f}%", "",
                          "| Метод | MAE, s | ΔMAE vs old model | P90, s | Pass lower–upper | Under |",
                          "|---|---:|---:|---:|---:|---:|"])
            for method, value in pooled.items():
                score = value["metrics"]
                lines.append(f"| {method} | {score['mae_seconds']:,.2f} | {(score['mae_seconds']/old_mae-1)*100:+.2f}% | "
                             f"{score['p90_absolute_error_seconds']:,.2f} | {value['pass_lower']*100:.2f}–{value['pass_upper']*100:.2f}% | "
                             f"{value['signed']['under_share']*100:.2f}% |")
            lines.extend(["", "### Короткие и длинные ожидания", "",
                          "| Метод | <6h: N / MAE, s / pass | >=6h: N / MAE, s / pass |",
                          "|---|---:|---:|"])
            for method, value in pooled.items():
                short, long = [value["target_slices"][name] for name in ("under_6h", "at_least_6h")]
                lines.append(f"| {method} | {short['n']:,} / {short['mae_seconds']:,.2f} / {short['pass_lower']*100:.2f}% | "
                             f"{long['n']:,} / {long['mae_seconds']:,.2f} / {long['pass_lower']*100:.2f}% |")
            lines.extend(["", "### По дням", "", "| День | Метод | N | MAE, s | Pass lower |", "|---|---|---:|---:|---:|"])
            for day in range(5, 8):
                for method, value in metrics[rule][str(day)].items():
                    lines.append(f"| {day} | {method} | {value['observed_reads']:,} | {value['metrics']['mae_seconds']:,.2f} | {value['pass_lower']*100:.2f}% |")
            lines.append("")
    lines.extend(["## Что проверили", "",
                  "Train labels ограничены train cutoff; validation и дни 5–7 labels совпадают "
                  "со старыми результатами. 512 train Write проверены независимым линейным поиском "
                  "(2 workloads × 2 rules × 128). Независимые checker'ы подтвердили 16 окон × 5 методов: "
                  "MAE/P90/bounds, signed error, оба target-среза, pooled, frozen выбор, "
                  "восстановленные модели и адресные медианы. Baseline пересчитан из train truth. "
                  "86 unit-тестов прошли.", "",
                  "Протокол: `docs/protocols/long-history-protocol.md`. Артефакты: `results/long-history/`.", "",
                  "```bash", ".venv/bin/python -m read_prediction.experiments.long_history proj_1",
                  ".venv/bin/python -m read_prediction.experiments.long_history prn_1",
                  ".venv/bin/python -m read_prediction.checks.long_history proj_1",
                  ".venv/bin/python -m read_prediction.checks.long_history prn_1",
                  ".venv/bin/python -m read_prediction.long_history_reporting", "```", "",
                  "Новые fit отказываются перезаписывать результаты. Для независимого подтверждения "
                  "нужен заранее замороженный рецепт на workload с ещё не просмотренными будущими днями."])
    report = PROJECT_ROOT / "reports/long-history.ru.md"
    report.write_text("\n".join(lines) + "\n")
    print(report)


if __name__ == "__main__":
    main()
