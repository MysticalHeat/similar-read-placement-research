"""Independent point counts and chronological feature audit of the 90% experiment."""

import argparse
import json
import math

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT


def independent_metrics(target, prediction, annotation, write_seconds=None, end_event=None):
    following = annotation["next_write_event_index"]
    observed = following >= 0
    if end_event is not None:
        observed &= following < end_event
        lower = 144 * 3600 - write_seconds
    else:
        lower = annotation["overwrite_censor_lower_bound_seconds"]
    errors = np.abs(prediction - target)
    known_passes = np.count_nonzero(errors[observed] < annotation["overwrite_seconds"][observed])
    certified = np.count_nonzero(errors[~observed] < lower[~observed])
    n = len(target)
    return {"n": n, "mae_seconds": math.fsum(errors) / n, "known_n": int(observed.sum()),
            "zero_interval_n": int(np.count_nonzero(observed & (annotation["overwrite_seconds"] == 0))),
            "known_passes": int(known_passes), "censored_certified_passes": int(certified),
            "pass_lower_bound": float((known_passes + certified) / n),
            "pass_upper_bound": float((known_passes + np.count_nonzero(~observed)) / n),
            "meets_90_percent": bool((known_passes + certified) / n >= .90)}


def compare(recorded, calculated):
    for key, value in calculated.items():
        if isinstance(value, float):
            np.testing.assert_allclose(recorded[key], value, rtol=1e-12, atol=1e-12, err_msg=key)
        else:
            assert recorded[key] == value, key


def check(workload):
    folder = PROJECT_ROOT / "results/overwrite90" / workload
    original = PROJECT_ROOT / "results/mae-improvement" / workload
    selection = json.loads((folder / "selection.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    result = json.loads((folder / "diagnostic.json").read_text())
    for field in ("input_hashes", "code_hashes", "validation_output_hashes"):
        for relative, expected in selection[field].items():
            assert fingerprint(PROJECT_ROOT / relative)["sha256"] == expected, relative
    assert fingerprint(folder / "selection.json")["sha256"] == frozen["selection_sha256"]
    assert selection["goal"] == .90 and result["goal"] == .90
    assert not selection["independent_holdout"] and not selection["abstention"]
    chosen = min(selection["validation"], key=lambda name: (-selection["validation"][name]["pass_lower_bound"],
                                                           selection["validation"][name]["mae_seconds"], name))
    assert chosen == selection["chosen"] == result["chosen"]
    holdout = json.loads((original / "holdout.json").read_text())
    with np.load(original / "holdout-day6.predictions.npz") as source:
        target6, writes6 = source["target_seconds"], source["write_seconds"]
    with np.load(PROJECT_ROOT / "results/overwrite-comparison" / workload / "day6.comparison.npz") as source:
        annotation6 = {key: source[key] for key in source.files}
    with np.load(folder / "validation.predictions.npz") as saved:
        for name, expected in selection["validation"].items():
            compare(expected, independent_metrics(target6, saved[name], annotation6, writes6,
                                                  holdout["days"]["6"]["coverage"]["end_event_exclusive"]))
    with np.load(original / "holdout-day7.predictions.npz") as source:
        day7 = {key: source[key] for key in source.files if key in
                ("write_event_index", "target_seconds", "current", "write_seconds")}
    with np.load(PROJECT_ROOT / "results/overwrite-comparison" / workload / "day7.comparison.npz") as source:
        annotation7 = {key: source[key] for key in source.files}
    with np.load(folder / "day7.predictions.npz") as source:
        prediction = source["prediction"]
        np.testing.assert_array_equal(source["write_event_index"], day7["write_event_index"])
    assert np.isfinite(prediction).all() and np.all(prediction >= 0)
    compare(result["selected"], independent_metrics(day7["target_seconds"], prediction, annotation7))
    compare(result["current"], independent_metrics(day7["target_seconds"], day7["current"], annotation7))
    # Rebuild sample features from raw saved pairs, not the producer's grouped history.
    keys = ("offset_bytes", "write_event_index", "next_read_event_index", "target_seconds",
            "write_seconds", "next_read_seconds", "current", "address_median")
    parts = []
    lengths = []
    for day in range(2, 8):
        path = original / (f"day{day}.predictions.npz" if day < 5 else f"holdout-day{day}.predictions.npz")
        with np.load(path) as source:
            parts.append({key: source[key] for key in keys})
        lengths.append(len(parts[-1]["target_seconds"]))
    history = {key: np.concatenate([part[key] for part in parts]) for key in keys}
    del parts
    sample = np.unique(np.linspace(0, len(prediction) - 1, min(64, len(prediction)), dtype=int))
    rows = sum(lengths[:-1]) + sample
    features, simple = [], []
    origin = holdout["source"]["first_timestamp"] / 10_000_000
    for row in rows:
        previous = np.flatnonzero((history["offset_bytes"] == history["offset_bytes"][row]) &
                                 (history["next_read_event_index"] < history["write_event_index"][row]))
        current = history["current"][row]
        if len(previous):
            recent = history["target_seconds"][previous[-5:]]
            last, median, mean = recent[-1], np.median(recent), recent.mean()
            age = history["write_seconds"][row] - history["next_read_seconds"][previous[-1]]
            statistics = [last, median, mean, age, len(previous)]
        else:
            last = median = mean = current
            statistics = [np.nan] * 4 + [0]
        phase = 2 * np.pi * ((history["write_seconds"][row] + origin) % 86400) / 86400
        features.append([*np.log1p([current, history["address_median"][row], *statistics]),
                         np.sin(phase), np.cos(phase), np.log1p(history["offset_bytes"][row])])
        name = chosen
        if name.startswith("current_scale_"):
            value = current * int(name.rsplit("_", 1)[-1]) / 100
        elif name.startswith("current_median5_"):
            weight = int(name.rsplit("_", 1)[-1]) / 100
            value = weight * current + (1 - weight) * median
        else:
            value = {"current": current, "address_median": history["address_median"][row],
                     "last_completed": last, "median5": median, "mean5": mean}.get(name)
        simple.append(value)
    if selection["recipe"]["kind"] == "model":
        path = folder / "selected.lightgbm.txt"
        assert fingerprint(path)["sha256"] == frozen["model_sha256"]
        booster = lgb.Booster(model_file=str(path))
        expected = booster.predict(np.asarray(features, dtype=np.float32), num_threads=2)
        if selection["recipe"]["log_target"]:
            expected = np.expm1(expected)
        expected = np.maximum(0, expected)
        assert booster.num_trees() == selection["recipe"]["best_iteration"]
    else:
        expected = np.asarray(simple)
    np.testing.assert_allclose(prediction[sample], expected, rtol=1e-12, atol=1e-12)
    verified = {"workload": workload, "independent_holdout": False, "new_fits": 0,
                "validation_candidates_independently_recounted": len(selection["validation"]),
                "day7_rows_independently_recounted": len(prediction),
                "causal_predictions_independently_rebuilt": len(sample), "selection_verified": True}
    (folder / "verification.json").write_text(json.dumps(verified, indent=2) + "\n")
    print(json.dumps(verified, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    check(parser.parse_args().workload)
