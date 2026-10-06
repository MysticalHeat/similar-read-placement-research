"""Finite-window three-state gate; no-event is not an eventual negative cause."""

import argparse
import gc
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.paths import PROJECT_ROOT
from read_prediction.artifacts import fingerprint
from read_prediction.experiments.all_write import capped, snapshot, quality, choose, predict_blocks, TICKS
from read_prediction.experiments.overwrite90 import hashes, dump, metrics

OUTPUT = PROJECT_ROOT / "results/window-outcome"


def labels(meta, cutoff):
    state = snapshot(meta, cutoff)[0]
    return np.where(state < 0, 2, state).astype(np.int8)


def matrix(features, meta, origin):
    # Planned deadline follows from the present clock, never from future EOF.
    birth_day = (meta["timestamp"]-origin) // (86400*TICKS) + 1
    remaining = (origin+birth_day*86400*TICKS-meta["timestamp"]) / TICKS
    return np.column_stack((features, np.log1p(remaining))).astype(np.float32)


def probabilities(booster, features, meta, origin):
    result = np.empty(len(meta))
    for start in range(0, len(result), 200_000):
        end = min(start+200_000, len(result))
        result[start:end] = booster.predict(matrix(features[start:end], meta[start:end], origin), num_threads=2)[:, 1]
    return result


