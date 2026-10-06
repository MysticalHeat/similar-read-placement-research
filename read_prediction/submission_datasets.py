"""Dataset suitability comparison for submission from the 36-trace screening."""

import json

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT
from read_prediction.submission_overwrite import verified_metrics

SUFFICIENCY = PROJECT_ROOT / "results/data-sufficiency/summary.json"
RANGE_SUFFICIENCY = PROJECT_ROOT / "results/data-sufficiency-range/summary.json"
THRESHOLDS = {"train_observed_labels": 10_000, "validation_observed_labels": 2_000,
              "train_distinct_offsets": 100, "validation_distinct_offsets": 50,
              "train_distinct_target_reads": 1_000, "validation_distinct_target_reads": 200}
SELECTED = ("proj_1", "prn_1")
CONTROLS = ("usr_1", "prxy_1")


def compact(entry):
    return {"workload": entry["workload"], "full_window": entry["full_window"],
            "basic_eligible": entry["basic_eligible"],
            "basic_failure_reasons": entry["basic_failure_reasons"],
            "target_event_support": entry["target_event_support"],
            "read_first_support": entry["read_first_support"],
            "train_observed_labels": entry["train"]["observed_labels"],
            "validation_observed_labels": entry["validation"]["observed_labels"],
            "train_coverage": entry["train"]["coverage"],
            "validation_coverage": entry["validation"]["coverage"],
            "train_distinct_offsets": entry["train"]["distinct_labelled_offsets"],
            "validation_distinct_offsets": entry["validation"]["distinct_labelled_offsets"],
            "train_distinct_target_reads": entry["train"]["distinct_target_reads"],
            "validation_distinct_target_reads": entry["validation"]["distinct_target_reads"],
            "train_largest_address_share": entry["train"]["largest_address_label_share"],
            "validation_largest_address_share": entry["validation"]["largest_address_label_share"],
            "train_effective_address_count": entry["train"]["effective_address_count"],
            "validation_effective_address_count": entry["validation"]["effective_address_count"]}


def collect_datasets():
    screening = json.loads(SUFFICIENCY.read_text())
    ranges = json.loads(RANGE_SUFFICIENCY.read_text())
    traces = sorted((compact(entry) for entry in screening["results"]),
                    key=lambda row: row["validation_observed_labels"], reverse=True)
    by_name = {row["workload"]: row for row in traces}
    eligible = list(screening["recommended_new_workloads"])
    range_entries = {entry["workload"]: entry for entry in ranges["results"]}
    range_confirmation = []
    for name in eligible:
        entry = range_entries[name]
        range_confirmation.append({
            "workload": name,
            "train_observed_labels": entry["train"]["observed_labels"],
            "validation_observed_labels": entry["validation"]["observed_labels"],
            "train_coverage": entry["train"]["coverage"],
            "validation_coverage": entry["validation"]["coverage"],
            "train_distinct_target_reads": entry["train"]["distinct_target_reads"],
            "validation_distinct_target_reads": entry["validation"]["distinct_target_reads"],
            "basic_eligible": entry["basic_eligible"]})
    sources = {str(SUFFICIENCY.relative_to(PROJECT_ROOT)): fingerprint(SUFFICIENCY),
               str(RANGE_SUFFICIENCY.relative_to(PROJECT_ROOT)): fingerprint(RANGE_SUFFICIENCY)}
    trace_windows = {}
    for name in SELECTED:
        source = json.loads((PROJECT_ROOT / f"results/new-workloads/{name}/source.json").read_text())
        sources[str((PROJECT_ROOT / f"results/new-workloads/{name}/source.json").relative_to(PROJECT_ROOT))] = fingerprint(
            PROJECT_ROOT / f"results/new-workloads/{name}/source.json")
        trace_windows[name] = {"requested_hours": source["requested_hours"],
                               "stop_reason": source["stop_reason"]}
    means = verified_metrics("mean-overwrite")
    task_fit = {}
    for name in SELECTED:
        task_fit[name] = {}
        for rule in ("same_start", "range"):
            pooled = means[name][rule]["windows"]["pooled"]
            task_fit[name][rule] = {"observed_reads": pooled["observed_reads"],
                                    "all_writes": pooled["all_writes"],
                                    "coverage": pooled["coverage"]}
    failed = [row for row in traces if not row["basic_eligible"]]
    reasons = {}
    for row in failed:
        for reason in row["basic_failure_reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    validation_ranks = {name: rank + 1 for rank, name in enumerate(
        sorted(eligible, key=lambda name: by_name[name]["validation_observed_labels"], reverse=True))}
    return {"protocol": {"train_window_hours": 14.4, "validation_window_hours": 4.8,
                         "thresholds": THRESHOLDS,
                         "censoring": "labels must complete inside their own window; future days not inspected"},
            "traces": traces, "eligible_new_workloads": eligible,
            "validation_label_ranks": validation_ranks,
            "range_confirmation": range_confirmation, "controls": list(CONTROLS),
            "selected": list(SELECTED), "selection_trace_windows": trace_windows,
            "task_fit": task_fit,
            "failed_traces": len(failed), "failed_reason_counts": reasons,
            "source_fingerprints": sources}


