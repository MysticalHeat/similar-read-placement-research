"""Independent day-two artifact checks and selected source-history audit."""

import hashlib
import json
import math
from pathlib import Path

import lightgbm as lgb
import numpy as np

from verify_extended import audit_source


def main():
    root = Path(__file__).resolve().parent
    output = root / "results/prxy-day2"
    result = json.loads((output / "results.json").read_text())
    frozen = json.loads((output / "frozen-models.json").read_text())
    assert result["fits"] == 0 and frozen == result["frozen"]
    for name, digest in result["code_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    selection_path = root / "results/prxy-validation-diagnosis/selected-model.json"
    assert hashlib.sha256(selection_path.read_bytes()).hexdigest() == frozen["selection_hash"]
    model_path = root / "results/prxy-validation-diagnosis/no_counts_log_l2.lightgbm.txt"
    assert hashlib.sha256(model_path.read_bytes()).hexdigest() == frozen["model_hashes"]["selected_no_counts"]
    original_path = root / "results/next-read-24h/prxy_1.lightgbm.txt"
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == frozen["model_hashes"]["original_all_features"]
    baseline = json.loads((output / "frozen-baselines.json").read_text())
    coverage = result["coverage"]
    assert coverage["writes"] == coverage["observed_targets"] + coverage["right_censored"]
    with np.load(output / "predictions.npz") as data:
        writes, reads = data["write_event_index"], data["next_read_event_index"]
        write_times, read_times = data["write_seconds"], data["next_read_seconds"]
        targets, offsets = data["target_seconds"], data["offset_bytes"]
        assert len(targets) == coverage["observed_targets"]
        assert np.all(np.diff(writes) > 0)
        assert np.all((writes >= coverage["start_event"]) & (reads > writes) & (reads < coverage["end_event_exclusive"]))
        assert np.all((write_times >= 24 * 3600) & (write_times < 48 * 3600) & (read_times < 48 * 3600))
        np.testing.assert_allclose(read_times - write_times, targets, atol=1e-9, rtol=1e-10)
        np.testing.assert_array_equal(data["global_median"], np.full(len(targets), baseline["global_median_seconds"]))
        address_predictions = np.fromiter((baseline["address_medians_seconds"].get(str(int(a)), baseline["global_median_seconds"]) for a in offsets), dtype=float, count=len(offsets))
        np.testing.assert_array_equal(address_predictions, data["address_median"])
        method_predictions = {name: data[name] for name in result["metrics"]}
        for name, metric in result["metrics"].items():
            predictions = method_predictions[name]
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
                assert math.isclose(value, metric[key], rel_tol=1e-10, abs_tol=1e-10)
        selected_predictions = data["selected_no_counts"]
        selected = {int(writes[i]): {"offset": int(offsets[i]), "read_index": int(reads[i]),
                                    "target": float(targets[i]), "prediction": float(selected_predictions[i])}
                    for i in np.linspace(0, len(writes) - 1, 64, dtype=int)}
        phase_checks = {}
        phase_total = 0
        for hour in range(24, 48):
            mask = (write_times >= hour * 3600) & (write_times < (hour + 1) * 3600)
            phase_total += int(mask.sum())
            for name, metric in result["hourly_metrics"][str(hour)].items():
                if not mask.any():
                    assert metric is None
                    continue
                assert metric["n"] == int(mask.sum())
                mae = math.fsum(np.abs(targets[mask] - method_predictions[name][mask])) / int(mask.sum())
                assert math.isclose(mae, metric["mae_seconds"], rel_tol=1e-10)
            phase_checks[str(hour)] = result["hourly_metrics"][str(hour)]["selected_no_counts"]["mae_seconds"] < result["hourly_metrics"][str(hour)]["address_median"]["mae_seconds"]
        assert phase_total == len(targets)
        rare_errors = {
            name: {"abs_error_over_60s_fraction": float((np.abs(targets - method_predictions[name]) > 60).mean()),
                   "abs_error_over_600s_fraction": float((np.abs(targets - method_predictions[name]) > 600).mean()),
                   "p99_abs_error_seconds": float(np.quantile(np.abs(targets - method_predictions[name]), .99))}
            for name in ("address_median", "selected_no_counts")
        }
    model = lgb.Booster(model_file=str(model_path))
    audited = audit_source(result, selected, model, columns=frozen["feature_indices"])
    verification = {"rows_verified": len(targets), "methods_verified": 4, "fits": 0,
                    "model_and_selection_hashes_unchanged": True,
                    "source_samples_audited": audited, "prefix_hash_independently_verified": True,
                    "hours_with_smaller_selected_mae": sum(phase_checks.values()),
                    "all_hour_mae_verified": True, "rare_error_diagnostics": rare_errors}
    (output / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
