"""Confirm range-label training support for all shortlisted new workloads."""

import json
from collections import Counter

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import load_duration
from read_prediction.experiments.data_sufficiency import eligibility
from read_prediction.experiments.prxy0_check import verify_direct
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import TRACE_SOURCES
from read_prediction.range_label import TICKS, label_writes, outcome_state


def summarize(events, rows, labels):
    seen = labels["read"] >= 0
    labelled = Counter(map(int, events["offset"][rows[seen]]))
    n = int(seen.sum())
    states = outcome_state(labels["read"], labels["overwrite"])
    return {
        "writes": len(rows), "observed_labels": n, "unobserved_labels": len(rows) - n,
        "coverage": n / len(rows) if len(rows) else None,
        "distinct_labelled_offsets": len(labelled),
        "distinct_target_reads": len(np.unique(labels["read"][seen])),
        "largest_address_label_share": max(labelled.values()) / n if n else None,
        "effective_address_count": n * n / sum(v * v for v in labelled.values()) if n else 0,
        "read_first": int((states == 1).sum()), "write_first": int((states == 0).sum()),
        "unresolved_first_event": int((states < 0).sum()),
    }, labelled


def main():
    screening = PROJECT_ROOT / "results/data-sufficiency/summary.json"
    previous = json.loads(screening.read_text())
    candidates = previous["recommended_new_workloads"]
    folder = PROJECT_ROOT / "results/data-sufficiency-range"
    folder.mkdir(exist_ok=False)
    results = []
    for workload in candidates:
        original = next(r for r in previous["results"] if r["workload"] == workload)
        # The loader shares this process-local source registry with the pipeline.
        TRACE_SOURCES[workload] = (original["source_archive"], original["source_member"])
        output = folder / workload
        output.mkdir()
        events, source = load_duration(PROJECT_ROOT / "dataset", workload, 19.2, 100_000_000,
                                       output / "events.bin")
        if source["stop_reason"] != "duration_reached":
            raise ValueError(f"Incomplete window for {workload}")
        if source["prefix_sha256"] != original["prefix_sha256"]:
            raise ValueError(f"Source mismatch for {workload}")
        origin = source["first_timestamp"]
        split = int(np.searchsorted(events["timestamp"], origin + round(14.4 * 3600 * TICKS)))
        metrics, histograms = {}, {}
        queries = 0
        for name, begin, end in (("train", 0, split), ("validation", split, len(events))):
            rows = np.flatnonzero(events["is_read"][begin:end] == 0) + begin
            labels = label_writes(events[:end], rows, begin)
            metrics[name], histograms[name] = summarize(events, rows, labels)
            np.savez(output / f"{name}.labels.npz", write_rows=rows, **labels)
            queries += verify_direct(events, rows, labels, end, "range")
        validation_n = metrics["validation"]["observed_labels"]
        shared = sum(count for offset, count in histograms["validation"].items()
                     if offset in histograms["train"])
        result = {"workload": workload, "source": source, **metrics,
                  "verified_direct_queries": queries,
                  "validation_labels_on_training_labelled_offsets_share": shared / validation_n,
                  **eligibility(metrics["train"], metrics["validation"], True)}
        results.append(result)
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(workload, "range train", metrics["train"]["observed_labels"],
              "validation", validation_n, "recommended", result["recommended_for_next_check"],
              "read_first_support", result["read_first_support"], flush=True)
    summary = {"results": results, "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in (
        screening, PROJECT_ROOT / "docs/protocols/data-sufficiency-protocol.md",
        PROJECT_ROOT / "docs/protocols/data-sufficiency-range-protocol.md",
        PROJECT_ROOT / "read_prediction/experiments/data_sufficiency_range.py",
        PROJECT_ROOT / "read_prediction/range_label.py",
        PROJECT_ROOT / "read_prediction/experiments/prxy0_check.py")}}
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
