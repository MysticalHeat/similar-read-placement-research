"""Verify complete-study predictions, frozen choices and independent source samples."""

import hashlib
import json
import math
from pathlib import Path

import lightgbm as lgb
import numpy as np

from verify_extended import audit_source

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results/final-study"


def check_metrics(targets, predictions, metric):
    if not len(targets):
        assert metric is None
        return
    assert metric["n"] == len(targets)
    assert np.isfinite(predictions).all() and np.all(predictions >= 0)
    errors = np.abs(targets - predictions)
    calculated = {
        "mae_seconds": math.fsum(errors) / len(errors),
        "median_absolute_error_seconds": float(np.median(errors)),
        "p90_absolute_error_seconds": float(np.quantile(errors, .9)),
        "rmse_seconds": math.sqrt(math.fsum(errors ** 2) / len(errors)),
        "mae_log1p_seconds": math.fsum(np.abs(np.log1p(targets) - np.log1p(predictions))) / len(errors),
    }
    for key, value in calculated.items():
        assert math.isclose(value, metric[key], rel_tol=1e-10, abs_tol=1e-9)


def check_hashes(mapping):
    for path, digest in mapping.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path


def sample_records(data, method):
    indices, reads, offsets = data["write_event_index"], data["next_read_event_index"], data["offset_bytes"]
    targets, predictions = data["target_seconds"], data[method]
    return {int(indices[i]): {"offset": int(offsets[i]), "read_index": int(reads[i]),
                             "target": float(targets[i]), "prediction": float(predictions[i])}
            for i in np.unique(np.linspace(0, len(indices) - 1, min(64, len(indices)), dtype=int))} if len(indices) else {}


def main():
    selection = json.loads((OUTPUT / "usr-selection/selection.json").read_text())
    check_hashes(selection["code_hashes"])
    with np.load(OUTPUT / "usr-selection/validation.predictions.npz") as validation:
        for method, metric in selection["metrics"].items():
            check_metrics(validation["target_seconds"], validation[method], metric)
        assert selection["method"] == min(selection["metrics"], key=lambda m: selection["metrics"][m]["mae_seconds"])
        validation_samples = sample_records(validation, selection["method"])
    verified = {"usr_selection_methods_checked": 7, "usr_selection_verified": selection["method"], "workloads": {}}
    for workload in ("usr_1", "prxy_1"):
        folder = OUTPUT / workload
        result = json.loads((folder / "results.json").read_text())
        check_hashes(result["frozen"]["hashes"])
        check_hashes(result["baseline_pin"]["code_hashes"])
        pin = json.loads((OUTPUT / f"{workload}.baseline-pin.json").read_text())
        assert pin == result["baseline_pin"] and result["baseline_frozen_before_evaluation"]
        baseline = json.loads((folder / "baselines.json").read_text())
        assert hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest() == pin["baseline_values_sha256"]
        assert hashlib.sha256((ROOT / pin["baseline_path"]).read_bytes()).hexdigest() == pin["baseline_file_sha256"]
        assert result["frozen"]["new_fits"] == 0
        samples, day_counts = {}, {}
        if workload == "usr_1":
            samples.update(validation_samples)
        total = 0
        for day in (2, 3, 4):
            entry = result["days"][str(day)]
            coverage = entry["coverage"]
            assert coverage["writes"] == coverage["observed_targets"] + coverage["right_censored"]
            expected_role = "previously_evaluated_replication" if workload == "prxy_1" and day == 2 else "new_future_period"
            assert entry["evaluation_role"] == expected_role
            with np.load(folder / f"day{day}.predictions.npz") as data:
                writes, reads = data["write_event_index"], data["next_read_event_index"]
                write_times, read_times = data["write_seconds"], data["next_read_seconds"]
                targets, offsets = data["target_seconds"], data["offset_bytes"]
                assert len(writes) == coverage["observed_targets"]
                assert np.all(np.diff(writes) > 0)
                assert np.all((writes >= coverage["start_event"]) & (writes < coverage["end_event_exclusive"]))
                assert np.all((reads > writes) & (reads < coverage["end_event_exclusive"]))
                assert np.all((write_times >= (day - 1) * 86400) & (read_times < day * 86400))
                np.testing.assert_allclose(read_times - write_times, targets, atol=1e-9, rtol=1e-10)
                np.testing.assert_array_equal(data["global_median"], np.full(len(targets), baseline["global_median_seconds"]))
                expected = np.fromiter((baseline["address_medians_seconds"].get(str(int(a)), baseline["global_median_seconds"]) for a in offsets), dtype=float, count=len(offsets))
                np.testing.assert_array_equal(data["address_median"], expected)
                for method, metric in entry["metrics"].items():
                    check_metrics(targets, data[method], metric)
                samples.update(sample_records(data, "selected"))
                day_counts[str(day)] = len(writes)
                total += len(writes)
        frozen = result["frozen"]["selection"]
        assert frozen["kind"] == "model" and frozen["log_target"]
        model = lgb.Booster(model_file=str(ROOT / frozen["model_path"]))
        audited = audit_source(result, samples, model, columns=frozen["columns"])
        verified["workloads"][workload] = {"prediction_rows_verified": total, "days": day_counts,
                                          "source_samples_audited": audited,
                                          "source_prefix_hash_independently_verified": True,
                                          "frozen_model_and_baseline_verified": True}
        print(f"{workload}: verified {total:,} future rows, {audited} source histories", flush=True)
    (OUTPUT / "verification.json").write_text(json.dumps(verified, indent=2) + "\n")
    print("Final study verification passed; no fits.")


if __name__ == "__main__":
    main()
