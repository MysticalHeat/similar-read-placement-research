"""Package verified mean-overwrite and per-record 90% results for submission."""

import json
import math

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT


def verified_metrics(relative):
    folder = PROJECT_ROOT / "results" / relative
    verification = json.loads((folder / "verification.json").read_text())
    if not verification["passed"] or verification["metrics_fingerprint"] != fingerprint(folder / "metrics.json"):
        raise ValueError(f"Unverified metrics: {relative}")
    provenance = json.loads((folder / "provenance.json").read_text())
    for name in ("metrics.json", "frozen.json"):
        path = folder / name
        if provenance["hashes"][str(path.relative_to(PROJECT_ROOT))] != fingerprint(path):
            raise ValueError(f"Artifact fingerprint mismatch: {path}")
    return json.loads((folder / "metrics.json").read_text())


def combine_metrics(mean, passes, workload, rule, window, method):
    """Require identical cohorts before joining the two different criteria."""
    n = mean["observed_reads"]
    if n != passes["observed_reads"] or mean["all_writes"] != passes["all_writes"]:
        raise ValueError("Mean and per-record criteria have different cohorts")
    observed = mean["methods"][method]["observed_read"]
    if not math.isclose(observed["mae_seconds"], passes["metrics"]["mae_seconds"], rel_tol=1e-10):
        raise ValueError("Mean and per-record criteria have different MAE")
    confirmed = passes["confirmed_pass_count"]
    uncertain = passes["unknown_pass_count"]
    lower, upper = confirmed / n, (confirmed + uncertain) / n
    if not math.isclose(lower, passes["pass_lower"]) or not math.isclose(upper, passes["pass_upper"]):
        raise ValueError("Per-record bounds do not match counts")
    if lower >= .9:
        status = "passed"
    elif upper < .9:
        status = "failed"
    else:
        status = "undetermined"
    return {"workload": workload, "rule": rule, "window": window, "method": method,
            "observed_reads": n, "all_writes": mean["all_writes"],
            "paired_n": mean["paired_n"], "censored_n": mean["censored_n"],
            "observed_read": observed, "paired": mean["methods"][method]["paired"],
            "confirmed_pass_count": confirmed, "unknown_pass_count": uncertain,
            "pass_lower": lower, "pass_upper": upper, "ninety_percent_status": status}


def collect_results():
    means = verified_metrics("mean-overwrite")
    parents = {workload: verified_metrics(f"long-history/{workload}") for workload in means}
    mixtures = verified_metrics("mixture/prn_1")
    frozen = json.loads((PROJECT_ROOT / "results/mean-overwrite/frozen.json").read_text())
    mixture_frozen = json.loads((PROJECT_ROOT / "results/mixture/prn_1/frozen.json").read_text())
    parent_frozen = {workload: json.loads((PROJECT_ROOT / f"results/long-history/{workload}/frozen.json").read_text()) for workload in means}
    rows, candidates = [], []
    for workload, rules in means.items():
        for rule, record in rules.items():
            selected = record["selected"]
            assert selected == frozen[workload][rule]["selected"]
            for window, mean in record["windows"].items():
                names = mean["methods"] if window == "pooled" else (selected,)
                for method in names:
                    is_mixture = method.startswith("mix_")
                    if window == "validation":
                        validation = mixture_frozen[rule] if is_mixture else parent_frozen[workload][rule]
                        passes = validation["validation"][method]
                    else:
                        source = mixtures if is_mixture else parents[workload]
                        key = window.removeprefix("day")
                        passes = source[rule][key][method]
                    row = combine_metrics(mean, passes, workload, rule, window, method)
                    if method == selected:
                        rows.append(row)
                    if window == "pooled":
                        candidates.append(row)
    sources = {}
    for relative in ("mean-overwrite", "long-history/proj_1", "long-history/prn_1", "mixture/prn_1"):
        for name in ("metrics.json", "frozen.json", "verification.json"):
            path = PROJECT_ROOT / "results" / relative / name
            sources[str(path.relative_to(PROJECT_ROOT))] = fingerprint(path)
    return {"evaluation_role": "development; days 5–7 already inspected",
            "selection": "minimum observed-Read MAE on validation day 4; no pass-count constraint",
            "ninety_percent_threshold": .9, "selected_results": rows,
            "pooled_candidates": candidates, "source_fingerprints": sources}


