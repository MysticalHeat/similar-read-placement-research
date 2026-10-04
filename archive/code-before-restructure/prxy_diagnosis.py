"""Train/validation-only prxy_1 diagnosis: three fixed ablations, no test scoring."""

import hashlib
import json
from pathlib import Path
import time

import lightgbm as lgb
import numpy as np

from next_read import FEATURE_NAMES, score
from next_read_extended import load_duration, make_compact_samples


def predict_chunks(model, features, rows, columns, log_target):
    predictions = np.empty(len(rows))
    for start in range(0, len(rows), 250_000):
        end = min(start + 250_000, len(rows))
        values = model.predict(features[rows[start:end]][:, columns], num_threads=2)
        predictions[start:end] = np.maximum(0, np.expm1(values) if log_target else values)
    return predictions


def describe(values):
    finite = values[np.isfinite(values)]
    return {"missing_fraction": float(1 - len(finite) / len(values)),
            "quantiles_raw": dict(zip(["p10", "p50", "p90", "p99", "max"], np.expm1(np.quantile(finite, [.1, .5, .9, .99, 1])).tolist())) if len(finite) else None}


def address_extrapolation(train_offsets, train_values, val_offsets, val_values):
    order = np.argsort(train_offsets, kind="stable")
    addresses = train_offsets[order]
    starts = np.r_[0, np.flatnonzero(np.diff(addresses)) + 1]
    unique = addresses[starts]
    maxima = np.maximum.reduceat(train_values[order], starts)
    positions = np.searchsorted(unique, val_offsets)
    clipped = np.minimum(positions, len(unique) - 1)
    known = (positions < len(unique)) & (unique[clipped] == val_offsets)
    above = known & (val_values > maxima[clipped] + 1e-12)
    return {"known_address_fraction": float(known.mean()),
            "above_own_address_train_max_fraction": float(above.mean())}