def dataset_selection_markdown(datasets):
    by_name = {row["workload"]: row for row in datasets["traces"]}
    ranges = {row["workload"]: row for row in datasets["range_confirmation"]}
    lines = ["# Dataset selection: screening all 36 MSR Cambridge traces", "",
             "Before training, every trace was screened with fixed windows and thresholds (train 0–14.4 h, validation 14.4–19.2 h from the trace start). "
             "A label counts only if the first next Read completes inside its own window; writes censored at the window end are not training examples. "
             "Future days were never opened during screening, so selection uses data availability, not later accuracy.", "",
             "| Trace | Train labels | Validation labels | Validation addresses | Validation target Reads | Same-start eligible |",
             "|---|---:|---:|---:|---:|---|"]
    for row in datasets["traces"]:
        if row["basic_eligible"]:
            role = " (control, earlier stage)" if row["workload"] in datasets["controls"] else ""
            lines.append(f"| {row['workload']}{role} | {row['train_observed_labels']:,} | {row['validation_observed_labels']:,} | {row['validation_distinct_offsets']:,} | {row['validation_distinct_target_reads']:,} | yes |")
    lines += ["", f"The remaining {datasets['failed_traces']} traces failed at least one threshold; "
              "the most common reasons are " + ", ".join(
                  f"`{reason}` ({count})" for reason, count in sorted(
                      datasets["failed_reason_counts"].items(), key=lambda item: -item[1])) + ". "
              "For example, `src1_0` and `src1_1` have many train labels but zero validation labels under this protocol.", "",
              "## Range confirmation of the six new candidates", "",
              "The six eligible new traces were re-labeled by byte-range intersection on the 512-byte grid and re-checked against the same thresholds.", "",
              "| Trace | Train labels | Validation labels | Train target Reads | Validation coverage | Range eligible |",
              "|---|---:|---:|---:|---:|---|"]
    for name in datasets["eligible_new_workloads"]:
        row = ranges[name]
        lines.append(f"| {name} | {row['train_observed_labels']:,} | {row['validation_observed_labels']:,} | {row['train_distinct_target_reads']:,} | {row['validation_coverage']:.2%} | {'yes' if row['basic_eligible'] else 'no'} |")
    lines += ["", "## Why proj_1 and prn_1 were chosen", ""]
    proj, prn = by_name["proj_1"], by_name["prn_1"]
    lines += [f"- **Most training signal.** proj_1 has {proj['train_observed_labels']:,} train and {proj['validation_observed_labels']:,} validation same-start labels; "
              f"prn_1 has {prn['train_observed_labels']:,} and {prn['validation_observed_labels']:,} — ranks "
              f"{datasets['validation_label_ranks']['proj_1']} and {datasets['validation_label_ranks']['prn_1']} among the six new candidates.",
              f"- **Many distinct target events, also under range.** proj_1 reaches {ranges['proj_1']['train_distinct_target_reads']:,} distinct completing Reads in train "
              f"({ranges['proj_1']['validation_distinct_target_reads']:,} in validation) and prn_1 {ranges['prn_1']['train_distinct_target_reads']:,} "
              f"({ranges['prn_1']['validation_distinct_target_reads']:,}). Our per-record criteria (mean overwrite, ≥90% pass) need many independent events, not repeated writes to one address.",
              f"- **Most diverse addresses.** The largest single-address share of validation labels is {proj['validation_largest_address_share']:.2%} for proj_1 and "
              f"{prn['validation_largest_address_share']:.2%} for prn_1, with effective address counts {proj['validation_effective_address_count']:.0f} and "
              f"{prn['validation_effective_address_count']:.1f}. By comparison, hm_0 concentrates {by_name['hm_0']['validation_largest_address_share']:.2%} on one address "
              f"(effective count {by_name['hm_0']['validation_effective_address_count']:.1f}). A per-address median baseline and per-address history features need that diversity.",
              "- **Both labeling rules supported.** same_start and range pass the thresholds, so the same workflow evaluates both rules on the same traces.",
              "- **Full traces available for future days.** Both traces run the full 168 h "
              f"(`{datasets['selection_trace_windows']['proj_1']['stop_reason']}`), so frozen evaluation on days 5–7 is possible without running out of trace. "
              "This is what our development results use.", "",
              "## How this connects to the task results", "",
              "The screening thresholds are a starting filter, not a guarantee of predictive quality. What the selected traces actually delivered in our evaluation:", "",
              "| Trace / rule | Observed Read / all Write, days 5–7 | Coverage |",
              "|---|---:|---:|"]
    for name in datasets["selected"]:
        for rule in ("same_start", "range"):
            fit = datasets["task_fit"][name][rule]
            lines.append(f"| {name} / {rule} | {fit['observed_reads']:,} / {fit['all_writes']:,} | {fit['coverage']:.2%} |")
    lines += ["", "Roughly half of the writes have an observed Read within their day window, and the rest are censored. "
              "That is why MAE is reported only for observed-Read records and the ≥90% criterion is bounded rather than declared failed outright. "
              "Full details: `results.ipynb`, `reports/mean-overwrite.ru.md` and the protocols under `docs/protocols/`.", ""]
    return "\n".join(lines)
