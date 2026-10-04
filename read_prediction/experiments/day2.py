"""Frozen-model evaluation on prxy_1 hours [24,48), without fitting models."""

import hashlib
import json
import resource
import time

import lightgbm as lgb
import numpy as np

from read_prediction.pipeline import TICKS_PER_SECOND, fit_baselines, score
from read_prediction.extended import load_duration, make_compact_samples
from read_prediction.experiments.diagnosis import predict_chunks
from read_prediction.paths import PROJECT_ROOT, source_path


def window_masks(samples, train_end):
    timestamps = samples["timestamps"]
    origin = int(timestamps[0])
    start = int(np.searchsorted(timestamps, origin + 24 * 3600 * TICKS_PER_SECOND))
    end = int(np.searchsorted(timestamps, origin + 48 * 3600 * TICKS_PER_SECOND))
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    train = (writes < train_end) & (reads >= 0) & (reads < train_end)
    eligible = (writes >= start) & (writes < end)
    observed = eligible & (reads >= 0) & (reads < end)
    return train, eligible, observed, start, end


def main():
    output = PROJECT_ROOT / "results/prxy-day2"
    if output.exists():
        raise ValueError("Output exists; preserve previous evaluation")
    output.mkdir()
    started = time.monotonic()
    selection_path = PROJECT_ROOT / "results/prxy-validation-diagnosis/selected-model.json"
    selection = json.loads(selection_path.read_text())
    original_result = json.loads((PROJECT_ROOT / "results/next-read-24h/prxy_1.result.json").read_text())
    model_paths = {
        "selected_no_counts": PROJECT_ROOT / "results/prxy-validation-diagnosis" / selection["model_file"],
        "original_all_features": PROJECT_ROOT / "results/next-read-24h/prxy_1.lightgbm.txt",
    }
    frozen = {
        "window_hours_half_open": [24, 48], "primary_metric": "MAE seconds",
        "selected_method": selection["method"], "feature_indices": selection["feature_indices_in_original_schema"],
        "train_end_event_exclusive": original_result["split_coverage"]["train"]["end_event_exclusive"],
        "model_hashes": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in model_paths.items()},
        "selection_hash": hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        "fits_permitted": 0,
    }
    # Persist the choice before any new-window labels are computed.
    (output / "frozen-models.json").write_text(json.dumps(frozen, indent=2) + "\n")
    models = {name: lgb.Booster(model_file=str(path)) for name, path in model_paths.items()}
    assert models["selected_no_counts"].feature_name() == selection["feature_names"]
    events, source = load_duration(PROJECT_ROOT / "dataset", "prxy_1", 48, 70_000_000, output / "events.bin")
    if source["stop_reason"] != "duration_reached":
        raise ValueError(f"Full 48h prefix unavailable: {source['stop_reason']}")
    print(f"Building samples for {len(events):,} events", flush=True)
    samples = make_compact_samples(events, output / "features.npy")
    train, eligible, observed, start, end = window_masks(samples, frozen["train_end_event_exclusive"])
    assert int(train.sum()) == original_result["split_coverage"]["train"]["observed_targets"]
    median, addresses = fit_baselines(samples["offsets"][train], samples["targets"][train])
    assert median == original_result["baseline_global_median_seconds"]
    (output / "frozen-baselines.json").write_text(json.dumps({"global_median_seconds": median, "address_medians_seconds": addresses}, sort_keys=True) + "\n")
    rows = np.flatnonzero(observed)
    if not len(rows):
        raise ValueError("No observed day-two intervals")
    offsets, targets = samples["offsets"][observed], samples["targets"][observed]
    predictions = {
        "global_median": np.full(len(rows), median),
        "address_median": np.fromiter((addresses.get(int(a), median) for a in offsets), dtype=float, count=len(rows)),
        "original_all_features": predict_chunks(models["original_all_features"], samples["features"], rows, list(range(7)), True),
        "selected_no_counts": predict_chunks(models["selected_no_counts"], samples["features"], rows, frozen["feature_indices"], True),
    }
    timestamps = samples["timestamps"]
    writes, reads = samples["write_indices"][observed], samples["next_read_indices"][observed]
    np.savez(output / "predictions.npz", write_event_index=writes, next_read_event_index=reads,
             offset_bytes=offsets, target_seconds=targets,
             write_seconds=(timestamps[writes] - timestamps[0]) / TICKS_PER_SECOND,
             next_read_seconds=(timestamps[reads] - timestamps[0]) / TICKS_PER_SECOND, **predictions)
    metrics = {name: score(targets, pred) for name, pred in predictions.items()}
    origin = int(timestamps[0])
    hourly = {}
    write_seconds = (timestamps[writes] - origin) / TICKS_PER_SECOND
    for hour in range(24, 48):
        mask = (write_seconds >= hour * 3600) & (write_seconds < (hour + 1) * 3600)
        hourly[str(hour)] = {name: score(targets[mask], pred[mask]) for name, pred in predictions.items()}
    for name, path in model_paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == frozen["model_hashes"][name]
    result = {
        "window_hours": [24, 48], "workload": "prxy_1", "fits": 0,
        "source": source, "frozen": frozen, "metrics": metrics, "hourly_metrics": hourly,
        "coverage": {"start_event": start, "end_event_exclusive": end,
                     "writes": int(eligible.sum()), "observed_targets": len(rows),
                     "right_censored": int(eligible.sum()) - len(rows),
                     "observed_fraction": len(rows) / int(eligible.sum()),
                     "known_address_baseline_samples": sum(int(a) in addresses for a in offsets)},
        "code_sha256": {str(source_path(name).relative_to(PROJECT_ROOT)): hashlib.sha256(source_path(name).read_bytes()).hexdigest()
                        for name in ("prxy_day2.py", "next_read.py", "next_read_extended.py", "prxy_diagnosis.py")},
        "elapsed_seconds": time.monotonic() - started,
        "process_peak_rss_mib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    del samples, timestamps, events
    (output / "events.bin").unlink()
    (output / "features.npy").unlink()
    print(json.dumps(metrics, indent=2), flush=True)
    print("Frozen day-two evaluation complete; zero fits.", flush=True)


if __name__ == "__main__":
    main()
