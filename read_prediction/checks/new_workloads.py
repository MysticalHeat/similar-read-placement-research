"""Recompute saved metrics and frozen choices without training models."""

import argparse
import json

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.new_workloads import COLUMNS, METHODS
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import Event, make_samples
from read_prediction.range_label import TICKS


def independent_score(target, prediction):
    if not len(target):
        return None
    error = np.abs(target - prediction)
    return {"n": len(target), "mae_seconds": float(error.mean()),
            "median_absolute_error_seconds": float(np.median(error)),
            "p90_absolute_error_seconds": float(np.quantile(error, .9)),
            "rmse_seconds": float(np.sqrt(np.mean(error ** 2))),
            "mae_log1p_seconds": float(np.abs(np.log1p(target) - np.log1p(prediction)).mean())}


def compare(actual, expected):
    if isinstance(actual, dict):
        assert set(actual) == set(expected), (set(actual), set(expected))
        for key in actual:
            compare(actual[key], expected[key])
    elif actual is None:
        assert expected is None
    else:
        np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-10)


def recompute(events, saved, method, begin, end, boundary):
    rows, reads, overwrites = saved["write_rows"], saved["read"], saved["overwrite"]
    seen, overwritten = reads >= 0, overwrites >= 0
    assert np.all((rows >= begin) & (rows < end))
    assert np.all((reads[seen] > rows[seen]) & (reads[seen] < end))
    assert np.all((overwrites[overwritten] > rows[overwritten]) & (overwrites[overwritten] < end))
    assert np.all(events["is_read"][reads[seen]] == 1)
    assert np.all(events["is_read"][overwrites[overwritten]] == 0)
    target = (events["timestamp"][reads[seen]] - events["timestamp"][rows[seen]]) / TICKS
    compare(target, saved["target"][seen])
    compare((events["timestamp"][overwrites[overwritten]] - events["timestamp"][rows[overwritten]]) / TICKS,
            saved["lifetime"][overwritten])
    budget = (boundary - events["timestamp"][rows]).astype(float) / TICKS
    budget[overwritten] = saved["lifetime"][overwritten]
    prediction = saved[method]
    assert np.isfinite(prediction).all() and np.all(prediction >= 0)
    passed = np.abs(target - prediction[seen]) < budget[seen]
    unknown = ~overwritten[seen] & ~passed
    first = seen & (~overwritten | (reads < overwrites))
    write_first = overwritten & (~seen | (overwrites < reads))
    n, total = int(seen.sum()), len(rows)
    return {
        "all_writes": total, "observed_reads": n, "observed_read_coverage": n / total,
        "read_first": int(first.sum()), "write_first": int(write_first.sum()),
        "unresolved": int((~seen & ~overwritten).sum()), "observed_overwrites": int(overwritten.sum()),
        "confirmed_pass_count": int(passed.sum()), "unknown_pass_count": int(unknown.sum()),
        "pass_lower": float(passed.mean()) if n else None,
        "pass_upper": float((passed | unknown).mean()) if n else None,
        "confirmed_pass_all_writes": int(passed.sum()) / total,
        "metrics": independent_score(target, prediction[seen]),
        "read_first_metrics": independent_score(saved["target"][first], prediction[first]),
    }


