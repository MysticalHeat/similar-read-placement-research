"""Frozen first-day models and future-day diagnostics for prxy_0."""

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE, load_duration, make_compact_samples
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import Event, fit_baselines, make_samples, score
from read_prediction.range_label import (
    TICKS, first_future_same_start, label_writes, outcome_state, require_grid,
)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def local_labels(events, begin, end, rule):
    rows = np.flatnonzero(events["is_read"][begin:end] == 0) + begin
    if rule == "range":
        return rows, label_writes(events[:end], rows, begin)
    reads = np.flatnonzero(events["is_read"][begin:end] == 1) + begin
    labels = {}
    for name, candidates in (("read", reads), ("overwrite", rows)):
        labels[name] = first_future_same_start(
            events["offset"][rows], rows, events["offset"][candidates], candidates)
    for index_name, delay_name in (("read", "target"), ("overwrite", "lifetime")):
        present = labels[index_name] >= 0
        delay = np.full(len(rows), np.nan)
        delay[present] = (events["timestamp"][labels[index_name][present]]
                          - events["timestamp"][rows[present]]) / TICKS
        labels[delay_name] = delay
    return rows, labels


def baseline_predictions(method, offsets, median, addresses):
    if method == "global_median":
        return np.full(len(offsets), median)
    return np.asarray([addresses.get(int(offset), median) for offset in offsets])


def measure(events, rows, labels, predictions, boundary):
    seen = labels["read"] >= 0
    overwritten = labels["overwrite"] >= 0
    remainder = (boundary - events["timestamp"][rows]) / TICKS
    budget = np.where(overwritten, labels["lifetime"], remainder)
    error = np.abs(labels["target"][seen] - predictions[seen])
    passed = error < budget[seen]
    unknown = ~overwritten[seen] & ~passed
    n = int(seen.sum())
    states = outcome_state(labels["read"], labels["overwrite"])
    first = states == 1
    return {
        "all_writes": len(rows), "observed_reads": n,
        "observed_read_coverage": n / len(rows) if len(rows) else None,
        "read_first": int(first.sum()), "write_first": int((states == 0).sum()),
        "unresolved": int((states < 0).sum()),
        "observed_overwrites": int(overwritten.sum()),
        "confirmed_pass_count": int(passed.sum()), "unknown_pass_count": int(unknown.sum()),
        "pass_lower": float(passed.mean()) if n else None,
        "pass_upper": float((passed | unknown).mean()) if n else None,
        "confirmed_pass_all_writes": int(passed.sum()) / len(rows) if len(rows) else None,
        "metrics": score(labels["target"][seen], predictions[seen]),
        "read_first_metrics": score(labels["target"][first], predictions[first]),
    }


def verify_direct(events, rows, labels, end, rule):
    """Independent linear searches, not the packed-key label implementation."""
    selected = np.unique(np.linspace(0, len(rows) - 1, min(128, len(rows)), dtype=int))
    for position in selected:
        row = rows[position]
        future = events[row + 1:end]
        if rule == "range":
            match = ((future["offset"] < events["offset"][row] + events["size"][row])
                     & (future["offset"] + future["size"] > events["offset"][row]))
        else:
            match = future["offset"] == events["offset"][row]
        for name, flag in (("read", 1), ("overwrite", 0)):
            found = np.flatnonzero(match & (future["is_read"] == flag))
            expected = int(row + 1 + found[0]) if len(found) else -1
            if expected != labels[name][position]:
                raise AssertionError(f"{rule} {name} mismatch at event {row}")
    return len(selected)


