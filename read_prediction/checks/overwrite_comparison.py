"""Independently verify frozen overwrite-comparison artifacts."""

import argparse
import json
import math
import tempfile
from pathlib import Path

import numpy as np

from read_prediction.checks.mae_improvement import verify_hashes
from read_prediction.paths import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "results/overwrite-comparison"
SOURCE_OUTPUT = PROJECT_ROOT / "results/mae-improvement"
DAYS = (5, 6, 7)
METHODS = ("current", "address_median", "selected")
TICKS_PER_SECOND = 10_000_000
POOL_DTYPE = np.dtype([
    ("overwrite", "<f8"), ("lower_bound", "<f8"), ("read_before", "?"),
    *((f"{method}_error", "<f8") for method in METHODS),
])


def _sum(values):
    return math.fsum(float(value) for value in values)


def _distribution(values):
    if not len(values):
        return None
    p10, median, p90 = np.quantile(values, [0.1, 0.5, 0.9])
    return {
        "n": int(len(values)), "mean_seconds": _sum(values) / len(values),
        "median_seconds": float(median), "p10_seconds": float(p10),
        "p90_seconds": float(p90), "max_seconds": float(np.max(values)),
    }


def _paired(errors, durations):
    if not len(errors):
        return None
    mae = _sum(errors) / len(errors)
    mean_duration = _sum(durations) / len(durations)
    positive_duration = durations > 0
    ratios = errors[positive_duration] / durations[positive_duration]
    return {
        "n": int(len(errors)), "mae_seconds": mae,
        "fraction_error_lt_overwrite": float(np.count_nonzero(errors < durations) / len(errors)),
        "mae_lt_mean_overwrite": mae < mean_duration,
        "mae_lt_median_overwrite": mae < float(np.median(durations)),
        "median_error_to_overwrite_ratio": (
            float(np.quantile(ratios, 0.5)) if len(ratios) else None
        ),
        "p90_error_to_overwrite_ratio": (
            float(np.quantile(ratios, 0.9)) if len(ratios) else None
        ),
    }


def _independent_summary(overwrite, lower_bound, read_before, errors):
    n = len(overwrite)
    known = np.isfinite(overwrite)
    censored = ~known
    read_first_known = read_before & known
    result = {
        "n": int(n), "overwrite_observed_n": int(known.sum()),
        "overwrite_censored_n": int(censored.sum()),
        "zero_overwrite_n": int(np.count_nonzero(known & (overwrite == 0))),
        "read_before_overwrite_n": int(read_before.sum()),
        "overwrite_before_read_n": int(np.count_nonzero(known & ~read_before)),
        "fraction_read_before_overwrite": float(read_before.sum() / n) if n else None,
        "overwrite_distribution": _distribution(overwrite[known]),
        "read_first_overwrite_distribution": _distribution(overwrite[read_first_known]),
        "methods": {},
    }
    for method, method_errors in errors.items():
        paired_errors = method_errors[known]
        paired_durations = overwrite[known]
        read_first_errors = method_errors[read_before]
        read_first_paired_errors = method_errors[read_first_known]
        read_first_paired_durations = overwrite[read_first_known]
        definitely_pass = int(np.count_nonzero(method_errors[censored] < lower_bound[censored]))
        known_pass = int(np.count_nonzero(method_errors[known] < overwrite[known]))
        result["methods"][method] = {
            "all_mae_seconds": _sum(method_errors) / n if n else None,
            "paired": _paired(paired_errors, paired_durations),
            "read_first_mae_seconds": (
                _sum(read_first_errors) / len(read_first_errors) if len(read_first_errors) else None
            ),
            "read_first_paired": _paired(read_first_paired_errors, read_first_paired_durations),
            "censored_definitely_error_lt_overwrite_n": definitely_pass,
            "fraction_error_lt_overwrite_lower_bound": (
                (known_pass + definitely_pass) / n if n else None
            ),
            "fraction_error_lt_overwrite_upper_bound": (
                (known_pass + int(censored.sum())) / n if n else None
            ),
        }
    return result


def _assert_tree(recorded, expected, label):
    assert isinstance(recorded, dict) and set(recorded) == set(expected), f"{label}: fields differ"
    for key, value in expected.items():
        actual = recorded[key]
        where = f"{label}.{key}"
        if isinstance(value, dict):
            _assert_tree(actual, value, where)
        elif value is None:
            assert actual is None, f"{where}: expected null"
        elif isinstance(value, bool):
            assert type(actual) is bool and actual == value, f"{where}: mismatch"
        elif isinstance(value, int):
            assert type(actual) is int and actual == value, f"{where}: mismatch"
        elif isinstance(value, float):
            assert isinstance(actual, (int, float)) and math.isfinite(actual), f"{where}: not finite"
            assert math.isclose(actual, value, rel_tol=1e-9, abs_tol=1e-8), (
                f"{where}: {actual} != {value}"
            )
        else:
            assert actual == value, f"{where}: mismatch"


