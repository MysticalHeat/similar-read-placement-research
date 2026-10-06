"""Bounded-memory all-Write preparation and competing-outcome diagnostics."""

import argparse
import gc
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.extended import load_duration, EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT
from read_prediction.experiments.overwrite90 import dump, hashes, metrics
from read_prediction.artifacts import fingerprint

OUTPUT = PROJECT_ROOT / "results/all-write"
META = np.dtype([(name, "<i8") for name in ("write", "read", "overwrite", "timestamp")] +
                [("target", "<f8"), ("lifetime", "<f8")])
N_FEATURES = 17
BUCKET_DTYPE = np.dtype([("index", "<i8"), *EVENT_DTYPE.descr])
THRESHOLDS = (.5, .6, .7, .8, .9, .95, .99)
TICKS = 10_000_000


def buckets(offsets):
    return ((offsets >> 9) ^ (offsets >> 21) ^ (offsets >> 33)) & 127


def prepare(events, folder, start_seconds=96 * 3600):
    origin = int(events["timestamp"][0])
    start_event = np.searchsorted(events["timestamp"], origin + int(start_seconds * TICKS))
    all_writes = np.flatnonzero(events["is_read"] == 0)
    first_write = int(np.searchsorted(all_writes, start_event))
    count = len(all_writes) - first_write
    if not count:
        raise ValueError("No eligible Write")
    features = np.lib.format.open_memmap(folder / "features.npy", mode="w+", dtype=np.float64, shape=(count, N_FEATURES))
    meta = np.lib.format.open_memmap(folder / "meta.npy", mode="w+", dtype=META, shape=(count,))
    # Seed global lag features chronologically, avoiding random source-cache reads.
    for begin in range(first_write, len(all_writes), 200_000):
        end = min(begin+200_000, len(all_writes))
        rows = slice(begin-first_write, end-first_write)
        previous = all_writes[np.maximum(np.arange(begin, end)-1, 0)]
        index = all_writes[begin:end]
        features[rows, 15] = np.abs(events["offset"][index] - events["offset"][previous])
        features[rows, 16] = (events["timestamp"][index] - events["timestamp"][previous]) / TICKS
    if first_write == 0:
        features[0, 15:] = np.nan
    features.flush()
    files = [(folder / f"bucket-{i}.bin").open("wb") for i in range(128)]
    seconds = int((int(events["timestamp"][-1]) - origin) // TICKS) + 1
    volume = np.zeros((2, seconds), dtype=np.int64)
    try:
        for begin in range(0, len(events), 250_000):
            end = min(begin + 250_000, len(events))
            chunk = events[begin:end]
            ids = buckets(chunk["offset"])
            order = np.argsort(ids, kind="stable")
            counts = np.bincount(ids, minlength=128)
            boundaries = np.r_[0, np.cumsum(counts)]
            records = np.empty(len(chunk), dtype=BUCKET_DTYPE)
            records["index"] = np.arange(begin, end)
            for field in EVENT_DTYPE.names:
                records[field] = chunk[field]
            for i in range(128):
                if counts[i]:
                    files[i].write(records[order[boundaries[i]:boundaries[i+1]]].tobytes())
            clock = (chunk["timestamp"] - origin) // TICKS
            lo, hi = int(clock[0]), int(clock[-1]) + 1
            for kind in (0, 1):
                mask = chunk["is_read"] == kind
                volume[kind, lo:hi] += np.bincount(clock[mask] - lo, minlength=hi-lo)
    finally:
        for file in files:
            file.close()
    prefix = np.column_stack((np.zeros(2, dtype=np.int64), np.cumsum(volume, axis=1)))
    del volume
    for bucket in range(128):
        path = folder / f"bucket-{bucket}.bin"
        records = np.fromfile(path, dtype=BUCKET_DTYPE)
        if not len(records):
            path.unlink()
            continue
        grouped = records[np.argsort(records["offset"], kind="stable")]
        del records
        is_read = grouped["is_read"].astype(bool)
        rp, wp = np.flatnonzero(is_read), np.flatnonzero(~is_read)
        reads, writes = grouped[rp], grouped[wp]
        del grouped, is_read
        ro, wo = reads["offset"], writes["offset"]
        for begin in range(0, len(writes), 200_000):
            end = min(begin + 200_000, len(writes))
            slot = np.arange(begin, end)
            global_rows = np.searchsorted(all_writes, writes["index"][begin:end])
            keep = global_rows >= first_write
            if not keep.any():
                continue
            slot, global_rows = slot[keep], global_rows[keep]
            index = writes["index"][slot]
            rows = global_rows - first_write
            offset, timestamp = writes["offset"][slot], writes["timestamp"][slot]
            rslot = np.searchsorted(rp, wp[slot], side="right")
            prior_reads = rslot - np.searchsorted(ro, offset, side="left")
            prior_writes = slot - np.searchsorted(wo, offset, side="left")
            values = np.full((len(rows), N_FEATURES), np.nan)
            values[:, :4] = np.column_stack((offset, writes["size"][slot], prior_reads, prior_writes))
            previous_write = writes[np.maximum(slot - 1, 0)]
            has_write = prior_writes > 0
            values[has_write, 5] = (timestamp[has_write] - previous_write["timestamp"][has_write]) / TICKS
            values[has_write, 8] = previous_write["size"][has_write]
            values[:, 7] = prior_writes
            next_read = np.full(len(rows), -1, dtype=np.int64)
            target = np.full(len(rows), np.nan)
            if len(reads):
                previous_read = reads[np.clip(rslot-1, 0, len(reads)-1)]
                previous_two = reads[np.clip(rslot-2, 0, len(reads)-1)]
                has_read, has_gap = prior_reads > 0, prior_reads > 1
                values[has_read, 4] = (timestamp[has_read] - previous_read["timestamp"][has_read]) / TICKS
                values[has_gap, 6] = (previous_read["timestamp"][has_gap] - previous_two["timestamp"][has_gap]) / TICKS
                values[has_read, 7] = slot[has_read] - np.searchsorted(wp, rp[rslot[has_read]-1], side="right")
                candidate = reads[np.minimum(rslot, len(reads)-1)]
                found = (rslot < len(reads)) & (candidate["offset"] == offset)
                next_read[found] = candidate["index"][found]
                target[found] = (candidate["timestamp"][found] - timestamp[found]) / TICKS
            candidate = writes[np.minimum(slot + 1, len(writes)-1)]
            found = (slot+1 < len(writes)) & (candidate["offset"] == offset)
            following = np.where(found, candidate["index"], -1)
            lifetime = np.full(len(rows), np.nan)
            lifetime[found] = (candidate["timestamp"][found] - timestamp[found]) / TICKS
            clock = (timestamp - origin) // TICKS
            for kind, column in ((1, 9), (0, 10)):
                values[:, column] = prefix[kind, clock] - prefix[kind, np.maximum(clock-1, 0)]
                values[:, column+2] = prefix[kind, clock] - prefix[kind, np.maximum(clock-60, 0)]
            values[:, 15:] = features[rows, 15:]
            values[:, :13] = np.log1p(values[:, :13])
            values[:, 15:] = np.log1p(values[:, 15:])
            phase = 2 * np.pi * (timestamp % (86400*TICKS)) / (86400*TICKS)
            values[:, 13], values[:, 14] = np.sin(phase), np.cos(phase)
            features[rows] = values
            for field, value in (("write", index), ("read", next_read), ("overwrite", following),
                                 ("timestamp", timestamp), ("target", target), ("lifetime", lifetime)):
                meta[field][rows] = value
        features.flush()
        meta.flush()
        path.unlink()
        del reads, writes, rp, wp, ro, wo
        if bucket % 16 == 0:
            print(f"Prepared bucket {bucket}/128", flush=True)
    np.testing.assert_array_equal(meta["write"], all_writes[first_write:])
    return features, meta


def snapshot(meta, end_event):
    read = np.where(meta["read"] >= 0, meta["read"], np.iinfo(np.int64).max)
    write = np.where(meta["overwrite"] >= 0, meta["overwrite"], np.iinfo(np.int64).max)
    first = np.minimum(read, write)
    state = np.full(len(meta), -1, dtype=np.int8)
    resolved = first < end_event
    state[resolved] = (read[resolved] < write[resolved]).astype(np.int8)
    observed_read = (meta["read"] >= 0) & (meta["read"] < end_event)
    known_write = (meta["overwrite"] >= 0) & (meta["overwrite"] < end_event)
    return state, observed_read, known_write


def quality(meta, prediction, probability, threshold, end_event, end_timestamp):
    state, observed, known_write = snapshot(meta, end_event)
    mask = probability >= threshold
    n = int(mask.sum())
    positive = int(np.count_nonzero(mask & (state == 1)))
    censored = int(np.count_nonzero(mask & (state < 0)))
    budget = np.where(known_write, meta["lifetime"], (end_timestamp - meta["timestamp"]) / TICKS)
    passed = observed & (np.abs(meta["target"] - prediction) < budget)
    count_pass = int(np.count_nonzero(mask & passed))
    evaluable = mask & observed
    error = float(np.abs(meta["target"][evaluable] - prediction[evaluable]).mean()) if evaluable.any() else None
    return {"selected_n": n, "all_writes": len(meta), "coverage": n / len(meta),
            "read_first_lower": positive / n if n else None,
            "read_first_upper": (positive+censored) / n if n else None,
            "selected_censored": censored, "selected_observed_read": int(evaluable.sum()),
            "confirmed_error_lt_overwrite_lower": count_pass / n if n else None,
            "observed_selected_mae_seconds": error,
            "qualifies": bool(n and n / len(meta) >= .1 and positive / n >= .9 and count_pass / n >= .9)}


def choose(values):
    qualified = [key for key, value in values.items() if value["qualifies"]]
    if qualified:
        return min(qualified, key=lambda key: (-values[key]["coverage"], values[key]["observed_selected_mae_seconds"], key))
    broad = [key for key, value in values.items() if value["coverage"] >= .1]
    if broad:
        return min(broad, key=lambda key: (-min(values[key]["read_first_lower"], values[key]["confirmed_error_lt_overwrite_lower"]),
                                          -values[key]["coverage"], key))
    return min(values, key=lambda key: (-values[key]["coverage"], key))


def capped(rows, maximum):
    if len(rows) > maximum:
        rows = np.sort(np.random.default_rng(42).choice(rows, maximum, replace=False))
    return rows


def predict_blocks(model, features, log=False, columns=None):
    result = np.empty(len(features))
    for start in range(0, len(result), 200_000):
        end = min(start+200_000, len(result))
        values = features[start:end]
        if columns is not None:
            values = values[:, columns]
        value = model.predict(values, num_threads=2)
        result[start:end] = np.maximum(0, np.expm1(value) if log else value)
    return result


def run(workload):
    folder = OUTPUT / workload
    folder.mkdir(parents=True, exist_ok=False)
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 168, 200_000_000, folder / "events.bin")
    if source["stop_reason"] == "event_cap_reached":
        raise ValueError("Incomplete source prefix: event cap")
    old = PROJECT_ROOT / "results/mae-improvement" / workload
    old_holdout = json.loads((old / "holdout.json").read_text())
    assert json.loads(json.dumps(source)) == old_holdout["source"]
    dump(folder / "source.json", source)
    features, meta = prepare(events, folder)
    cutoffs = {day: int(np.searchsorted(events["timestamp"], source["first_timestamp"] + day*86400*TICKS)) for day in (4, 5, 6, 7)}
    slices = {day: slice(np.searchsorted(meta["write"], cutoffs[day-1]), np.searchsorted(meta["write"], cutoffs[day])) for day in (5, 6, 7)}
    inputs = [old / "holdout.json", old / "selection.json", folder / "source.json", folder / "features.npy", folder / "meta.npy", folder / "events.bin"]
    current_definition = json.loads((old / "selection.json").read_text())["definitions"]["current"]
    current_path = PROJECT_ROOT / current_definition["model_path"]
    inputs.append(current_path)
    current_model = lgb.Booster(model_file=str(current_path))
    current = predict_blocks(current_model, features, log=current_definition["log_target"], columns=current_definition["columns"])
    for day in (5, 6, 7):
        path = old / f"holdout-day{day}.predictions.npz"
        inputs.append(path)
        with np.load(path) as saved:
            row = np.searchsorted(meta["write"], saved["write_event_index"])
            np.testing.assert_array_equal(meta["write"][row], saved["write_event_index"])
            current[row] = saved["current"]
    states = {day: snapshot(meta[slices[day]], cutoffs[day])[0] for day in (5, 6)}
    train_meta, val_meta = meta[slices[5]], meta[slices[6]]
    train_x, val_x = features[slices[5]], features[slices[6]]
    known_train = capped(np.flatnonzero(states[5] >= 0), 2_000_000)
    known_val = capped(np.flatnonzero(states[6] >= 0), 1_000_000)
    positive_train = capped(np.flatnonzero(states[5] == 1), 1_000_000)
    positive_val = capped(np.flatnonzero(states[6] == 1), 1_000_000)
    params = dict(n_estimators=96, min_child_samples=200, learning_rate=.1, reg_lambda=1.,
                  n_jobs=2, random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)
    probabilities, predictions, recipes = {}, {"current": current[slices[6]]}, {}
    for leaves in (31, 63):
        name = f"gate_{leaves}"
        model = lgb.LGBMClassifier(**params, num_leaves=leaves)
        model.fit(np.asarray(train_x[known_train], dtype=np.float32), states[5][known_train],
                  eval_set=[(np.asarray(val_x[known_val], dtype=np.float32), states[6][known_val])],
                  callbacks=[lgb.early_stopping(12, verbose=False)])
        model.booster_.save_model(str(folder / f"validation-{name}.lightgbm.txt"))
        probabilities[name] = predict_blocks(model.booster_, val_x)
        recipes[name] = {"kind": "gate", "params": {**params, "num_leaves": leaves}, "best_iteration": model.best_iteration_}
        print(f"{workload}: fitted {name}, trees={model.best_iteration_}", flush=True)
        del model
        gc.collect()
    for log in (False, True):
        name = "time_log_l1" if log else "time_raw_l1"
        model = lgb.LGBMRegressor(**params, num_leaves=31, objective="regression_l1", metric="None")
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
        recipes[name] = {"kind": "time", "log": log, "params": {**params, "num_leaves": 31, "objective": "regression_l1", "metric": "None"}, "best_iteration": model.best_iteration_}
        print(f"{workload}: fitted {name}, trees={model.best_iteration_}", flush=True)
        del model
        gc.collect()
    combinations = {}
    for gate, probability in probabilities.items():
        for time, prediction in predictions.items():
            for threshold in THRESHOLDS:
                combinations[f"{gate}/{time}/{threshold}"] = quality(val_meta, prediction, probability, threshold,
                                                                      cutoffs[6], source["first_timestamp"] + 144*3600*TICKS)
    chosen = choose(combinations)
    np.savez(folder / "validation.predictions.npz", **probabilities, **predictions)
    selection = {"workload": workload, "chosen": chosen, "validation": combinations, "recipes": recipes,
                 "independent_holdout": False, "cutoffs": cutoffs, "sample_caps": {"gate_train": 2_000_000, "time_train": 1_000_000, "validation": 1_000_000},
                 "input_hashes": hashes(inputs), "code_hashes": hashes([Path(__file__), PROJECT_ROOT / "read_prediction/checks/all_write.py",
                     PROJECT_ROOT / "read_prediction/extended.py", PROJECT_ROOT / "read_prediction/experiments/overwrite90.py",
                     PROJECT_ROOT / "docs/protocols/all-write-protocol.md"]),
                 "validation_hashes": hashes([folder / "validation.predictions.npz", *folder.glob("validation-*.lightgbm.txt")])}
    dump(folder / "selection.json", selection)
    print(f"{workload}: froze {chosen}: {combinations[chosen]}", flush=True)
    del probabilities, predictions
    gc.collect()
    gate_name, time_name, threshold = chosen.split("/")
    combined = slice(slices[5].start, slices[6].stop)
    combined_state = snapshot(meta[combined], cutoffs[6])[0]
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
            target = meta["target"][combined][rows]
            model = lgb.LGBMRegressor(**model_params)
            model.fit(values, np.log1p(target) if recipe["log"] else target)
        path = folder / f"{role}.lightgbm.txt"
        model.booster_.save_model(str(path))
        paths.append(path)
        del model, values
        gc.collect()
    dump(folder / "frozen.json", {"selection_sha256": fingerprint(folder / "selection.json")["sha256"], "models": hashes(paths)})
    test_meta = meta[slices[7]]
    probability = predict_blocks(lgb.Booster(model_file=str(folder / "gate.lightgbm.txt")), features[slices[7]])
    prediction = current[slices[7]] if time_name == "current" else predict_blocks(
        lgb.Booster(model_file=str(folder / "time.lightgbm.txt")), features[slices[7]], recipes[time_name]["log"])
    threshold = float(threshold)
    end_timestamp = min(source["last_timestamp"], source["first_timestamp"] + 168*3600*TICKS)
    full_quality = quality(test_meta, prediction, probability, threshold, cutoffs[7], end_timestamp)
    state, observed, known_write = snapshot(test_meta, cutoffs[7])
    budget = np.where(known_write, test_meta["lifetime"], (end_timestamp - test_meta["timestamp"]) / TICKS)
    routed = np.where(probability >= threshold, prediction, current[slices[7]])
    original_metric = metrics(test_meta["target"][observed], routed[observed], budget[observed], known_write[observed])
    result = {"workload": workload, "chosen": chosen, "independent_holdout": False,
              "all_write_selective": full_quality, "original_observed_routed": original_metric,
              "original_observed_current": metrics(test_meta["target"][observed], current[slices[7]][observed], budget[observed], known_write[observed]),
              "outcomes": {"all_writes": len(state), "read_first": int((state==1).sum()), "write_first": int((state==0).sum()), "censored": int((state<0).sum()), "observed_reads": int(observed.sum())}}
    np.savez(folder / "day7.predictions.npz", probability=probability, prediction=prediction, current=current[slices[7]])
    dump(folder / "diagnostic.json", result)
    print(f"{workload}: {result}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    run(parser.parse_args().workload)
