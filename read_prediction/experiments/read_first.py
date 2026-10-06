"""Causal read-before-overwrite gate and conditional read-delay prediction."""

import argparse
import gc
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT
from read_prediction.experiments.overwrite90 import (
    load_history, causal_history, matrix, metrics, snapshot_budget, hashes, dump,
)

OUTPUT = PROJECT_ROOT / "results/read-first"
THRESHOLDS = (.5, .7, .8, .9, .95, .99)


def outcome_history(writes, reads, offsets, labels):
    """Labels enter history at Read, when completed-cohort membership is known."""
    result = np.full((len(writes), 3), np.nan)
    result[:, 2] = 0
    order = np.argsort(offsets, kind="stable")
    grouped = offsets[order]
    boundaries = np.r_[0, np.flatnonzero(np.diff(grouped)) + 1, len(order)]
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        rows = order[start:end]
        # These rows all have known outcomes by Read; future labels are not used.
        previous = np.searchsorted(reads[rows], writes[rows], side="left") - 1
        valid = previous >= 0
        selected, last = rows[valid], previous[valid]
        if not len(last):
            continue
        result[selected, 0] = labels[rows[last]]
        recent = np.full((5, len(last)), np.nan)
        for lag in range(5):
            available = last >= lag
            recent[lag, available] = labels[rows[last[available] - lag]]
        result[selected, 1] = np.nanmean(recent, axis=0)
        result[selected, 2] = last + 1
    result[:, 2] = np.log1p(result[:, 2])
    return result


def gate_metrics(target, prediction, budget, known, truth, probability, threshold):
    selected = probability >= threshold
    count = int(selected.sum())
    precision = float(truth[selected].mean()) if count else None
    quality = metrics(target[selected], prediction[selected], budget[selected], known[selected]) if count else None
    return {"selected_n": count, "coverage": count / len(target), "read_first_precision": precision,
            "read_first_recall": float(np.count_nonzero(selected & truth) / truth.sum()) if truth.any() else None,
            "selected": quality,
            "qualifies_selective": bool(count and count / len(target) >= .1 and precision >= .9 and quality["pass_lower_bound"] >= .9)}


def choose(candidates):
    qualified = [name for name, metric in candidates.items() if metric["qualifies_selective"]]
    if qualified:
        return min(qualified, key=lambda name: (-candidates[name]["coverage"], candidates[name]["selected"]["mae_seconds"], name))
    return min(candidates, key=lambda name: (
        -min(candidates[name]["read_first_precision"] or 0,
             candidates[name]["selected"]["pass_lower_bound"] if candidates[name]["selected"] else 0),
        -candidates[name]["coverage"],
        candidates[name]["selected"]["mae_seconds"] if candidates[name]["selected"] else float("inf"), name))


