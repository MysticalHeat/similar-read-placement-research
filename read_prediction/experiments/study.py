"""Complete the fixed-offset study: day-one selection, frozen days 2--4."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import lightgbm as lgb
import numpy as np

from read_prediction.pipeline import FEATURE_NAMES, TICKS_PER_SECOND, fit_baselines, score
from read_prediction.extended import load_duration, make_compact_samples
from read_prediction.experiments.diagnosis import predict_chunks
from read_prediction.paths import PROJECT_ROOT, source_path
from read_prediction.provenance import check_recorded_hash

OUTPUT = PROJECT_ROOT / "results/final-study"
METHODS = ["global_median", "address_median", "original", "selected"]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fingerprint(paths):
    return {str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def period_prediction(features, rows, median):
    history = features[rows][:, [4, 6]]
    known = np.isfinite(history).all(axis=1)
    prediction = np.full(len(rows), median)
    prediction[known] = np.maximum(0, np.expm1(history[known, 1]) - np.expm1(history[known, 0]))
    return prediction


def daily_mask(samples, day):
    """Half-open day; its next-read labels must finish before that day's end."""
    ts = samples["timestamps"]
    origin = int(ts[0])
    start = int(np.searchsorted(ts, origin + (day - 1) * 86400 * TICKS_PER_SECOND))
    end = int(np.searchsorted(ts, origin + day * 86400 * TICKS_PER_SECOND))
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    eligible = (writes >= start) & (writes < end)
    observed = eligible & (reads >= 0) & (reads < end)
    return eligible, observed, start, end


def select_usr():
    output = OUTPUT / "usr-selection"
    output.mkdir(parents=True, exist_ok=False)
    prior = json.loads((PROJECT_ROOT / "results/next-read-24h/usr_1.result.json").read_text())
    cutoff = prior["split_coverage"]["validation"]["end_event_exclusive"]
    train_end = prior["split_coverage"]["train"]["end_event_exclusive"]
    events, source = load_duration(PROJECT_ROOT / "dataset", "usr_1", 24, cutoff, output / "events.bin")
    assert len(events) == cutoff
    samples = make_compact_samples(events, output / "features.npy")
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    train = (writes < train_end) & (reads >= 0) & (reads < train_end)
    validation = (writes >= train_end) & (reads >= 0)
    train_rows, val_rows = np.flatnonzero(train), np.flatnonzero(validation)
    targets = samples["targets"][validation]
    if not len(targets):
        raise ValueError("No completed validation intervals for usr_1")
    median, addresses = fit_baselines(samples["offsets"][train], samples["targets"][train])
    baseline = {"global_median_seconds": median, "address_medians_seconds": addresses}
    dump(output / "baselines.json", baseline)
    predictions = {
        "global_median": np.full(len(targets), median),
        "address_median": np.fromiter((addresses.get(int(a), median) for a in samples["offsets"][validation]), dtype=float, count=len(targets)),
        "period_remaining": period_prediction(samples["features"], val_rows, median),
    }
    original_path = PROJECT_ROOT / "results/next-read-24h/usr_1.lightgbm.txt"
    original = lgb.Booster(model_file=str(original_path))
    predictions["original_log_l2"] = predict_chunks(original, samples["features"], val_rows, list(range(7)), True)
    with np.load(PROJECT_ROOT / "results/next-read-24h/usr_1.validation.predictions.npz") as previous:
        np.testing.assert_array_equal(writes[validation], previous["write_event_index"])
        np.testing.assert_array_equal(targets, previous["target_seconds"])
        np.testing.assert_allclose(predictions["original_log_l2"], previous["lightgbm"], rtol=1e-12, atol=1e-12)
    definitions = {
        "global_median": {"kind": "global_median"},
        "address_median": {"kind": "address_median"},
        "period_remaining": {"kind": "period_remaining"},
        "original_log_l2": {"kind": "model", "columns": list(range(7)), "log_target": True, "model_path": str(original_path.relative_to(PROJECT_ROOT))},
    }
    candidates = [("no_counts_log_l2", [0, 1, 4, 5, 6], "regression", True),
                  ("all_features_raw_l1", list(range(7)), "regression_l1", False),
                  ("no_counts_raw_l1", [0, 1, 4, 5, 6], "regression_l1", False)]
    for name, columns, objective, log_target in candidates:
        print(f"usr_1: fixed validation candidate {name}", flush=True)
        params = {**prior["model_params"], "objective": objective}
        model = lgb.LGBMRegressor(**params)
        training_targets = samples["targets"][train]
        model.fit(samples["features"][train_rows][:, columns], np.log1p(training_targets) if log_target else training_targets, feature_name=[FEATURE_NAMES[c] for c in columns])
        path = output / f"{name}.lightgbm.txt"
        model.booster_.save_model(str(path))
        predictions[name] = predict_chunks(model.booster_, samples["features"], val_rows, columns, log_target)
        definitions[name] = {"kind": "model", "columns": columns, "log_target": log_target,
                             "model_path": str(path.relative_to(PROJECT_ROOT)), "params": params}
    metrics = {name: score(targets, prediction) for name, prediction in predictions.items()}
    winner = min(metrics, key=lambda name: metrics[name]["mae_seconds"])
    selection = {"workload": "usr_1", "method": winner, **definitions[winner],
                 "selection_metric": "validation MAE seconds", "metrics": metrics,
                 "train_end_event_exclusive": train_end, "source": source,
                 "train_observed_targets": int(train.sum()), "validation_observed_targets": len(targets),
                 "new_fits": 3, "definitions": definitions,
                 "code_hashes": fingerprint([Path(__file__), source_path("next_read_extended.py"), source_path("next_read.py"), source_path("prxy_diagnosis.py")])}
    np.savez(output / "validation.predictions.npz", write_event_index=writes[validation], next_read_event_index=reads[validation],
             target_seconds=targets, offset_bytes=samples["offsets"][validation], **predictions)
    dump(output / "selection.json", selection)
    del samples, events
    (output / "events.bin").unlink()
    (output / "features.npy").unlink()
    print(f"usr_1 selected on validation only: {winner}, MAE {metrics[winner]['mae_seconds']:.3f}s", flush=True)


