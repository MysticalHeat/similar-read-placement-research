"""Bounded MAE search on exposed days, followed by frozen days 5--7."""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import resource
import time

import lightgbm as lgb
import numpy as np

from read_prediction.extended import load_duration, make_compact_samples
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import FEATURE_NAMES, TICKS_PER_SECOND, fit_baselines, score
from read_prediction.experiments.study import daily_mask

OUTPUT = PROJECT_ROOT / "results/mae-improvement"
EXTRA_NAMES = ["log_last_completed_write_read_seconds", "log_recent_completed_median_seconds",
               "time_of_day_sin", "time_of_day_cos"]
PROFILES = {"balanced": {"num_leaves": 31, "min_child_samples": 50},
            "regularized": {"num_leaves": 15, "min_child_samples": 200}}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fingerprints(paths):
    return {p.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def seconds_mae(y_true_log, y_pred_log):
    targets = np.expm1(y_true_log)
    predictions = np.maximum(0, np.expm1(y_pred_log))
    return "mae_seconds", float(np.abs(targets - predictions).mean()), False


def blend(model_pred, baseline_pred, weight):
    if not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Model weight must be finite and in [0, 1]")
    return weight * np.asarray(model_pred) + (1 - weight) * np.asarray(baseline_pred)


def pooled_mae(days):
    metrics = [metric for metric in days.values() if metric is not None]
    count = sum(metric["n"] for metric in metrics)
    if not count:
        raise ValueError("No completed development intervals")
    return sum(metric["n"] * metric["mae_seconds"] for metric in metrics) / count


def choose_candidate(development):
    return min(development, key=lambda name: pooled_mae(development[name]))


def causal_history_features(samples, events, path=None):
    """Statistics of labels whose reads precede the current write in row order."""
    offsets, writes = samples["offsets"], samples["write_indices"]
    shape = (len(writes), len(EXTRA_NAMES))
    extra = (np.empty(shape) if path is None else
             np.lib.format.open_memmap(path, mode="w+", dtype=np.float64, shape=shape))
    extra[:, :2] = np.nan
    period = 86400 * TICKS_PER_SECOND
    for start in range(0, len(writes), 250_000):
        end = min(start + 250_000, len(writes))
        phase = 2 * np.pi * (events["timestamp"][writes[start:end]] % period) / period
        extra[start:end, 2] = np.sin(phase)
        extra[start:end, 3] = np.cos(phase)
    order = np.argsort(offsets, kind="stable")
    grouped_offsets = offsets[order]
    boundaries = np.r_[0, np.flatnonzero(np.diff(grouped_offsets)) + 1, len(order)]
    del grouped_offsets
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        rows = order[start:end]
        reads = samples["next_read_indices"][rows].copy()
        reads[reads < 0] = np.iinfo(np.int64).max
        position = np.searchsorted(reads, writes[rows], side="left") - 1
        known = position >= 0
        if not known.any():
            continue
        targets = samples["targets"][rows]
        last = position[known]
        extra[rows[known], 0] = np.log1p(targets[last])
        history = np.full((5, len(last)), np.nan)
        for lag in range(5):
            valid = last >= lag
            history[lag, valid] = targets[last[valid] - lag]
        extra[rows[known], 1] = np.log1p(np.nanmedian(history, axis=0))
    if isinstance(extra, np.memmap):
        extra.flush()
    return extra


def feature_matrix(samples, rows, columns):
    values = np.empty((len(rows), len(columns)))
    for index, column in enumerate(columns):
        if column < len(FEATURE_NAMES):
            values[:, index] = samples["features"][rows, column]
        else:
            values[:, index] = samples["extra"][rows, column - len(FEATURE_NAMES)]
    return values


def predict(model, samples, rows, columns):
    predictions = np.empty(len(rows))
    for start in range(0, len(rows), 250_000):
        end = min(start + 250_000, len(rows))
        values = feature_matrix(samples, rows[start:end], columns)
        predictions[start:end] = np.maximum(0, np.expm1(model.predict(values, num_threads=2)))
    return predictions


def prediction_rows(samples, events, rows):
    writes, reads = samples["write_indices"][rows], samples["next_read_indices"][rows]
    origin = int(events["timestamp"][0])
    return {"write_event_index": writes, "next_read_event_index": reads,
            "offset_bytes": samples["offsets"][rows], "target_seconds": samples["targets"][rows],
            "write_seconds": (events["timestamp"][writes] - origin) / TICKS_PER_SECOND,
            "next_read_seconds": (events["timestamp"][reads] - origin) / TICKS_PER_SECOND}


def coverage(samples, day):
    eligible, observed, start, end = daily_mask(samples, day)
    total, known = int(eligible.sum()), int(observed.sum())
    return np.flatnonzero(observed), {"start_event": start, "end_event_exclusive": end,
                                    "writes": total, "observed_targets": known,
                                    "right_censored": total - known,
                                    "observed_fraction": known / total if total else None}


def address_predictions(offsets, baselines):
    addresses, median = baselines["address_medians_seconds"], baselines["global_median_seconds"]
    return np.fromiter((addresses.get(str(int(a)), median) for a in offsets), float, len(offsets))


def add_blends(definitions, names):
    for name in names:
        definition = definitions[name]
        for weight in (.25, .5, .75):
            definitions[f"{name}_blend_{int(weight * 100)}"] = {
                **definition, "kind": "blend", "model_method": name, "model_weight": weight,
            }


def fit_candidates(samples, train_rows, val_rows, output, definitions, validation, history=False, profile=None):
    added = []
    profiles = PROFILES if profile is None else {profile: PROFILES[profile]}
    for objective in ("regression", "regression_l1"):
        loss = "log_l2" if objective == "regression" else "log_l1"
        for feature_set, base_columns in (("all", list(range(7))), ("no_counts", [0, 1, 4, 5, 6])):
            columns = base_columns + (list(range(7, 11)) if history else [])
            train_x, val_x = feature_matrix(samples, train_rows, columns), feature_matrix(samples, val_rows, columns)
            train_y, val_y = np.log1p(samples["targets"][train_rows]), np.log1p(samples["targets"][val_rows])
            for profile_name, settings in profiles.items():
                name = f"{loss}_{feature_set}_{profile_name}" + ("_history" if history else "")
                params = {"objective": objective, "metric": "None", "n_estimators": 1000,
                          "learning_rate": .05, "reg_lambda": 1., "random_state": 42,
                          "n_jobs": 2, "deterministic": True, "force_col_wise": True,
                          "verbosity": -1, **settings}
                print(f"Fitting {name}: train={len(train_rows):,}, validation={len(val_rows):,}", flush=True)
                started = time.monotonic()
                model = lgb.LGBMRegressor(**params)
                names = FEATURE_NAMES + EXTRA_NAMES
                model.fit(train_x, train_y, feature_name=[names[c] for c in columns],
                          eval_set=[(val_x, val_y)], eval_metric=seconds_mae,
                          callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)])
                model_path = output / f"{name}.lightgbm.txt"
                model.booster_.save_model(str(model_path), num_iteration=model.best_iteration_)
                loaded = lgb.Booster(model_file=str(model_path))
                expected = model.predict(val_x[:256], num_iteration=model.best_iteration_)
                np.testing.assert_allclose(loaded.predict(val_x[:256], num_threads=2), expected, rtol=1e-12, atol=1e-12)
                val_prediction = np.maximum(0, np.expm1(loaded.predict(val_x, num_threads=2)))
                validation[name] = score(samples["targets"][val_rows], val_prediction)
                definitions[name] = {"kind": "model", "model_path": model_path.relative_to(PROJECT_ROOT).as_posix(),
                                     "columns": columns, "log_target": True, "params": params,
                                     "profile": profile_name, "history_features": history,
                                     "best_iteration": model.best_iteration_, "fit_seconds": time.monotonic() - started}
                print(f"  best_iteration={model.best_iteration_}, validation MAE={validation[name]['mae_seconds']:.4f}s", flush=True)
                added.append(name)
                del model, loaded
            del train_x, val_x, train_y, val_y
            gc.collect()
    add_blends(definitions, added)
    return added


