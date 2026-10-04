"""Project locations shared by command-line modules and notebooks."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT_ROOT / "reports"
NOTEBOOKS = PROJECT_ROOT / "notebooks"

SOURCE_PATHS = {
    "next_read.py": "read_prediction/pipeline.py",
    "next_read_extended.py": "read_prediction/extended.py",
    "prxy_diagnosis.py": "read_prediction/experiments/diagnosis.py",
    "prxy_day2.py": "read_prediction/experiments/day2.py",
    "final_study.py": "read_prediction/experiments/study.py",
    "run_final_evaluation.py": "read_prediction/experiments/run_study.py",
    "render_final_report.py": "read_prediction/reporting.py",
    "verify_pilot.py": "read_prediction/checks/pilot.py",
    "verify_extended.py": "read_prediction/checks/extended.py",
    "verify_diagnosis.py": "read_prediction/checks/diagnosis.py",
    "verify_day2.py": "read_prediction/checks/day2.py",
    "verify_final_study.py": "read_prediction/checks/study.py",
}


def source_path(legacy_name):
    """Resolve historical script names when recording new source fingerprints."""
    return PROJECT_ROOT / SOURCE_PATHS[legacy_name]


def recorded_archive_path(recorded):
    """Prefer the current checkout's dataset when auditing historical records."""
    path = Path(recorded)
    local = PROJECT_ROOT / "dataset" / path.name
    return local if local.is_file() else path
