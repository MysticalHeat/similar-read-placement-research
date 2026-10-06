"""Fixed new-workload recipes with frozen validation selections."""

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import load_duration, make_compact_samples
from read_prediction.experiments.prxy0_check import (
    baseline_predictions, dump, local_labels, measure, verify_direct,
)
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import TRACE_SOURCES, fit_baselines, score
from read_prediction.range_label import TICKS, require_grid

COLUMNS = {"all_features": list(range(7)), "no_counts": [0, 1, 4, 5, 6]}
METHODS = [*COLUMNS, "global_median", "address_median"]


def pool(windows, folder, rule, method):
    totals = {key: sum(m[key] for m in windows) for key in (
        "all_writes", "observed_reads", "read_first", "write_first", "unresolved",
        "observed_overwrites", "confirmed_pass_count", "unknown_pass_count")}
    n = totals["observed_reads"]
    targets, predictions = [], []
    for day in range(2, 8):
        with np.load(folder / f"{rule}.day{day}.npz") as saved:
            seen = saved["read"] >= 0
            targets.append(saved["target"][seen])
            predictions.append(saved[method][seen])
    return {**totals, "coverage": n / totals["all_writes"],
            "pass_lower": totals["confirmed_pass_count"] / n if n else None,
            "pass_upper": (totals["confirmed_pass_count"] + totals["unknown_pass_count"]) / n if n else None,
            "confirmed_pass_all_writes": totals["confirmed_pass_count"] / totals["all_writes"],
            "metrics": score(np.concatenate(targets), np.concatenate(predictions))}


def choose(validation):
    supported = {name: metrics for name, metrics in validation.items() if metrics["metrics"]}
    if not supported:
        raise ValueError("No validation targets")
    best_pass = min(supported, key=lambda name: (
        -supported[name]["pass_lower"], supported[name]["metrics"]["mae_seconds"], name))
    best_mae = min(supported, key=lambda name: (supported[name]["metrics"]["mae_seconds"], name))
    return best_pass, best_mae