def summary_markdown(results):
    lines = ["# Latest results: MAE, mean overwrite time and the 90% threshold", "",
             "**On prn_1, MAE is below even the lower bound on mean time to overwrite, but the requirement that `error < overwrite` for at least 90% of records is not met.** These are two different criteria.", "",
             "Predictors are selected by minimum validation MAE on day 4. For prn_1, the selection is a **25% log-L2 + 75% raw-L1** mixture in seconds; for proj_1, it is the per-address median. Days 5–7 have already been inspected: this is development evaluation, not a new holdout.", "",
             "- `same_start`: the next Read/Write with the same starting Offset, regardless of size.",
             "- `range`: the next Read/Write whose byte range intersects the written range; partial overlap is sufficient, not a complete overwrite.", "",
             "## Main comparison: all writes with an observed Read, days 5–7", "",
             "MAE and mean overwrite time refer to the same records. Unknown overwrite times are retained: the observation-window boundary gives only a lower bound on the interval, not its actual value. If MAE is below this lower bound on the mean, the condition is proven.", "",
             "The 90% criterion is `P(abs(prediction − target) < overwrite) ≥ 0.90`. The lower bound counts confirmed passes; the upper bound additionally treats every unresolved case as a pass. If even the upper bound is below 90%, the condition definitely fails.", "",
             "| Workload / rule | Method | Observed Read N / all Write N | MAE, s | Mean overwrite ≥, s | MAE / lower bound | MAE < mean | Fraction error < overwrite | ≥90% |",
             "|---|---|---:|---:|---:|---:|---|---:|---|"]
    mean_status = {"passed": "proven", "failed": "no", "undetermined": "undetermined"}
    pass_status = {"passed": "yes", "failed": "no", "undetermined": "undetermined"}
    pooled = [row for row in results["selected_results"] if row["window"] == "pooled"]
    for row in pooled:
        metric = row["observed_read"]
        lines.append(f"| {row['workload']} / {row['rule']} | {row['method']} | {row['observed_reads']:,} / {row['all_writes']:,} | {metric['mae_seconds']:.2f} | {metric['mean_overwrite_lower_seconds']:.2f} | {metric['ratio_upper_bound']:.4f} | {mean_status[metric['status']]} | {row['pass_lower']:.2%}–{row['pass_upper']:.2%} | {pass_status[row['ninety_percent_status']]} |")
    lines += ["", "For prn_1, the mean-time condition also holds on each of days 5, 6 and 7 separately. A condition on averages does not guarantee small errors for most records. MAE is undefined for writes without an observed Read, so this result does not extend to all writes.", "",
              "## Control comparison: observed Read and known overwrite only", "",
              "This is a different cohort. Here every evaluated candidate has MAE above mean overwrite time. Unknown intervals are excluded, so the conclusion differs from the main table.", "",
              "| Workload / rule | Paired N | MAE, s | Mean overwrite, s | MAE / mean | MAE < mean |",
              "|---|---:|---:|---:|---:|---|"]
    for row in pooled:
        paired = row["paired"]
        lines.append(f"| {row['workload']} / {row['rule']} | {row['paired_n']:,} | {paired['mae_seconds']:.2f} | {paired['mean_overwrite_seconds']:.2f} | {paired['ratio']:.4f} | {'yes' if paired['passed'] else 'no'} |")
    lines += ["", "## Evaluated candidates and the 90% threshold", "",
              "| Workload / rule | Candidates | Highest upper bound on pass fraction | ≥90% reached |",
              "|---|---:|---:|---|"]
    for row in pooled:
        group = [candidate for candidate in results["pooled_candidates"] if (candidate["workload"], candidate["rule"]) == (row["workload"], row["rule"])]
        upper = max(candidate["pass_upper"] for candidate in group)
        lines.append(f"| {row['workload']} / {row['rule']} | {len(group)} | {upper:.2%} | {'no' if upper < .9 else 'see individual bounds'} |")
    lines += ["", "Numerical results, daily metrics and source fingerprints are embedded in results.ipynb and saved in overwrite-results.json. Mean-overwrite calculations were independently verified for 20 windows; the parent long-history/mixture metrics were also verified.", "",
              "Source results in the research repository: results/mean-overwrite/, results/long-history/{proj_1,prn_1}/, results/mixture/prn_1/. Protocol: docs/protocols/mean-overwrite-protocol.md.", ""]
    return "\n".join(lines)
