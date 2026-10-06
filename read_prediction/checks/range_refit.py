"""Independent verification of range-refit diagnostics."""

import argparse
import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.checks.range_label import reference_first
from read_prediction.experiments.all_write import META, quality
from read_prediction.experiments.overwrite90 import metrics
from read_prediction.paths import PROJECT_ROOT


def meta_view(labels, rows):
    """Build the structured META layout expected by the frozen all-write helpers."""
    result = np.empty(len(labels["write"][rows]), dtype=META)
    for field in META.names:
        result[field] = labels[field][rows]
    return result


def verify(workload):
    folder = PROJECT_ROOT / "results/range-refit" / workload
    parent = PROJECT_ROOT / "results/all-write" / workload
    selection = json.loads((folder / "selection.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    result = json.loads((folder / "diagnostic.json").read_text())
    for section in ("input_hashes", "code_hashes", "validation_hashes"):
        for path, expected in selection[section].items():
            assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected, path
    assert fingerprint(folder / "selection.json")["sha256"] == frozen["selection_sha256"]
    for path, expected in frozen["models"].items():
        assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected

    source = json.loads((parent / "source.json").read_text())
    origin = source["first_timestamp"]
    events = np.memmap(parent / "events.bin", mode="r",
                       dtype=[("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")],
                       shape=(source["loaded_events"],))
    cutoffs = {day: int(np.searchsorted(events["timestamp"], origin + day * 86400 * 10_000_000)) for day in (4, 5, 6, 7)}
    labels = np.load(folder / "labels.npz")
    meta_rows = np.asarray(np.load(parent / "meta.npy", mmap_mode="r")["write"])
    np.testing.assert_array_equal(labels["write"], meta_rows)
    # Day-7 labels must equal the frozen range-label diagnostic exactly.
    day7 = np.load(PROJECT_ROOT / "results/range-label" / workload / "labeling.npz")
    begin7 = int(np.searchsorted(labels["write"], cutoffs[6]))
    np.testing.assert_array_equal(labels["read"][begin7:], day7["new_read"])
    np.testing.assert_array_equal(labels["overwrite"][begin7:], day7["new_write"])
    same = np.isfinite(labels["target"][begin7:]) & np.isfinite(day7["new_target"])
    np.testing.assert_allclose(labels["target"][begin7:][same], day7["new_target"][same], rtol=0, atol=1e-9)
    assert int((~same).sum()) == int((day7["new_read"] < 0).sum())
    del day7

    # Independent slow labeling of sampled day-5/6 writes.
    rng = np.random.default_rng(42)
    sample = np.sort(rng.choice(begin7, 32, replace=False))
    mismatches = 0
    for slot in sample:
        row = int(labels["write"][slot])
        reference = reference_first(events[cutoffs[4]:], cutoffs[4], row, int(events[row]["offset"]), int(events[row]["size"]))
        for saved_key, reference_key in (("read", "intersect_read"), ("overwrite", "intersect_write")):
            if int(labels[saved_key][slot]) != reference[reference_key]:
                mismatches += 1
    assert mismatches == 0, f"{mismatches} reference mismatches"

    # Replay the validation selection.
    slices = {day: slice(int(np.searchsorted(labels["write"], cutoffs[day - 1])),
                         int(np.searchsorted(labels["write"], cutoffs[day]))) for day in (5, 6, 7)}
    val = meta_view(labels, slices[6])
    with np.load(folder / "validation.predictions.npz") as saved:
        saved_predictions = {key: saved[key] for key in saved.files}
    for name, expected in selection["validation"].items():
        gate, time_name, threshold = name.split("/")
        recomputed = quality(val, saved_predictions[time_name],
                             saved_predictions[gate], float(threshold), cutoffs[6], origin + 144 * 3600 * 10_000_000)
        for key, value in expected.items():
            actual = recomputed[key]
            if isinstance(value, float) and isinstance(actual, float):
                assert abs(value - actual) < 1e-12, (name, key)
            else:
                assert value == actual or (value is None and actual is None), (name, key, actual, value)
    values = selection["validation"]
    qualified = [name for name, value in values.items() if value["qualifies"]]
    if qualified:
        chosen = min(qualified, key=lambda name: (-values[name]["coverage"], values[name]["observed_selected_mae_seconds"], name))
    else:
        broad = [name for name, value in values.items() if value["coverage"] >= .1]
        chosen = (min(broad, key=lambda name: (-min(values[name]["read_first_lower"], values[name]["confirmed_error_lt_overwrite_lower"]), -values[name]["coverage"], name))
                  if broad else min(values, key=lambda name: (-values[name]["coverage"], name)))
    assert chosen == selection["chosen"] == result["chosen"]

    # Recompute the day-7 diagnostic from saved predictions and labels.
    test_meta = meta_view(labels, slices[7])
    with np.load(folder / "day7.predictions.npz") as saved:
        probability, prediction, current = saved["probability"], saved["prediction"], saved["current"]
    gate_name, time_name, threshold = chosen.split("/")
    recomputed = quality(test_meta, prediction, probability, float(threshold), cutoffs[7],
                         min(source["last_timestamp"], origin + 168 * 3600 * 10_000_000))
    for key, value in result["all_write_selective"].items():
        actual = recomputed[key]
        if isinstance(value, float) and isinstance(actual, float):
            assert abs(value - actual) < 1e-12, (key, actual, value)
        else:
            assert value == actual, (key, actual, value)
    assert np.all((probability >= 0) & (probability <= 1)) and np.all(prediction >= 0)

    end_timestamp = min(source["last_timestamp"], origin + 168 * 3600 * 10_000_000)
    old_test = np.load(parent / "meta.npy", mmap_mode="r")[slices[7]]
    observed_old = (old_test["read"] >= 0) & (old_test["read"] < cutoffs[7])
    known_old = (old_test["overwrite"] >= 0) & (old_test["overwrite"] < cutoffs[7])
    budget_old = np.where(known_old, old_test["lifetime"], (end_timestamp - old_test["timestamp"]) / 10_000_000)
    routed = np.where(probability >= float(threshold), prediction, current)
    recomputed_current = metrics(old_test["target"][observed_old], current[observed_old], budget_old[observed_old], known_old[observed_old])
    recomputed_routed = metrics(old_test["target"][observed_old], routed[observed_old], budget_old[observed_old], known_old[observed_old])
    assert abs(recomputed_current["pass_lower_bound"] - result["original_observed_current"]["pass_lower_bound"]) < 1e-12
    assert abs(recomputed_routed["pass_lower_bound"] - result["original_observed_routed"]["pass_lower_bound"]) < 1e-12
    observed_range = test_meta["read"] >= 0
    known_range = test_meta["overwrite"] >= 0
    budget_range = np.where(known_range, test_meta["lifetime"], (end_timestamp - test_meta["timestamp"]) / 10_000_000)
    recomputed_range = metrics(test_meta["target"][observed_range], routed[observed_range], budget_range[observed_range], known_range[observed_range])
    assert abs(recomputed_range["pass_lower_bound"] - result["range_observed_routed"]["pass_lower_bound"]) < 1e-12
    selected = probability >= float(threshold)
    observed_selected = selected & observed_range
    zero_pass = int(np.count_nonzero(observed_selected & (test_meta["target"] < budget_range)))
    assert abs(zero_pass / int(selected.sum()) - result["zero_on_selected"]["zero_pass_lower"]) < 1e-12
    (folder / "verification.json").write_text(json.dumps({
        "workload": workload, "verified": True, "reference_sample": 32, "reference_mismatches": mismatches,
        "recomputed": {"original_current_pass": recomputed_current["pass_lower_bound"],
                       "original_routed_pass": recomputed_routed["pass_lower_bound"],
                       "range_routed_pass": recomputed_range["pass_lower_bound"]}}, indent=2) + "\n")
    print(f"{workload}: range-refit verification passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    verify(parser.parse_args().workload)