def main(resume=False):
    folder = PROJECT_ROOT / "results/prxy0-check"
    if resume:
        if (folder / "frozen.json").exists():
            raise ValueError("Cannot resume a frozen/completed run")
        source = json.loads((folder / "source.json").read_text())
        events = np.memmap(folder / "events.bin", mode="r", dtype=EVENT_DTYPE,
                           shape=(source["loaded_events"],))
        samples = {"features": np.load(folder / "features.npy", mmap_mode="r"),
                   "write_indices": np.flatnonzero(events["is_read"] == 0)}
    else:
        folder.mkdir(exist_ok=False)
        events, source = load_duration(PROJECT_ROOT / "dataset", "prxy_0", 168, 100_000_000,
                                       folder / "events.bin")
        dump(folder / "source.json", source)
        samples = make_compact_samples(events, folder / "features.npy")
    if source["stop_reason"] == "event_cap_reached":
        raise ValueError("Unexpected event-cap truncation")
    require_grid(events["offset"], events["size"])
    # Independent feature implementation on a short prefix.
    prefix = events[:2000]
    reference = make_samples([Event(int(e["timestamp"]), "Read" if e["is_read"] else "Write",
                                   int(e["offset"]), int(e["size"])) for e in prefix])
    compact = make_compact_samples(prefix)
    for key in ("features", "write_indices", "next_read_indices", "targets"):
        np.testing.assert_allclose(compact[key], reference[key], equal_nan=True)
    origin = source["first_timestamp"]
    cutoff = lambda hours: int(np.searchsorted(events["timestamp"], origin + round(hours * 3600 * TICKS)))
    boundaries = (cutoff(14.4), cutoff(19.2))
    frozen = {}
    fitted = {}
    for rule in ("same_start", "range"):
        train_rows, train = local_labels(events, 0, boundaries[0], rule)
        valid_rows, valid = local_labels(events, boundaries[0], boundaries[1], rule)
        train_seen, valid_seen = train["read"] >= 0, valid["read"] >= 0
        if train_seen.sum() < 100:
            raise ValueError(f"Insufficient training Read labels: {rule}")
        train_positions = np.searchsorted(samples["write_indices"], train_rows[train_seen])
        valid_positions = np.searchsorted(samples["write_indices"], valid_rows)
        median, addresses = fit_baselines(events["offset"][train_rows[train_seen]], train["target"][train_seen])
        predictions, models = {}, {}
        columns = {"all_features": list(range(7)), "no_counts": [0, 1, 4, 5, 6]}
        for method, cols in columns.items():
            model = lgb.LGBMRegressor(
                objective="regression", n_estimators=150, learning_rate=.05, num_leaves=31,
                min_child_samples=50, reg_lambda=1., random_state=42, n_jobs=2,
                deterministic=True, force_col_wise=True, verbosity=-1)
            model.fit(samples["features"][train_positions][:, cols], np.log1p(train["target"][train_seen]))
            model.booster_.save_model(str(folder / f"{rule}.{method}.lightgbm.txt"))
            predictions[method] = np.maximum(0, np.expm1(model.booster_.predict(
                samples["features"][valid_positions][:, cols], num_threads=2)))
            models[method] = model
        for method in ("global_median", "address_median"):
            predictions[method] = baseline_predictions(method, events["offset"][valid_rows], median, addresses)
        validation = {name: score(valid["target"][valid_seen], pred[valid_seen])
                      for name, pred in predictions.items()}
        selected = (min(validation, key=lambda name: validation[name]["mae_seconds"])
                    if valid_seen.sum() >= 100 else "no_counts")
        frozen[rule] = {"selected": selected, "train_n": int(train_seen.sum()),
                        "selection_basis": "validation_mae" if valid_seen.sum() >= 100 else "fixed_fallback_insufficient_validation",
                        "validation_n": int(valid_seen.sum()), "validation": validation,
                        "global_median": median}
        dump(folder / f"{rule}.address_medians.json", {str(k): v for k, v in addresses.items()})
        fitted[rule] = (models, columns, median, addresses)
    dump(folder / "frozen.json", frozen)
    print("Frozen selections:", json.dumps(frozen), flush=True)
    result, verification = {}, {"feature_prefix_events": len(prefix), "direct_label_queries": 0}
    for rule in ("same_start", "range"):
        models, columns, median, addresses = fitted[rule]
        result[rule] = {}
        pooled = {}
        for day in range(2, 8):
            begin, end = cutoff((day - 1) * 24), cutoff(day * 24)
            if begin == end:
                continue
            rows, labels = local_labels(events, begin, end, rule)
            if not len(rows):
                continue
            boundary = min(origin + day * 86400 * TICKS, source["last_timestamp"])
            positions = np.searchsorted(samples["write_indices"], rows)
            predictions = {method: np.maximum(0, np.expm1(model.booster_.predict(
                samples["features"][positions][:, columns[method]], num_threads=2)))
                           for method, model in models.items()}
            for method in ("global_median", "address_median"):
                predictions[method] = baseline_predictions(method, events["offset"][rows], median, addresses)
            day_metrics = {method: measure(events, rows, labels, pred, boundary)
                           for method, pred in predictions.items()}
            result[rule][str(day)] = day_metrics
            np.savez(folder / f"{rule}.day{day}.npz", write_rows=rows, **labels, **predictions)
            verification["direct_label_queries"] += verify_direct(events, rows, labels, end, rule)
            for method in models:
                restored = lgb.Booster(model_file=str(folder / f"{rule}.{method}.lightgbm.txt"))
                np.testing.assert_allclose(predictions[method][:128], np.maximum(0, np.expm1(
                    restored.predict(samples["features"][positions[:128]][:, columns[method]], num_threads=2))))
            for method, metrics in day_metrics.items():
                pooled.setdefault(method, []).append(metrics)
            print(rule, day, "selected", frozen[rule]["selected"],
                  json.dumps(day_metrics[frozen[rule]["selected"]]), flush=True)
        result[rule]["pooled"] = {}
        for method, metrics in pooled.items():
            totals = {key: sum(m[key] for m in metrics) for key in (
                "all_writes", "observed_reads", "read_first", "write_first", "unresolved",
                "confirmed_pass_count", "unknown_pass_count")}
            n = totals["observed_reads"]
            totals.update(pass_lower=totals["confirmed_pass_count"] / n,
                          pass_upper=(totals["confirmed_pass_count"] + totals["unknown_pass_count"]) / n,
                          mae_seconds=sum(m["metrics"]["mae_seconds"] * m["observed_reads"]
                                          for m in metrics if m["metrics"]) / n)
            result[rule]["pooled"][method] = totals
    dump(folder / "metrics.json", result)
    verification["inputs"] = {"source_prefix_sha256": source["prefix_sha256"]}
    verification["hashes"] = {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in (
        Path(__file__), PROJECT_ROOT / "docs/protocols/prxy0-protocol.md",
        PROJECT_ROOT / "read_prediction/range_label.py", PROJECT_ROOT / "read_prediction/extended.py",
        PROJECT_ROOT / "read_prediction/pipeline.py", folder / "frozen.json", folder / "metrics.json")}
    dump(folder / "verification.json", verification)
    print("Verification passed:", verification["direct_label_queries"], "direct queries", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    main(parser.parse_args().resume)
