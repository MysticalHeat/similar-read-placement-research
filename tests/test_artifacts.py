import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np

from read_prediction.artifacts import build_manifest, verify_manifest
from read_prediction.checks.extended import audit_source
from read_prediction.paths import PROJECT_ROOT


class ArtifactTests(unittest.TestCase):
    def test_git_rules_match_artifact_storage_policy(self):
        manifest = json.loads((PROJECT_ROOT / "artifacts/manifest.json").read_text())
        expected = {path for path, entry in manifest["files"].items() if entry["storage"] == "external"}
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"],
            input="\n".join(manifest["files"]) + "\n", text=True, capture_output=True, cwd=PROJECT_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), expected)

    def make_bundle(self, root):
        dataset = root / "dataset"
        dataset.mkdir()
        (dataset / "README.md").write_text("dataset documentation")
        (dataset / "trace.tar").write_bytes(b"raw trace")
        for workload in ("usr_1", "prxy_1"):
            folder = root / "results/final-study" / workload
            folder.mkdir(parents=True)
            model = folder / "model.lightgbm.txt"
            model.write_bytes(b"saved model")
            (folder / "frozen.json").write_text(json.dumps({"selection": {
                "model_path": model.relative_to(root).as_posix(), "columns": [0], "log_target": True,
            }}))
            (folder / "predictions.npz").write_bytes(b"prediction array")

    def test_manifest_classifies_models_metadata_and_external_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_bundle(root)
            manifest = build_manifest(root)
            self.assertEqual(len(manifest["files"]), 7)
            self.assertNotIn("dataset/README.md", manifest["files"])
            self.assertEqual(manifest["files"]["dataset/trace.tar"]["storage"], "external")
            model = manifest["selected_models"]["usr_1"]["model_path"]
            self.assertEqual(manifest["files"][model]["storage"], "git")
            self.assertEqual(verify_manifest(manifest, root, include_external=True), 7)

    def test_git_bundle_can_be_verified_without_external_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_bundle(root)
            manifest = build_manifest(root)
            for relative, entry in manifest["files"].items():
                if entry["storage"] == "external":
                    (root / relative).unlink()
            self.assertEqual(verify_manifest(manifest, root), 4)
            with self.assertRaisesRegex(ValueError, "Missing artifact"):
                verify_manifest(manifest, root, include_external=True)

    def test_modified_model_fails_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_bundle(root)
            manifest = build_manifest(root)
            model = manifest["selected_models"]["usr_1"]["model_path"]
            (root / model).write_bytes(b"other model")
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                verify_manifest(manifest, root)

    def test_source_audit_works_after_checkout_relocation(self):
        lines = [
            b"0,usr,1,Read,512,4096,0\n",
            b"10000000,usr,1,Write,512,4096,0\n",
            b"20000000,usr,1,Read,512,4096,0\n",
            b"30000000,usr,1,Read,512,4096,0\n",
        ]
        result = {"source": {
            "archive": "/previous/checkout/dataset/trace.tar",
            "member": "usr_1.csv.gz", "loaded_events": 3,
            "first_timestamp": 0, "first_excluded_timestamp": 30000000,
            "prefix_sha256": hashlib.sha256(b"".join(lines[:3])).hexdigest(),
        }}
        selected = {1: {"offset": 512, "read_index": 2, "target": 1.0, "prediction": 1.0}}
        model = Mock()
        model.predict.return_value = np.log1p([1.0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "dataset").mkdir()
            compressed = gzip.compress(b"".join(lines))
            with tarfile.open(root / "dataset/trace.tar", "w") as archive:
                info = tarfile.TarInfo("usr_1.csv.gz")
                info.size = len(compressed)
                archive.addfile(info, io.BytesIO(compressed))
            with patch("read_prediction.paths.PROJECT_ROOT", root):
                self.assertEqual(audit_source(result, selected, model), 1)
            matrix = model.predict.call_args.args[0]
            np.testing.assert_allclose(matrix[0, :5], np.log1p([512, 4096, 1, 0, 1]))


if __name__ == "__main__":
    unittest.main()
