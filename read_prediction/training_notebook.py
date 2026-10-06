"""Build standalone training for the latest prn_1/proj_1 validation-MAE recipe."""

import inspect

import nbformat

from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.prxy0_check import local_labels
from read_prediction.notebook_format import format_literal
from read_prediction.notebook_selected_training import (
    MIX_WEIGHTS, PARAMETERS, TRACE_SOURCES, export_predictors, load_four_days,
    smoke_events, train_events, train_latest, validation_metrics,
)
from read_prediction.notebook_training import prepare_samples
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import FEATURE_NAMES, TICKS_PER_SECOND, fit_baselines
from read_prediction.range_label import (
    BLOCK, _INDEX_BITS, _INDEX_MASK, _INDEX_MOD, _expand_blocks, _keys,
    first_future_intersecting, first_future_same_start, label_writes, require_grid,
)
from read_prediction.submission_models import RAW_FEATURES


def function_source(function):
    return inspect.getsource(function).strip()


def build_notebook():
    inference_source = (PROJECT_ROOT / "read_prediction/submission_predict.py").read_text()
    functions = (require_grid, _expand_blocks, _keys, first_future_intersecting,
                 first_future_same_start, label_writes, local_labels, prepare_samples,
                 fit_baselines, load_four_days, validation_metrics, train_events,
                 train_latest, export_predictors, smoke_events)
    return nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# Training the latest models: prn_1 / proj_1\n\n"
            "Standalone notebook: preparation and labeling code is embedded; the read_prediction package is not required. "
            "Full training requires numpy, lightgbm and msr-cambridge1.tar in DATASET.\n\n"
            "- Train: days 1–3 `[0, 72h)`; validation: day 4 `[72h, 96h)`. Labels in each window cannot use events after its end.\n"
            "- same_start requires matching starting Offsets; range requires overlapping byte ranges.\n"
            "- Train log-L2 on log1p(seconds) and raw-L1 on seconds for both rules. All seven causal features are transformed with log1p.\n"
            "- proj_1 candidates: log-L2/raw-L1/per-address median. prn_1 additionally includes three mixtures: 75/25, 50/50, 25/75, after converting predictions to seconds.\n"
            "- Select minimum validation MAE, breaking ties by method name. Pass fraction does not constrain selection. Models are not refitted on validation.\n\n"
            "The published run selected 25% log-L2 + 75% raw-L1 for prn_1 and the per-address median for proj_1. "
            "This notebook repeats selection; future days 5–7 are not loaded here. "
            "The development-day 5–7 conclusions about MAE < mean overwrite and failure to reach ≥90% are in results.ipynb."
        ),
        nbformat.v4.new_code_cell(
            "from array import array\n"
            "from pathlib import Path\n"
            "from tempfile import TemporaryDirectory\n"
            "import gzip\nimport hashlib\nimport importlib.util\nimport json\nimport tarfile\n\n"
            "import lightgbm as lgb\nimport numpy as np\n\n"
            "notebook_directory = Path('submission') if Path('submission/training.ipynb').is_file() else Path('.')\n"
            "notebook_directory = notebook_directory.resolve()\n"
            "DATASET = notebook_directory.parent / 'dataset'\n"
            "OUTPUT = notebook_directory / 'trained' / 'long-history-retrain'\n"
            "WORKLOADS = ('prn_1', 'proj_1')\n"
            "SMOKE_TEST = False  # True: artificial trace only, not measured results.\n"
            "print('DATASET:', DATASET, '\\nOUTPUT:', OUTPUT)",
            metadata={"tags": ["training-configuration"]},
        ),
        nbformat.v4.new_markdown_cell(
            "## Seven features available at Write time\n\n"
            "Offset (bytes), size (bytes), previous Read/Write counts, seconds since the last Read/Write, "
            "and the last completed Read-to-Read interval. History is keyed by the same starting Offset and is available before the current Write, "
            "including under the range rule. Missing history is NaN. ResponseTime and future events are not features. "
            "Writes without a Read before the end of their own window are excluded from regression; coverage is reported separately."
        ),
        nbformat.v4.new_code_cell(
            f"TICKS_PER_SECOND = TICKS = {TICKS_PER_SECOND:_}\n"
            f"BLOCK = {BLOCK}\n_INDEX_BITS = {_INDEX_BITS}\n_INDEX_MASK = {_INDEX_MASK}\n_INDEX_MOD = {_INDEX_MOD}\n"
            f"FEATURE_NAMES = {format_literal(FEATURE_NAMES)}\n"
            f"RAW_FEATURES = {format_literal(RAW_FEATURES)}\n"
            f"EVENT_DTYPE = np.dtype({format_literal(EVENT_DTYPE.descr)})\n"
            f"TRACE_SOURCES = {format_literal(TRACE_SOURCES)}\n"
            f"PARAMETERS = {format_literal(PARAMETERS)}\n"
            f"MIX_WEIGHTS = {format_literal(MIX_WEIGHTS)}\n"
            f"INFERENCE_SOURCE = {inference_source!r}"
        ),
        *[nbformat.v4.new_code_cell(function_source(function)) for function in functions],
        nbformat.v4.new_markdown_cell(
            "## Training and export\n\n"
            "Choose a new OUTPUT directory: an existing bundle is not overwritten. Outputs include LightGBM models, "
            "address medians, training-results.json with validation metrics, models.json with the selected method and "
            "fingerprints, and predict.py for inference. For unknown overwrite times, remaining observation time is used only as "
            "a lower bound. SMOKE_TEST checks execution on artificial data and is not evidence of predictive quality."
        ),
        nbformat.v4.new_code_cell(
            "OUTPUT.parent.mkdir(parents=True, exist_ok=True)\n"
            "OUTPUT.mkdir(exist_ok=False)\n"
            "training_results = {}\n"
            "for workload in WORKLOADS:\n"
            "    if SMOKE_TEST:\n"
            "        training_results[workload] = train_events(smoke_events(), workload, OUTPUT, PARAMETERS, MIX_WEIGHTS)\n"
            "    else:\n"
            "        training_results[workload] = train_latest(workload, DATASET, OUTPUT, PARAMETERS, MIX_WEIGHTS)\n"
            "mode = 'artificial_smoke' if SMOKE_TEST else 'real_four_day'\n"
            "exported = export_predictors(training_results, OUTPUT, MIX_WEIGHTS, INFERENCE_SOURCE, mode)\n"
            "print('Mode:', 'ARTIFICIAL SMOKE TEST' if SMOKE_TEST else 'REAL FOUR-DAY TRAINING')\n"
            "print('Exported predictors:', json.dumps(exported['predictors'], indent=2))"
        ),
        nbformat.v4.new_code_cell(
            "from IPython.display import Markdown, display\n\n"
            "rows = ['| Workload / rule | Candidate | Train N | Validation N | MAE, s | Mean overwrite ≥, s | Pass lower–upper | Selected |',\n"
            "        '|---|---|---:|---:|---:|---:|---:|---|']\n"
            "for workload, rules in training_results.items():\n"
            "    for rule, result in rules.items():\n"
            "        for method, metric in result['validation'].items():\n"
            "            rows.append(f\"| {workload} / {rule} | {method} | {result['training_samples']} | {metric['n']} | {metric['mae_seconds']:.2f} | {metric['mean_overwrite_lower_seconds']:.2f} | {metric['pass_lower']:.2%}–{metric['pass_upper']:.2%} | {method == result['selected']} |\")\n"
            "display(Markdown('\\n'.join(rows)))"
        ),
        nbformat.v4.new_code_cell(
            "spec = importlib.util.spec_from_file_location('trained_predictor', OUTPUT / 'predict.py')\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "predictor = module.SelectedPredictor(OUTPUT)\n"
            "raw_features = [[4096, 512, 0, 0, np.nan, np.nan, np.nan]]\n"
            "for workload in WORKLOADS:\n"
            "    for rule in ('same_start', 'range'):\n"
            "        seconds = predictor.predict_seconds(workload, rule, raw_features)\n"
            "        assert np.isfinite(seconds).all() and (seconds >= 0).all()\n"
            "        print(workload, rule, 'illustrative prediction, seconds:', seconds)"
        ),
    ], metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})


def main():
    folder = PROJECT_ROOT / "submission"
    folder.mkdir(exist_ok=True)
    notebook = build_notebook()
    nbformat.validate(notebook)
    nbformat.write(notebook, folder / "training.ipynb")
    print("Saved standalone submission/training.ipynb for prn_1/proj_1.")


if __name__ == "__main__":
    main()
