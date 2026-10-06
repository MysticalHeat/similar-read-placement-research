"""Independent replay of long-history predictions, medians, and selections."""

import argparse
import json

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.checks.new_workloads import compare, independent_score, recompute
from read_prediction.extended import EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import TICKS

CANDIDATES = ("log_l2", "raw_l1", "address_median")
METHODS = (*CANDIDATES, "previous_model", "previous_address_median")


def signed_metrics(target, prediction, lifetime, remaining):
    if not len(target):
        return None
    difference = prediction - target
    error = np.abs(difference)
    known = np.isfinite(lifetime)
    passed = error < np.where(known, lifetime, remaining)
    unknown = ~known & ~passed
    positive = target > 0
    return {"n": len(target), "mae_seconds": float(error.mean()), "p90_seconds": float(np.quantile(error, .9)),
            "absolute_error_sum_seconds": float(error.sum()),
            "confirmed_pass_count": int(passed.sum()), "unknown_pass_count": int(unknown.sum()),
            "pass_lower": float(passed.mean()), "pass_upper": float((passed | unknown).mean()),
            "over_share": float((difference > 0).mean()), "under_share": float((difference < 0).mean()),
            "exact_share": float((difference == 0).mean()), "bias_seconds": float(difference.mean()),
            "over_mae_contribution_seconds": float(difference[difference > 0].sum() / len(target)),
            "under_mae_contribution_seconds": float(-difference[difference < 0].sum() / len(target)),
            "median_prediction_target_ratio": float(np.median(prediction[positive] / target[positive])) if positive.any() else None}


