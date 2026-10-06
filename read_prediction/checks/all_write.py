"""Independent all-Write counts, source histories and frozen prediction audit."""

import argparse
import json

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT

TICKS = 10_000_000


def reference(events, index, address_indices):
    """Direct past/future event filtering, independent of bucket preparation."""
    offset, timestamp = int(events["offset"][index]), int(events["timestamp"][index])
    past = address_indices[address_indices < index]
    reads = past[events["is_read"][past] == 1]
    writes = past[events["is_read"][past] == 0]
    value = [offset, int(events["size"][index]), len(reads), len(writes), np.nan, np.nan, np.nan,
             len(writes), np.nan, 0, 0, 0, 0, 0, 0, np.nan, np.nan]
    if len(reads):
        value[4] = (timestamp - int(events["timestamp"][reads[-1]])) / TICKS
        value[7] = int(np.count_nonzero(writes > reads[-1]))
    if len(reads) > 1:
        value[6] = (int(events["timestamp"][reads[-1]]) - int(events["timestamp"][reads[-2]])) / TICKS
    if len(writes):
        value[5] = (timestamp - int(events["timestamp"][writes[-1]])) / TICKS
        value[8] = int(events["size"][writes[-1]])
    origin = int(events["timestamp"][0])
    second = (timestamp-origin) // TICKS
    for window, column in ((1, 9), (60, 11)):
        start = np.searchsorted(events["timestamp"], origin+max(0, second-window)*TICKS)
        end = np.searchsorted(events["timestamp"], origin+second*TICKS)
        kinds = events["is_read"][start:end]
        value[column], value[column+1] = int(kinds.sum()), int(len(kinds)-kinds.sum())
    end = index
    while end:
        start = max(0, end-50_000)
        candidates = np.flatnonzero(events["is_read"][start:end] == 0)
        if len(candidates):
            previous = start + candidates[-1]
            value[15] = abs(offset-int(events["offset"][previous]))
            value[16] = (timestamp-int(events["timestamp"][previous])) / TICKS
            break
        end = start
    value = np.asarray(value, dtype=float)
    value[:13] = np.log1p(value[:13])
    value[15:] = np.log1p(value[15:])
    phase = 2*np.pi*(timestamp % (86400*TICKS))/(86400*TICKS)
    value[13], value[14] = np.sin(phase), np.cos(phase)
    future = address_indices[address_indices > index]
    next_read = future[events["is_read"][future] == 1]
    next_write = future[events["is_read"][future] == 0]
    r, w = int(next_read[0]) if len(next_read) else -1, int(next_write[0]) if len(next_write) else -1
    return value, r, w


def counts(meta, prediction, probability, threshold, end_event, end_timestamp):
    selected = probability >= threshold
    n = int(selected.sum())
    read_known = (meta["read"] >= 0) & (meta["read"] < end_event)
    write_known = (meta["overwrite"] >= 0) & (meta["overwrite"] < end_event)
    positive = read_known & (~write_known | (meta["read"] < meta["overwrite"]))
    unknown = ~read_known & ~write_known
    budget = (end_timestamp-meta["timestamp"]) / TICKS
    budget[write_known] = meta["lifetime"][write_known]
    error = np.abs(prediction-meta["target"])
    certified = read_known & (error < budget)
    observed = selected & read_known
    p = int(np.count_nonzero(selected & positive))
    u = int(np.count_nonzero(selected & unknown))
    success = int(np.count_nonzero(selected & certified))
    return {"selected_n": n, "all_writes": len(meta), "coverage": n/len(meta),
            "read_first_lower": p/n if n else None, "read_first_upper": (p+u)/n if n else None,
            "selected_censored": u, "selected_observed_read": int(observed.sum()),
            "confirmed_error_lt_overwrite_lower": success/n if n else None,
            "observed_selected_mae_seconds": float(error[observed].sum()/observed.sum()) if observed.any() else None,
            "qualifies": bool(n and n/len(meta) >= .1 and p/n >= .9 and success/n >= .9)}


def compare(expected, actual):
    for key, value in actual.items():
        if isinstance(value, float):
            np.testing.assert_allclose(expected[key], value, rtol=1e-12, atol=1e-12, err_msg=key)
        else:
            assert expected[key] == value, key