def evaluate_development(samples, events, output, definitions, baselines, workload):
    development = {name: {} for name in definitions}
    coverages = {}
    for day in (2, 3, 4):
        rows, coverages[str(day)] = coverage(samples, day)
        path = output / f"day{day}.predictions.npz"
        data = prediction_rows(samples, events, rows)
        if path.exists():
            with np.load(path) as previous:
                for name in definitions:
                    if name in previous.files:
                        data[name] = previous[name]
        data["address_median"] = address_predictions(data["offset_bytes"], baselines)
        for name, definition in definitions.items():
            if name in data:
                continue
            if definition["kind"] == "model":
                model = lgb.Booster(model_file=str(PROJECT_ROOT / definition["model_path"]))
                data[name] = predict(model, samples, rows, definition["columns"])
                del model
            elif definition["kind"] == "blend":
                data[name] = blend(data[definition["model_method"]], data["address_median"], definition["model_weight"])
        with np.load(PROJECT_ROOT / f"results/final-study/{workload}/day{day}.predictions.npz") as previous:
            np.testing.assert_array_equal(data["write_event_index"], previous["write_event_index"])
            np.testing.assert_array_equal(data["target_seconds"], previous["target_seconds"])
            np.testing.assert_allclose(data["current"], previous["selected"], rtol=1e-12, atol=1e-12)
            np.testing.assert_array_equal(data["address_median"], previous["address_median"])
        for name in definitions:
            development[name][str(day)] = score(data["target_seconds"], data[name])
        np.savez(path, **data)
        winner = min(definitions, key=lambda name: development[name][str(day)]["mae_seconds"])
        print(f"{workload} development day {day}: best {winner}, MAE={development[winner][str(day)]['mae_seconds']:.4f}s", flush=True)
        del data
        gc.collect()
    return development, coverages


