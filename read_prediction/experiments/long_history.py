"""Three-day history and raw-L1 comparison with immutable previous benchmarks."""

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.new_workloads import choose
from read_prediction.experiments.new_workloads_diagnostics import distribution, metrics as error_metrics
from read_prediction.experiments.prxy0_check import baseline_predictions, dump, local_labels, measure, verify_direct
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import fit_baselines, score
from read_prediction.range_label import TICKS

CANDIDATES = ("log_l2", "raw_l1", "address_median")
METHODS = (*CANDIDATES, "previous_model", "previous_address_median")


def predict(model, features, method):
    values = model.predict(features, num_threads=2)
    return np.maximum(0, np.expm1(values) if method == "log_l2" else values)


def detailed(events, rows, labels, prediction, boundary):
    result = measure(events, rows, labels, prediction, boundary)
    seen = labels["read"] >= 0
    remaining = (boundary - events["timestamp"][rows]) / TICKS
    result["signed"] = error_metrics(labels["target"][seen], prediction[seen],
                                     labels["lifetime"][seen], remaining[seen])
    result["target_slices"] = {}
    for name, condition in (("under_6h", labels["target"] < 21600),
                             ("at_least_6h", labels["target"] >= 21600)):
        mask = seen & condition
        result["target_slices"][name] = error_metrics(labels["target"][mask], prediction[mask],
                                                      labels["lifetime"][mask], remaining[mask])
    return result


def pooled(folder, rule, method, windows):
    totals = {key: sum(m[key] for m in windows) for key in (
        "all_writes", "observed_reads", "read_first", "write_first", "unresolved",
        "observed_overwrites", "confirmed_pass_count", "unknown_pass_count")}
    parts = {key: [] for key in ("target", "prediction", "lifetime", "remaining")}
    for day in range(5, 8):
        with np.load(folder / f"{rule}.day{day}.npz") as saved:
            seen = saved["read"] >= 0
            for key, value in (("target", saved["target"]), ("prediction", saved[method]),
                               ("lifetime", saved["lifetime"]), ("remaining", saved["remaining"])):
                parts[key].append(value[seen])
    data = {key: np.concatenate(value) for key, value in parts.items()}
    signed = error_metrics(data["target"], data["prediction"], data["lifetime"], data["remaining"])
    slices = {}
    for name, mask in (("under_6h", data["target"] < 21600), ("at_least_6h", data["target"] >= 21600)):
        slices[name] = error_metrics(*(data[key][mask] for key in ("target", "prediction", "lifetime", "remaining")))
    return {**totals, "coverage": totals["observed_reads"] / totals["all_writes"],
            "pass_lower": signed["pass_lower"], "pass_upper": signed["pass_upper"],
            "metrics": score(data["target"], data["prediction"]), "signed": signed, "target_slices": slices}