def verify(workload):
    folder = PROJECT_ROOT / "results/all-write" / workload
    selection = json.loads((folder / "selection.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    result = json.loads((folder / "diagnostic.json").read_text())
    source = json.loads((folder / "source.json").read_text())
    for section in ("input_hashes", "code_hashes", "validation_hashes"):
        for path, expected in selection[section].items():
            assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected, path
    assert fingerprint(folder / "selection.json")["sha256"] == frozen["selection_sha256"]
    for path, expected in frozen["models"].items():
        assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected
    meta, features = np.load(folder / "meta.npy", mmap_mode="r"), np.load(folder / "features.npy", mmap_mode="r")
    events = np.memmap(folder / "events.bin", mode="r", dtype=EVENT_DTYPE, shape=(source["loaded_events"],))
    cut = {int(day): event for day, event in selection["cutoffs"].items()}
    ranges = {day: slice(np.searchsorted(meta["write"], cut[day-1]), np.searchsorted(meta["write"], cut[day])) for day in (6, 7)}
    with np.load(folder / "validation.predictions.npz") as saved:
        validation = {key: saved[key] for key in saved.files}
    for name, expected in selection["validation"].items():
        gate, time, threshold = name.split("/")
        compare(expected, counts(meta[ranges[6]], validation[time], validation[gate], float(threshold),
                                 cut[6], source["first_timestamp"]+144*3600*TICKS))
    values = selection["validation"]
    qualified = [name for name, v in values.items() if v["qualifies"]]
    broad = [name for name, v in values.items() if v["coverage"] >= .1]
    if qualified:
        chosen = min(qualified, key=lambda name: (-values[name]["coverage"], values[name]["observed_selected_mae_seconds"], name))
    elif broad:
        chosen = min(broad, key=lambda name: (-min(values[name]["read_first_lower"], values[name]["confirmed_error_lt_overwrite_lower"]), -values[name]["coverage"], name))
    else:
        chosen = min(values, key=lambda name: (-values[name]["coverage"], name))
    assert chosen == selection["chosen"] == result["chosen"]
    with np.load(folder / "day7.predictions.npz") as saved:
        probability, prediction, current = saved["probability"], saved["prediction"], saved["current"]
    assert np.isfinite(prediction).all() and np.all(prediction >= 0)
    assert np.isfinite(probability).all() and np.all((probability >= 0) & (probability <= 1))
    gate_name, time_name, threshold = chosen.split("/")
    end_timestamp = min(source["last_timestamp"], source["first_timestamp"]+168*3600*TICKS)
    compare(result["all_write_selective"], counts(meta[ranges[7]], prediction, probability, float(threshold), cut[7], end_timestamp))
    # Preserve and independently check the old exact evaluation cohort.
    old = PROJECT_ROOT / "results/mae-improvement" / workload
    test_meta = meta[ranges[7]]
    observed = (test_meta["read"] >= 0) & (test_meta["read"] < cut[7])
    with np.load(old / "holdout-day7.predictions.npz") as saved:
        np.testing.assert_array_equal(test_meta["write"][observed], saved["write_event_index"])
        np.testing.assert_array_equal(test_meta["read"][observed], saved["next_read_event_index"])
        np.testing.assert_allclose(test_meta["target"][observed], saved["target_seconds"], rtol=0, atol=0)
        np.testing.assert_array_equal(current[observed], saved["current"])
    known = (test_meta["overwrite"] >= 0) & (test_meta["overwrite"] < cut[7])
    budget = (end_timestamp-test_meta["timestamp"]) / TICKS
    budget[known] = test_meta["lifetime"][known]
    routed = np.where(probability >= float(threshold), prediction, current)
    for key, pred in (("original_observed_current", current), ("original_observed_routed", routed)):
        error = np.abs(test_meta["target"][observed]-pred[observed])
        passed = error < budget[observed]
        known_subset = known[observed]
        k, c, n = int(np.count_nonzero(passed & known_subset)), int(np.count_nonzero(passed & ~known_subset)), len(error)
        compare(result[key], {"n": n, "mae_seconds": float(error.sum()/n), "known_n": int(known_subset.sum()),
               "zero_interval_n": int(np.count_nonzero(known_subset & (budget[observed]==0))),
               "known_passes": k, "censored_certified_passes": c,
               "pass_lower_bound": (k+c)/n, "pass_upper_bound": (k+int((~known_subset).sum()))/n,
               "meets_90_percent": bool((k+c)/n >= .9)})
    del validation
    samples = np.unique(np.linspace(0, len(meta)-1, min(64, len(meta)), dtype=int))
    wanted = np.unique(events["offset"][meta["write"][samples]])
    matching = []
    for start in range(0, len(events), 250_000):
        end = min(start+250_000, len(events))
        offsets = events["offset"][start:end]
        positions = np.minimum(np.searchsorted(wanted, offsets), len(wanted)-1)
        matching.append(start+np.flatnonzero(wanted[positions] == offsets))
    matching = np.concatenate(matching)
    offsets = events["offset"][matching]
    audited = []
    for row in samples:
        index = int(meta["write"][row])
        address_indices = matching[offsets == events["offset"][index]]
        value, read, write = reference(events, index, address_indices)
        np.testing.assert_allclose(features[row], value, rtol=1e-12, atol=1e-12, equal_nan=True)
        assert int(meta["read"][row]) == read and int(meta["overwrite"][row]) == write
        if read >= 0:
            assert meta["target"][row] == (int(events["timestamp"][read])-int(events["timestamp"][index]))/TICKS
        if write >= 0:
            assert meta["lifetime"][row] == (int(events["timestamp"][write])-int(events["timestamp"][index]))/TICKS
        audited.append({"row": int(row), "write": index, "read": read, "overwrite": write,
                        "features": [float(x) if np.isfinite(x) else None for x in value]})
    # Frozen model replay; the feature cache has a separate source audit above.
    local_samples = np.unique(np.linspace(0, len(test_meta)-1, 64, dtype=int))
    sampled_values = features[ranges[7]][local_samples]
    gate = lgb.Booster(model_file=str(folder / "gate.lightgbm.txt"))
    np.testing.assert_allclose(probability[local_samples], gate.predict(sampled_values, num_threads=2), rtol=1e-12, atol=1e-12)
    if time_name == "current":
        np.testing.assert_array_equal(prediction, current)
    else:
        time_model = lgb.Booster(model_file=str(folder / "time.lightgbm.txt"))
        value = time_model.predict(sampled_values, num_threads=2)
        if selection["recipes"][time_name]["log"]:
            value = np.expm1(value)
        np.testing.assert_allclose(prediction[local_samples], np.maximum(0, value), rtol=1e-12, atol=1e-12)
    record = {"workload": workload, "all_write_rows": len(meta), "validation_combinations_recounted": len(values),
              "day7_all_writes_recounted": len(test_meta), "original_cohort_preserved": True,
              "source_feature_and_next_event_samples": len(audited), "frozen_prediction_samples": len(local_samples),
              "new_fits": 0, "independent_holdout": False}
    (folder / "source-audit.json").write_text(json.dumps(audited, indent=2) + "\n")
    (folder / "verification.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    verify(parser.parse_args().workload)
