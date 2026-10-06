"""Independently recount gate quality and reconstruct sampled causal predictions."""

import argparse
import json

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT
from read_prediction.checks.overwrite90 import independent_metrics, compare


def selective(target, prediction, annotation, truth, probability, threshold, writes=None, cutoff=None):
    mask = probability >= threshold
    count = int(mask.sum())
    quality = None
    precision = None
    if count:
        selected_annotation = {key: value[mask] for key, value in annotation.items()}
        quality = independent_metrics(target[mask], prediction[mask], selected_annotation,
                                      writes[mask] if writes is not None else None, cutoff)
        precision = int(np.count_nonzero(truth & mask)) / count
    return {"selected_n": count, "coverage": count / len(target), "read_first_precision": precision,
            "read_first_recall": int(np.count_nonzero(truth & mask)) / int(truth.sum()) if truth.any() else None,
            "selected": quality,
            "qualifies_selective": bool(count and count / len(target) >= .1 and precision >= .9 and quality["pass_lower_bound"] >= .9)}


def compare_selective(expected, actual):
    for key, value in actual.items():
        if key == "selected" and value is not None:
            compare(expected[key], value)
        elif isinstance(value, float):
            np.testing.assert_allclose(expected[key], value, rtol=1e-12, atol=1e-12)
        else:
            assert expected[key] == value, key


