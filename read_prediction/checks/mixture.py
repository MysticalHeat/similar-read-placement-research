"""Independent mixture reconstruction and metric/selection verification."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.checks.long_history import signed_metrics
from read_prediction.checks.new_workloads import compare, independent_score, recompute
from read_prediction.extended import EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import TICKS


def main():
    folder = PROJECT_ROOT / "results/mixture/prn_1"
    parent = PROJECT_ROOT / "results/long-history/prn_1"
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    frozen = json.loads((folder / "frozen.json").read_text())
    published = json.loads((folder / "metrics.json").read_text())
    source = json.loads((PROJECT_ROOT / "results/new-workloads/prn_1/source.json").read_text())
    events = np.memmap(PROJECT_ROOT / "results/new-workloads/prn_1/events.bin", mode="r", dtype=EVENT_DTYPE)
    origin = source["first_timestamp"]
    weights = {"mix_log75": .75, "mix_log50": .5, "mix_log25": .25}
    methods = ("log_l2", "raw_l1", *weights)
    checked = 0
    for rule in ("same_start", "range"):
        pooled = {method: {key: [] for key in ("target", "prediction", "lifetime", "remaining")}
                  for method in methods}
        for day in range(4, 8):
            window = "validation" if day == 4 else f"day{day}"
            expected = frozen[rule]["validation"] if day == 4 else published[rule][str(day)]
            begin, end = map(int, np.searchsorted(events["timestamp"],
                             [origin + (day - 1) * 86400 * TICKS, origin + day * 86400 * TICKS]))
            boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
            with np.load(folder / f"{rule}.{window}.npz") as saved, np.load(parent / f"{rule}.{window}.npz") as old:
                for key in ("write_rows", "read", "overwrite", "target", "lifetime", "remaining", "log_l2", "raw_l1"):
                    np.testing.assert_array_equal(saved[key], old[key])
                for method, weight in weights.items():
                    compare(saved[method], weight * old["log_l2"] + (1 - weight) * old["raw_l1"])
                seen = saved["read"] >= 0
                target, lifetime, remaining = saved["target"][seen], saved["lifetime"][seen], saved["remaining"][seen]
                for method in methods:
                    basic = {key: value for key, value in expected[method].items() if key not in ("signed", "target_slices")}
                    compare(recompute(events, saved, method, begin, end, boundary), basic)
                    prediction = saved[method][seen]
                    compare(signed_metrics(target, prediction, lifetime, remaining), expected[method]["signed"])
                    for name, mask in (("under_6h", target < 21600), ("at_least_6h", target >= 21600)):
                        compare(signed_metrics(target[mask], prediction[mask], lifetime[mask], remaining[mask]),
                                expected[method]["target_slices"][name])
                    if day > 4:
                        for key, value in (("target", target), ("prediction", prediction), ("lifetime", lifetime), ("remaining", remaining)):
                            pooled[method][key].append(value)
            checked += 1
        valid = frozen[rule]["validation"]
        candidates = [name for name in weights if valid[name]["metrics"]["mae_seconds"] < valid["log_l2"]["metrics"]["mae_seconds"]
                      and valid[name]["confirmed_pass_count"] >= valid["log_l2"]["confirmed_pass_count"]]
        order = lambda name: (valid[name]["metrics"]["mae_seconds"], -valid[name]["confirmed_pass_count"], name)
        selected = min(candidates, key=order) if candidates else "log_l2"
        assert candidates == frozen[rule]["eligible_mixtures"] and selected == frozen[rule]["selected"]
        assert min(weights, key=order) == frozen[rule]["mae_best_mixture"]
        for method, parts in pooled.items():
            data = {key: np.concatenate(value) for key, value in parts.items()}
            metric = published[rule]["pooled"][method]
            compare(independent_score(data["target"], data["prediction"]), metric["metrics"])
            compare(signed_metrics(*(data[key] for key in ("target", "prediction", "lifetime", "remaining"))), metric["signed"])
            for name, mask in (("under_6h", data["target"] < 21600), ("at_least_6h", data["target"] >= 21600)):
                compare(signed_metrics(*(data[key][mask] for key in ("target", "prediction", "lifetime", "remaining"))), metric["target_slices"][name])
            for key in ("all_writes", "observed_reads", "read_first", "write_first", "unresolved",
                        "observed_overwrites", "confirmed_pass_count", "unknown_pass_count"):
                assert metric[key] == sum(published[rule][str(day)][method][key] for day in range(5, 8))
            compare(metric["coverage"], metric["observed_reads"] / metric["all_writes"])
            compare(metric["pass_lower"], metric["signed"]["pass_lower"])
            compare(metric["pass_upper"], metric["signed"]["pass_upper"])
        chosen, baseline = [published[rule]["pooled"][name] for name in (selected, "log_l2")]
        assert published[rule]["frozen_improves_both"] == (chosen["metrics"]["mae_seconds"] < baseline["metrics"]["mae_seconds"]
                                                         and chosen["confirmed_pass_count"] >= baseline["confirmed_pass_count"])
    result = {"passed": True, "verified_windows": checked, "methods_per_window": len(methods),
              "mixtures_reconstructed_from_parent": True,
              "checker_fingerprint": fingerprint(PROJECT_ROOT / "read_prediction/checks/mixture.py"),
              "metrics_fingerprint": fingerprint(folder / "metrics.json")}
    (folder / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Mixture verification passed:", checked, "windows x", len(methods), "methods")


if __name__ == "__main__":
    main()