def run(workload):
    output = OUTPUT / workload
    output.mkdir(parents=True, exist_ok=False)
    data, slices, inputs = load_history(workload)
    base_history = causal_history(data)
    original = PROJECT_ROOT / "results/mae-improvement" / workload
    inputs.append(original / "holdout.json")
    holdout = json.loads(inputs[-1].read_text())
    annotations = {}
    for day in (5, 6, 7):
        path = PROJECT_ROOT / "results/overwrite-comparison" / workload / f"day{day}.comparison.npz"
        inputs.append(path)
        with np.load(path) as saved:
            annotations[day] = {key: saved[key] for key in saved.files}
        np.testing.assert_array_equal(data["write_event_index"][slices[day]], annotations[day]["write_event_index"])
    rows56 = slice(slices[5].start, slices[6].stop)
    rows57 = slice(slices[5].start, slices[7].stop)
    labels = np.concatenate([annotations[day]["read_before_overwrite"] for day in (5, 6, 7)])
    outcomes = outcome_history(data["write_event_index"][rows57], data["next_read_event_index"][rows57],
                               data["offset_bytes"][rows57], labels)
    origin = holdout["source"]["first_timestamp"] / 10_000_000
    def features(day):
        rows = slices[day]
        local = slice(rows.start - slices[5].start, rows.stop - slices[5].start)
        return np.column_stack((matrix(data, base_history, rows, origin), outcomes[local])).astype(np.float32)
    train_x, val_x = features(5), features(6)
    n5, n6 = len(train_x), len(val_x)
    truth5, truth6 = labels[:n5], labels[n5:n5+n6]
    target5, target6 = data["target_seconds"][slices[5]], data["target_seconds"][slices[6]]
    budget6, known6 = snapshot_budget(data, slices[6], annotations[6], 144 * 3600,
                                      holdout["days"]["6"]["coverage"]["end_event_exclusive"])
    probabilities, predictions, recipes = {}, {"current": data["current"][slices[6]]}, {}
    params = dict(n_estimators=80, min_child_samples=200, learning_rate=.1, reg_lambda=1.,
                  n_jobs=2, random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)
    for leaves in (15, 31):
        name = f"gate_{leaves}"
        model = lgb.LGBMClassifier(**params, num_leaves=leaves)
        model.fit(train_x, truth5, eval_set=[(val_x, truth6)],
                  callbacks=[lgb.early_stopping(12, verbose=False)])
        probabilities[name] = model.predict_proba(val_x)[:, 1]
        recipes[name] = {"kind": "classifier", "params": {**params, "num_leaves": leaves}, "best_iteration": model.best_iteration_}
        model.booster_.save_model(str(output / f"validation-{name}.lightgbm.txt"))
        print(f"{workload}: trained {name}, trees={model.best_iteration_}", flush=True)
    for log_target in (False, True):
        name = "time_log_l1" if log_target else "time_raw_l1"
        model = lgb.LGBMRegressor(**params, num_leaves=31, objective="regression_l1", metric="None")
        def mae(y_true, prediction):
            value = np.maximum(0, np.expm1(prediction) if log_target else prediction)
            return "seconds_mae", float(np.abs(target6[truth6] - value).mean()), False
        model.fit(train_x[truth5], np.log1p(target5[truth5]) if log_target else target5[truth5],
                  eval_set=[(val_x[truth6], np.log1p(target6[truth6]) if log_target else target6[truth6])],
                  eval_metric=mae, callbacks=[lgb.early_stopping(12, verbose=False)])
        value = model.predict(val_x)
        predictions[name] = np.maximum(0, np.expm1(value) if log_target else value)
        recipes[name] = {"kind": "regressor", "log_target": log_target, "best_iteration": model.best_iteration_,
                         "params": {**params, "num_leaves": 31, "objective": "regression_l1", "metric": "None"}}
        model.booster_.save_model(str(output / f"validation-{name}.lightgbm.txt"))
        print(f"{workload}: trained {name}, trees={model.best_iteration_}", flush=True)
    combinations, combinations_recipes = {}, {}
    for gate, probability in probabilities.items():
        for time, prediction in predictions.items():
            for threshold in THRESHOLDS:
                name = f"{gate}/{time}/{threshold}"
                combinations[name] = gate_metrics(target6, prediction, budget6, known6, truth6, probability, threshold)
                combinations_recipes[name] = {"gate": gate, "time": time, "threshold": threshold}
    chosen = choose(combinations)
    np.savez(output / "validation.predictions.npz", **probabilities, **predictions)
    selection = {"workload": workload, "chosen": chosen, "combination": combinations_recipes[chosen],
                 "recipes": recipes, "validation": combinations, "goal": .9, "independent_holdout": False,
                 "input_hashes": hashes(inputs), "code_hashes": hashes([Path(__file__),
                     PROJECT_ROOT / "read_prediction/checks/read_first.py",
                     PROJECT_ROOT / "read_prediction/checks/overwrite90.py",
                     PROJECT_ROOT / "read_prediction/experiments/overwrite90.py",
                     PROJECT_ROOT / "docs/protocols/read-first-protocol.md"]),
                 "validation_output_hashes": hashes([output / "validation.predictions.npz", *output.glob("validation-*.lightgbm.txt")])}
    dump(output / "selection.json", selection)
    print(f"{workload}: froze {chosen}; validation={combinations[chosen]}", flush=True)
    del train_x, val_x, probabilities, predictions, model
    gc.collect()
    train_x = np.concatenate((features(5), features(6)))
    train_truth = np.r_[truth5, truth6]
    train_y = data["target_seconds"][rows56]
    combination = selection["combination"]
    model_paths = []
    for role in ("gate", "time"):
        name = combination[role]
        if name == "current":
            continue
        recipe = recipes[name]
        model_params = {**recipe["params"], "n_estimators": recipe["best_iteration"]}
        if role == "gate":
            model = lgb.LGBMClassifier(**model_params)
            model.fit(train_x, train_truth)
        else:
            model = lgb.LGBMRegressor(**model_params)
            model.fit(train_x[train_truth], np.log1p(train_y[train_truth]) if recipe["log_target"] else train_y[train_truth])
        path = output / f"{role}.lightgbm.txt"
        model.booster_.save_model(str(path))
        model_paths.append(path)
    dump(output / "frozen.json", {"selection_sha256": fingerprint(output / "selection.json")["sha256"], "models": hashes(model_paths)})
    del train_x, model
    gc.collect()
    gate = lgb.Booster(model_file=str(output / "gate.lightgbm.txt"))
    time_model = lgb.Booster(model_file=str(output / "time.lightgbm.txt")) if combination["time"] != "current" else None
    probability = np.empty(slices[7].stop - slices[7].start)
    prediction = data["current"][slices[7]].copy()
    for begin in range(0, len(probability), 250_000):
        end = min(begin + 250_000, len(probability))
        rows = slice(slices[7].start + begin, slices[7].start + end)
        local = slice(rows.start - slices[5].start, rows.stop - slices[5].start)
        values = np.column_stack((matrix(data, base_history, rows, origin), outcomes[local])).astype(np.float32)
        probability[begin:end] = gate.predict(values, num_threads=2)
        if time_model is not None:
            value = time_model.predict(values, num_threads=2)
            recipe = recipes[combination["time"]]
            prediction[begin:end] = np.maximum(0, np.expm1(value) if recipe["log_target"] else value)
    known = np.isfinite(annotations[7]["overwrite_seconds"])
    budget = np.where(known, annotations[7]["overwrite_seconds"], annotations[7]["overwrite_censor_lower_bound_seconds"])
    truth7 = annotations[7]["read_before_overwrite"]
    target7 = data["target_seconds"][slices[7]]
    selected = probability >= combination["threshold"]
    routed = np.where(selected, prediction, data["current"][slices[7]])
    result = {"workload": workload, "chosen": chosen, "independent_holdout": False,
              "selective": gate_metrics(target7, prediction, budget, known, truth7, probability, combination["threshold"]),
              "routed_all": metrics(target7, routed, budget, known),
              "current_all": metrics(target7, data["current"][slices[7]], budget, known),
              "coverage": holdout["days"]["7"]["coverage"]}
    np.savez(output / "day7.predictions.npz", write_event_index=data["write_event_index"][slices[7]],
             probability=probability, prediction=prediction, routed=routed)
    dump(output / "diagnostic.json", result)
    print(f"{workload}: {result}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    run(parser.parse_args().workload)
