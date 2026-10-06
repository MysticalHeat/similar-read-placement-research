"""Check submission snapshots and execute the notebook outside the repository."""

import json
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
import numpy as np
from nbclient import NotebookClient

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.paths import PROJECT_ROOT
from read_prediction.submission_datasets import collect_datasets, dataset_selection_markdown
from read_prediction.submission_overwrite import collect_results, summary_markdown
from read_prediction.submission_predict import SelectedPredictor


def verify_predictions(folder):
    predictor = SelectedPredictor(folder)
    metadata = predictor.metadata
    assert fingerprint(folder / "predict.py") == fingerprint(PROJECT_ROOT / "read_prediction/submission_predict.py")
    for name, relative in metadata["sources"].items():
        assert fingerprint(folder / name) == fingerprint(PROJECT_ROOT / relative) == metadata["files"][name]
    checked = 0
    for workload, rules in metadata["predictors"].items():
        events = np.memmap(PROJECT_ROOT / f"results/new-workloads/{workload}/events.bin", dtype=EVENT_DTYPE, mode="r")
        writes = np.flatnonzero(events["is_read"] == 0)
        features = np.load(PROJECT_ROOT / f"results/new-workloads/{workload}/features.npy", mmap_mode="r")
        for rule, recipe in rules.items():
            for window in ("validation", "day5", "day6", "day7"):
                parent = "mixture" if recipe["method"] == "mix_log25" else "long-history"
                with np.load(PROJECT_ROOT / f"results/{parent}/{workload}/{rule}.{window}.npz") as saved:
                    positions = np.unique(np.linspace(0, len(saved["write_rows"]) - 1, 128, dtype=int))
                    rows = saved["write_rows"][positions]
                    inputs = features[np.searchsorted(writes, rows)]
                    raw = np.expm1(inputs)
                    # These four columns were integers before log1p.
                    raw[:, :4] = np.rint(raw[:, :4])
                    actual = predictor.predict_seconds(workload, rule, raw)
                    np.testing.assert_allclose(actual, saved[recipe["method"]][positions], rtol=1e-10, atol=1e-8)
                    checked += len(positions)
        del events, features
    return checked


def main():
    folder = PROJECT_ROOT / "submission"
    cyrillic = re.compile(r"[\u0400-\u04ff]")
    for name in ("README.md", "predict.py", "models.json", "overwrite-results.json",
                 "dataset-comparison.json", "results.ipynb", "training.ipynb"):
        text = (folder / name).read_text()
        if name.endswith((".json", ".ipynb")):
            text = json.dumps(json.loads(text), ensure_ascii=False)
        assert not cyrillic.search(text), f"Non-English submission content: {name}"
    assert not cyrillic.search((PROJECT_ROOT / "notebooks/final_results.ipynb").read_text())
    recorded = json.loads((folder / "overwrite-results.json").read_text())
    assert recorded == collect_results(), "Submission snapshot differs from verified results"
    recorded_datasets = json.loads((folder / "dataset-comparison.json").read_text())
    assert recorded_datasets == collect_datasets(), "Dataset snapshot differs from the screening results"
    assert len(recorded_datasets["traces"]) == 36 and recorded_datasets["failed_traces"] == 28
    assert recorded_datasets["selected"] == ["proj_1", "prn_1"]
    assert len(recorded_datasets["eligible_new_workloads"]) == 6
    assert all(row["basic_eligible"] for row in recorded_datasets["range_confirmation"])
    notebook = nbformat.read(folder / "results.ipynb", as_version=4)
    summary = summary_markdown(recorded)
    assert notebook.cells[0].source == summary
    assert any(cell.source == dataset_selection_markdown(recorded_datasets) for cell in notebook.cells)
    assert (folder / "README.md").read_text().startswith(summary + "\n" + dataset_selection_markdown(recorded_datasets))
    for row in recorded["pooled_candidates"]:
        assert row["ninety_percent_status"] == "failed"
        assert row["paired"] is not None and not row["paired"]["passed"]
    for row in recorded["selected_results"]:
        if row["workload"] == "prn_1":
            assert row["observed_read"]["status"] == "passed"
    checked_predictions = verify_predictions(folder)
    metadata = json.loads((folder / "models.json").read_text())
    with TemporaryDirectory(prefix="submission-check-", dir="/tmp/opencode") as directory:
        names = ("usr_1.lightgbm.txt", "prxy_1.lightgbm.txt", "overwrite-results.json",
                 "dataset-comparison.json", "models.json", *metadata["files"])
        for name in names:
            shutil.copyfile(folder / name, Path(directory) / name)
        notebook.cells.append(nbformat.v4.new_code_cell(
            "import json\n"
            "from pathlib import Path\n"
            "assert overwrite_results == json.loads(Path('overwrite-results.json').read_text())\n"
            "print('Portable submission snapshot matches notebook values')"
        ))
        NotebookClient(notebook, timeout=60, kernel_name="python3",
                       resources={"metadata": {"path": directory}}).execute()
    print("Submission verified: source fingerprints, dataset screening, both criteria,", checked_predictions,
          "saved predictions and standalone notebook execution")


if __name__ == "__main__":
    main()