def _check_rows(original, annotations, source_end_seconds):
    required_original = ("write_event_index", "next_read_event_index", "write_seconds", "target_seconds", *METHODS)
    required_annotations = (
        "write_event_index", "next_write_event_index", "overwrite_seconds",
        "overwrite_censor_lower_bound_seconds", "read_before_overwrite",
    )
    assert set(required_original).issubset(original.files)
    assert set(required_annotations).issubset(annotations.files)
    writes = np.asarray(annotations["write_event_index"])
    original_writes = np.asarray(original["write_event_index"])
    reads = np.asarray(original["next_read_event_index"])
    next_writes = np.asarray(annotations["next_write_event_index"])
    overwrite = np.asarray(annotations["overwrite_seconds"])
    lower = np.asarray(annotations["overwrite_censor_lower_bound_seconds"])
    read_before = np.asarray(annotations["read_before_overwrite"])
    targets = np.asarray(original["target_seconds"])
    lengths = {len(value) for value in (writes, original_writes, reads, next_writes,
                                        overwrite, lower, read_before, targets)}
    assert len(lengths) == 1, "Prediction and annotation row counts differ"
    assert np.issubdtype(writes.dtype, np.integer) and np.issubdtype(next_writes.dtype, np.integer)
    assert np.issubdtype(reads.dtype, np.integer)
    np.testing.assert_array_equal(writes, original_writes)
    assert np.all(writes >= 0) and np.all(reads > writes)
    assert np.all(np.diff(writes) > 0), "Holdout writes are not in source-row order"
    known = next_writes >= 0
    assert np.all(next_writes[known] > writes[known]), "A next overwrite is not after its write row"
    assert np.all(next_writes[~known] == -1), "Unknown next-overwrite index must be -1"
    assert np.isfinite(overwrite[known]).all() and np.all(overwrite[known] >= 0)
    assert np.isnan(overwrite[~known]).all(), "Censored overwrite durations must be NaN"
    assert read_before.dtype == np.dtype(bool)
    expected_read_before = ~known | (reads < next_writes)
    np.testing.assert_array_equal(read_before, expected_read_before,
                                  err_msg="Read/overwrite ordering must use source event indices")
    assert np.isfinite(lower).all() and np.all(lower >= 0)
    expected_lower = source_end_seconds - np.asarray(original["write_seconds"])
    np.testing.assert_allclose(lower, expected_lower, rtol=1e-10, atol=1e-7,
                               err_msg="Censor lower bound is not source-end minus write time")
    assert np.isfinite(targets).all() and np.all(targets >= 0)
    errors = {}
    for method in METHODS:
        prediction = np.asarray(original[method])
        assert np.isfinite(prediction).all() and np.all(prediction >= 0)
        errors[method] = np.abs(targets - prediction)
    return targets, overwrite, lower, read_before, errors


def _verify_recorded_paths(root, recorded, expected_paths, label):
    assert isinstance(recorded, dict) and recorded, f"{label} is empty"
    verify_hashes(root, recorded)
    normalized = {Path(path).as_posix() for path in recorded}
    missing = set(expected_paths) - normalized
    assert not missing, f"{label} is missing required inputs: {sorted(missing)}"