def verify(workload):
    folder = PROJECT_ROOT / "results/long-history" / workload
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    parent = PROJECT_ROOT / provenance["parent"]
    source = json.loads((parent / "source.json").read_text())
    previous_frozen = json.loads((parent / "frozen.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    published = json.loads((folder / "metrics.json").read_text())
    events = np.memmap(parent / "events.bin", mode="r", dtype=EVENT_DTYPE)
    features = np.load(parent / "features.npy", mmap_mode="r")
    all_writes = np.flatnonzero(events["is_read"] == 0)
    origin = source["first_timestamp"]
    cutoffs = {day: int(np.searchsorted(events["timestamp"], origin + day * 86400 * TICKS)) for day in range(3, 8)}
    checked_windows = 0
    for rule in ("same_start", "range"):
        with np.load(folder / f"{rule}.train.npz") as saved:
            rows = saved["write_rows"]
            np.testing.assert_array_equal(rows, all_writes[all_writes < cutoffs[3]])
            seen = saved["read"] >= 0
            reads = saved["read"][seen]
            assert np.all((reads > rows[seen]) & (reads < cutoffs[3]))
            target = (events["timestamp"][reads] - events["timestamp"][rows[seen]]) / TICKS
            compare(target, saved["target"][seen])
            assert len(target) == frozen[rule]["train_n"]
            offsets = events["offset"][rows[seen]]
            order = np.argsort(offsets, kind="stable")
            sorted_offsets, sorted_targets = offsets[order], target[order]
            unique, starts = np.unique(sorted_offsets, return_index=True)
            ends = np.r_[starts[1:], len(target)]
            addresses = {str(int(offset)): float(np.median(sorted_targets[begin:end]))
                         for offset, begin, end in zip(unique, starts, ends)}
            compare(addresses, json.loads((folder / f"{rule}.address_medians.json").read_text()))
            median = float(np.median(target))
            compare(median, frozen[rule]["global_median"])
        models = {method: lgb.Booster(model_file=str(folder / f"{rule}.{method}.lightgbm.txt"))
                  for method in ("log_l2", "raw_l1")}
        pooled = {method: {key: [] for key in ("target", "prediction", "lifetime", "remaining")}
                  for method in METHODS}
        for day in range(4, 8):
            name = "validation" if day == 4 else f"day{day}"
            expected = frozen[rule]["validation"] if day == 4 else published[rule][str(day)]
            boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
            with np.load(folder / f"{rule}.{name}.npz") as saved, np.load(parent / f"{rule}.day{day}.npz") as old:
                rows = saved["write_rows"]
                np.testing.assert_array_equal(rows, old["write_rows"])
                for key in ("read", "overwrite", "target", "lifetime"):
                    np.testing.assert_array_equal(saved[key], old[key])
                np.testing.assert_array_equal(saved["previous_model"], old[previous_frozen[rule]["selected"]])
                np.testing.assert_array_equal(saved["previous_address_median"], old["address_median"])
                compare(saved["remaining"], (boundary - events["timestamp"][rows]) / TICKS)
                subset = np.unique(np.linspace(0, len(rows) - 1, min(128, len(rows)), dtype=int))
                positions = np.searchsorted(all_writes, rows[subset])
                seen = saved["read"] >= 0
                for method in METHODS:
                    basic = {key: value for key, value in expected[method].items() if key not in ("signed", "target_slices")}
                    compare(recompute(events, saved, method, cutoffs[day - 1], cutoffs[day], boundary), basic)
                    target, prediction = saved["target"][seen], saved[method][seen]
                    lifetime, remaining = saved["lifetime"][seen], saved["remaining"][seen]
                    compare(signed_metrics(target, prediction, lifetime, remaining), expected[method]["signed"])
                    for label, mask in (("under_6h", target < 21600), ("at_least_6h", target >= 21600)):
                        compare(signed_metrics(target[mask], prediction[mask], lifetime[mask], remaining[mask]),
                                expected[method]["target_slices"][label])
                    if method in models:
                        pred = models[method].predict(features[positions], num_threads=2)
                        pred = np.maximum(0, np.expm1(pred) if method == "log_l2" else pred)
                        compare(pred, saved[method][subset])
                    elif method == "address_median":
                        compare(np.asarray([addresses.get(str(int(offset)), median) for offset in events["offset"][rows[subset]]]),
                                saved[method][subset])
                    if day > 4:
                        for key, values in (("target", target), ("prediction", prediction), ("lifetime", lifetime), ("remaining", remaining)):
                            pooled[method][key].append(values)
                checked_windows += 1
        valid = frozen[rule]["validation"]
        best_pass = min(CANDIDATES, key=lambda method: (-valid[method]["pass_lower"], valid[method]["metrics"]["mae_seconds"], method))
        best_mae = min(CANDIDATES, key=lambda method: (valid[method]["metrics"]["mae_seconds"], method))
        assert best_pass == frozen[rule]["selected"] and best_mae == frozen[rule]["mae_selected"]
        for method, parts in pooled.items():
            data = {key: np.concatenate(value) for key, value in parts.items()}
            metric = published[rule]["pooled"][method]
            compare(independent_score(data["target"], data["prediction"]), metric["metrics"])
            compare(signed_metrics(*(data[key] for key in ("target", "prediction", "lifetime", "remaining"))), metric["signed"])
            for label, mask in (("under_6h", data["target"] < 21600), ("at_least_6h", data["target"] >= 21600)):
                compare(signed_metrics(*(data[key][mask] for key in ("target", "prediction", "lifetime", "remaining"))),
                        metric["target_slices"][label])
            for key in ("all_writes", "observed_reads", "read_first", "write_first", "unresolved",
                        "observed_overwrites", "confirmed_pass_count", "unknown_pass_count"):
                assert metric[key] == sum(published[rule][str(day)][method][key] for day in range(5, 8))
            compare(metric["coverage"], metric["observed_reads"] / metric["all_writes"])
            compare(metric["pass_lower"], metric["signed"]["pass_lower"])
            compare(metric["pass_upper"], metric["signed"]["pass_upper"])
    verification = {"passed": True, "verified_windows": checked_windows,
                    "methods_per_window": len(METHODS), "training_medians_recomputed": True,
                    "checker_fingerprint": fingerprint(PROJECT_ROOT / "read_prediction/checks/long_history.py"),
                    "metrics_fingerprint": fingerprint(folder / "metrics.json")}
    (folder / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(workload, "long-history independent checks passed:", checked_windows, "windows x", len(METHODS), "methods")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("proj_1", "prn_1"))
    verify(parser.parse_args().workload)
