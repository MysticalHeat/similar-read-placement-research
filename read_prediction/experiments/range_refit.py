"""Refit gate and conditional time on byte-range labeled outcomes."""

import argparse
import gc
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.experiments.all_write import (
    META,
    N_FEATURES,
    THRESHOLDS,
    capped,
    choose,
    predict_blocks,
    quality,
    snapshot,
)
from read_prediction.experiments.overwrite90 import dump, hashes, metrics
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import label_writes

OUTPUT = PROJECT_ROOT / "results/range-refit"
PARAMS = dict(n_estimators=96, min_child_samples=200, learning_rate=.1, reg_lambda=1.,
              n_jobs=2, random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)


def labeled_meta(parent, cutoffs, regions=16):
    """Range-labeled META array for every all-write row (days 5-7)."""
    source = json.loads((parent / "source.json").read_text())
    events = np.memmap(parent / "events.bin", mode="r",
                       dtype=[("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")],
                       shape=(source["loaded_events"],))
    old_meta = np.load(parent / "meta.npy", mmap_mode="r")
    labels = label_writes(events, np.asarray(old_meta["write"]), begin=int(cutoffs[4]), regions=regions)
    labeled = np.empty(len(old_meta), dtype=META)
    labeled["write"] = old_meta["write"]
    labeled["timestamp"] = old_meta["timestamp"]
    labeled["read"] = labels["read"]
    labeled["overwrite"] = labels["overwrite"]
    labeled["target"] = labels["target"]
    labeled["lifetime"] = labels["lifetime"]
    del events
    return labeled, old_meta, source


