"""Fixed 24-hour follow-up, with compact disk-backed events and features."""

import argparse
import gzip
import hashlib
import json
import platform
import resource
import tarfile
import time
from array import array
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.pipeline import (
    FEATURE_NAMES, TICKS_PER_SECOND, TRACE_SOURCES,
    fit_baselines, save_report, score, split_masks,
)
from read_prediction.paths import PROJECT_ROOT, source_path

EVENT_DTYPE = np.dtype([
    ("timestamp", "<i8"), ("offset", "<i8"),
    ("size", "<i8"), ("is_read", "<i8"),
])


def load_duration(dataset, workload, hours, max_events, cache):
    """Stream a half-open time window to disk; never retain Python event objects."""
    archive, member = TRACE_SOURCES[workload]
    origin = previous = volume = None
    count = reads = 0
    digest = hashlib.sha256()
    buffer = array("q")
    if buffer.itemsize != 8 or np.little_endian is False:
        raise RuntimeError("Compact writer currently requires a little-endian 64-bit array('q')")
    stop_reason, boundary_timestamp = "end_of_trace", None
    with tarfile.open(dataset / archive) as tar, cache.open("wb") as output:
        raw = tar.extractfile(member)
        if raw is None:
            raise ValueError(f"Not a regular file: {member}")
        with raw, gzip.GzipFile(fileobj=raw) as stream:
            for line in stream:
                fields = line.strip().split(b",")
                if len(fields) != 7:
                    raise ValueError(f"Row {count + 1}: expected seven columns")
                ts, host, disk, kind, offset, size, response = fields
                timestamp, offset, size = int(ts), int(offset), int(size)
                if origin is None:
                    origin = timestamp
                    volume = (host.decode("ascii"), int(disk))
                if previous is not None and timestamp < previous:
                    raise ValueError("Nonchronological source")
                if (host.decode("ascii"), int(disk)) != volume:
                    raise ValueError("Multiple logical volumes")
                if timestamp >= origin + round(hours * 3600 * TICKS_PER_SECOND):
                    stop_reason, boundary_timestamp = "duration_reached", timestamp
                    break
                if count >= max_events:
                    stop_reason, boundary_timestamp = "event_cap_reached", timestamp
                    break
                if kind not in (b"Read", b"Write") or offset < 0 or size <= 0 or int(response) < 0:
                    raise ValueError(f"Invalid source row {count + 1}")
                is_read = int(kind == b"Read")
                buffer.extend((timestamp, offset, size, is_read))
                digest.update(line)
                count += 1
                reads += is_read
                previous = timestamp
                if count % 250_000 == 0:
                    buffer.tofile(output)
                    buffer = array("q")
                if count % 2_000_000 == 0:
                    print(f"  {workload}: {count:,} events, {(timestamp - origin) / TICKS_PER_SECOND / 3600:.2f} h", flush=True)
            buffer.tofile(output)
    if count < 200:
        raise ValueError("Too few events")
    events = np.memmap(cache, mode="r", dtype=EVENT_DTYPE, shape=(count,))
    return events, {
        "archive": str(dataset / archive), "member": member, "volume": volume,
        "prefix_sha256": digest.hexdigest(), "loaded_events": count,
        "requested_hours": hours, "max_events": max_events, "stop_reason": stop_reason,
        "first_timestamp": origin, "last_timestamp": previous,
        "first_excluded_timestamp": boundary_timestamp,
        "counts": {"Read": reads, "Write": count - reads},
    }


