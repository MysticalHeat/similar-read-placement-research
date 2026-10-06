"""Independently verify the MAE-improvement experiment artifacts."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from read_prediction.checks.study import check_metrics, sample_records
from read_prediction.paths import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "results/mae-improvement"
DEVELOPMENT_DAYS = (2, 3, 4)
HOLDOUT_DAYS = (5, 6, 7)
PREDICTION_FIELDS = (
    "write_event_index", "next_read_event_index", "offset_bytes", "write_seconds",
    "next_read_seconds", "target_seconds",
)
METRIC_FIELDS = (
    "mae_seconds", "median_absolute_error_seconds", "p90_absolute_error_seconds",
    "rmse_seconds", "mae_log1p_seconds",
)


def _safe_relative_path(value):
    path = Path(value)
    assert not path.is_absolute(), f"Expected a relative artifact path: {value}"
    assert ".." not in path.parts, f"Artifact path escapes project root: {value}"
    return path


def verify_hashes(root, hashes):
    """Verify recorded artifact bytes at their exact relative paths.

    This deliberately does not use the historical-source resolver: a frozen
    experiment hash must match the file named in the experiment record.
    """
    assert isinstance(hashes, dict) and hashes, "Frozen hash map is empty"
    for relative, expected in hashes.items():
        path = root / _safe_relative_path(relative)
        assert path.is_file(), f"Missing frozen artifact: {relative}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"Frozen SHA256 mismatch: {relative}"
    return len(hashes)


def _check_score_record(metric, label):
    if metric is None:
        return
    assert isinstance(metric, dict), f"Invalid score record: {label}"
    assert isinstance(metric.get("n"), int) and metric["n"] > 0, f"Invalid score count: {label}"
    for field in METRIC_FIELDS:
        value = metric[field]
        assert math.isfinite(value) and value >= 0, f"Invalid {field}: {label}"


def verify_frozen(root, workload, selection, frozen, output):
    """Check freeze metadata, selected definition, and exact artifact hashes."""
    assert output.name == workload
    assert type(frozen["new_fits"]) is int and frozen["new_fits"] == 0, (
        "Frozen evaluation must not fit new models"
    )
    assert frozen["development_days"] == list(DEVELOPMENT_DAYS)
    assert frozen["test_days"] == list(HOLDOUT_DAYS)

    definitions = selection["definitions"]
    method = selection["selected_method"]
    assert method in definitions
    expected_selection = {**definitions[method], "method": method}
    assert frozen["selection"] == expected_selection, "Frozen selection differs from selection.json"

    expected_selection_path = (output / "selection.json").relative_to(root).as_posix()
    selection_path = _safe_relative_path(frozen["selection_path"]).as_posix()
    assert selection_path == expected_selection_path, "Frozen selection_path is not this workload's selection.json"

    hashes = frozen["hashes"]
    hash_paths = {_safe_relative_path(name).as_posix() for name in hashes}
    assert selection_path in hash_paths, "selection.json is not covered by frozen hashes"
    baseline_path = (output / "baselines.json").relative_to(root).as_posix()
    assert baseline_path in hash_paths, "baselines.json is not covered by frozen hashes"
    for name, definition in definitions.items():
        model_path = definition.get("model_path")
        if model_path is not None:
            normalized = _safe_relative_path(model_path).as_posix()
            assert normalized in hash_paths, f"Model for {name} is not covered by frozen hashes"
    checked_hashes = verify_hashes(root, hashes)
    return checked_hashes


def _validate_definitions(definitions):
    assert isinstance(definitions, dict) and definitions
    for method, definition in definitions.items():
        assert isinstance(definition, dict), f"Invalid definition for {method}"
        kind = definition.get("kind")
        assert kind in {"model", "address_median", "blend"}, f"Unknown kind for {method}: {kind}"
        if kind == "model":
            assert definition.get("model_path"), f"Model path missing for {method}"
            assert isinstance(definition.get("columns"), list), f"Model columns missing for {method}"
        elif kind == "address_median":
            assert definition.get("model_path") is None
        else:
            assert isinstance(definition.get("columns"), list), f"Blend columns missing for {method}"
            weight = definition["model_weight"]
            assert math.isfinite(weight) and 0 <= weight <= 1, f"Invalid model weight for {method}"
            if definition.get("model_path") is not None:
                _safe_relative_path(definition["model_path"])


def _blend_model_method(method, definition, definitions):
    explicit = definition.get("model_method")
    if explicit is not None:
        assert explicit in definitions, f"Unknown model_method for blend {method}: {explicit}"
        assert definitions[explicit]["kind"] == "model", f"Blend {method} source is not a model"
        model_method = explicit
    else:
        model_path = definition.get("model_path")
        candidates = [
            name for name, candidate in definitions.items()
            if candidate["kind"] == "model"
            and (model_path is None or candidate.get("model_path") == model_path)
        ]
        assert len(candidates) == 1, (
            f"Blend {method} must identify exactly one model by model_path or model_method"
        )
        model_method = candidates[0]

    model_definition = definitions[model_method]
    if definition.get("model_path") is not None:
        assert definition["model_path"] == model_definition["model_path"]
    assert definition["columns"] == model_definition["columns"]
    return model_method


def _check_blends(data, definitions, methods):
    for method in methods:
        definition = definitions[method]
        if definition["kind"] != "blend":
            continue
        model_method = _blend_model_method(method, definition, definitions)
        baseline_method = definition.get("baseline_method", "address_median")
        assert definitions[baseline_method]["kind"] == "address_median"
        model_prediction = data[model_method]
        baseline_prediction = data[baseline_method]
        weight = float(definition["model_weight"])
        reconstructed = weight * model_prediction + (1 - weight) * baseline_prediction
        np.testing.assert_allclose(data[method], reconstructed, rtol=1e-12, atol=1e-12,
                                   err_msg=f"Blend reconstruction failed for {method}")


def _validate_coverage(coverage, count):
    start = coverage["start_event"]
    end = coverage["end_event_exclusive"]
    writes = coverage["writes"]
    observed = coverage["observed_targets"]
    censored = coverage["right_censored"]
    assert all(isinstance(value, int) for value in (start, end, writes, observed, censored))
    assert 0 <= start <= end
    assert writes == observed + censored
    assert observed == count
    fraction = coverage["observed_fraction"]
    if writes:
        assert math.isclose(fraction, observed / writes, rel_tol=1e-12, abs_tol=1e-12)
    else:
        assert fraction is None


def _check_prediction_rows(data, coverage, day, end_seconds=None, total_events=None):
    for field in PREDICTION_FIELDS:
        assert field in data.files, f"Missing prediction row field: {field}"
    arrays = {field: np.asarray(data[field]) for field in PREDICTION_FIELDS}
    lengths = {len(values) for values in arrays.values()}
    assert len(lengths) == 1, "Prediction row fields have different lengths"
    count = len(arrays["target_seconds"])
    if coverage is not None:
        _validate_coverage(coverage, count)

    writes = arrays["write_event_index"]
    reads = arrays["next_read_event_index"]
    offsets = arrays["offset_bytes"]
    write_seconds = arrays["write_seconds"]
    read_seconds = arrays["next_read_seconds"]
    targets = arrays["target_seconds"]
    assert np.issubdtype(writes.dtype, np.integer)
    assert np.issubdtype(reads.dtype, np.integer)
    assert np.issubdtype(offsets.dtype, np.integer)
    assert np.all(offsets >= 0)
    assert np.all(writes >= 0) and np.all(reads >= 0)
    if total_events is not None:
        assert np.all((writes < total_events) & (reads < total_events))
    assert np.all(np.diff(writes) > 0), "Write event indices are not strictly chronological"
    assert np.all(reads > writes)
    if coverage is not None:
        assert np.all((writes >= coverage["start_event"]) & (writes < coverage["end_event_exclusive"]))
        assert np.all(reads < coverage["end_event_exclusive"])
    assert np.isfinite(write_seconds).all() and np.isfinite(read_seconds).all()
    assert np.isfinite(targets).all() and np.all(targets >= 0)
    assert np.all(np.diff(write_seconds) >= 0), "Write timestamps are not chronological"
    assert np.all(write_seconds >= (day - 1) * 86400)
    assert np.all(write_seconds < day * 86400)
    assert np.all(read_seconds < day * 86400)
    if end_seconds is not None:
        assert math.isfinite(end_seconds) and 0 <= end_seconds <= day * 86400
        assert np.all(write_seconds <= end_seconds + 1e-9)
        assert np.all(read_seconds <= end_seconds + 1e-9)
    np.testing.assert_allclose(read_seconds - write_seconds, targets, rtol=1e-10, atol=1e-9,
                               err_msg=f"Day {day}: target does not equal next-read minus write time")
    return arrays


def _check_baselines(data, arrays, baselines):
    global_median = baselines["global_median_seconds"]
    addresses = baselines["address_medians_seconds"]
    assert math.isfinite(global_median) and global_median >= 0
    assert all(math.isfinite(value) and value >= 0 for value in addresses.values())
    offsets = arrays["offset_bytes"]
    expected = np.fromiter(
        (addresses.get(str(int(offset)), global_median) for offset in offsets),
        dtype=float, count=len(offsets),
    )
    np.testing.assert_array_equal(data["address_median"], expected,
                                  err_msg="Address-median predictions differ from baselines.json")


def _check_prediction_values(data, methods):
    for method in methods:
        assert method in data.files, f"Missing prediction array for {method}"
        prediction = np.asarray(data[method])
        assert np.isfinite(prediction).all() and np.all(prediction >= 0), (
            f"Predictions for {method} must be finite and nonnegative"
        )


def _check_validation_records(validation, methods):
    assert validation and set(validation).issubset(methods)
    for method, metric in validation.items():
        _check_score_record(metric, f"validation/{method}")


def _verify_first_day_validation(root, output, selection, definitions, methods, baselines):
    prior_path = root / "results/next-read-24h" / f"{selection['workload']}.result.json"
    prior = json.loads(prior_path.read_text())
    expected_train_end = prior["split_coverage"]["train"]["end_event_exclusive"]
    expected_validation_end = prior["split_coverage"]["validation"]["end_event_exclusive"]
    train_end = selection["train_end_event_exclusive"]
    validation_end = selection["validation_end_event_exclusive"]
    assert train_end == expected_train_end
    assert validation_end == expected_validation_end
    assert selection["train_observed_targets"] == prior["split_coverage"]["train"]["observed_targets"]
    assert selection["validation_observed_targets"] == prior["split_coverage"]["validation"]["observed_targets"]
    new_model_count = sum(
        definition["kind"] == "model" and name != "current"
        for name, definition in definitions.items()
    )
    assert selection["new_fits"] == new_model_count

    validation = selection["validation"]
    assert set(validation) == set(methods)
    with np.load(output / "validation.predictions.npz", allow_pickle=False) as data:
        arrays = _check_prediction_rows(
            data, None, day=1, total_events=selection["source"]["loaded_events"],
        )
        writes, reads = arrays["write_event_index"], arrays["next_read_event_index"]
        assert len(writes) == selection["validation_observed_targets"]
        assert np.all((writes >= train_end) & (writes < validation_end))
        assert np.all(reads < validation_end)
        assert {"current", "address_median", *methods}.issubset(data.files)
        _check_baselines(data, arrays, baselines)
        _check_prediction_values(data, methods)
        _check_blends(data, definitions, methods)
        for method in methods:
            check_metrics(arrays["target_seconds"], data[method], validation[method])
    return len(writes)


def verify_workload(workload, root=PROJECT_ROOT, output_root=OUTPUT, audit_source_enabled=False):
    assert workload in {"usr_1", "prxy_1"}
    output = output_root / workload
    selection = json.loads((output / "selection.json").read_text())
    frozen = json.loads((output / "frozen.json").read_text())
    holdout = json.loads((output / "holdout.json").read_text())
    baselines = json.loads((output / "baselines.json").read_text())
    definitions = selection["definitions"]
    _validate_definitions(definitions)
    checked_hashes = verify_frozen(root, workload, selection, frozen, output)

    development = selection["development"]
    methods = list(development)
    assert set(methods) == set(definitions)
    assert "current" in definitions and definitions["current"]["kind"] == "model"
    assert "address_median" in definitions and definitions["address_median"]["kind"] == "address_median"
    assert set(selection["pooled_development_mae"]) == set(methods)
    _check_validation_records(selection["validation"], methods)
    assert all(set(development[method]) == {str(day) for day in DEVELOPMENT_DAYS} for method in methods)
    validation_rows = _verify_first_day_validation(
        root, output, selection, definitions, methods, baselines,
    )
    total_events = holdout["source"]["loaded_events"]
    assert selection["source"]["first_timestamp"] == holdout["source"]["first_timestamp"]

    total_development_rows = 0
    absolute_error_sums = {method: [] for method in methods}
    row_counts = {method: 0 for method in methods}
    for day in DEVELOPMENT_DAYS:
        path = output / f"day{day}.predictions.npz"
        with np.load(path, allow_pickle=False) as data:
            coverage = selection.get("development_coverage", {}).get(str(day))
            arrays = _check_prediction_rows(data, coverage, day, total_events=total_events)
            assert {"current", "address_median", *methods}.issubset(data.files)
            _check_baselines(data, arrays, baselines)
            _check_prediction_values(data, methods)
            _check_blends(data, definitions, methods)
            for method in methods:
                metric = development[method][str(day)]
                check_metrics(arrays["target_seconds"], data[method], metric)
                if len(arrays["target_seconds"]):
                    errors = np.abs(arrays["target_seconds"] - data[method])
                    absolute_error_sums[method].append(math.fsum(errors))
                    row_counts[method] += len(errors)
            total_development_rows += len(arrays["target_seconds"])

    pooled = {}
    for method in methods:
        assert row_counts[method] > 0, f"No development targets for {method}"
        pooled[method] = math.fsum(absolute_error_sums[method]) / row_counts[method]
    for method in methods:
        recorded = selection["pooled_development_mae"][method]
        assert math.isfinite(recorded) and recorded >= 0
        assert math.isclose(pooled[method], recorded, rel_tol=1e-10, abs_tol=1e-10), (
            f"Pooled development MAE mismatch for {method}"
        )
    winner = min(pooled, key=lambda method: pooled[method])
    assert selection["selected_method"] == winner, "Selected method is not the development MAE minimum"

    assert set(holdout["days"]) == {str(day) for day in HOLDOUT_DAYS}
    assert type(holdout["new_fits"]) is int and holdout["new_fits"] == 0
    holdout_rows = {}
    holdout_blend_reconstruction_verified = True
    selected_definition = definitions[selection["selected_method"]]
    selected_prediction_reconstruction_verified = (
        selected_definition["kind"] in {"address_median", "blend"}
        or selection["selected_method"] == "current"
    )
    for day in HOLDOUT_DAYS:
        entry = holdout["days"][str(day)]
        assert entry["evaluation_role"] == "new_future_period"
        coverage = entry["coverage"]
        end_seconds = float(entry["end_seconds"])
        path = output / f"holdout-day{day}.predictions.npz"
        with np.load(path, allow_pickle=False) as data:
            arrays = _check_prediction_rows(data, coverage, day, end_seconds, total_events)
            methods_in_holdout = ("current", "address_median", "selected")
            _check_prediction_values(data, methods_in_holdout)
            _check_baselines(data, arrays, baselines)
            assert set(entry["metrics"]) == set(methods_in_holdout)
            for method in methods_in_holdout:
                check_metrics(arrays["target_seconds"], data[method], entry["metrics"][method])
            if selected_definition["kind"] == "blend":
                model_method = _blend_model_method(selection["selected_method"], selected_definition, definitions)
                model_key = "selected_model_prediction" if "selected_model_prediction" in data.files else model_method
                if model_key in data.files:
                    model_prediction = np.asarray(data[model_key])
                    assert np.isfinite(model_prediction).all() and np.all(model_prediction >= 0)
                    baseline_method = selected_definition.get("baseline_method", "address_median")
                    weight = float(selected_definition["model_weight"])
                    reconstructed = (weight * model_prediction
                                     + (1 - weight) * data[baseline_method])
                    np.testing.assert_allclose(data["selected"], reconstructed, rtol=1e-12, atol=1e-12,
                                               err_msg=f"Holdout day {day}: selected blend reconstruction failed")
                else:
                    holdout_blend_reconstruction_verified = False
                    selected_prediction_reconstruction_verified = False
            elif selected_definition["kind"] == "address_median":
                np.testing.assert_array_equal(data["selected"], data["address_median"])
            elif selection["selected_method"] == "current":
                np.testing.assert_array_equal(data["selected"], data["current"])
            holdout_rows[str(day)] = len(arrays["target_seconds"])

    audited = None
    source_audit_skipped_reason = None
    if audit_source_enabled:
        source = holdout["source"]
        if source.get("first_excluded_timestamp") is None:
            source_audit_skipped_reason = (
                "source ends at EOF; existing audit_source requires a following excluded event"
            )
        else:
            current = definitions["current"]
            model_path = root / _safe_relative_path(current["model_path"])
            assert current.get("columns") is not None
            import lightgbm as lgb

            from read_prediction.checks.extended import audit_source

            model = lgb.Booster(model_file=str(model_path))
            samples = {}
            for day in (*DEVELOPMENT_DAYS, *HOLDOUT_DAYS):
                filename = (f"day{day}.predictions.npz" if day in DEVELOPMENT_DAYS
                            else f"holdout-day{day}.predictions.npz")
                with np.load(output / filename, allow_pickle=False) as data:
                    samples.update(sample_records(data, "current"))
            audited = audit_source({"source": source}, samples, model, columns=current["columns"])

    verification = {
        "workload": workload,
        "new_fits": 0,
        "frozen_hashes_verified": checked_hashes,
        "selection_verified": winner,
        "first_day_validation_rows_verified": validation_rows,
        "development_rows_verified": total_development_rows,
        "development_rows_by_method": row_counts,
        "holdout_rows_by_day": holdout_rows,
        "blend_reconstruction_verified": True,
        "holdout_blend_reconstruction_verified": holdout_blend_reconstruction_verified,
        "selected_prediction_reconstruction_verified": selected_prediction_reconstruction_verified,
        "holdout_metrics_verified": True,
        "source_samples_audited": audited,
        "source_audit_skipped_reason": source_audit_skipped_reason,
    }
    (output / "verification.json").write_text(json.dumps(verification, indent=2, allow_nan=False) + "\n")
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True, choices=("usr_1", "prxy_1"))
    parser.add_argument("--audit-source", action="store_true",
                        help="stream the recorded trace and audit sampled current-model predictions")
    args = parser.parse_args(argv)
    result = verify_workload(args.workload, audit_source_enabled=args.audit_source)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