def verify_workload(workload, root=PROJECT_ROOT, output_root=OUTPUT):
    assert workload in {"usr_1", "prxy_1"}
    output = output_root / workload
    source_output = root / "results/mae-improvement" / workload
    record = json.loads((output / "summary.json").read_text())
    holdout = json.loads((source_output / "holdout.json").read_text())
    frozen = json.loads((source_output / "frozen.json").read_text())
    selection = json.loads((source_output / "selection.json").read_text())
    assert record["source"] == holdout["source"], "Recorded source differs from the original holdout"
    assert type(record["new_fits"]) is int and record["new_fits"] == 0
    assert type(holdout["new_fits"]) is int and holdout["new_fits"] == 0
    assert set(record["days"]) == {str(day) for day in DAYS}
    assert isinstance(record["elapsed_seconds"], (int, float))
    assert math.isfinite(record["elapsed_seconds"]) and record["elapsed_seconds"] >= 0
    verify_hashes(root, frozen["hashes"])

    required_inputs = {
        f"results/mae-improvement/{workload}/holdout.json",
        f"results/mae-improvement/{workload}/frozen.json",
        *(f"results/mae-improvement/{workload}/holdout-day{day}.predictions.npz" for day in DAYS),
    }
    model_paths = {selection["definitions"]["current"].get("model_path"),
                   frozen["selection"].get("model_path")}
    required_inputs.update(path for path in model_paths if path)
    _verify_recorded_paths(root, record["input_hashes"], required_inputs, "input_hashes")
    required_code = {
        "read_prediction/experiments/overwrite_comparison.py",
        "read_prediction/checks/overwrite_comparison.py",
        "docs/protocols/mae-improvement-protocol.md",
        "docs/protocols/overwrite-comparison-protocol.md",
    }
    _verify_recorded_paths(root, record["code_hashes"], required_code, "code_hashes")

    total_rows = sum(int(holdout["days"][str(day)]["coverage"]["observed_targets"]) for day in DAYS)
    if total_rows:
        with tempfile.TemporaryDirectory(prefix="overwrite-check-", dir="/tmp/opencode") as directory:
            pool = np.memmap(Path(directory) / "rows.bin", mode="w+", dtype=POOL_DTYPE, shape=(total_rows,))
            pooled_rows = pool
            offset = 0
            daily_row_counts = []
            for day in DAYS:
                key = str(day)
                original_path = source_output / f"holdout-day{day}.predictions.npz"
                annotation_path = output / f"day{day}.comparison.npz"
                original_coverage = holdout["days"][key]["coverage"]
                with np.load(original_path, allow_pickle=False) as original, \
                        np.load(annotation_path, allow_pickle=False) as annotations:
                    values = _check_rows(
                        original, annotations,
                        (holdout["source"]["last_timestamp"] - holdout["source"]["first_timestamp"])
                        / TICKS_PER_SECOND,
                    )
                    targets, overwrite, lower, read_before, errors = values
                    count = len(targets)
                    assert count > 0, f"Day {day} has no observed holdout rows"
                    assert count == original_coverage["observed_targets"]
                    assert record["days"][key]["coverage"] == original_coverage
                    expected = _independent_summary(overwrite, lower, read_before, errors)
                    _assert_tree({name: value for name, value in record["days"][key].items()
                                  if name != "coverage"}, expected, f"day {day}")
                    for method in METHODS:
                        old_metric = holdout["days"][key]["metrics"][method]
                        assert old_metric["n"] == count
                        old_mae = old_metric["mae_seconds"]
                        assert math.isclose(expected["methods"][method]["all_mae_seconds"], old_mae,
                                            rel_tol=1e-9, abs_tol=1e-8), (
                            f"Day {day} {method}: MAE differs from original holdout"
                        )
                        pooled_rows[f"{method}_error"][offset:offset + count] = errors[method]
                    pooled_rows["overwrite"][offset:offset + count] = overwrite
                    pooled_rows["lower_bound"][offset:offset + count] = lower
                    pooled_rows["read_before"][offset:offset + count] = read_before
                    offset += count
                    daily_row_counts.append(count)
                del values, errors, targets, overwrite, lower, read_before

            pooled_rows.flush()
            pooled_errors = {method: pooled_rows[f"{method}_error"] for method in METHODS}
            pooled = _independent_summary(
                pooled_rows["overwrite"], pooled_rows["lower_bound"], pooled_rows["read_before"],
                pooled_errors,
            )
            _assert_tree(record["pooled"], pooled, "pooled")
            verified_samples = record["source_samples_verified"]
            assert type(verified_samples) is int
            assert verified_samples == sum(min(64, count) for count in daily_row_counts)
    else:
        raise AssertionError("Empty holdout: this is not a full days 5--7 comparison")

    verification = {
        "workload": workload, "new_fits": 0,
        "input_hashes_verified": len(record["input_hashes"]),
        "code_hashes_verified": len(record["code_hashes"]),
        "rows_verified_by_day": {
            str(day): int(holdout["days"][str(day)]["coverage"]["observed_targets"])
            for day in DAYS
        },
        "source_samples_verified": verified_samples,
        "pooled_metrics_independently_recomputed": True,
    }
    (output / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True, choices=("usr_1", "prxy_1"))
    args = parser.parse_args(argv)
    print(json.dumps(verify_workload(args.workload), indent=2))


if __name__ == "__main__":
    main()
