"""Standalone latest-model training helpers embedded in submission/training.ipynb."""

from array import array
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory

import lightgbm as lgb
import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.notebook_training import prepare_samples
from read_prediction.experiments.prxy0_check import local_labels
from read_prediction.pipeline import fit_baselines
from read_prediction.range_label import TICKS, require_grid
from read_prediction.submission_models import RAW_FEATURES

TRACE_SOURCES = {"prn_1": ("msr-cambridge1.tar", "MSR-Cambridge/prn_1.csv.gz"),
                 "proj_1": ("msr-cambridge1.tar", "MSR-Cambridge/proj_1.csv.gz")}
PARAMETERS = {"n_estimators": 150, "learning_rate": .05, "num_leaves": 31,
              "min_child_samples": 50, "reg_lambda": 1., "random_state": 42,
              "n_jobs": 2, "deterministic": True, "force_col_wise": True, "verbosity": -1}
MIX_WEIGHTS = {"mix_log75": .75, "mix_log50": .5, "mix_log25": .25}


def load_four_days(dataset_directory, workload, cache_path, max_events=100_000_000):
    archive_name, member_name = TRACE_SOURCES[workload]
    buffer = array("q")
    if buffer.itemsize != 8 or not np.little_endian:
        raise RuntimeError("The event cache requires little-endian 64-bit integers")
    count, origin, previous, volume = 0, None, None, None
    reached_boundary = False
    with tarfile.open(Path(dataset_directory) / archive_name) as archive, cache_path.open("wb") as cache:
        member = archive.extractfile(member_name)
        if member is None:
            raise ValueError(f"Missing trace: {member_name}")
        with member, gzip.GzipFile(fileobj=member) as trace:
            for line in trace:
                fields = line.strip().split(b",")
                if len(fields) != 7:
                    raise ValueError(f"Invalid row: {count + 1}")
                timestamp, host, disk, operation, offset, size, response = fields
                timestamp, offset, size = int(timestamp), int(offset), int(size)
                current_volume = (host.decode("ascii"), int(disk))
                if origin is None:
                    origin, volume = timestamp, current_volume
                if previous is not None and timestamp < previous:
                    raise ValueError("Timestamps must be chronological")
                if current_volume != volume:
                    raise ValueError("Multiple logical volumes")
                if timestamp >= origin + 4 * 86400 * TICKS:
                    reached_boundary = True
                    break
                if count >= max_events:
                    raise ValueError("Event cap reached before four-day boundary")
                if operation not in (b"Read", b"Write") or offset < 0 or size <= 0 or int(response) < 0:
                    raise ValueError("Invalid I/O event")
                buffer.extend((timestamp, offset, size, int(operation == b"Read")))
                count += 1
                previous = timestamp
                if count % 250_000 == 0:
                    buffer.tofile(cache)
                    buffer = array("q")
                if count % 2_000_000 == 0:
                    print(workload, f"{count:,} events", flush=True)
            buffer.tofile(cache)
    if not reached_boundary or not count:
        raise ValueError("Trace does not establish the full four-day observation window")
    return np.memmap(cache_path, mode="r", dtype=EVENT_DTYPE, shape=(count,))


def validation_metrics(events, rows, labels, prediction, boundary):
    seen = labels["read"] >= 0
    if not seen.any():
        raise ValueError("No observed validation Read targets")
    known = labels["overwrite"][seen] >= 0
    error = np.abs(labels["target"][seen] - prediction[seen])
    remaining = (boundary - events["timestamp"][rows[seen]]) / TICKS
    lower_intervals = np.where(known, labels["lifetime"][seen], remaining)
    passed = error < lower_intervals
    uncertain = ~known & ~passed
    mae, lower = float(error.mean()), float(lower_intervals.mean())
    if mae < lower:
        mean_status = "passed"
    elif known.all():
        mean_status = "failed"
    else:
        mean_status = "undetermined"
    return {"n": int(seen.sum()), "all_writes": len(rows), "mae_seconds": mae,
            "mean_overwrite_lower_seconds": lower, "mean_status": mean_status,
            "pass_lower": float(passed.mean()), "pass_upper": float((passed | uncertain).mean())}


