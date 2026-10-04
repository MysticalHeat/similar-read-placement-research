"""Bounded, chronological write-to-next-read pilot; raw traces stay in tar files."""

import argparse
import csv
import gzip
import hashlib
import json
import platform
import resource
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import sklearn

TICKS_PER_SECOND = 10_000_000
FEATURE_NAMES = [
    "log_offset_bytes", "log_size_bytes", "log_prior_read_count",
    "log_prior_write_count", "log_seconds_since_read",
    "log_seconds_since_write", "log_last_read_read_interval_seconds",
]
TRACE_SOURCES = {
    "usr_1": ("msr-cambridge2.tar", "MSR-Cambridge/usr_1.csv.gz"),
    "prxy_1": ("msr-cambridge1.tar", "MSR-Cambridge/prxy_1.csv.gz"),
}


@dataclass(frozen=True)
class Event:
    timestamp: int
    kind: str
    offset: int
    size: int


@dataclass
class History:
    reads: int = 0
    writes: int = 0
    last_read: int | None = None
    last_write: int | None = None
    last_read_gap: float | None = None


def load_prefix(dataset: Path, workload: str, limit: int):
    """Read precisely a bounded prefix, validating one volume and source order."""
    archive, member = TRACE_SOURCES[workload]
    events = []
    digest = hashlib.sha256()
    volume = None
    with tarfile.open(dataset / archive) as tar:
        raw = tar.extractfile(member)
        if raw is None:
            raise ValueError(f"Not a regular trace file: {member}")
        with raw, gzip.GzipFile(fileobj=raw) as stream:
            for index in range(limit):
                line = stream.readline()
                if not line:
                    break
                digest.update(line)
                fields = next(csv.reader([line.decode("ascii")]))
                if len(fields) != 7:
                    raise ValueError(f"Row {index + 1}: expected 7 fields")
                ts, host, disk, kind, offset, size, response = fields
                row_volume = (host, int(disk))
                if volume is not None and volume != row_volume:
                    raise ValueError("Multiple volumes in one trace")
                volume = row_volume
                event = Event(int(ts), kind, int(offset), int(size))
                if kind not in {"Read", "Write"} or event.offset < 0 or event.size <= 0:
                    raise ValueError(f"Invalid event at row {index + 1}")
                if int(response) < 0:
                    raise ValueError("Negative response time")
                if events and event.timestamp < events[-1].timestamp:
                    raise ValueError(f"Nonchronological trace at row {index + 1}")
                events.append(event)
    if len(events) < 100:
        raise ValueError("Too few events for a chronological pilot")
    return events, {
        "archive": str(dataset / archive), "member": member,
        "prefix_sha256": digest.hexdigest(), "volume": volume,
        "requested_events": limit, "loaded_events": len(events),
    }


def make_samples(events):
    """Causal features in a forward pass; future truth in a separate reverse pass.

    Same-time ties use trace row order. Multiple writes before a read each target
    that read, irrespective of intervening overwrites (address, not version).
    """
    features, write_indices, offsets = [], [], []
    state = {}
    for index, event in enumerate(events):
        if event.offset not in state:
            state[event.offset] = History()
        history = state[event.offset]
        if event.kind == "Write":
            since_read = None if history.last_read is None else (event.timestamp - history.last_read) / TICKS_PER_SECOND
            since_write = None if history.last_write is None else (event.timestamp - history.last_write) / TICKS_PER_SECOND
            values = [event.offset, event.size, history.reads, history.writes, since_read, since_write, history.last_read_gap]
            features.append([np.nan if v is None else np.log1p(v) for v in values])
            write_indices.append(index)
            offsets.append(event.offset)
            history.writes += 1
            history.last_write = event.timestamp
        else:
            history.reads += 1
            history.last_read_gap = None if history.last_read is None else (event.timestamp - history.last_read) / TICKS_PER_SECOND
            history.last_read = event.timestamp

    indices = np.asarray(write_indices, dtype=np.int64)
    next_reads = np.full(len(indices), -1, dtype=np.int64)
    future_reads = {}
    write_position = len(indices) - 1
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if event.kind == "Read":
            future_reads[event.offset] = index
        else:
            next_reads[write_position] = future_reads.get(event.offset, -1)
            write_position -= 1
    timestamps = np.asarray([event.timestamp for event in events], dtype=np.int64)
    targets = np.full(len(indices), np.nan)
    observed = next_reads >= 0
    targets[observed] = (timestamps[next_reads[observed]] - timestamps[indices[observed]]) / TICKS_PER_SECOND
    return {
        "features": np.asarray(features, dtype=np.float64).reshape(-1, len(FEATURE_NAMES)),
        "write_indices": indices, "offsets": np.asarray(offsets, dtype=np.int64),
        "next_read_indices": next_reads, "targets": targets, "timestamps": timestamps,
    }