def save_validation(samples, events, rows, output, definitions, baselines):
    data = prediction_rows(samples, events, rows)
    data["address_median"] = address_predictions(data["offset_bytes"], baselines)
    metrics = {}
    for name, definition in definitions.items():
        if definition["kind"] == "model":
            model = lgb.Booster(model_file=str(PROJECT_ROOT / definition["model_path"]))
            data[name] = predict(model, samples, rows, definition["columns"])
            del model
        elif definition["kind"] == "blend":
            data[name] = blend(data[definition["model_method"]], data["address_median"], definition["model_weight"])
        metrics[name] = score(data["target_seconds"], data[name])
    np.savez(output / "validation.predictions.npz", **data)
    return metrics


def select(workload):
    output = OUTPUT / workload
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 96, 130_000_000, output / "events.bin")
    if source["stop_reason"] != "duration_reached":
        raise ValueError("Full development prefix not reached")
    prior = json.loads((PROJECT_ROOT / f"results/next-read-24h/{workload}.result.json").read_text())
    historical = json.loads((PROJECT_ROOT / f"results/final-study/{workload}/results.json").read_text())
    assert source["prefix_sha256"] == historical["source"]["prefix_sha256"]
    samples = make_compact_samples(events, output / "features.npy")
    train_end = prior["split_coverage"]["train"]["end_event_exclusive"]
    val_end = prior["split_coverage"]["validation"]["end_event_exclusive"]
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    train = (writes < train_end) & (reads >= 0) & (reads < train_end)
    validation_mask = (writes >= train_end) & (writes < val_end) & (reads >= 0) & (reads < val_end)
    train_rows, val_rows = np.flatnonzero(train), np.flatnonzero(validation_mask)
    assert len(train_rows) == prior["split_coverage"]["train"]["observed_targets"]
    assert len(val_rows) == prior["split_coverage"]["validation"]["observed_targets"]
    median, addresses = fit_baselines(samples["offsets"][train], samples["targets"][train])
    baselines = {"global_median_seconds": median, "address_medians_seconds": {str(k): v for k, v in addresses.items()}}
    dump(output / "baselines.json", baselines)
    current = json.loads((PROJECT_ROOT / f"results/final-study/{workload}/frozen.json").read_text())["selection"]
    definitions = {"current": {**current, "kind": "model"},
                   "address_median": {"kind": "address_median", "model_path": None, "columns": []}}
    add_blends(definitions, ["current"])
    validation = {}
    fit_candidates(samples, train_rows, val_rows, output, definitions, validation)
    development, coverages = evaluate_development(samples, events, output, definitions, baselines, workload)
    round_one = {name: pooled_mae(days) for name, days in development.items()}
    reference = min(round_one["current"], round_one["address_median"])
    history_round = min(round_one.values()) > reference * .95
    if history_round:
        best_model = min((name for name, d in definitions.items() if d["kind"] == "model" and name != "current"),
                         key=lambda name: round_one[name])
        profile = definitions[best_model]["profile"]
        print(f"{workload}: first round improvement <5%; add causal completed-label history ({profile})", flush=True)
        samples["extra"] = causal_history_features(samples, events, output / "extra.npy")
        fit_candidates(samples, train_rows, val_rows, output, definitions, validation, history=True, profile=profile)
        development, coverages = evaluate_development(samples, events, output, definitions, baselines, workload)
    validation = save_validation(samples, events, val_rows, output, definitions, baselines)
    winner = choose_candidate(development)
    pooled = {name: pooled_mae(days) for name, days in development.items()}
    selection = {"workload": workload, "selected_method": winner, "definitions": definitions,
                 "selection_metric": "pooled development MAE seconds, exposed days 2--4",
                 "development": development, "development_coverage": coverages,
                 "pooled_development_mae": pooled, "validation": validation,
                 "round_one_pooled_mae": round_one, "history_round_triggered": history_round,
                 "train_end_event_exclusive": train_end, "validation_end_event_exclusive": val_end,
                 "train_observed_targets": len(train_rows), "validation_observed_targets": len(val_rows),
                 "source": source, "new_fits": 12 if history_round else 8,
                 "elapsed_seconds": time.monotonic() - started,
                 "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
    dump(output / "selection.json", selection)
    paths = [output / "selection.json", output / "baselines.json", Path(__file__),
             PROJECT_ROOT / "read_prediction/extended.py", PROJECT_ROOT / "read_prediction/pipeline.py",
             PROJECT_ROOT / "read_prediction/checks/mae_improvement.py",
             PROJECT_ROOT / "docs/protocols/mae-improvement-protocol.md"]
    paths.extend(PROJECT_ROOT / d["model_path"] for d in definitions.values() if d.get("model_path"))
    dump(output / "frozen.json", {"selection": {**definitions[winner], "method": winner},
                                  "selection_path": (output / "selection.json").relative_to(PROJECT_ROOT).as_posix(),
                                  "hashes": fingerprints(paths), "development_days": [2, 3, 4],
                                  "test_days": [5, 6, 7], "new_fits": 0})
    print(f"FROZEN {workload}: {winner}, pooled development MAE={pooled[winner]:.4f}s; current={pooled['current']:.4f}s", flush=True)
    del samples, events
    gc.collect()
    for name in ("events.bin", "features.npy", "extra.npy"):
        (output / name).unlink(missing_ok=True)


def evaluate(workload):
    for other in ("usr_1", "prxy_1"):
        if not (OUTPUT / other / "frozen.json").exists():
            raise ValueError("Freeze both workloads before opening any holdout")
    output = OUTPUT / workload
    if (output / "holdout.json").exists():
        raise ValueError("Holdout already evaluated")
    frozen = json.loads((output / "frozen.json").read_text())
    from read_prediction.checks.mae_improvement import verify_hashes
    verify_hashes(PROJECT_ROOT, frozen["hashes"])
    selection = json.loads((output / "selection.json").read_text())
    definitions = selection["definitions"]
    chosen = definitions[selection["selected_method"]]
    baselines = json.loads((output / "baselines.json").read_text())
    started = time.monotonic()
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 168, 200_000_000, output / "events.bin")
    if source["stop_reason"] == "event_cap_reached":
        raise ValueError("Event cap reached, not an acceptable partial holdout")
    last_seconds = (source["last_timestamp"] - source["first_timestamp"]) / TICKS_PER_SECOND
    if last_seconds <= 144 * 3600:
        raise ValueError("Need data after 144h for holdout day 7")
    samples = make_compact_samples(events, output / "features.npy")
    if any(c >= 7 for c in chosen["columns"]):
        samples["extra"] = causal_history_features(samples, events, output / "extra.npy")
    current_definition = definitions["current"]
    current = lgb.Booster(model_file=str(PROJECT_ROOT / current_definition["model_path"]))
    selected_model = None if chosen["kind"] == "address_median" else lgb.Booster(model_file=str(PROJECT_ROOT / chosen["model_path"]))
    days = {}
    for day in (5, 6, 7):
        rows, cov = coverage(samples, day)
        data = prediction_rows(samples, events, rows)
        data["address_median"] = address_predictions(data["offset_bytes"], baselines)
        data["current"] = predict(current, samples, rows, current_definition["columns"])
        if selected_model is None:
            data["selected"] = data["address_median"].copy()
        else:
            model_prediction = predict(selected_model, samples, rows, chosen["columns"])
            if chosen["kind"] == "blend":
                data["selected_model_prediction"] = model_prediction
                data["selected"] = blend(model_prediction, data["address_median"], chosen["model_weight"])
            else:
                data["selected"] = model_prediction
        metrics = {name: score(data["target_seconds"], data[name]) for name in ("current", "address_median", "selected")}
        np.savez(output / f"holdout-day{day}.predictions.npz", **data)
        end_seconds = day * 86400 if source["stop_reason"] == "duration_reached" else min(day * 86400, last_seconds)
        days[str(day)] = {"metrics": metrics, "coverage": cov, "end_seconds": end_seconds,
                          "partial_day": end_seconds < day * 86400, "evaluation_role": "new_future_period"}
        errors = {name: f"{metric['mae_seconds']:.4f}s" if metric else "n/a" for name, metric in metrics.items()}
        print(f"HOLDOUT {workload} day {day}: current={errors['current']}, selected={errors['selected']}, N={len(rows):,}", flush=True)
        del data
        gc.collect()
    dump(output / "holdout.json", {"source": source, "days": days, "new_fits": 0,
                                  "elapsed_seconds": time.monotonic() - started,
                                  "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
    del samples, events
    gc.collect()
    for name in ("events.bin", "features.npy", "extra.npy"):
        (output / name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("select", "evaluate"))
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    args = parser.parse_args()
    (select if args.stage == "select" else evaluate)(args.workload)


if __name__ == "__main__":
    main()
