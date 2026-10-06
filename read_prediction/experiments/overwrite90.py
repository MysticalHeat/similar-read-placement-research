"""Bounded, causal diagnostic search for 90% error-before-overwrite coverage."""

import argparse
import gc
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "results/overwrite90"
GOAL = .90
FIELDS = ("write_event_index", "next_read_event_index", "offset_bytes", "target_seconds",
          "write_seconds", "next_read_seconds", "current", "address_median")
FEATURES = ("log_current", "log_address_median", "log_last_completed", "log_median5",
            "log_mean5", "log_completed_read_age", "log_completed_pairs", "tod_sin", "tod_cos", "log_offset")


def dump(path, record):
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def hashes(paths):
    return {p.relative_to(PROJECT_ROOT).as_posix(): fingerprint(p)["sha256"] for p in sorted(set(paths))}


def load_history(workload):
    folder = PROJECT_ROOT / "results/mae-improvement" / workload
    parts, paths, slices = [], [], {}
    start = 0
    for day in range(2, 8):
        path = folder / (f"day{day}.predictions.npz" if day < 5 else f"holdout-day{day}.predictions.npz")
        with np.load(path) as data:
            part = {key: data[key] for key in FIELDS}
        end = start + len(part["target_seconds"])
        slices[day] = slice(start, end)
        parts.append(part)
        paths.append(path)
        start = end
    data = {key: np.concatenate([part[key] for part in parts]) for key in FIELDS}
    assert np.all(np.diff(data["write_event_index"]) > 0)
    assert np.all(data["next_read_event_index"] > data["write_event_index"])
    return data, slices, paths


def causal_history(data):
    """Last/median/mean delays and age/count of pairs already completed by Write."""
    result = np.full((len(data["target_seconds"]), 5), np.nan)
    result[:, 4] = 0
    order = np.argsort(data["offset_bytes"], kind="stable")
    offsets = data["offset_bytes"][order]
    bounds = np.r_[0, np.flatnonzero(np.diff(offsets)) + 1, len(order)]
    for begin, end in zip(bounds[:-1], bounds[1:]):
        rows = order[begin:end]
        reads = data["next_read_event_index"][rows]
        assert np.all(np.diff(reads) >= 0)
        previous = np.searchsorted(reads, data["write_event_index"][rows], side="left") - 1
        valid = previous >= 0
        if not valid.any():
            continue
        selected, last = rows[valid], previous[valid]
        result[selected, 0] = data["target_seconds"][rows[last]]
        recent = np.full((5, len(last)), np.nan)
        for lag in range(5):
            available = last >= lag
            recent[lag, available] = data["target_seconds"][rows[last[available] - lag]]
        result[selected, 1] = np.nanmedian(recent, axis=0)
        result[selected, 2] = np.nanmean(recent, axis=0)
        result[selected, 3] = data["write_seconds"][selected] - data["next_read_seconds"][rows[last]]
        result[selected, 4] = last + 1
    return result


def matrix(data, history, rows, origin):
    values = np.empty((len(data["target_seconds"][rows]), len(FEATURES)), dtype=np.float32)
    values[:, 0] = np.log1p(data["current"][rows])
    values[:, 1] = np.log1p(data["address_median"][rows])
    values[:, 2:7] = np.log1p(history[rows])
    phase = 2 * np.pi * ((data["write_seconds"][rows] + origin) % 86400) / 86400
    values[:, 7], values[:, 8] = np.sin(phase), np.cos(phase)
    values[:, 9] = np.log1p(data["offset_bytes"][rows])
    return values


def simple_predictions(data, history, rows):
    current = data["current"][rows]
    last, median, mean = (np.where(np.isfinite(history[rows, i]), history[rows, i], current) for i in range(3))
    predictions = {"current": current, "address_median": data["address_median"][rows],
                   "last_completed": last, "median5": median, "mean5": mean}
    for weight in (.25, .5, .75):
        predictions[f"current_median5_{int(weight * 100)}"] = weight * current + (1 - weight) * median
    for scale in (.5, .75, 1.25):
        predictions[f"current_scale_{int(scale * 100)}"] = scale * current
    return predictions


