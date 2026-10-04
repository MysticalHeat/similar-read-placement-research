"""Verify recorded bytes, including immutable pre-restructure source snapshots."""

import hashlib
from pathlib import Path

from read_prediction.paths import PROJECT_ROOT, SOURCE_PATHS, source_path

SOURCE_ARCHIVE = PROJECT_ROOT / "archive/code-before-restructure"


def check_recorded_hash(relative_path, expected):
    """Return the exact matching file or fail; never replace a recorded digest.

    Old runs used root-level script names. Their source bytes are preserved in
    the archive; current package code has independent fingerprints on new runs.
    Non-source artifacts must always match at their recorded path.
    """
    path = Path(relative_path)
    candidates = [PROJECT_ROOT / path]
    if str(path) in SOURCE_PATHS:
        candidates.extend([source_path(str(path)), SOURCE_ARCHIVE / path.name])
    for candidate in candidates:
        if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == expected:
            return candidate
    raise AssertionError(f"Recorded SHA256 does not match: {relative_path}")