def make_compact_samples(events, features_path=None, block_size=250_000):
    """Group by offset stably; recover causal history and next reads vectorially.

    Sorting is only a preparation shortcut: each group's order is still source
    row order, and samples are scattered back into chronological write order.
    """
    order = np.argsort(events["offset"], kind="stable")
    sorted_is_read = events["is_read"][order].astype(bool)
    read_positions = np.flatnonzero(sorted_is_read)
    write_positions = np.flatnonzero(~sorted_is_read)
    read_events = order[read_positions]
    write_events = order[write_positions]
    del order, sorted_is_read
    read_offsets = events["offset"][read_events]
    write_offsets = events["offset"][write_events]
    chronological_writes = np.flatnonzero(events["is_read"] == 0)
    n_writes = len(chronological_writes)
    shape = (n_writes, len(FEATURE_NAMES))
    features = (np.empty(shape, dtype=np.float64) if features_path is None else
                np.lib.format.open_memmap(features_path, mode="w+", dtype=np.float64, shape=shape))
    next_reads = np.full(n_writes, -1, dtype=np.int64)
    targets = np.full(n_writes, np.nan)

    for start in range(0, n_writes, block_size):
        end = min(start + block_size, n_writes)
        writes = write_events[start:end]
        offsets = write_offsets[start:end]
        timestamps = events["timestamp"][writes]
        rows = np.searchsorted(chronological_writes, writes)
        read_slot = np.searchsorted(read_positions, write_positions[start:end], side="right")
        prior_reads = read_slot - np.searchsorted(read_offsets, offsets, side="left")
        prior_writes = np.arange(start, end) - np.searchsorted(write_offsets, offsets, side="left")
        values = np.full((end - start, len(FEATURE_NAMES)), np.nan)
        values[:, 0] = offsets
        values[:, 1] = events["size"][writes]
        values[:, 2] = prior_reads
        values[:, 3] = prior_writes
        previous_writes = write_events[np.maximum(np.arange(start, end) - 1, 0)]
        known_write = prior_writes > 0
        values[known_write, 5] = (timestamps[known_write] - events["timestamp"][previous_writes[known_write]]) / TICKS_PER_SECOND
        if len(read_events):
            previous_reads = read_events[np.clip(read_slot - 1, 0, len(read_events) - 1)]
            previous_two = read_events[np.clip(read_slot - 2, 0, len(read_events) - 1)]
            known_read, known_gap = prior_reads > 0, prior_reads > 1
            values[known_read, 4] = (timestamps[known_read] - events["timestamp"][previous_reads[known_read]]) / TICKS_PER_SECOND
            values[known_gap, 6] = (events["timestamp"][previous_reads[known_gap]] - events["timestamp"][previous_two[known_gap]]) / TICKS_PER_SECOND
            candidates = read_events[np.minimum(read_slot, len(read_events) - 1)]
            found = (read_slot < len(read_events)) & (events["offset"][candidates] == offsets)
            next_reads[rows[found]] = candidates[found]
            targets[rows[found]] = (events["timestamp"][candidates[found]] - timestamps[found]) / TICKS_PER_SECOND
        features[rows] = np.log1p(values)
    if isinstance(features, np.memmap):
        features.flush()
    return {
        "features": features, "write_indices": chronological_writes,
        "offsets": events["offset"][chronological_writes],
        "next_read_indices": next_reads, "targets": targets,
        "timestamps": events["timestamp"],
    }