def metrics(target, prediction, budget, observed):
    error = np.abs(target - prediction)
    passed = error < budget
    known_passes = int(np.count_nonzero(passed & observed))
    censored_passes = int(np.count_nonzero(passed & ~observed))
    n = len(error)
    return {"n": n, "mae_seconds": float(error.mean()),
            "known_n": int(observed.sum()), "zero_interval_n": int(np.count_nonzero(observed & (budget == 0))),
            "known_passes": known_passes, "censored_certified_passes": censored_passes,
            "pass_lower_bound": (known_passes + censored_passes) / n,
            "pass_upper_bound": (known_passes + int((~observed).sum())) / n,
            "meets_90_percent": bool((known_passes + censored_passes) / n >= GOAL)}


def snapshot_budget(data, rows, annotation, end_seconds, end_event):
    observed = (annotation["next_write_event_index"] >= 0) & (annotation["next_write_event_index"] < end_event)
    budget = np.where(observed, annotation["overwrite_seconds"], end_seconds - data["write_seconds"][rows])
    assert np.isfinite(budget).all() and np.all(budget >= 0)
    return budget, observed


def weights(budget, observed):
    result = np.clip(1 / np.maximum(budget, 1.), .01, 1.)
    result[observed & (budget == 0)] = 0
    return result


def select(validation):
    return min(validation, key=lambda name: (-validation[name]["pass_lower_bound"], validation[name]["mae_seconds"], name))