def main():
    root = Path(__file__).resolve().parent
    output = root / "results/prxy-validation-diagnosis"
    if output.exists():
        raise ValueError("Diagnosis output exists; preserve it before another run")
    output.mkdir()
    started = time.monotonic()
    previous = json.loads((root / "results/next-read-24h/prxy_1.result.json").read_text())
    cutoff = previous["split_coverage"]["validation"]["end_event_exclusive"]
    train_end = previous["split_coverage"]["train"]["end_event_exclusive"]
    # Cap at the exact last validation row: test rows are not stored or labelled.
    events, source = load_duration(root / "dataset", "prxy_1", 24, cutoff, output / "events.bin")
    assert len(events) == cutoff
    samples = make_compact_samples(events, output / "features.npy")
    writes, reads = samples["write_indices"], samples["next_read_indices"]
    masks = {
        "train": (writes < train_end) & (reads >= 0) & (reads < train_end),
        "validation": (writes >= train_end) & (reads >= 0),
    }
    selected = {name: np.flatnonzero(mask) for name, mask in masks.items()}
    truth = {name: samples["targets"][mask] for name, mask in masks.items()}
    offsets = {name: samples["offsets"][mask] for name, mask in masks.items()}
    features = samples["features"]
    with np.load(root / "results/next-read-24h/prxy_1.validation.predictions.npz") as saved:
        np.testing.assert_array_equal(writes[masks["validation"]], saved["write_event_index"])
        np.testing.assert_array_equal(truth["validation"], saved["target_seconds"])
        val_baselines = {method: saved[method] for method in ("global_median", "address_median")}
        original_predictions = saved["lightgbm"]
    reference = lgb.Booster(model_file=str(root / "results/next-read-24h/prxy_1.lightgbm.txt"))
    val_reference = predict_chunks(reference, features, selected["validation"], list(range(7)), True)
    np.testing.assert_allclose(val_reference, original_predictions, rtol=1e-12, atol=1e-12)
    metrics = {"validation": {method: score(truth["validation"], pred) for method, pred in val_baselines.items()}, "train": {}}
    predictions = {**val_baselines, "original_log_l2": val_reference}
    metrics["validation"]["original_log_l2"] = score(truth["validation"], val_reference)
    train_reference = predict_chunks(reference, features, selected["train"], list(range(7)), True)
    metrics["train"]["original_log_l2"] = score(truth["train"], train_reference)
    np.testing.assert_allclose(metrics["train"]["original_log_l2"]["mae_seconds"], previous["metrics"]["train"]["lightgbm"]["mae_seconds"], rtol=1e-12)

    distributions = {}
    for column, name in enumerate(FEATURE_NAMES):
        distributions[name] = {split: describe(features[rows, column]) for split, rows in selected.items()}
        if column in (2, 3):
            distributions[name]["address_extrapolation"] = address_extrapolation(
                offsets["train"], features[selected["train"], column],
                offsets["validation"], features[selected["validation"], column])

    no_counts = [0, 1, 4, 5, 6]
    candidates = [
        ("no_counts_log_l2", no_counts, "regression", True),
        ("all_features_raw_l1", list(range(7)), "regression_l1", False),
        ("no_counts_raw_l1", no_counts, "regression_l1", False),
    ]
    recipe = {}
    for name, columns, objective, log_target in candidates:
        print(f"Fitting fixed candidate {name}", flush=True)
        params = {**previous["model_params"], "objective": objective}
        recipe[name] = {"columns": columns, "objective": objective, "log_target": log_target, "params": params}
        model = lgb.LGBMRegressor(**params)
        model.fit(features[selected["train"]][:, columns], np.log1p(truth["train"]) if log_target else truth["train"], feature_name=[FEATURE_NAMES[c] for c in columns])
        model.booster_.save_model(str(output / f"{name}.lightgbm.txt"))
        for split, rows in selected.items():
            prediction = predict_chunks(model.booster_, features, rows, columns, log_target)
            metrics[split][name] = score(truth[split], prediction)
            if split == "validation":
                predictions[name] = prediction
        print(f"  validation MAE: {metrics['validation'][name]['mae_seconds']:.4f} s", flush=True)

    val_features = features[selected["validation"]]
    last_gap, age = np.expm1(val_features[:, 6]), np.expm1(val_features[:, 4])
    known = np.isfinite(last_gap) & np.isfinite(age)
    period_prediction = val_baselines["global_median"].copy()
    period_prediction[known] = np.maximum(0, last_gap[known] - age[known])
    predictions["previous_read_period_remaining"] = period_prediction
    metrics["validation"]["previous_read_period_remaining"] = score(truth["validation"], period_prediction)

    cohorts = {}
    for lo, hi in zip([0, 5, 15, 30, 60, 120], [5, 15, 30, 60, 120, np.inf]):
        mask = np.isfinite(age) & (age >= lo) & (age < hi)
        cohorts[f"seconds_since_read_{lo}_{hi}"] = {method: score(truth["validation"][mask], pred[mask]) for method, pred in predictions.items()}
    mask = ~np.isfinite(age)
    cohorts["no_prior_read"] = {method: score(truth["validation"][mask], pred[mask]) for method, pred in predictions.items()}
    signed = {method: {"mean_prediction_minus_target_seconds": float((pred - truth["validation"]).mean()),
                      "prediction_p10_p50_p90": np.quantile(pred, [.1, .5, .9]).tolist()} for method, pred in predictions.items()}
    # Selection includes the strong baseline: a new model is not required to win.
    winner = min(metrics["validation"], key=lambda method: metrics["validation"][method]["mae_seconds"])
    np.savez(output / "validation.predictions.npz", target_seconds=truth["validation"], write_event_index=writes[masks["validation"]], **predictions)
    record = {
        "scope": "prxy_1 completed train/validation intervals only; no test scoring",
        "source": source, "selection_metric": "validation MAE seconds", "selected_method": winner,
        "recipe": recipe, "feature_distributions": distributions, "metrics": metrics,
        "validation_age_cohorts": cohorts, "signed_prediction_error": signed,
        "validation_target_p10_p50_p90": np.quantile(truth["validation"], [.1, .5, .9]).tolist(),
        "target_distributions": {name: dict(zip(["p10", "p50", "p90", "p99"], np.quantile(values, [.1, .5, .9, .99]).tolist())) for name, values in truth.items()},
        "previous_period_history_fraction": float(known.mean()),
        "elapsed_seconds": time.monotonic() - started,
        "code_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("prxy_diagnosis.py", "next_read_extended.py", "next_read.py")},
    }
    (output / "results.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    del samples, features, events
    (output / "events.bin").unlink()
    (output / "features.npy").unlink()
    print(f"Selected by validation MAE: {winner}; no test scored", flush=True)


if __name__ == "__main__":
    main()
