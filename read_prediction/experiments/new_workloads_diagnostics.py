"""Budget, transfer, and signed-error diagnostics of frozen saved predictions."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.prxy0_check import dump, local_labels
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import TICKS

BUDGET_NAMES = ["zero", "0_to_1ms", "1_to_10ms", "10_to_100ms", "100ms_to_1s",
                "1_to_10s", "10s_to_1min", "1_to_10min", "10min_to_1h", "at_least_1h", "unknown"]
SIZE_NAMES = ["up_to_512B", "512B_to_4KiB", "4_to_16KiB", "16_to_64KiB", "over_64KiB"]
TARGET_NAMES = ["under_1s", "1s_to_1min", "1_to_10min", "10min_to_1h", "1_to_6h", "at_least_6h"]


def distribution(values):
    if not len(values):
        return None
    quantiles = np.quantile(values, [.1, .5, .9, .99])
    return {"n": len(values), "mean_seconds": float(np.mean(values)),
            **{key: float(value) for key, value in zip(("q10", "q50", "q90", "q99"), quantiles)}}


def budget_groups(lifetime):
    known = np.isfinite(lifetime)
    groups = np.full(len(lifetime), 10, dtype=np.int8)
    groups[known] = np.searchsorted([0, .001, .01, .1, 1, 10, 60, 600, 3600], lifetime[known], side="right")
    groups[known & (lifetime == 0)] = 0
    return groups


def metrics(target, prediction, lifetime, remaining):
    n = len(target)
    if not n:
        return None
    signed = prediction - target
    error = np.abs(signed)
    known = np.isfinite(lifetime)
    budget = np.where(known, lifetime, remaining)
    passed = error < budget
    unknown = ~known & ~passed
    positive_target = target > 0
    return {
        "n": n, "mae_seconds": float(error.mean()), "p90_seconds": float(np.quantile(error, .9)),
        "absolute_error_sum_seconds": float(error.sum()),
        "confirmed_pass_count": int(passed.sum()), "unknown_pass_count": int(unknown.sum()),
        "pass_lower": float(passed.mean()), "pass_upper": float((passed | unknown).mean()),
        "over_share": float((signed > 0).mean()), "under_share": float((signed < 0).mean()),
        "exact_share": float((signed == 0).mean()), "bias_seconds": float(signed.mean()),
        "over_mae_contribution_seconds": float(np.maximum(signed, 0).mean()),
        "under_mae_contribution_seconds": float(np.maximum(-signed, 0).mean()),
        "median_prediction_target_ratio": float(np.median(prediction[positive_target] / target[positive_target]))
        if positive_target.any() else None,
    }


def slices(groups, names, data):
    result = {}
    for i, name in enumerate(names):
        mask = groups == i
        count = int(mask.sum())
        result[name] = {
            "n": count, "share": count / len(groups) if len(groups) else None,
            "target_distribution": distribution(data["target"][mask]),
            "methods": {method: metrics(data["target"][mask], data[method][mask],
                                         data["lifetime"][mask], data["remaining"][mask])
                        for method in ("model", "address_median", "zero")},
        }
    return result


def collect(events, features, all_writes, folder, rule, window, method, source):
    origin = source["first_timestamp"]
    day = int(window[3:]) if window.startswith("day") else 0
    boundary = (origin + round(19.2 * 3600 * TICKS) if not day
                else min(origin + day * 86400 * TICKS, source["last_timestamp"]))
    with np.load(folder / f"{rule}.{window}.npz") as saved:
        seen = saved["read"] >= 0
        rows = saved["write_rows"][seen]
        reads = saved["read"][seen]
        positions = np.searchsorted(all_writes, rows)
        return {
            "target": saved["target"][seen], "lifetime": saved["lifetime"][seen],
            "remaining": (boundary - events["timestamp"][rows]) / TICKS,
            "model": saved[method][seen], "address_median": saved["address_median"][seen],
            "zero": np.zeros(len(rows)), "offset": events["offset"][rows],
            "write_size": events["size"][rows], "read_size": events["size"][reads],
            "prior_reads": np.rint(np.expm1(features[positions, 2])).astype(np.int64),
            "day": np.full(len(rows), day, dtype=np.int8),
        }


def diagnose(workload, output):
    folder = PROJECT_ROOT / "results/new-workloads" / workload
    source = json.loads((folder / "source.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    published = json.loads((folder / "metrics.json").read_text())
    verification = json.loads((folder / "verification.json").read_text())
    assert verification["passed"] and verification["metrics_fingerprint"] == fingerprint(folder / "metrics.json")
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    events = np.memmap(folder / "events.bin", dtype=EVENT_DTYPE, mode="r")
    features = np.load(folder / "features.npy", mmap_mode="r")
    all_writes = np.flatnonzero(events["is_read"] == 0)
    train_end = int(np.searchsorted(events["timestamp"], source["first_timestamp"] + round(14.4 * 3600 * TICKS)))
    train_offsets = np.unique(events["offset"][:train_end])
    result = {"workload": workload, "rules": {}}
    for rule in ("same_start", "range"):
        selected = frozen[rule]["selected"]
        if rule == "range":
            with np.load(PROJECT_ROOT / "results/data-sufficiency-range" / workload / "train.labels.npz") as saved:
                seen = saved["read"] >= 0
                train_targets = saved["target"][seen]
                labelled_offsets = np.unique(events["offset"][saved["write_rows"][seen]])
        else:
            train_rows, labels = local_labels(events, 0, train_end, rule)
            seen = labels["read"] >= 0
            train_targets = labels["target"][seen]
            labelled_offsets = np.unique(events["offset"][train_rows[seen]])
        validation = collect(events, features, all_writes, folder, rule, "validation", selected, source)
        days = [collect(events, features, all_writes, folder, rule, f"day{day}", selected, source)
                for day in range(2, 8)]
        future = {key: np.concatenate([day[key] for day in days]) for key in validation}
        rule_result = {"selected": selected, "train_target_distribution": distribution(train_targets),
                       "train_label_coverage": len(train_targets) / int((all_writes < train_end).sum()),
                       "windows": {}}
        for window, data in (("validation", validation), ("future", future)):
            overall = {method: metrics(data["target"], data[method], data["lifetime"], data["remaining"])
                       for method in ("model", "address_median", "zero")}
            expected = frozen[rule]["validation"][selected] if window == "validation" else published[rule]["pooled"][selected]
            for method, saved_method in (("model", selected), ("address_median", "address_median")):
                expected_method = (frozen[rule]["validation"][saved_method] if window == "validation"
                                   else published[rule]["pooled"][saved_method])
                actual = overall[method]
                assert actual["n"] == expected_method["observed_reads"]
                assert actual["confirmed_pass_count"] == expected_method["confirmed_pass_count"]
                assert actual["unknown_pass_count"] == expected_method["unknown_pass_count"]
                np.testing.assert_allclose(actual["mae_seconds"], expected_method["metrics"]["mae_seconds"])
            address_groups = np.where(np.isin(data["offset"], labelled_offsets), 0,
                                      np.where(np.isin(data["offset"], train_offsets), 1, 2))
            families = {
                "budgets": slices(budget_groups(data["lifetime"]), BUDGET_NAMES, data),
                "addresses": slices(address_groups, ["training_labelled", "training_seen_unlabelled", "training_unseen"], data),
                "write_sizes": slices(np.searchsorted([512, 4096, 16384, 65536], data["write_size"], side="left"), SIZE_NAMES, data),
                "read_write_size": slices(np.sign(data["read_size"] - data["write_size"]) + 1, ["read_smaller", "equal", "read_larger"], data),
                "target_intervals": slices(np.searchsorted([1, 60, 600, 3600, 21600], data["target"], side="right"), TARGET_NAMES, data),
                "prior_read_history": slices(np.where(data["prior_reads"] == 0, 0, np.where(data["prior_reads"] < 5, 1, 2)), ["none", "1_to_4", "at_least_5"], data),
            }
            if window == "future":
                families["days"] = slices(data["day"] - 2, [str(day) for day in range(2, 8)], data)
            for family in families.values():
                assert sum(group["n"] for group in family.values()) == len(data["target"])
                for method in overall:
                    summaries = [g["methods"][method] for g in family.values() if g["n"]]
                    assert sum(m["confirmed_pass_count"] for m in summaries) == overall[method]["confirmed_pass_count"]
                    assert sum(m["unknown_pass_count"] for m in summaries) == overall[method]["unknown_pass_count"]
                    np.testing.assert_allclose(sum(m["absolute_error_sum_seconds"] for m in summaries), overall[method]["absolute_error_sum_seconds"])
            zero_n = families["budgets"]["zero"]["n"]
            rule_result["windows"][window] = {
                "n": len(data["target"]), "coverage": expected.get("coverage", expected.get("observed_read_coverage")),
                "zero_budget_ceiling": 1 - zero_n / len(data["target"]),
                "target_distribution": distribution(data["target"]),
                "model_prediction_distribution": distribution(data["model"]),
                "median_prediction_distribution": distribution(data["address_median"]),
                "overall": overall, **families,
            }
        result["rules"][rule] = rule_result
    dump(output / f"{workload}.json", result)
    return result


def main():
    output = PROJECT_ROOT / "results/new-workloads-diagnostics"
    output.mkdir(exist_ok=False)
    for workload in ("proj_1", "prn_1"):
        result = diagnose(workload, output)
        print(workload, {rule: data["windows"]["future"]["overall"]["model"]
                         for rule, data in result["rules"].items()}, flush=True)
    inputs = [PROJECT_ROOT / "docs/protocols/new-workloads-diagnostics-protocol.md",
              PROJECT_ROOT / "read_prediction/experiments/new_workloads_diagnostics.py"]
    for workload in ("proj_1", "prn_1"):
        folder = PROJECT_ROOT / "results/new-workloads" / workload
        inputs.extend([folder / "frozen.json", folder / "metrics.json", folder / "provenance.json",
                       folder / "verification.json", output / f"{workload}.json"])
    dump(output / "verification.json", {"passed": True, "slice_partitions_checked": True,
         "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in inputs}})


if __name__ == "__main__":
    main()