def split_masks(samples, split_by="time"):
    """60/20/20 duration (or event-count) cuts aligned to timestamps.

    No training/validation truth crosses its cutoff. Test truth ends with prefix.
    Excluded writes are right-censored, not assigned an artificial long interval.
    """
    timestamps = samples["timestamps"]
    n = len(timestamps)
    if split_by == "time":
        origin, duration = int(timestamps[0]), int(timestamps[-1]) - int(timestamps[0])
        cut_timestamps = [origin + int(duration * fraction) for fraction in (0.6, 0.8)]
    elif split_by == "events":
        cut_timestamps = [timestamps[int(n * fraction)] for fraction in (0.6, 0.8)]
    else:
        raise ValueError(f"Unknown split method: {split_by}")
    first, second = [int(np.searchsorted(timestamps, cutoff, side="left")) for cutoff in cut_timestamps]
    if not 0 < first < second < n:
        raise ValueError("Timestamp ties prevent distinct temporal splits")
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    masks, coverage = {}, {}
    for name, start, end in [("train", 0, first), ("validation", first, second), ("test", second, n)]:
        eligible = (writes >= start) & (writes < end)
        complete = eligible & (reads >= 0) & (reads < end)
        masks[name] = complete
        total, known = int(eligible.sum()), int(complete.sum())
        coverage[name] = {
            "start_event": start, "end_event_exclusive": end,
            "start_seconds": float((timestamps[start] - timestamps[0]) / TICKS_PER_SECOND),
            "last_event_seconds": float((timestamps[end - 1] - timestamps[0]) / TICKS_PER_SECOND),
            "writes": total, "observed_targets": known, "right_censored": total - known,
            "observed_fraction": known / total if total else None,
        }
    return masks, coverage


def fit_baselines(offsets, targets):
    """Frozen medians of completed training intervals; no evaluation truth."""
    median = float(np.median(targets))
    groups = {}
    for offset, target in zip(offsets, targets):
        groups.setdefault(int(offset), []).append(float(target))
    return median, {offset: float(np.median(values)) for offset, values in groups.items()}


def score(targets, predictions):
    if len(targets) == 0:
        return None
    if not np.isfinite(predictions).all() or (predictions < 0).any():
        raise ValueError("Predictions must be finite and nonnegative")
    error = np.abs(targets - predictions)
    return {
        "n": len(targets), "mae_seconds": float(error.mean()),
        "median_absolute_error_seconds": float(np.median(error)),
        "p90_absolute_error_seconds": float(np.quantile(error, 0.9)),
        "rmse_seconds": float(np.sqrt(np.mean(error ** 2))),
        "mae_log1p_seconds": float(np.abs(np.log1p(targets) - np.log1p(predictions)).mean()),
    }