def train_events(events, workload, directory, parameters, weights):
    require_grid(events["offset"], events["size"])
    origin = int(events["timestamp"][0])
    train_end, valid_end = map(int, np.searchsorted(events["timestamp"],
                                                   [origin + 3 * 86400 * TICKS, origin + 4 * 86400 * TICKS]))
    if not 0 < train_end < valid_end:
        raise ValueError("Train days 1–3 and validation day 4 must be nonempty")
    with TemporaryDirectory() as temporary:
        samples = prepare_samples(events[:valid_end], Path(temporary) / "features.npy")
        writes, features = samples["write_indices"], samples["features"]
        results = {}
        for rule in ("same_start", "range"):
            train_rows, train = local_labels(events, 0, train_end, rule)
            rows, valid = local_labels(events, train_end, valid_end, rule)
            seen = train["read"] >= 0
            if not seen.any():
                raise ValueError(f"No training Read targets: {workload}/{rule}")
            train_x = features[np.searchsorted(writes, train_rows[seen])]
            validation_x = features[np.searchsorted(writes, rows)]
            predictions, model_files = {}, {}
            for method in ("log_l2", "raw_l1"):
                objective = "regression" if method == "log_l2" else "regression_l1"
                target = np.log1p(train["target"][seen]) if method == "log_l2" else train["target"][seen]
                model = lgb.LGBMRegressor(objective=objective, **parameters)
                model.fit(train_x, target)
                name = f"{workload}.{rule}.{method}.lightgbm.txt"
                model.booster_.save_model(str(directory / name))
                model_files[method] = name
                values = model.booster_.predict(validation_x, num_threads=2)
                predictions[method] = np.maximum(0, np.expm1(values) if method == "log_l2" else values)
            median, addresses = fit_baselines(events["offset"][train_rows[seen]], train["target"][seen])
            address_file = f"{workload}.{rule}.address_medians.json"
            (directory / address_file).write_text(json.dumps({str(key): value for key, value in addresses.items()}, indent=2) + "\n")
            predictions["address_median"] = np.asarray([addresses.get(int(offset), median) for offset in events["offset"][rows]])
            if workload == "prn_1":
                predictions.update({name: weight * predictions["log_l2"] + (1 - weight) * predictions["raw_l1"]
                                    for name, weight in weights.items()})
            metrics = {name: validation_metrics(events, rows, valid, prediction, origin + 4 * 86400 * TICKS)
                       for name, prediction in predictions.items()}
            selected = min(metrics, key=lambda name: (metrics[name]["mae_seconds"], name))
            results[rule] = {"selected": selected, "training_samples": int(seen.sum()),
                             "validation": metrics, "models": model_files,
                             "address_medians": address_file, "global_median_seconds": median}
        del samples, features
    return results


def train_latest(workload, dataset_directory, output_directory, parameters, weights):
    with TemporaryDirectory() as temporary:
        events = load_four_days(dataset_directory, workload, Path(temporary) / "events.bin")
        result = train_events(events, workload, output_directory, parameters, weights)
        del events
    return result


def export_predictors(training_results, directory, weights, inference_source, training_mode):
    metadata = {"raw_feature_order": RAW_FEATURES, "input_transform": "log1p for LightGBM; raw offset for address median",
                "missing_history": "NaN", "output": "seconds from Write to first subsequent Read",
                "history_key": "same starting Offset for both labeling rules; before current Write",
                "train_window": "days 1–3", "selection_window": "day 4 observed-Read MAE",
                "training_mode": training_mode, "evaluation_role": "validation only; no future-day evaluation",
                "predictors": {}, "files": {}}
    for workload, rules in training_results.items():
        metadata["predictors"][workload] = {}
        for rule, result in rules.items():
            method = result["selected"]
            recipe = {"method": method}
            if method == "address_median":
                recipe.update(address_medians=result["address_medians"], global_median_seconds=result["global_median_seconds"])
                names = [result["address_medians"]]
            elif method in weights:
                recipe.update(models=result["models"], weight_log_l2=weights[method])
                names = list(result["models"].values())
            else:
                recipe["models"] = {method: result["models"][method]}
                names = list(recipe["models"].values())
            metadata["predictors"][workload][rule] = recipe
            for name in names:
                path = directory / name
                metadata["files"][name] = {"size_bytes": path.stat().st_size,
                                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (directory / "predict.py").write_text(inference_source)
    path = directory / "predict.py"
    metadata["files"]["predict.py"] = {"size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (directory / "models.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (directory / "training-results.json").write_text(json.dumps(training_results, indent=2) + "\n")
    return metadata


def smoke_events():
    """Small artificial four-day trace for checking the notebook, not evidence."""
    rows = []
    for day in range(4):
        for index in range(64):
            timestamp = (day * 86400 + index * 1200) * TICKS
            offset = (index % 8) * 512
            read_offset = offset + 512 if index % 3 == 0 else offset
            rows.extend([(timestamp, offset, 1024, 0),
                         (timestamp + (10 + index % 5) * TICKS, read_offset, 512, 1),
                         (timestamp + 30 * TICKS, offset, 512, 0)])
    return np.asarray(rows, dtype=EVENT_DTYPE)
