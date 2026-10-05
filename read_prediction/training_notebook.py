"""Build a standalone training notebook using the frozen models' recipes."""

import inspect
import json

import nbformat

from read_prediction.extended import EVENT_DTYPE
from read_prediction.pipeline import FEATURE_NAMES, TICKS_PER_SECOND, TRACE_SOURCES
from read_prediction.notebook_training import (
    fit_model,
    load_events,
    make_split_masks,
    predict_validation,
    prepare_samples,
    train_workload,
)
from read_prediction.notebook_features import FEATURE_DESCRIPTION
from read_prediction.notebook_format import format_literal
from read_prediction.paths import PROJECT_ROOT


def function_source(function):
    return inspect.getsource(function).strip()


def main():
    configurations = {}
    for workload in ("usr_1", "prxy_1"):
        previous = json.loads((PROJECT_ROOT / "results/next-read-24h" / f"{workload}.result.json").read_text())
        frozen = json.loads((PROJECT_ROOT / "results/final-study" / workload / "frozen.json").read_text())
        configurations[workload] = {
            "train_end": previous["split_coverage"]["train"]["end_event_exclusive"],
            "validation_end": previous["split_coverage"]["validation"]["end_event_exclusive"],
            "columns": frozen["selection"]["columns"],
            "params": previous["model_params"],
        }
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(FEATURE_DESCRIPTION),
        nbformat.v4.new_code_cell(
            "from array import array\n"
            "from pathlib import Path\n"
            "from tempfile import TemporaryDirectory\n"
            "import gzip\n"
            "import tarfile\n\n"
            "import lightgbm as lgb\n"
            "import numpy as np\n\n"
            "notebook_directory = Path('.')\n"
            "if Path('submission/training.ipynb').is_file():\n"
            "    notebook_directory = Path('submission')\n"
            "notebook_directory = notebook_directory.resolve()\n\n"
            "DATASET = notebook_directory.parent / 'dataset'\n"
            "OUTPUT = notebook_directory / 'trained'"
        ),
        nbformat.v4.new_code_cell(
            f"TICKS_PER_SECOND = {TICKS_PER_SECOND:_}\n\n"
            f"FEATURE_NAMES = {format_literal(FEATURE_NAMES)}\n\n"
            f"TRACE_SOURCES = {format_literal(TRACE_SOURCES)}\n\n"
            f"EVENT_DTYPE = np.dtype({format_literal(EVENT_DTYPE.descr)})\n\n"
            f"model_configurations = {format_literal(configurations)}"
        ),
        *[nbformat.v4.new_code_cell(function_source(function)) for function in (
            load_events, prepare_samples, make_split_masks,
            fit_model, predict_validation, train_workload,
        )],
        nbformat.v4.new_code_cell(
            "OUTPUT.mkdir(parents=True, exist_ok=True)\n"
            "training_results = []\n\n"
            "for workload, configuration in model_configurations.items():\n"
            "    result = train_workload(workload, configuration, DATASET, OUTPUT)\n"
            "    training_results.append(result)"
        ),
        nbformat.v4.new_code_cell(
            "header = (\n"
            "    f'{\"trace\":<8} {\"train_n\":>10} '\n"
            "    f'{\"validation_n\":>13} {\"validation_mae_s\":>18}'\n"
            ")\n"
            "print(header)\n\n"
            "for result in training_results:\n"
            "    print(\n"
            "        f'{result[\"workload\"]:<8} '\n"
            "        f'{result[\"training_samples\"]:>10,} '\n"
            "        f'{result[\"validation_samples\"]:>13,} '\n"
            "        f'{result[\"validation_mae_seconds\"]:>18.2f}'\n"
            "    )"
        ),
    ], metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})
    folder = PROJECT_ROOT / "submission"
    folder.mkdir(exist_ok=True)
    nbformat.write(notebook, folder / "training.ipynb")
    print("Saved submission/training.ipynb.")


if __name__ == "__main__":
    main()