def verify(workload):
    folder = PROJECT_ROOT / "results/new-workloads" / workload
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    source = json.loads((folder / "source.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    metrics = json.loads((folder / "metrics.json").read_text())
    events = np.memmap(folder / "events.bin", mode="r", dtype=EVENT_DTYPE)
    features = np.load(folder / "features.npy", mmap_mode="r")
    writes = np.flatnonzero(events["is_read"] == 0)
    origin = source["first_timestamp"]
    prefix = events[:2000]
    reference = make_samples([Event(int(e["timestamp"]), "Read" if e["is_read"] else "Write",
                                   int(e["offset"]), int(e["size"])) for e in prefix])
    compare(features[:len(reference["write_indices"])], reference["features"])
    checked = 0
    for rule in ("same_start", "range"):
        models = {method: lgb.Booster(model_file=str(folder / f"{rule}.{method}.lightgbm.txt"))
                  for method in COLUMNS}
        addresses = json.loads((folder / f"{rule}.address_medians.json").read_text())
        pooled = {method: [] for method in METHODS}
        for window in ["validation", *[f"day{day}" for day in range(2, 8)]]:
            if window == "validation":
                begin_ts, end_ts = origin + round(14.4 * 3600 * TICKS), origin + round(19.2 * 3600 * TICKS)
                expected = frozen[rule]["validation"]
            else:
                day = int(window[3:])
                begin_ts, end_ts = origin + (day - 1) * 86400 * TICKS, origin + day * 86400 * TICKS
                expected = metrics[rule][str(day)]
            begin, end = map(int, np.searchsorted(events["timestamp"], [begin_ts, end_ts]))
            boundary = min(end_ts, source["last_timestamp"])
            with np.load(folder / f"{rule}.{window}.npz") as saved:
                rows = saved["write_rows"]
                np.testing.assert_array_equal(rows, writes[(writes >= begin) & (writes < end)])
                subset = np.unique(np.linspace(0, len(rows) - 1, min(128, len(rows)), dtype=int))
                positions = np.searchsorted(writes, rows[subset])
                for method in METHODS:
                    compare(recompute(events, saved, method, begin, end, boundary), expected[method])
                    if method in models:
                        prediction = np.maximum(0, np.expm1(models[method].predict(
                            features[positions][:, COLUMNS[method]], num_threads=2)))
                    else:
                        median = frozen[rule]["global_median"]
                        prediction = np.asarray([addresses.get(str(int(offset)), median)
                                                 if method == "address_median" else median
                                                 for offset in events["offset"][rows[subset]]])
                    compare(prediction, saved[method][subset])
                    if window != "validation":
                        seen = saved["read"] >= 0
                        pooled[method].append((saved["target"][seen], saved[method][seen]))
                checked += 1
        validation = frozen[rule]["validation"]
        best_pass = min(METHODS, key=lambda name: (-validation[name]["pass_lower"],
                         validation[name]["metrics"]["mae_seconds"], name))
        best_mae = min(METHODS, key=lambda name: (validation[name]["metrics"]["mae_seconds"], name))
        assert best_pass == frozen[rule]["selected"] and best_mae == frozen[rule]["mae_selected"]
        for method in METHODS:
            published = metrics[rule]["pooled"][method]
            windows = [metrics[rule][str(day)][method] for day in range(2, 8)]
            for key in ("all_writes", "observed_reads", "read_first", "write_first", "unresolved",
                        "observed_overwrites", "confirmed_pass_count", "unknown_pass_count"):
                assert published[key] == sum(m[key] for m in windows)
            n = published["observed_reads"]
            compare(published["pass_lower"], published["confirmed_pass_count"] / n)
            compare(published["pass_upper"], (published["confirmed_pass_count"] + published["unknown_pass_count"]) / n)
            compare(published["coverage"], n / published["all_writes"])
            compare(published["confirmed_pass_all_writes"], published["confirmed_pass_count"] / published["all_writes"])
            compare(published["metrics"], independent_score(
                np.concatenate([p[0] for p in pooled[method]]), np.concatenate([p[1] for p in pooled[method]])))
    output = {"verified_windows": checked, "verified_methods_per_window": len(METHODS),
              "direct_label_queries_from_experiment": provenance["direct_queries"],
              "checker_fingerprint": fingerprint(PROJECT_ROOT / "read_prediction/checks/new_workloads.py"),
              "metrics_fingerprint": fingerprint(folder / "metrics.json"), "passed": True}
    (folder / "verification.json").write_text(json.dumps(output, indent=2) + "\n")
    print(workload, "independent metric/selection/prediction verification passed:", checked, "windows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("proj_1", "prn_1"))
    verify(parser.parse_args().workload)
