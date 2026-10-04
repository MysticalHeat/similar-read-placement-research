"""Verify saved pilot artifacts without retraining, then execute report notebook."""

import csv
import json
import math

import lightgbm as lgb
import nbformat
from nbclient import NotebookClient

from read_prediction.paths import NOTEBOOKS, PROJECT_ROOT
from read_prediction.provenance import check_recorded_hash


def main():
    root = PROJECT_ROOT
    output = root / "results/next-read-pilot"
    record = json.loads((output / "results.json").read_text())
    check_recorded_hash("next_read.py", record["code_sha256"])
    checked_rows = 0
    for workload, result in record["results"].items():
        model = lgb.Booster(model_file=str(output / f"{workload}.lightgbm.txt"))
        assert model.feature_name() == result["feature_names"]
        for split in ["validation", "test"]:
            coverage = result["split_coverage"][split]
            assert coverage["writes"] == coverage["observed_targets"] + coverage["right_censored"]
            with (output / f"{workload}.{split}.predictions.csv").open() as file:
                rows = list(csv.DictReader(file))
            assert len(rows) == coverage["observed_targets"]
            previous_index = -1
            for row in rows:
                index = int(row["write_event_index"])
                write = float(row["write_seconds"])
                read = float(row["next_read_seconds"])
                target = float(row["target_seconds"])
                assert previous_index < index < coverage["end_event_exclusive"]
                assert index >= coverage["start_event"]
                assert coverage["start_seconds"] <= write <= read <= coverage["last_event_seconds"]
                assert math.isclose(read - write, target, abs_tol=1e-9, rel_tol=1e-10)
                previous_index = index
            for method, metric in result["metrics"][split].items():
                if not rows:
                    assert metric is None
                    continue
                errors, log_errors = [], []
                for row in rows:
                    target, prediction = float(row["target_seconds"]), float(row[method])
                    assert math.isfinite(prediction) and prediction >= 0
                    errors.append(abs(target - prediction))
                    log_errors.append(abs(math.log1p(target) - math.log1p(prediction)))
                assert metric["n"] == len(rows)
                assert math.isclose(math.fsum(errors) / len(rows), metric["mae_seconds"], rel_tol=1e-10)
                assert math.isclose(math.fsum(log_errors) / len(rows), metric["mae_log1p_seconds"], rel_tol=1e-10)
            checked_rows += len(rows)
    notebook = nbformat.read(NOTEBOOKS / "history/next_read_prediction.ipynb", as_version=4)
    nbformat.validate(notebook)
    NotebookClient(notebook, timeout=60, kernel_name="python3", resources={"metadata": {"path": str(root / "notebooks/history")}}).execute()
    executed = sum(cell.cell_type == "code" and cell.execution_count is not None for cell in notebook.cells)
    print(f"Verified {checked_rows:,} prediction rows, metrics, split bounds, model files and code hash.")
    print(f"Notebook executed successfully: {executed} code cells; no retraining.")


if __name__ == "__main__":
    main()