def run_workload(dataset, workload, limit, output):
    started = time.monotonic()
    events, source = load_prefix(dataset, workload, limit)
    samples = make_samples(events)
    masks, coverage = split_masks(samples)
    train = masks["train"]
    if train.sum() < 100:
        raise ValueError(f"{workload}: only {train.sum()} completed training intervals")
    median, by_offset = fit_baselines(samples["offsets"][train], samples["targets"][train])
    # Fixed recipe, no tuning or early stopping; each workload has its own model.
    params = dict(
        objective="regression", n_estimators=150, learning_rate=0.05,
        num_leaves=31, min_child_samples=50, reg_lambda=1.0,
        random_state=42, n_jobs=2, deterministic=True, force_col_wise=True, verbosity=-1,
    )
    model = lgb.LGBMRegressor(**params)
    model.fit(samples["features"][train], np.log1p(samples["targets"][train]), feature_name=FEATURE_NAMES)
    output.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(output / f"{workload}.lightgbm.txt"))
    metrics = {}
    for name in ["train", "validation", "test"]:
        mask = masks[name]
        offsets, targets = samples["offsets"][mask], samples["targets"][mask]
        predictions = {
            "global_median": np.full(len(targets), median),
            "address_median": np.asarray([by_offset.get(int(offset), median) for offset in offsets]),
            "lightgbm": np.maximum(0, np.expm1(model.predict(samples["features"][mask]))) if len(targets) else np.empty(0),
        }
        metrics[name] = {method: score(targets, pred) for method, pred in predictions.items()}
        if not len(targets):
            print(f"{workload}/{name}: no completed intervals; metrics unavailable", flush=True)
        if name != "train":
            with (output / f"{workload}.{name}.predictions.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["write_event_index", "offset_bytes", "write_seconds", "next_read_seconds", "target_seconds", *predictions])
                for j, row in enumerate(np.flatnonzero(mask)):
                    write = samples["write_indices"][row]
                    read = samples["next_read_indices"][row]
                    origin = samples["timestamps"][0]
                    writer.writerow([int(write), int(samples["offsets"][row]),
                                     (int(samples["timestamps"][write]) - int(origin)) / TICKS_PER_SECOND,
                                     (int(samples["timestamps"][read]) - int(origin)) / TICKS_PER_SECOND,
                                     float(targets[j]), *[float(pred[j]) for pred in predictions.values()]])
    counts = {kind: sum(e.kind == kind for e in events) for kind in ["Read", "Write"]}
    return {
        "source": source, "counts": counts,
        "duration_seconds": (events[-1].timestamp - events[0].timestamp) / TICKS_PER_SECOND,
        "distinct_start_offsets": len({e.offset for e in events}),
        "split_by": "duration", "split_coverage": coverage, "metrics": metrics,
        "baseline_global_median_seconds": median,
        "model_params": params, "feature_names": FEATURE_NAMES,
        "feature_importance_gain": dict(zip(FEATURE_NAMES, model.booster_.feature_importance(importance_type="gain").tolist())),
        "elapsed_seconds": time.monotonic() - started,
    }


def save_report(output, results):
    lines = [
        "# Write → next read: MSR Cambridge pilot", "",
        "Target: seconds from a write to the first later read with the same starting byte offset.",
        "Same-timestamp events follow trace row order; zero intervals are permitted.",
        "Separate fixed LightGBM models; 60/20/20 duration cuts aligned to timestamps; no tuning.",
        "Features are past-only, ResponseTime is not used. Baselines use completed training intervals only.", "",
        "## Test metrics (completed intervals only)", "",
        "| Workload | Method | N | MAE, s | Median AE, s | P90 AE, s | MAE log1p(s) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for workload, result in results.items():
        for method, metric in result["metrics"]["test"].items():
            if metric is None:
                lines.append(f"| {workload} | {method} | 0 | unavailable | unavailable | unavailable | unavailable |")
            else:
                lines.append(f"| {workload} | {method} | {metric['n']} | {metric['mae_seconds']:.4f} | {metric['median_absolute_error_seconds']:.4f} | {metric['p90_absolute_error_seconds']:.4f} | {metric['mae_log1p_seconds']:.4f} |")
    lines += ["", "## Observation coverage", "", "| Workload | Split | Writes | Observed next reads | Right-censored | Observed fraction |", "|---|---|---:|---:|---:|---:|"]
    for workload, result in results.items():
        lines += [f"| {workload} | {name} | {c['writes']} | {c['observed_targets']} | {c['right_censored']} | {c['observed_fraction']:.1%} |" for name, c in result["split_coverage"].items()]
    lines += ["", "## Scope and limitations", "",
              "- This is a bounded initial prefix, not the full workload. Prefixes cover different durations.",
              "- Evaluation excludes writes without a read before their split ends. Long intervals are disproportionately excluded: metrics are conditional on observed next reads, not all writes.",
              "- Exact starting offsets are used, not intersecting byte ranges or 4 KiB pages.",
              "- Intervening writes do not cancel a sample: this predicts address access, not data-version consumption.",
              "- Address medians are frozen at the training cutoff; training scores are descriptive in-sample scores.",
              "- Correlated requests and a single prefix do not establish generalization across a full week or SSD performance gains.",
              "- The log-space model optimizes squared log error; this need not minimize MAE in seconds.", "",
              "Data attribution: Narayanan, Donnelly, Rowstron, *Write Off-Loading: Practical Power Management for Enterprise Storage*, FAST 2008.",
              "https://www.usenix.org/legacy/events/fast08/tech/full_papers/narayanan/narayanan.pdf", ""]
    (output / "report.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("dataset"))
    parser.add_argument("--max-events", type=int, default=1_000_000)
    parser.add_argument("--output", type=Path, default=Path("results/next-read-pilot"))
    parser.add_argument("--workloads", nargs="+", choices=list(TRACE_SOURCES), default=list(TRACE_SOURCES))
    args = parser.parse_args()
    if args.max_events < 200:
        parser.error("--max-events must be at least 200 (training needs 100 completed intervals)")
    if args.output.exists():
        parser.error("Output already exists; choose a new directory to preserve previous runs")
    started = time.monotonic()
    results = {}
    for workload in args.workloads:
        print(f"Running {workload}, at most {args.max_events:,} events", flush=True)
        results[workload] = run_workload(args.dataset, workload, args.max_events, args.output)
        print(json.dumps(results[workload]["metrics"]["test"], indent=2), flush=True)
    record = {
        "target": "write-to-first-next-read seconds, same starting offset",
        "python": platform.python_version(), "numpy": np.__version__, "lightgbm": lgb.__version__,
        "scikit_learn": sklearn.__version__,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "elapsed_seconds": time.monotonic() - started,
        "process_peak_rss_mib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    save_report(args.output, results)
    print(f"Saved report and predictions to {args.output}", flush=True)


if __name__ == "__main__":
    main()
