"""Build the results notebook and model files from the frozen experiment results."""

import hashlib
import json
import shutil

import nbformat
from nbclient import NotebookClient

from read_prediction.paths import PROJECT_ROOT
from read_prediction.notebook_features import FEATURE_DESCRIPTION, RESULTS_NOTE
from read_prediction.notebook_format import format_literal
from read_prediction.submission_datasets import collect_datasets, dataset_selection_markdown
from read_prediction.submission_models import package_models
from read_prediction.submission_overwrite import collect_results, summary_markdown
from read_prediction.training_notebook import build_notebook


def main():
    overwrite_results = collect_results()
    overwrite_summary = summary_markdown(overwrite_results)
    dataset_results = collect_datasets()
    dataset_summary = dataset_selection_markdown(dataset_results)
    folder = PROJECT_ROOT / "submission"
    folder.mkdir(exist_ok=True)
    package_models(folder)
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
        nbformat.v4.new_markdown_cell(overwrite_summary),
        nbformat.v4.new_code_cell(
            f"overwrite_results = {format_literal(overwrite_results)}\n\n"
            "# The embedded values make this notebook independent of the research repo.\n"
            "for row in overwrite_results['selected_results']:\n"
            "    metric = row['observed_read']\n"
            "    n = row['observed_reads']\n"
            "    assert abs(row['pass_lower'] - row['confirmed_pass_count'] / n) < 1e-10\n"
            "    assert abs(row['pass_upper'] - (row['confirmed_pass_count'] + row['unknown_pass_count']) / n) < 1e-10\n"
            "    if metric['status'] == 'passed':\n"
            "        assert metric['mae_seconds'] < metric['mean_overwrite_lower_seconds']\n"
            "    if row['ninety_percent_status'] == 'failed':\n"
            "        assert row['pass_upper'] < 0.90\n"
            "print('Embedded mean-overwrite and 90% results checked:', len(overwrite_results['selected_results']), 'rows')"
        ),
        nbformat.v4.new_markdown_cell(dataset_summary),
        nbformat.v4.new_code_cell(
            f"dataset_comparison = {format_literal(dataset_results)}\n\n"
            "# The embedded screening snapshot is independent of the research repo.\n"
            "assert len(dataset_comparison['traces']) == 36\n"
            "assert dataset_comparison['failed_traces'] == 28\n"
            "assert dataset_comparison['selected'] == ['proj_1', 'prn_1']\n"
            "assert len(dataset_comparison['eligible_new_workloads']) == 6\n"
            "assert all(row['basic_eligible'] for row in dataset_comparison['range_confirmation'])\n"
            "assert all(entry['requested_hours'] == 168 for entry in dataset_comparison['selection_trace_windows'].values())\n"
            "print('Dataset screening snapshot checked:', len(dataset_comparison['traces']), 'traces,',\n"
            "      dataset_comparison['failed_traces'], 'rejected,', len(dataset_comparison['eligible_new_workloads']), 'new candidates')"
        ),
        nbformat.v4.new_markdown_cell(
            "## Validation and individual days: both criteria\n\n"
            "These predictors are selected by validation MAE. Mean overwrite time is represented by its lower bound; "
            "an undetermined status does not mean failure. The error < overwrite fraction uses the same observed-Read records."
        ),
        nbformat.v4.new_code_cell(
            "from IPython.display import Markdown, display\n\n"
            "table = ['| Workload / rule | Window | MAE, s | Mean overwrite ≥, s | MAE < mean | error < overwrite | ≥90% |',\n"
            "         '|---|---|---:|---:|---|---:|---|']\n"
            "mean_status = {'passed': 'proven', 'failed': 'no', 'undetermined': 'undetermined'}\n"
            "pass_status = {'passed': 'yes', 'failed': 'no', 'undetermined': 'undetermined'}\n"
            "for row in overwrite_results['selected_results']:\n"
            "    metric = row['observed_read']\n"
            "    table.append(f\"| {row['workload']} / {row['rule']} | {row['window']} | {metric['mae_seconds']:.2f} | {metric['mean_overwrite_lower_seconds']:.2f} | {mean_status[metric['status']]} | {row['pass_lower']:.2%}–{row['pass_upper']:.2%} | {pass_status[row['ninety_percent_status']]} |\")\n"
            "display(Markdown('\\n'.join(table)))"
        ),
        nbformat.v4.new_markdown_cell(
            "## Selected predictors: prn_1 / proj_1\n\n"
            "`predict.py` loads the packaged models and checks their fingerprints. "
            "prn_1 uses 25% log-L2 + 75% raw-L1 **after conversion to seconds**; "
            "proj_1 uses training-only per-address medians with a global-median fallback.\n\n"
            "Input columns (raw, **do not apply log1p yourself**): offset bytes, size bytes, "
            "prior Read count, prior Write count, seconds since last Read, seconds since last Write, "
            "last completed Read-to-Read interval. Missing history is NaN. "
            "History is keyed by the same starting Offset for both rules, available before the current Write. "
            "The labeling rules differ, not the feature history. See models.json."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import importlib.util\n"
            "import numpy as np\n\n"
            "model_directory = Path('submission') if Path('submission/models.json').is_file() else Path('.')\n"
            "spec = importlib.util.spec_from_file_location('submission_predict', model_directory / 'predict.py')\n"
            "predict_module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(predict_module)\n"
            "selected_predictor = predict_module.SelectedPredictor(model_directory)\n\n"
            "# Illustrative input, not a measured evaluation sample.\n"
            "raw_features = [[4096, 512, 0, 0, np.nan, np.nan, np.nan]]\n"
            "for workload in ('prn_1', 'proj_1'):\n"
            "    for rule in ('same_start', 'range'):\n"
            "        prediction = selected_predictor.predict_seconds(workload, rule, raw_features)\n"
            "        assert np.isfinite(prediction).all() and (prediction >= 0).all()\n"
            "        print(workload, rule, 'predicted seconds:', prediction)"
        ),
        nbformat.v4.new_markdown_cell(
            "## Earlier frozen-model experiment: usr_1 / prxy_1\n\n"
            "The inference code and two model files below belong to the earlier days 2–4 experiment. "
            "The proj_1/prn_1 results above use different predictors and days 5–7; "
            "their recorded metrics are embedded for review."
        ),
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
    nbformat.write(build_notebook(), folder / "training.ipynb")
    (folder / "overwrite-results.json").write_text(json.dumps(overwrite_results, indent=2, ensure_ascii=False) + "\n")
    (folder / "dataset-comparison.json").write_text(json.dumps(dataset_results, indent=2, ensure_ascii=False) + "\n")
    (folder / "README.md").write_text(
        overwrite_summary + "\n" + dataset_summary + "\n## Submission contents\n\n"
        "- `results.ipynb` — both new criteria, the 36-trace dataset screening and the earlier usr_1/prxy_1 comparison; already executed, with no raw traces needed for viewing.\n"
        "- `overwrite-results.json` — a portable snapshot of verified metrics, daily results and fingerprints.\n"
        "- `dataset-comparison.json` — the 36-trace screening snapshot and the reasons proj_1/prn_1 were selected.\n"
        "- `predict.py` and `models.json` — selected predictor loading, feature order, mixture weights and fingerprints.\n"
        "- `prn_1.{same_start,range}.{log_l2,raw_l1}.lightgbm.txt` — four models, two for each mixture.\n"
        "- `proj_1.{same_start,range}.address_medians.json` — selected address medians; the global fallback is specified in models.json.\n"
        "- `training.ipynb` — standalone prn_1/proj_1 training on days 1–3, selection on validation day 4 and export to trained/long-history-retrain; requires DATASET containing msr-cambridge1.tar.\n"
        "- `usr_1.lightgbm.txt`, `prxy_1.lightgbm.txt` — earlier frozen models for the legacy inference section in results.ipynb.\n\n"
        "Build from the research project root: `.venv/bin/python -m read_prediction.submission`.\n\n"
        "Verify the metric snapshot and notebook execution outside the repository: `.venv/bin/python -m read_prediction.checks.submission`.\n"
        "Test the training notebook on an artificial four-day trace: `.venv/bin/python -m read_prediction.checks.training_notebook`.\n"
    )
    print("Saved submission notebook, metrics, selected prn_1/proj_1 predictors and earlier frozen models.")


if __name__ == "__main__":
    main()