def verify(workload):
    folder = PROJECT_ROOT / "results/read-first" / workload
    original = PROJECT_ROOT / "results/mae-improvement" / workload
    selection = json.loads((folder / "selection.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    result = json.loads((folder / "diagnostic.json").read_text())
    for section in ("input_hashes", "code_hashes", "validation_output_hashes"):
        for name, expected in selection[section].items():
            assert fingerprint(PROJECT_ROOT / name)["sha256"] == expected, name
    assert fingerprint(folder / "selection.json")["sha256"] == frozen["selection_sha256"]
    for path, expected in frozen["models"].items():
        assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected
    holdout = json.loads((original / "holdout.json").read_text())
    day_data, annotations = {}, {}
    for day in (6, 7):
        with np.load(original / f"holdout-day{day}.predictions.npz") as data:
            day_data[day] = {key: data[key] for key in ("target_seconds", "write_seconds", "write_event_index", "current")}
        with np.load(PROJECT_ROOT / "results/overwrite-comparison" / workload / f"day{day}.comparison.npz") as data:
            annotations[day] = {key: data[key] for key in data.files}
    with np.load(folder / "validation.predictions.npz") as data:
        validation = {key: data[key] for key in data.files}
    for name, expected in selection["validation"].items():
        gate, time, threshold = name.split("/")
        actual = selective(day_data[6]["target_seconds"], validation[time], annotations[6],
                           annotations[6]["read_before_overwrite"], validation[gate], float(threshold),
                           day_data[6]["write_seconds"], holdout["days"]["6"]["coverage"]["end_event_exclusive"])
        compare_selective(expected, actual)
    candidates = selection["validation"]
    qualified = [name for name, metric in candidates.items() if metric["qualifies_selective"]]
    if qualified:
        chosen = min(qualified, key=lambda name: (-candidates[name]["coverage"], candidates[name]["selected"]["mae_seconds"], name))
    else:
        chosen = min(candidates, key=lambda name: (
            -min(candidates[name]["read_first_precision"] or 0,
                 candidates[name]["selected"]["pass_lower_bound"] if candidates[name]["selected"] else 0),
            -candidates[name]["coverage"],
            candidates[name]["selected"]["mae_seconds"] if candidates[name]["selected"] else float("inf"), name))
    assert chosen == selection["chosen"] == result["chosen"]
    with np.load(folder / "day7.predictions.npz") as data:
        prediction, probability, routed = data["prediction"], data["probability"], data["routed"]
        np.testing.assert_array_equal(day_data[7]["write_event_index"], data["write_event_index"])
    assert np.isfinite(probability).all() and np.all((probability >= 0) & (probability <= 1))
    assert np.isfinite(prediction).all() and np.all(prediction >= 0)
    threshold = selection["combination"]["threshold"]
    compare_selective(result["selective"], selective(day_data[7]["target_seconds"], prediction, annotations[7],
                       annotations[7]["read_before_overwrite"], probability, threshold))
    np.testing.assert_array_equal(routed, np.where(probability >= threshold, prediction, day_data[7]["current"]))
    compare(result["routed_all"], independent_metrics(day_data[7]["target_seconds"], routed, annotations[7]))
    compare(result["current_all"], independent_metrics(day_data[7]["target_seconds"], day_data[7]["current"], annotations[7]))
    del validation
    # Independent direct searches over past completed pairs, including outcome history.
    keys = ("offset_bytes", "write_event_index", "next_read_event_index", "target_seconds",
            "write_seconds", "next_read_seconds", "current", "address_median")
    parts, lengths, outcome_parts = [], [], []
    for day in range(2, 8):
        path = original / (f"day{day}.predictions.npz" if day < 5 else f"holdout-day{day}.predictions.npz")
        with np.load(path) as data:
            part = {key: data[key] for key in keys}
        parts.append(part)
        lengths.append(len(part["target_seconds"]))
        if day >= 5:
            with np.load(PROJECT_ROOT / "results/overwrite-comparison" / workload / f"day{day}.comparison.npz") as data:
                outcome_parts.append(data["read_before_overwrite"])
    history = {key: np.concatenate([part[key] for part in parts]) for key in keys}
    del parts
    outcomes = np.concatenate(outcome_parts)
    outcome_begin = sum(lengths[:3])
    samples = np.unique(np.linspace(0, len(prediction)-1, min(64, len(prediction)), dtype=int))
    features = []
    origin = holdout["source"]["first_timestamp"] / 10_000_000
    for row in sum(lengths[:-1]) + samples:
        previous = np.flatnonzero((history["offset_bytes"] == history["offset_bytes"][row]) &
                                  (history["next_read_event_index"] < history["write_event_index"][row]))
        current, baseline = history["current"][row], history["address_median"][row]
        if len(previous):
            delays = history["target_seconds"][previous[-5:]]
            statistics = [delays[-1], np.median(delays), delays.mean(),
                          history["write_seconds"][row] - history["next_read_seconds"][previous[-1]], len(previous)]
        else:
            statistics = [np.nan] * 4 + [0]
        phase = 2 * np.pi * ((history["write_seconds"][row] + origin) % 86400) / 86400
        resolved = previous[previous >= outcome_begin] - outcome_begin
        fate = [outcomes[resolved[-1]], outcomes[resolved[-5:]].mean(), np.log1p(len(resolved))] if len(resolved) else [np.nan, np.nan, 0]
        features.append([*np.log1p([current, baseline, *statistics]), np.sin(phase), np.cos(phase),
                         np.log1p(history["offset_bytes"][row]), *fate])
    features = np.asarray(features, dtype=np.float32)
    gate = lgb.Booster(model_file=str(folder / "gate.lightgbm.txt"))
    np.testing.assert_allclose(probability[samples], gate.predict(features, num_threads=2), rtol=1e-12, atol=1e-12)
    time = selection["combination"]["time"]
    if time == "current":
        expected_time = day_data[7]["current"][samples]
    else:
        booster = lgb.Booster(model_file=str(folder / "time.lightgbm.txt"))
        expected_time = booster.predict(features, num_threads=2)
        if selection["recipes"][time]["log_target"]:
            expected_time = np.expm1(expected_time)
        expected_time = np.maximum(0, expected_time)
    np.testing.assert_allclose(prediction[samples], expected_time, rtol=1e-12, atol=1e-12)
    record = {"workload": workload, "validation_combinations_recounted": len(candidates),
              "day7_rows_recounted": len(prediction), "causal_gate_and_time_samples_rebuilt": len(samples),
              "new_fits": 0, "independent_holdout": False, "selection_verified": True}
    (folder / "verification.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    verify(parser.parse_args().workload)