def train_and_evaluate(samples, workload, output):
    masks, coverage = split_masks(samples)
    train = masks["train"]
    if train.sum() < 100:
        raise ValueError(f"Only {train.sum()} completed training intervals for {workload}")
    median, addresses = fit_baselines(samples["offsets"][train], samples["targets"][train])
    # Exactly the pilot's fixed recipe, without early stopping or tuning.
    params = dict(
        objective="regression", n_estimators=150, learning_rate=0.05,
        num_leaves=31, min_child_samples=50, reg_lambda=1.0,
        random_state=42, n_jobs=2, deterministic=True, force_col_wise=True, verbosity=-1,
    )
    model = lgb.LGBMRegressor(**params)
    model.fit(samples["features"][train], np.log1p(samples["targets"][train]), feature_name=FEATURE_NAMES)
    model.booster_.save_model(str(output / f"{workload}.lightgbm.txt"))
    metrics, support = {}, {}
    for name, mask in masks.items():
        offsets, targets = samples["offsets"][mask], samples["targets"][mask]
        predictions = {
            "global_median": np.full(len(targets), median),
            "address_median": np.fromiter((addresses.get(int(a), median) for a in offsets), dtype=float, count=len(offsets)),
            "lightgbm": np.empty(len(targets)),
        }
        selected = np.flatnonzero(mask)
        for start in range(0, len(selected), 250_000):
            end = min(start + 250_000, len(selected))
            log_predictions = model.booster_.predict(samples["features"][selected[start:end]], num_threads=2)
            predictions["lightgbm"][start:end] = np.maximum(0, np.expm1(log_predictions))
        metrics[name] = {method: score(targets, pred) for method, pred in predictions.items()}
        support[name] = int(sum(int(a) in addresses for a in offsets))
        if name != "train":
            writes = samples["write_indices"][mask]
            reads = samples["next_read_indices"][mask]
            timestamps = samples["timestamps"]
            np.savez(output / f"{workload}.{name}.predictions.npz",
                     write_event_index=writes, next_read_event_index=reads,
                     offset_bytes=offsets,
                     write_seconds=(timestamps[writes] - timestamps[0]) / TICKS_PER_SECOND,
                     next_read_seconds=(timestamps[reads] - timestamps[0]) / TICKS_PER_SECOND,
                     target_seconds=targets, **predictions)
        print(f"  {workload}/{name}: {len(targets):,} observed intervals", flush=True)
    return {
        "split_by": "duration", "split_coverage": coverage, "metrics": metrics,
        "baseline_global_median_seconds": median,
        "address_baseline_supported_samples": support,
        "feature_names": FEATURE_NAMES, "model_params": params,
        "feature_importance_gain": dict(zip(FEATURE_NAMES, model.booster_.feature_importance(importance_type="gain").tolist())),
    }


def run_workload(dataset, workload, hours, cap, output):
    started = time.monotonic()
    cache = output / f"{workload}.events.bin"
    features_path = output / f"{workload}.features.npy"
    events, source = load_duration(dataset, workload, hours, cap, cache)
    if source["stop_reason"] != "duration_reached":
        raise ValueError(f"{workload}: full {hours} hours not reached: {source['stop_reason']}; cached prefix retained")
    print(f"  {workload}: building samples for {len(events):,} events", flush=True)
    samples = make_compact_samples(events, features_path)
    result = train_and_evaluate(samples, workload, output)
    result.update(
        source=source, counts=source["counts"],
        duration_seconds=(int(events["timestamp"][-1]) - int(events["timestamp"][0])) / TICKS_PER_SECOND,
        elapsed_seconds=time.monotonic() - started,
    )
    # Cache is reproducible from source hashes; retain only models and predictions.
    del samples, events
    cache.unlink()
    features_path.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=PROJECT_ROOT / "dataset")
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--max-events", type=int, default=40_000_000)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results/next-read-24h")
    args = parser.parse_args()
    if args.hours <= 0 or args.max_events < 200:
        parser.error("Positive hours and at least 200 events required")
    if args.output.exists():
        parser.error("Output exists; choose a new directory")
    args.output.mkdir(parents=True)
    started = time.monotonic()
    results = {}
    for workload in TRACE_SOURCES:
        print(f"Running {workload}: first {args.hours:g} hours, cap {args.max_events:,} events", flush=True)
        results[workload] = run_workload(args.dataset, workload, args.hours, args.max_events, args.output)
        # Retain a completed workload even if the second one fails.
        (args.output / f"{workload}.result.json").write_text(json.dumps(results[workload], indent=2, allow_nan=False) + "\n")
    record = {
        "target": "write-to-first-next-read seconds, same starting offset",
        "hours": args.hours, "python": platform.python_version(),
        "numpy": np.__version__, "lightgbm": lgb.__version__,
        "code_sha256": {
            str(path.relative_to(PROJECT_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [source_path("next_read_extended.py"), source_path("next_read.py")]
        },
        "elapsed_seconds": time.monotonic() - started,
        "process_peak_rss_mib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    save_report(args.output, results)
    print(f"Saved extended results to {args.output}", flush=True)


if __name__ == "__main__":
    main()
