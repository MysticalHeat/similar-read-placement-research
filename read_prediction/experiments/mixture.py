"""Frozen convex mixtures of saved prn_1 long-history predictions."""

import json
from pathlib import Path

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.long_history import detailed, pooled
from read_prediction.experiments.prxy0_check import dump
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import TICKS

WEIGHTS = {"mix_log75": .75, "mix_log50": .5, "mix_log25": .25}
METHODS = ("log_l2", "raw_l1", *WEIGHTS)


def predictions(saved):
    log, raw = saved["log_l2"], saved["raw_l1"]
    return {"log_l2": log.copy(), "raw_l1": raw.copy(),
            **{name: weight * log + (1 - weight) * raw for name, weight in WEIGHTS.items()}}


def select(validation):
    baseline = validation["log_l2"]
    eligible = [name for name in WEIGHTS
                if validation[name]["metrics"]["mae_seconds"] < baseline["metrics"]["mae_seconds"]
                and validation[name]["confirmed_pass_count"] >= baseline["confirmed_pass_count"]]
    key = lambda name: (validation[name]["metrics"]["mae_seconds"],
                        -validation[name]["confirmed_pass_count"], name)
    return (min(eligible, key=key) if eligible else "log_l2"), eligible, min(WEIGHTS, key=key)


def main():
    parent = PROJECT_ROOT / "results/long-history/prn_1"
    folder = PROJECT_ROOT / "results/mixture/prn_1"
    folder.mkdir(parents=True, exist_ok=False)
    verification = json.loads((parent / "verification.json").read_text())
    assert verification["passed"] and verification["metrics_fingerprint"] == fingerprint(parent / "metrics.json")
    provenance = json.loads((parent / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    source = json.loads((PROJECT_ROOT / "results/new-workloads/prn_1/source.json").read_text())
    events = np.memmap(PROJECT_ROOT / "results/new-workloads/prn_1/events.bin", mode="r", dtype=EVENT_DTYPE)
    origin = source["first_timestamp"]
    frozen, results = {}, {}
    for rule in ("same_start", "range"):
        with np.load(parent / f"{rule}.validation.npz") as saved:
            rows = saved["write_rows"]
            labels = {name: saved[name] for name in ("read", "overwrite", "target", "lifetime")}
            estimates = predictions(saved)
            validation = {method: detailed(events, rows, labels, pred, origin + 4 * 86400 * TICKS)
                          for method, pred in estimates.items()}
            np.savez(folder / f"{rule}.validation.npz", write_rows=rows, **labels,
                     remaining=saved["remaining"], **estimates)
        selected, eligible, mae_best = select(validation)
        frozen[rule] = {"selected": selected, "eligible_mixtures": eligible,
                        "mae_best_mixture": mae_best, "weights_log_l2": WEIGHTS, "validation": validation}
    dump(folder / "frozen.json", frozen)
    print("Frozen selections:", {rule: (data["selected"], data["eligible_mixtures"]) for rule, data in frozen.items()}, flush=True)
    for rule in ("same_start", "range"):
        results[rule] = {}
        for day in range(5, 8):
            with np.load(parent / f"{rule}.day{day}.npz") as saved:
                rows = saved["write_rows"]
                labels = {name: saved[name] for name in ("read", "overwrite", "target", "lifetime")}
                estimates = predictions(saved)
                boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
                results[rule][str(day)] = {method: detailed(events, rows, labels, pred, boundary)
                                           for method, pred in estimates.items()}
                np.savez(folder / f"{rule}.day{day}.npz", write_rows=rows, **labels,
                         remaining=saved["remaining"], **estimates)
        results[rule]["pooled"] = {method: pooled(folder, rule, method, [results[rule][str(day)][method] for day in range(5, 8)])
                                   for method in METHODS}
        chosen = results[rule]["pooled"][frozen[rule]["selected"]]
        baseline = results[rule]["pooled"]["log_l2"]
        results[rule]["frozen_improves_both"] = (chosen["metrics"]["mae_seconds"] < baseline["metrics"]["mae_seconds"]
                                                and chosen["confirmed_pass_count"] >= baseline["confirmed_pass_count"])
        print(rule, "pooled", {method: (data["metrics"]["mae_seconds"], data["pass_lower"])
                               for method, data in results[rule]["pooled"].items()}, flush=True)
    dump(folder / "metrics.json", results)
    paths = [Path(__file__), PROJECT_ROOT / "docs/protocols/mixture-protocol.md",
             PROJECT_ROOT / "read_prediction/experiments/long_history.py",
             PROJECT_ROOT / "read_prediction/experiments/new_workloads_diagnostics.py",
             PROJECT_ROOT / "read_prediction/experiments/prxy0_check.py",
             parent / "provenance.json", parent / "verification.json",
             folder / "frozen.json", folder / "metrics.json", *folder.glob("*.npz")]
    for rule in ("same_start", "range"):
        paths.extend(parent / f"{rule}.{window}.npz" for window in ("validation", "day5", "day6", "day7"))
    dump(folder / "provenance.json", {"hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in paths}})


if __name__ == "__main__":
    main()
