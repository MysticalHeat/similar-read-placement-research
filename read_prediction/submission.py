"""Build the results notebook and model files from the frozen experiment results."""

import hashlib
import json
import shutil

import nbformat
from nbclient import NotebookClient

from read_prediction.paths import PROJECT_ROOT
from read_prediction.notebook_features import FEATURE_DESCRIPTION, RESULTS_NOTE
from read_prediction.notebook_format import format_literal


def main():
    folder = PROJECT_ROOT / "submission"
    folder.mkdir(exist_ok=True)
    rows, columns = [], {}
    for workload in ("usr_1", "prxy_1"):
        result = json.loads((PROJECT_ROOT / "results/final-study" / workload / "results.json").read_text())
        selection = result["frozen"]["selection"]
        columns[workload] = selection["columns"]
        source = PROJECT_ROOT / selection["model_path"]
        expected = result["frozen"]["hashes"][selection["model_path"]]
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen model fingerprint mismatch: {workload}")
        shutil.copyfile(source, folder / f"{workload}.lightgbm.txt")
        for day, entry in result["days"].items():
            rows.append({
                "workload": workload,
                "day": int(day),
                "observed_intervals": entry["coverage"]["observed_targets"],
                "coverage_fraction": entry["coverage"]["observed_fraction"],
                "baseline_mae_seconds": entry["metrics"]["address_median"]["mae_seconds"],
                "model_mae_seconds": entry["metrics"]["selected"]["mae_seconds"],
                "evaluation_role": entry["evaluation_role"],
            })

    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(FEATURE_DESCRIPTION),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n\n"
            "import lightgbm as lgb\n"
            "import numpy as np\n\n"
            "model_directory = Path('.')\n"
            "if Path('submission/usr_1.lightgbm.txt').is_file():\n"
            "    model_directory = Path('submission')\n\n"
            "models = {}\n"
            "for workload in ('usr_1', 'prxy_1'):\n"
            "    model_path = model_directory / f'{workload}.lightgbm.txt'\n"
            "    models[workload] = lgb.Booster(model_file=str(model_path))"
        ),
        nbformat.v4.new_code_cell(
            "{workload: model.feature_name() for workload, model in models.items()}"
        ),
        nbformat.v4.new_code_cell(
            f"FEATURE_COLUMNS = {format_literal(columns)}\n\n\n"
            "def predict_seconds(workload, raw_features):\n"
            "    raw_features = np.atleast_2d(np.asarray(raw_features, dtype=float))\n"
            "    log_features = np.log1p(raw_features)\n"
            "    selected_features = log_features[:, FEATURE_COLUMNS[workload]]\n\n"
            "    log_predictions = models[workload].predict(selected_features, num_threads=2)\n"
            "    return np.maximum(0, np.expm1(log_predictions))"
        ),
        nbformat.v4.new_code_cell(
            f"recorded_results = {format_literal(rows)}"
        ),
        nbformat.v4.new_code_cell(
            "header = (\n"
            "    f'{\"trace\":<8} {\"day\":>3} {\"n\":>9} {\"coverage_%\":>11} '\n"
            "    f'{\"baseline_mae_s\":>15} {\"model_mae_s\":>12}  {\"evaluation_role\"}'\n"
            ")\n"
            "print(header)\n\n"
            "for result in recorded_results:\n"
            "    coverage_percent = 100 * result['coverage_fraction']\n"
            "    print(\n"
            "        f'{result[\"workload\"]:<8} {result[\"day\"]:>3} '\n"
            "        f'{result[\"observed_intervals\"]:>9,} {coverage_percent:>11.2f} '\n"
            "        f'{result[\"baseline_mae_seconds\"]:>15.2f} '\n"
            "        f'{result[\"model_mae_seconds\"]:>12.2f}  '\n"
            "        f'{result[\"evaluation_role\"]}'\n"
            "    )"
        ),
        nbformat.v4.new_markdown_cell(RESULTS_NOTE),
    ], metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})
    NotebookClient(notebook, timeout=60, kernel_name="python3",
                   resources={"metadata": {"path": str(folder)}}).execute()
    nbformat.write(notebook, folder / "results.ipynb")
    print("Saved submission/results.ipynb and both frozen models.")


if __name__ == "__main__":
    main()