def run(workload):
    folder = PROJECT_ROOT / "results/new-workloads" / workload
    folder.mkdir(parents=True, exist_ok=False)
    screening = json.loads((PROJECT_ROOT / "results/data-sufficiency" / f"{workload}.json").read_text())
    range_screening = json.loads((PROJECT_ROOT / "results/data-sufficiency-range" / workload / "summary.json").read_text())
    TRACE_SOURCES[workload] = (screening["source_archive"], screening["source_member"])
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 168, 100_000_000,
                                   folder / "events.bin")
    if source["stop_reason"] == "event_cap_reached":
        raise ValueError("Unexpected event cap")
    if source["last_timestamp"] < source["first_timestamp"] + 144 * 3600 * TICKS:
        raise ValueError("Source does not cover all six future day windows")
    require_grid(events["offset"], events["size"])
    dump(folder / "source.json", source)
    samples = make_compact_samples(events, folder / "features.npy")
    origin = source["first_timestamp"]

    def cutoff(hours):
        return int(np.searchsorted(events["timestamp"], origin + round(hours * 3600 * TICKS)))

    train_end, validation_end = cutoff(14.4), cutoff(19.2)
    # Every cached event of the screened prefix must match the original screening cache.
    range_cache = np.memmap(PROJECT_ROOT / "results/data-sufficiency-range" / workload / "events.bin",
                           dtype=events.dtype, mode="r")
    np.testing.assert_array_equal(events[:validation_end], range_cache)
    del range_cache
    frozen, fitted = {}, {}
    for rule in ("same_start", "range"):
        train_rows, train = local_labels(events, 0, train_end, rule)
        valid_rows, valid = local_labels(events, train_end, validation_end, rule)
        expected = screening if rule == "same_start" else range_screening
        for name, labels in (("train", train), ("validation", valid)):
            if int((labels["read"] >= 0).sum()) != expected[name]["observed_labels"]:
                raise ValueError(f"Screened label count mismatch: {workload}/{rule}/{name}")
            if rule == "range":
                with np.load(PROJECT_ROOT / "results/data-sufficiency-range" / workload / f"{name}.labels.npz") as saved:
                    for key in labels:
                        np.testing.assert_array_equal(labels[key], saved[key])
        seen = train["read"] >= 0
        positions = np.searchsorted(samples["write_indices"], train_rows[seen])
        valid_positions = np.searchsorted(samples["write_indices"], valid_rows)
        median, addresses = fit_baselines(events["offset"][train_rows[seen]], train["target"][seen])
        models, predictions = {}, {}
        for method, columns in COLUMNS.items():
            model = lgb.LGBMRegressor(
                objective="regression", n_estimators=150, learning_rate=.05, num_leaves=31,
                min_child_samples=50, reg_lambda=1., random_state=42, n_jobs=2,
                deterministic=True, force_col_wise=True, verbosity=-1)
            model.fit(samples["features"][positions][:, columns], np.log1p(train["target"][seen]))
            model.booster_.save_model(str(folder / f"{rule}.{method}.lightgbm.txt"))
            models[method] = model
            predictions[method] = np.maximum(0, np.expm1(model.booster_.predict(
                samples["features"][valid_positions][:, columns], num_threads=2)))
        for method in ("global_median", "address_median"):
            predictions[method] = baseline_predictions(method, events["offset"][valid_rows], median, addresses)
        validation = {method: measure(events, valid_rows, valid, pred, origin + round(19.2 * 3600 * TICKS))
                      for method, pred in predictions.items()}
        best_pass, best_mae = choose(validation)
        frozen[rule] = {"selected": best_pass, "mae_selected": best_mae,
                        "train_n": int(seen.sum()), "validation": validation, "global_median": median}
        np.savez(folder / f"{rule}.validation.npz", write_rows=valid_rows, **valid, **predictions)
        dump(folder / f"{rule}.address_medians.json", {str(k): v for k, v in addresses.items()})
        fitted[rule] = (models, median, addresses)
    dump(folder / "frozen.json", frozen)
    print(workload, "frozen", {rule: (f["selected"], f["mae_selected"]) for rule, f in frozen.items()}, flush=True)
    results, direct_queries = {}, 0
    for rule in ("same_start", "range"):
        models, median, addresses = fitted[rule]
        results[rule] = {}
        for day in range(2, 8):
            begin, end = cutoff((day - 1) * 24), cutoff(day * 24)
            rows, labels = local_labels(events, begin, end, rule)
            if not len(rows):
                raise ValueError(f"No Write in {workload} day {day}")
            boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
            positions = np.searchsorted(samples["write_indices"], rows)
            predictions = {}
            for method, model in models.items():
                predictions[method] = np.maximum(0, np.expm1(model.booster_.predict(
                    samples["features"][positions][:, COLUMNS[method]], num_threads=2)))
                restored = lgb.Booster(model_file=str(folder / f"{rule}.{method}.lightgbm.txt"))
                np.testing.assert_allclose(predictions[method][:128], np.maximum(0, np.expm1(
                    restored.predict(samples["features"][positions[:128]][:, COLUMNS[method]], num_threads=2))))
            for method in ("global_median", "address_median"):
                predictions[method] = baseline_predictions(method, events["offset"][rows], median, addresses)
            np.savez(folder / f"{rule}.day{day}.npz", write_rows=rows, **labels, **predictions)
            results[rule][str(day)] = {method: measure(events, rows, labels, pred, boundary)
                                       for method, pred in predictions.items()}
            direct_queries += verify_direct(events, rows, labels, end, rule)
            selected = results[rule][str(day)][frozen[rule]["selected"]]
            print(workload, rule, day, "N", selected["observed_reads"], "pass", selected["pass_lower"],
                  "MAE", selected["metrics"]["mae_seconds"] if selected["metrics"] else None, flush=True)
        results[rule]["pooled"] = {method: pool([results[rule][str(day)][method] for day in range(2, 8)],
                                                 folder, rule, method) for method in METHODS}
    dump(folder / "metrics.json", results)
    code = [Path(__file__), PROJECT_ROOT / "docs/protocols/new-workloads-protocol.md",
            PROJECT_ROOT / "read_prediction/experiments/prxy0_check.py",
            PROJECT_ROOT / "read_prediction/extended.py", PROJECT_ROOT / "read_prediction/range_label.py",
            PROJECT_ROOT / "read_prediction/pipeline.py"]
    outputs = [folder / "source.json", folder / "frozen.json", folder / "metrics.json",
               *folder.glob("*.npz"), *folder.glob("*.lightgbm.txt"), *folder.glob("*.address_medians.json")]
    dump(folder / "provenance.json", {"direct_queries": direct_queries, "screening_cache_equal": True,
         "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in [*code, *outputs]}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("proj_1", "prn_1"))
    run(parser.parse_args().workload)