def run(workload):
    folder = OUTPUT / workload
    folder.mkdir(parents=True, exist_ok=False)
    parent = PROJECT_ROOT / "results/all-write" / workload
    source = json.loads((parent / "source.json").read_text())
    origin = source["first_timestamp"]
    timestamps = np.memmap(parent / "events.bin", mode="r",
                           dtype=[("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")],
                           shape=(source["loaded_events"],))["timestamp"]
    cutoffs = {day: int(np.searchsorted(timestamps, origin + day * 86400 * 10_000_000)) for day in (4, 5, 6, 7)}
    del timestamps
    labeled, old_meta, source = labeled_meta(parent, cutoffs)
    del old_meta
    gc.collect()
    features = np.load(parent / "features.npy", mmap_mode="r")
    slices = {day: slice(int(np.searchsorted(labeled["write"], cutoffs[day - 1])),
                         int(np.searchsorted(labeled["write"], cutoffs[day]))) for day in (5, 6, 7)}
    # Internal consistency: day-7 labels must equal the frozen range-label diagnostic.
    day7 = np.load(PROJECT_ROOT / "results/range-label" / workload / "labeling.npz")
    test_slice = slices[7]
    np.testing.assert_array_equal(labeled["write"][test_slice], day7["write_index"])
    np.testing.assert_array_equal(labeled["read"][test_slice], day7["new_read"])
    np.testing.assert_array_equal(labeled["overwrite"][test_slice], day7["new_write"])
    same = np.isfinite(labeled["target"][test_slice]) & np.isfinite(day7["new_target"])
    np.testing.assert_allclose(labeled["target"][test_slice][same], day7["new_target"][same], rtol=0, atol=1e-9)
    assert int((~same).sum()) == int((day7["new_read"] < 0).sum())
    del day7
    old = PROJECT_ROOT / "results/mae-improvement" / workload
    inputs = [old / "holdout.json", parent / "source.json", parent / "features.npy", parent / "meta.npy",
              parent / "events.bin", parent / "validation.predictions.npz", parent / "day7.predictions.npz",
              PROJECT_ROOT / "results/range-label" / workload / "labeling.npz"]
    current_definition = json.loads((old / "selection.json").read_text())["definitions"]["current"]
    current_path = PROJECT_ROOT / current_definition["model_path"]
    inputs.append(current_path)
    with np.load(parent / "validation.predictions.npz") as saved:
        assert saved["current"].shape == (slices[6].stop - slices[6].start,)
        current_val = saved["current"].copy()
    with np.load(parent / "day7.predictions.npz") as saved:
        assert saved["current"].shape == (slices[7].stop - slices[7].start,)
        current_test = saved["current"].copy()

    train_meta, val_meta = labeled[slices[5]], labeled[slices[6]]
    states = {day: snapshot(labeled[slices[day]], cutoffs[day])[0] for day in (5, 6)}
    train_x, val_x = features[slices[5]], features[slices[6]]
    known_train = capped(np.flatnonzero(states[5] >= 0), 2_000_000)
    known_val = capped(np.flatnonzero(states[6] >= 0), 1_000_000)
    positive_train = capped(np.flatnonzero(states[5] == 1), 1_000_000)
    positive_val = capped(np.flatnonzero(states[6] == 1), 1_000_000)
    probabilities, predictions, recipes = {}, {"current": current_val}, {}
    for leaves in (31, 63):
        name = f"gate_{leaves}"
        model = lgb.LGBMClassifier(**PARAMS, num_leaves=leaves)
        model.fit(np.asarray(train_x[known_train], dtype=np.float32), states[5][known_train],
                  eval_set=[(np.asarray(val_x[known_val], dtype=np.float32), states[6][known_val])],
                  callbacks=[lgb.early_stopping(12, verbose=False)])
        model.booster_.save_model(str(folder / f"validation-{name}.lightgbm.txt"))
        probabilities[name] = predict_blocks(model.booster_, val_x)
        recipes[name] = {"kind": "gate", "params": {**PARAMS, "num_leaves": leaves}, "best_iteration": model.best_iteration_}
        print(f"{workload}: fitted {name}, trees={model.best_iteration_}", flush=True)
        del model
        gc.collect()
    for log in (False, True):
        name = "time_log_l1" if log else "time_raw_l1"
        model = lgb.LGBMRegressor(**PARAMS, num_leaves=31, objective="regression_l1", metric="None")
        target = train_meta["target"][positive_train]
        valid_target = val_meta["target"][positive_val]

        def measure(y_true, prediction):
            value = np.maximum(0, np.expm1(prediction) if log else prediction)
            return "seconds_mae", float(np.abs(valid_target - value).mean()), False

        model.fit(np.asarray(train_x[positive_train], dtype=np.float32), np.log1p(target) if log else target,
                  eval_set=[(np.asarray(val_x[positive_val], dtype=np.float32), np.log1p(valid_target) if log else valid_target)],
                  eval_metric=measure, callbacks=[lgb.early_stopping(12, verbose=False)])
        model.booster_.save_model(str(folder / f"validation-{name}.lightgbm.txt"))
        predictions[name] = predict_blocks(model.booster_, val_x, log)
        recipes[name] = {"kind": "time", "log": log, "params": {**PARAMS, "num_leaves": 31, "objective": "regression_l1", "metric": "None"}, "best_iteration": model.best_iteration_}
        print(f"{workload}: fitted {name}, trees={model.best_iteration_}", flush=True)
        del model
        gc.collect()
    combinations = {}
    for gate, probability in probabilities.items():
        for time, prediction in predictions.items():
            for threshold in THRESHOLDS:
                combinations[f"{gate}/{time}/{threshold}"] = quality(val_meta, prediction, probability, threshold,
                                                                     cutoffs[6], origin + 144 * 3600 * 10_000_000)
    chosen = choose(combinations)
    np.savez(folder / "validation.predictions.npz", **probabilities, **predictions)
    selection = {"workload": workload, "chosen": chosen, "validation": combinations, "recipes": recipes,
                 "independent_holdout": False, "cutoffs": cutoffs,
                 "sample_caps": {"gate_train": 2_000_000, "time_train": 1_000_000, "validation": 1_000_000},
                 "input_hashes": hashes(inputs), "code_hashes": hashes([Path(__file__), PROJECT_ROOT / "read_prediction/checks/range_refit.py",
                     PROJECT_ROOT / "read_prediction/range_label.py", PROJECT_ROOT / "read_prediction/experiments/all_write.py",
                     PROJECT_ROOT / "read_prediction/experiments/overwrite90.py",
                     PROJECT_ROOT / "docs/protocols/range-refit-protocol.md"]),
                 "validation_hashes": hashes([folder / "validation.predictions.npz", *folder.glob("validation-*.lightgbm.txt")])}
    dump(folder / "selection.json", selection)
    print(f"{workload}: froze {chosen}: {combinations[chosen]}", flush=True)
    del probabilities, predictions
    gc.collect()

    gate_name, time_name, threshold = chosen.split("/")
    combined = slice(slices[5].start, slices[6].stop)
    combined_state = snapshot(labeled[combined], cutoffs[6])[0]
    paths = []
    for role, name in (("gate", gate_name), ("time", time_name)):
        if name == "current":
            continue
        recipe = recipes[name]
        rows = capped(np.flatnonzero(combined_state >= 0 if role == "gate" else combined_state == 1),
                      2_000_000 if role == "gate" else 1_000_000)
        values = np.asarray(features[combined][rows], dtype=np.float32)
        model_params = {**recipe["params"], "n_estimators": recipe["best_iteration"]}
        if role == "gate":
            model = lgb.LGBMClassifier(**model_params)
            model.fit(values, combined_state[rows])
        else:
            target = labeled["target"][combined][rows]
            model = lgb.LGBMRegressor(**model_params)
            model.fit(values, np.log1p(target) if recipe["log"] else target)
        path = folder / f"{role}.lightgbm.txt"
        model.booster_.save_model(str(path))
        paths.append(path)
        del model, values
        gc.collect()
    dump(folder / "frozen.json", {"selection_sha256": fingerprint(folder / "selection.json")["sha256"], "models": hashes(paths)})

    test_meta = labeled[slices[7]]
    probability = predict_blocks(lgb.Booster(model_file=str(folder / "gate.lightgbm.txt")), features[slices[7]])
    prediction = current_test if time_name == "current" else predict_blocks(
        lgb.Booster(model_file=str(folder / "time.lightgbm.txt")), features[slices[7]], recipes[time_name]["log"])
    threshold = float(threshold)
    end_timestamp = min(source["last_timestamp"], origin + 168 * 3600 * 10_000_000)
    full_quality = quality(test_meta, prediction, probability, threshold, cutoffs[7], end_timestamp)
    routed = np.where(probability >= threshold, prediction, current_test)

    old_test = np.load(parent / "meta.npy", mmap_mode="r")[slices[7]]
    observed_old = (old_test["read"] >= 0) & (old_test["read"] < cutoffs[7])
    known_old = (old_test["overwrite"] >= 0) & (old_test["overwrite"] < cutoffs[7])
    budget_old = np.where(known_old, old_test["lifetime"], (end_timestamp - old_test["timestamp"]) / 10_000_000)
    original_current = metrics(old_test["target"][observed_old], current_test[observed_old], budget_old[observed_old], known_old[observed_old])
    published = json.loads((parent / "diagnostic.json").read_text())["original_observed_current"]["pass_lower_bound"]
    assert abs(original_current["pass_lower_bound"] - published) < 1e-9
    original_routed = metrics(old_test["target"][observed_old], routed[observed_old], budget_old[observed_old], known_old[observed_old])
    observed_range = test_meta["read"] >= 0
    known_range = test_meta["overwrite"] >= 0
    budget_range = np.where(known_range, test_meta["lifetime"], (end_timestamp - test_meta["timestamp"]) / 10_000_000)
    range_routed = metrics(test_meta["target"][observed_range], routed[observed_range], budget_range[observed_range], known_range[observed_range])

    selected = probability >= threshold
    observed_selected = selected & observed_range
    zero_pass = int(np.count_nonzero(observed_selected & (test_meta["target"] < budget_range)))
    zero_mae = float(np.abs(test_meta["target"][observed_selected]).mean()) if observed_selected.any() else None
    state_test = snapshot(test_meta, cutoffs[7])[0]
    result = {"workload": workload, "chosen": chosen, "independent_holdout": False,
              "all_write_selective": full_quality,
              "original_observed_current": original_current, "original_observed_routed": original_routed,
              "range_observed_routed": range_routed,
              "zero_on_selected": {"selected_n": int(selected.sum()),
                                   "observed_selected_n": int(observed_selected.sum()),
                                   "zero_pass_lower": zero_pass / int(selected.sum()) if selected.any() else None,
                                   "zero_mae_seconds": zero_mae},
              "outcomes": {"all_writes": len(test_meta),
                           "read_first": int((state_test == 1).sum()),
                           "write_first": int((state_test == 0).sum()),
                           "censored": int((state_test < 0).sum()),
                           "observed_reads": int(observed_range.sum())}}
    np.savez(folder / "day7.predictions.npz", probability=probability, prediction=prediction, current=current_test)
    np.savez(folder / "labels.npz", write=labeled["write"], read=labeled["read"], overwrite=labeled["overwrite"],
             target=labeled["target"], lifetime=labeled["lifetime"], timestamp=labeled["timestamp"])
    dump(folder / "diagnostic.json", result)
    print(f"{workload}: {json.dumps(result['all_write_selective'])}", flush=True)
    print(f"{workload}: routed original={original_routed['pass_lower_bound']:.4f} range={range_routed['pass_lower_bound']:.4f}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    run(parser.parse_args().workload)
