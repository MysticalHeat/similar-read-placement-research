import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from read_prediction import provenance
from read_prediction.paths import PROJECT_ROOT, SOURCE_PATHS, source_path


class StructureTests(unittest.TestCase):
    def test_all_active_modules_import_without_running_experiments(self):
        for legacy, relative in SOURCE_PATHS.items():
            self.assertTrue(source_path(legacy).is_file())
            importlib.import_module(relative.removesuffix(".py").replace("/", "."))

    def test_source_snapshots_match_original_checksums(self):
        folder = PROJECT_ROOT / "archive/code-before-restructure"
        manifest = json.loads((folder / "manifest.json").read_text())["sha256"]
        self.assertEqual(set(manifest), set(SOURCE_PATHS))
        for name, digest in manifest.items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
            self.assertEqual(provenance.check_recorded_hash(name, digest), folder / name)

    def test_legacy_hash_resolves_only_to_exact_archived_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive"
            archive.mkdir()
            active = root / "active.py"
            active.write_bytes(b"new package code\n")
            snapshot = archive / "next_read.py"
            snapshot.write_bytes(b"original experiment code\n")
            digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            with patch.object(provenance, "PROJECT_ROOT", root), patch.object(provenance, "SOURCE_ARCHIVE", archive), patch.object(provenance, "source_path", return_value=active):
                self.assertEqual(provenance.check_recorded_hash("next_read.py", digest), snapshot)
                with self.assertRaises(AssertionError):
                    provenance.check_recorded_hash("next_read.py", "0" * 64)

    def test_non_source_artifact_never_falls_back_to_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "model.txt"
            artifact.write_bytes(b"saved model\n")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            with patch.object(provenance, "PROJECT_ROOT", root):
                self.assertEqual(provenance.check_recorded_hash("model.txt", digest), artifact)
                with self.assertRaises(AssertionError):
                    provenance.check_recorded_hash("model.txt", "0" * 64)

    def test_historical_final_records_keep_valid_fingerprints(self):
        selection = json.loads((PROJECT_ROOT / "results/final-study/usr-selection/selection.json").read_text())
        for path, digest in selection["code_hashes"].items():
            provenance.check_recorded_hash(path, digest)
        for workload in ("usr_1", "prxy_1"):
            record = json.loads((PROJECT_ROOT / "results/final-study" / workload / "results.json").read_text())
            for fingerprints in (record["frozen"]["hashes"], record["baseline_pin"]["code_hashes"]):
                for path, digest in fingerprints.items():
                    provenance.check_recorded_hash(path, digest)


if __name__ == "__main__":
    unittest.main()