def frozen_selection(workload):
    if workload == "usr_1":
        path = OUTPUT / "usr-selection/selection.json"
        selection = json.loads(path.read_text())
        return path, {key: selection[key] for key in ("method", "kind", *(["columns", "log_target", "model_path"] if selection["kind"] == "model" else []))}
    path = PROJECT_ROOT / "results/prxy-validation-diagnosis/selected-model.json"
    selection = json.loads(path.read_text())
    return path, {"method": selection["method"], "kind": "model", "columns": selection["feature_indices_in_original_schema"],
                  "log_target": True, "model_path": str((path.parent / selection["model_file"]).relative_to(PROJECT_ROOT))}


def evaluate(workload):
    output = OUTPUT / workload
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    selection_path, selection = frozen_selection(workload)
    prior = json.loads((PROJECT_ROOT / f"results/next-read-24h/{workload}.result.json").read_text())
    original_path = PROJECT_ROOT / f"results/next-read-24h/{workload}.lightgbm.txt"
    model_paths = [original_path]
    if selection["kind"] == "model":
        model_paths.append(PROJECT_ROOT / selection["model_path"])
    frozen = {"selection": selection, "days": [2, 3, 4], "new_fits": 0,
              "hashes": fingerprint([selection_path, *model_paths, Path(__file__), source_path("next_read.py"), source_path("next_read_extended.py"), source_path("prxy_diagnosis.py")])}
    dump(output / "frozen.json", frozen)
    original = lgb.Booster(model_file=str(original_path))
    chosen = lgb.Booster(model_file=str(PROJECT_ROOT / selection["model_path"])) if selection["kind"] == "model" else None
    if chosen is not None:
        assert chosen.feature_name() == [FEATURE_NAMES[c] for c in selection["columns"]]
    events, source = load_duration(PROJECT_ROOT / "dataset", workload, 96, 130_000_000, output / "events.bin")
    if source["stop_reason"] != "duration_reached":
        raise ValueError(f"96h not reached: {source['stop_reason']}")
    print(f"{workload}: compact preparation, {len(events):,} events", flush=True)
    samples = make_compact_samples(events, output / "features.npy")
    train_end = prior["split_coverage"]["train"]["end_event_exclusive"]
    train = (samples["write_indices"] < train_end) & (samples["next_read_indices"] >= 0) & (samples["next_read_indices"] < train_end)
    assert int(train.sum()) == prior["split_coverage"]["train"]["observed_targets"]
    median, addresses = fit_baselines(samples["offsets"][train], samples["targets"][train])
    assert median == prior["baseline_global_median_seconds"]
    dump(output / "baselines.json", {"global_median_seconds": median, "address_medians_seconds": addresses})
    if workload == "prxy_1":
        previous_baselines = json.loads((PROJECT_ROOT / "results/prxy-day2/frozen-baselines.json").read_text())
        assert previous_baselines["address_medians_seconds"] == {str(k): v for k, v in addresses.items()}
    days = {}
    for day in (2, 3, 4):
        eligible, observed, start, end = daily_mask(samples, day)
        rows = np.flatnonzero(observed)
        targets, offsets = samples["targets"][observed], samples["offsets"][observed]
        predictions = {
            "global_median": np.full(len(rows), median),
            "address_median": np.fromiter((addresses.get(int(a), median) for a in offsets), dtype=float, count=len(rows)),
            "original": predict_chunks(original, samples["features"], rows, list(range(7)), True),
        }
        if chosen is not None:
            predictions["selected"] = predict_chunks(chosen, samples["features"], rows, selection["columns"], selection["log_target"])
        elif selection["kind"] == "period_remaining":
            predictions["selected"] = period_prediction(samples["features"], rows, median)
        else:
            predictions["selected"] = predictions[selection["kind"]].copy()
        metrics = {name: score(targets, prediction) for name, prediction in predictions.items()}
        ts = samples["timestamps"]
        writes, reads = samples["write_indices"][observed], samples["next_read_indices"][observed]
        np.savez(output / f"day{day}.predictions.npz", write_event_index=writes, next_read_event_index=reads, offset_bytes=offsets,
                 target_seconds=targets, write_seconds=(ts[writes] - ts[0]) / TICKS_PER_SECOND,
                 next_read_seconds=(ts[reads] - ts[0]) / TICKS_PER_SECOND, **predictions)
        total = int(eligible.sum())
        days[str(day)] = {"metrics": metrics, "coverage": {"start_event": start, "end_event_exclusive": end,
                          "writes": total, "observed_targets": len(rows), "right_censored": total - len(rows),
                          "observed_fraction": len(rows) / total if total else None}}
        if workload == "prxy_1" and day == 2:
            old = json.loads((PROJECT_ROOT / "results/prxy-day2/results.json").read_text())
            assert days[str(day)]["coverage"] == {key: old["coverage"][key] for key in days[str(day)]["coverage"]}
            for new_name, old_name in [("global_median", "global_median"), ("address_median", "address_median"), ("original", "original_all_features"), ("selected", "selected_no_counts")]:
                for key, value in metrics[new_name].items():
                    np.testing.assert_allclose(value, old["metrics"][old_name][key], rtol=1e-10, atol=1e-10)
        if len(rows):
            print(f"{workload}/day{day}: N={len(rows):,}, median MAE={metrics['address_median']['mae_seconds']:.3f}, selected MAE={metrics['selected']['mae_seconds']:.3f}", flush=True)
        else:
            print(f"{workload}/day{day}: no completed intervals; metrics unavailable", flush=True)
    for name, digest in frozen["hashes"].items():
        check_recorded_hash(name, digest)
    result = {"workload": workload, "source": source, "frozen": frozen, "days": days,
              "elapsed_seconds": time.monotonic() - started,
              "process_peak_rss_mib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
    dump(output / "results.json", result)
    del samples, events
    (output / "events.bin").unlink()
    (output / "features.npy").unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["select-usr", "evaluate"])
    parser.add_argument("--workload", choices=["usr_1", "prxy_1"])
    args = parser.parse_args()
    if args.stage == "select-usr":
        select_usr()
    elif args.workload:
        evaluate(args.workload)
    else:
        parser.error("evaluate requires --workload")


if __name__ == "__main__":
    main()
