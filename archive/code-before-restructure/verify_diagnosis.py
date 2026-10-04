"""Check diagnosis artifacts and the chosen log model, without any test scoring."""

import hashlib
import json
import math
from pathlib import Path

import lightgbm as lgb
import numpy as np

from verify_extended import audit_source


def main():
    root = Path(__file__).resolve().parent
    output = root / "results/prxy-validation-diagnosis"
    record = json.loads((output / "results.json").read_text())
    for name, digest in record["code_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    with np.load(output / "validation.predictions.npz") as data, np.load(root / "results/next-read-24h/prxy_1.validation.predictions.npz") as original:
        targets = data["target_seconds"]
        np.testing.assert_array_equal(targets, original["target_seconds"])
        np.testing.assert_array_equal(data["write_event_index"], original["write_event_index"])
        np.testing.assert_array_equal(data["original_log_l2"], original["lightgbm"])
        for method, metric in record["metrics"]["validation"].items():
            prediction = data[method]
            assert np.isfinite(prediction).all() and np.all(prediction >= 0)
            errors = np.abs(targets - prediction)
            checked = {
                "mae_seconds": math.fsum(errors) / len(errors),
                "median_absolute_error_seconds": float(np.median(errors)),
                "p90_absolute_error_seconds": float(np.quantile(errors, .9)),
                "rmse_seconds": math.sqrt(math.fsum(errors ** 2) / len(errors)),
                "mae_log1p_seconds": math.fsum(np.abs(np.log1p(targets) - np.log1p(prediction))) / len(errors),
            }
            assert metric["n"] == len(errors)
            for key, value in checked.items():
                assert math.isclose(value, metric[key], rel_tol=1e-10, abs_tol=1e-10)
        winner = min(record["metrics"]["validation"], key=lambda m: record["metrics"]["validation"][m]["mae_seconds"])
        assert winner == record["selected_method"]
        assert record["recipe"][winner]["log_target"]
        selected = {}
        offsets, write_indices, read_indices, predictions = original["offset_bytes"], data["write_event_index"], original["next_read_event_index"], data[winner]
        for row in np.linspace(0, len(targets) - 1, 64, dtype=int):
            selected[int(write_indices[row])] = {"offset": int(offsets[row]), "read_index": int(read_indices[row]), "target": float(targets[row]), "prediction": float(predictions[row])}
    model = lgb.Booster(model_file=str(output / f"{winner}.lightgbm.txt"))
    audited = audit_source({"source": record["source"]}, selected, model, record["recipe"][winner]["columns"])
    summary = {"validation_rows": len(targets), "methods_checked": len(record["metrics"]["validation"]),
               "selection_verified": winner, "source_histories_and_selected_predictions_audited": audited,
               "prefix_hash_independently_verified": True, "test_scored": False}
    (output / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