def run(workload):
    parent = PROJECT_ROOT / "results/all-write" / workload
    if not (parent / "verification.json").exists():
        raise ValueError("Verify all-write before this follow-up")
    folder = OUTPUT / workload
    folder.mkdir(parents=True, exist_ok=False)
    source = json.loads((parent / "source.json").read_text())
    origin = source["first_timestamp"]
    if source["last_timestamp"] < origin+144*3600*TICKS:
        raise ValueError("Training windows are not fully observed")
    parent_selection = json.loads((parent / "selection.json").read_text())
    cuts = {int(day): value for day, value in parent_selection["cutoffs"].items()}
    meta = np.load(parent / "meta.npy", mmap_mode="r")
    features = np.load(parent / "features.npy", mmap_mode="r")
    slices = {day: slice(np.searchsorted(meta["write"], cuts[day-1]), np.searchsorted(meta["write"], cuts[day])) for day in (5, 6, 7)}
    target5, target6 = labels(meta[slices[5]], cuts[5]), labels(meta[slices[6]], cuts[6])
    train_rows = capped(np.arange(len(target5)), 2_000_000)
    val_rows = capped(np.arange(len(target6)), 1_000_000)
    assert set(np.unique(target5[train_rows])) == {0, 1, 2}
    train_x = matrix(features[slices[5]][train_rows], meta[slices[5]][train_rows], origin)
    val_x = matrix(features[slices[6]][val_rows], meta[slices[6]][val_rows], origin)
    with np.load(parent / "validation.predictions.npz") as saved:
        predictions = {name: saved[name] for name in ("current", "time_raw_l1", "time_log_l1")}
    params = dict(n_estimators=96, min_child_samples=200, learning_rate=.1, reg_lambda=1.,
                  n_jobs=2, random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)
    probability, recipes = {}, {}
    for leaves in (31, 63):
        name = f"window_gate_{leaves}"
        model = lgb.LGBMClassifier(**params, num_leaves=leaves, objective="multiclass")
        model.fit(train_x, target5[train_rows], eval_set=[(val_x, target6[val_rows])],
                  callbacks=[lgb.early_stopping(12, verbose=False)])
        assert list(model.classes_) == [0, 1, 2]
        model.booster_.save_model(str(folder / f"validation-{name}.lightgbm.txt"))
        probability[name] = probabilities(model.booster_, features[slices[6]], meta[slices[6]], origin)
        recipes[name] = {"params": {**params, "num_leaves": leaves, "objective": "multiclass"}, "best_iteration": model.best_iteration_}
        print(f"{workload}: fitted {name}, trees={model.best_iteration_}", flush=True)
        del model
    candidates = {}
    for gate, p in probability.items():
        for time, prediction in predictions.items():
            for threshold in (.5, .6, .7, .8, .9, .95, .99):
                candidates[f"{gate}/{time}/{threshold}"] = quality(meta[slices[6]], prediction, p, threshold, cuts[6], origin+144*3600*TICKS)
    chosen = choose(candidates)
    np.savez(folder / "validation.predictions.npz", **probability, **predictions)
    inputs = [parent / name for name in ("source.json", "features.npy", "meta.npy", "selection.json", "verification.json", "validation.predictions.npz", "day7.predictions.npz")]
    selection = {"workload": workload, "chosen": chosen, "validation": candidates, "recipes": recipes,
                 "independent_holdout": False, "input_hashes": hashes(inputs),
                 "code_hashes": hashes([Path(__file__), PROJECT_ROOT / "read_prediction/checks/window_outcome.py",
                     PROJECT_ROOT / "read_prediction/experiments/all_write.py", PROJECT_ROOT / "read_prediction/checks/all_write.py",
                     PROJECT_ROOT / "read_prediction/experiments/overwrite90.py", PROJECT_ROOT / "docs/protocols/window-outcome-protocol.md"]),
                 "validation_hashes": hashes([folder / "validation.predictions.npz", *folder.glob("validation-*.lightgbm.txt")])}
    dump(folder / "selection.json", selection)
    print(f"{workload}: froze {chosen}: {candidates[chosen]}", flush=True)
    del train_x, val_x, probability, predictions
    gc.collect()
    gate_name, time_name, threshold = chosen.split("/")
    combined = slice(slices[5].start, slices[6].stop)
    # Preserve each birth window's own target, not a new combined deadline.
    combined_labels = np.r_[target5, target6]
    rows = capped(np.arange(len(combined_labels)), 2_000_000)
    recipe = recipes[gate_name]
    model = lgb.LGBMClassifier(**{**recipe["params"], "n_estimators": recipe["best_iteration"]})
    model.fit(matrix(features[combined][rows], meta[combined][rows], origin), combined_labels[rows])
    gate_path = folder / "gate.lightgbm.txt"
    model.booster_.save_model(str(gate_path))
    paths = [gate_path]
    if time_name != "current":
        recipe = parent_selection["recipes"][time_name]
        rows = capped(np.flatnonzero(combined_labels == 1), 1_000_000)
        model = lgb.LGBMRegressor(**{**recipe["params"], "n_estimators": recipe["best_iteration"]})
        truth = meta["target"][combined][rows]
        model.fit(np.asarray(features[combined][rows], dtype=np.float32), np.log1p(truth) if recipe["log"] else truth)
        time_path = folder / "time.lightgbm.txt"
        model.booster_.save_model(str(time_path))
        paths.append(time_path)
    dump(folder / "frozen.json", {"selection_sha256": fingerprint(folder / "selection.json")["sha256"], "models": hashes(paths)})
    del model
    gc.collect()
    with np.load(parent / "day7.predictions.npz") as saved:
        current = saved["current"]
    p = probabilities(lgb.Booster(model_file=str(gate_path)), features[slices[7]], meta[slices[7]], origin)
    prediction = current if time_name == "current" else predict_blocks(lgb.Booster(model_file=str(time_path)), features[slices[7]], recipe["log"])
    threshold = float(threshold)
    end = min(source["last_timestamp"], origin+168*3600*TICKS)
    test = meta[slices[7]]
    selected = quality(test, prediction, p, threshold, cuts[7], end)
    _, observed, known = snapshot(test, cuts[7])
    budget = np.where(known, test["lifetime"], (end-test["timestamp"])/TICKS)
    routed = np.where(p >= threshold, prediction, current)
    result = {"workload": workload, "chosen": chosen, "independent_holdout": False,
              "all_write_selective": selected,
              "original_observed_routed": metrics(test["target"][observed], routed[observed], budget[observed], known[observed]),
              "original_observed_current": metrics(test["target"][observed], current[observed], budget[observed], known[observed])}
    np.savez(folder / "day7.predictions.npz", probability=p, prediction=prediction, current=current)
    dump(folder / "diagnostic.json", result)
    print(f"{workload}: {result}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    run(parser.parse_args().workload)
