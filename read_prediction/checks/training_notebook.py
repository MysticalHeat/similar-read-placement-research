"""Execute the standalone training notebook on an artificial four-day trace."""

from tempfile import TemporaryDirectory

import nbformat
from nbclient import NotebookClient

from read_prediction.paths import PROJECT_ROOT


def verify_training_notebook(folder):
    notebook = nbformat.read(folder / "training.ipynb", as_version=4)
    nbformat.validate(notebook)
    configurations = [cell for cell in notebook.cells if "training-configuration" in cell.metadata.get("tags", [])]
    assert len(configurations) == 1
    with TemporaryDirectory(prefix="training-notebook-check-", dir="/tmp/opencode") as directory:
        configurations[0].source += f"\nSMOKE_TEST = True\nOUTPUT = Path({directory!r}) / 'trained'\n"
        notebook.cells.append(nbformat.v4.new_code_cell(
            "assert set(training_results) == {'prn_1', 'proj_1'}\n"
            "for workload, rules in training_results.items():\n"
            "    assert set(rules) == {'same_start', 'range'}\n"
            "    for rule, result in rules.items():\n"
            "        expected = min(result['validation'], key=lambda method: (result['validation'][method]['mae_seconds'], method))\n"
            "        assert expected == result['selected']\n"
            "        assert result['training_samples'] > 0\n"
            "        assert len(result['validation']) == (6 if workload == 'prn_1' else 3)\n"
            "        assert predictor.metadata['predictors'][workload][rule]['method'] == expected\n"
            "assert (OUTPUT / 'training-results.json').is_file()\n"
            "print('Training smoke test: four rules, eight LightGBM models, export and inference passed')"
        ))
        NotebookClient(notebook, timeout=120, kernel_name="python3",
                       resources={"metadata": {"path": directory}}).execute()
    print("Training notebook smoke test passed outside the repository; no real-trace retraining")


def main():
    verify_training_notebook(PROJECT_ROOT / "submission")


if __name__ == "__main__":
    main()