def run(workload):
    parent = PROJECT_ROOT / "results/new-workloads" / workload
    folder = PROJECT_ROOT / "results/long-history" / workload
    folder.mkdir(parents=True, exist_ok=False)
    previous_provenance = json.loads((parent / "provenance.json").read_text())
    for path, expected in previous_provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    source = json.loads((parent / "source.json").read_text())
    previous_frozen = json.loads((parent / "frozen.json").read_text())
    events = np.memmap(parent / "events.bin", mode="r", dtype=EVENT_DTYPE)
    features = np.load(parent / "features.npy", mmap_mode="r")
    writes = np.flatnonzero(events["is_read"] == 0)
    origin = source["first_timestamp"]
    cutoffs = {day: int(np.searchsorted(events["timestamp"], origin + day * 86400 * TICKS)) for day in range(3, 8)}
    fitted, frozen, train_queries = {}, {}, 0
    for rule in ("same_start", "range"):
        train_rows, train = local_labels(events, 0, cutoffs[3], rule)
        rows, labels = local_labels(events, cutoffs[3], cutoffs[4], rule)
        with np.load(parent / f"{rule}.day4.npz") as old:
            np.testing.assert_array_equal(rows, old["write_rows"])
            for key in labels:
                np.testing.assert_array_equal(labels[key], old[key])
            previous_predictions = {"previous_model": old[previous_frozen[rule]["selected"]].copy(),
                                    "previous_address_median": old["address_median"].copy()}
        np.savez(folder / f"{rule}.train.npz", write_rows=train_rows, **train)
        train_queries += verify_direct(events, train_rows, train, cutoffs[3], rule)
        seen = train["read"] >= 0
        positions = np.searchsorted(writes, train_rows[seen])
        validation_positions = np.searchsorted(writes, rows)
        median, addresses = fit_baselines(events["offset"][train_rows[seen]], train["target"][seen])
        dump(folder / f"{rule}.address_medians.json", {str(k): v for k, v in addresses.items()})
        models, predictions = {}, dict(previous_predictions)
        for method in ("log_l2", "raw_l1"):
            model = lgb.LGBMRegressor(
                objective="regression" if method == "log_l2" else "regression_l1",
                n_estimators=150, learning_rate=.05, num_leaves=31, min_child_samples=50,
                reg_lambda=1., random_state=42, n_jobs=2, deterministic=True,
                force_col_wise=True, verbosity=-1)
            target = np.log1p(train["target"][seen]) if method == "log_l2" else train["target"][seen]
            model.fit(features[positions], target)
            model.booster_.save_model(str(folder / f"{rule}.{method}.lightgbm.txt"))
            models[method] = model.booster_
            predictions[method] = predict(model.booster_, features[validation_positions], method)
        predictions["address_median"] = baseline_predictions("address_median", events["offset"][rows], median, addresses)
        boundary = origin + 4 * 86400 * TICKS
        validation = {method: detailed(events, rows, labels, pred, boundary) for method, pred in predictions.items()}
        selected, mae_selected = choose({method: validation[method] for method in CANDIDATES})
        frozen[rule] = {"selected": selected, "mae_selected": mae_selected, "global_median": median,
                        "train_n": int(seen.sum()), "train_target_distribution": distribution(train["target"][seen]),
                        "validation": validation}
        np.savez(folder / f"{rule}.validation.npz", write_rows=rows, **labels,
                 remaining=(boundary - events["timestamp"][rows]) / TICKS, **predictions)
        fitted[rule] = (models, median, addresses)
    dump(folder / "frozen.json", frozen)
    print(workload, "frozen", {rule: (data["selected"], data["mae_selected"]) for rule, data in frozen.items()}, flush=True)
    results = {}
    for rule in ("same_start", "range"):
        models, median, addresses = fitted[rule]
        results[rule] = {}
        for day in range(5, 8):
            with np.load(parent / f"{rule}.day{day}.npz") as saved:
                rows = saved["write_rows"].copy()
                labels = {key: saved[key].copy() for key in ("read", "overwrite", "target", "lifetime")}
                predictions = {"previous_model": saved[previous_frozen[rule]["selected"]].copy(),
                               "previous_address_median": saved["address_median"].copy()}
            positions = np.searchsorted(writes, rows)
            for method, model in models.items():
                predictions[method] = predict(model, features[positions], method)
                restored = lgb.Booster(model_file=str(folder / f"{rule}.{method}.lightgbm.txt"))
                np.testing.assert_allclose(predictions[method][:128], predict(restored, features[positions[:128]], method))
            predictions["address_median"] = baseline_predictions("address_median", events["offset"][rows], median, addresses)
            boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
            np.savez(folder / f"{rule}.day{day}.npz", write_rows=rows, **labels,
                     remaining=(boundary - events["timestamp"][rows]) / TICKS, **predictions)
            results[rule][str(day)] = {method: detailed(events, rows, labels, pred, boundary) for method, pred in predictions.items()}
            print(workload, rule, day, {method: (metrics["metrics"]["mae_seconds"], metrics["pass_lower"])
                                       for method, metrics in results[rule][str(day)].items()}, flush=True)
        results[rule]["pooled"] = {method: pooled(folder, rule, method, [results[rule][str(day)][method] for day in range(5, 8)])
                                   for method in METHODS}
    dump(folder / "metrics.json", results)
    paths = [Path(__file__), PROJECT_ROOT / "docs/protocols/long-history-protocol.md",
             PROJECT_ROOT / "read_prediction/experiments/new_workloads.py",
             PROJECT_ROOT / "read_prediction/experiments/new_workloads_diagnostics.py",
             PROJECT_ROOT / "read_prediction/experiments/prxy0_check.py",
             parent / "provenance.json", parent / "source.json", parent / "frozen.json",
             folder / "frozen.json", folder / "metrics.json", *folder.glob("*.npz"),
             *folder.glob("*.lightgbm.txt"), *folder.glob("*.address_medians.json")]
    dump(folder / "provenance.json", {"independent_train_queries": train_queries,
         "parent": str(parent.relative_to(PROJECT_ROOT)),
         "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in paths}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("proj_1", "prn_1"))
    run(parser.parse_args().workload)