def run(workload):
    output = OUTPUT / workload
    output.mkdir(parents=True, exist_ok=False)
    data, slices, inputs = load_history(workload)
    print(f"{workload}: build causal history for {len(data['target_seconds']):,} observed pairs", flush=True)
    history = causal_history(data)
    original = PROJECT_ROOT / "results/mae-improvement" / workload
    holdout_path = original / "holdout.json"
    holdout = json.loads(holdout_path.read_text())
    inputs.append(holdout_path)
    annotations = {}
    for day in (5, 6, 7):
        path = PROJECT_ROOT / "results/overwrite-comparison" / workload / f"day{day}.comparison.npz"
        inputs.append(path)
        with np.load(path) as saved:
            annotations[day] = {key: saved[key] for key in saved.files}
        np.testing.assert_array_equal(annotations[day]["write_event_index"], data["write_event_index"][slices[day]])
    origin = holdout["source"]["first_timestamp"] / 10_000_000
    validation_y = data["target_seconds"][slices[6]]
    validation_budget, validation_known = snapshot_budget(data, slices[6], annotations[6], 144 * 3600,
                                                          holdout["days"]["6"]["coverage"]["end_event_exclusive"])
    train_budget, train_known = snapshot_budget(data, slices[5], annotations[5], 120 * 3600,
                                                holdout["days"]["5"]["coverage"]["end_event_exclusive"])
    validation_predictions = simple_predictions(data, history, slices[6])
    validation = {name: metrics(validation_y, prediction, validation_budget, validation_known)
                  for name, prediction in validation_predictions.items()}
    recipes: dict[str, dict] = {name: {"kind": "simple"} for name in validation}
    train_x = matrix(data, history, slices[5], origin)
    val_x = matrix(data, history, slices[6], origin)
    train_y = data["target_seconds"][slices[5]]
    for log_target in (False, True):
        for weighted in (False, True):
            name = ("log_l1" if log_target else "raw_l1") + ("_weighted" if weighted else "_uniform")
            params = dict(objective="regression_l1", metric="None", n_estimators=64, num_leaves=15,
                          min_child_samples=200, learning_rate=.1, reg_lambda=1., n_jobs=2,
                          random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)
            def measure(y_true, prediction):
                predicted = np.maximum(0, np.expm1(prediction) if log_target else prediction)
                return "failure_fraction", float(np.mean(np.abs(validation_y - predicted) >= validation_budget)), False
            model = lgb.LGBMRegressor(**params)
            model.fit(train_x, np.log1p(train_y) if log_target else train_y,
                      sample_weight=weights(train_budget, train_known) if weighted else None,
                      eval_set=[(val_x, np.log1p(validation_y) if log_target else validation_y)],
                      eval_metric=measure, feature_name=list(FEATURES),
                      callbacks=[lgb.early_stopping(12, verbose=False)])
            predicted = model.predict(val_x)
            predicted = np.maximum(0, np.expm1(predicted) if log_target else predicted)
            validation_predictions[name] = predicted
            model.booster_.save_model(str(output / f"validation-{name}.lightgbm.txt"))
            validation[name] = metrics(validation_y, predicted, validation_budget, validation_known)
            recipes[name] = {"kind": "model", "log_target": log_target, "weighted": weighted,
                             "best_iteration": model.best_iteration_, "params": params}
            print(f"{workload}: {name}, trees={model.best_iteration_}, validation pass>={validation[name]['pass_lower_bound']:.2%}", flush=True)
            del model
    chosen = select(validation)
    np.savez(output / "validation.predictions.npz", **validation_predictions)
    del validation_predictions
    selection = {"workload": workload, "goal": GOAL, "chosen": chosen, "recipe": recipes[chosen],
                 "validation": validation, "selection_day": 6, "diagnostic_day": 7,
                 "independent_holdout": False, "abstention": False,
                 "input_hashes": hashes(inputs), "code_hashes": hashes([
                     Path(__file__), PROJECT_ROOT / "read_prediction/checks/overwrite90.py",
                     PROJECT_ROOT / "docs/protocols/overwrite90-protocol.md"]),
                 "validation_output_hashes": hashes([output / "validation.predictions.npz", *output.glob("validation-*.lightgbm.txt")])}
    dump(output / "selection.json", selection)
    print(f"{workload}: froze {chosen} before day-7 evaluation", flush=True)
    del train_x, val_x
    gc.collect()
    if recipes[chosen]["kind"] == "model":
        recipe = recipes[chosen]
        rows = slice(slices[5].start, slices[6].stop)
        train_x = matrix(data, history, rows, origin)
        train_y = data["target_seconds"][rows]
        budgets, known = [], []
        for day in (5, 6):
            budget, observed = snapshot_budget(data, slices[day], annotations[day], 144 * 3600,
                                               holdout["days"]["6"]["coverage"]["end_event_exclusive"])
            budgets.append(budget)
            known.append(observed)
        params = {**recipe["params"], "n_estimators": recipe["best_iteration"]}
        model = lgb.LGBMRegressor(**params)
        model.fit(train_x, np.log1p(train_y) if recipe["log_target"] else train_y,
                  sample_weight=weights(np.concatenate(budgets), np.concatenate(known)) if recipe["weighted"] else None,
                  feature_name=list(FEATURES))
        model_path = output / "selected.lightgbm.txt"
        model.booster_.save_model(str(model_path))
        dump(output / "frozen.json", {"selection_sha256": fingerprint(output / "selection.json")["sha256"],
                                      "model_sha256": fingerprint(model_path)["sha256"]})
        del train_x, model
        gc.collect()
        booster = lgb.Booster(model_file=str(model_path))
        prediction = np.empty(len(data["target_seconds"][slices[7]]))
        for begin in range(0, len(prediction), 250_000):
            end = min(begin + 250_000, len(prediction))
            block = slice(slices[7].start + begin, slices[7].start + end)
            values = booster.predict(matrix(data, history, block, origin), num_threads=2)
            prediction[begin:end] = np.maximum(0, np.expm1(values) if recipe["log_target"] else values)
    else:
        dump(output / "frozen.json", {"selection_sha256": fingerprint(output / "selection.json")["sha256"]})
        prediction = simple_predictions(data, history, slices[7])[chosen]
    annotation = annotations[7]
    known = np.isfinite(annotation["overwrite_seconds"])
    budget = np.where(known, annotation["overwrite_seconds"], annotation["overwrite_censor_lower_bound_seconds"])
    target = data["target_seconds"][slices[7]]
    result = {"workload": workload, "chosen": chosen, "goal": GOAL, "independent_holdout": False,
              "diagnostic_day": 7, "selected": metrics(target, prediction, budget, known),
              "current": metrics(target, data["current"][slices[7]], budget, known),
              "coverage": holdout["days"]["7"]["coverage"], "new_model_fits": 4 + int(recipes[chosen]["kind"] == "model")}
    np.savez(output / "day7.predictions.npz", write_event_index=data["write_event_index"][slices[7]], prediction=prediction)
    dump(output / "diagnostic.json", result)
    print(f"{workload}: day7 current>={result['current']['pass_lower_bound']:.2%}; {chosen}>={result['selected']['pass_lower_bound']:.2%}; target90={result['selected']['meets_90_percent']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    run(parser.parse_args().workload)


if __name__ == "__main__":
    main()
