"""UNRUN negative specifications R014-R017. No generator/fit; NOT E004 TOYS.

Future separate permission, frozen source/runtime and explicit test/disk budget needed.
All synthetic source snippets, temporary paths and mocked failures are test-only.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch


class AdapterNegativeSpecs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().with_name("synthetic_stage_adapter_v0.1.py")
        name = "_synthetic_adapter_negative_specs_v01"
        if name in sys.modules:
            raise ValueError("test adapter module already loaded")
        module = ModuleType(name)
        module.__file__ = str(path)
        sys.modules[name] = module
        exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), module.__dict__)
        cls.b = module  # future test-only exact source loading; no pyc/sys.path resolution

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-adapter-spec-")
        self.addCleanup(self.temp.cleanup)  # TEST TEMP ONLY, never research raw artifacts
        self.project = Path(self.temp.name).resolve()
        self.cache = patch.dict(sys.modules)
        self.cache.start()
        self.addCleanup(self.cache.stop)
        for name in self.b.COMPUTATIONAL:
            sys.modules.pop(name, None)  # isolate mocked caches in separately approved tests

    def session_stub(self, callback=None):
        s = self.b.Session.__new__(self.b.Session)
        s.c = {"persist_resource_receipt": callback, "checkpoint": lambda *_: {"operation_ref": "test"},
               "dispatch": {"operation_ref": "test"}}
        s.stage, s.raw = "test", self.project
        s.receipt_points, s.receipt_links, s.failure_reporting_error = set(), {}, None
        s.writer = self.b.Writer(self.project / "owned-test", self.limits())
        s.writer.create()
        return s

    @staticmethod
    def limits():
        return {"per_file": 65536, "total": 262144, "manifest_reserve": 16384, "failure_reserve": 8192}

    def context_stub(self, checkpoint):
        b = self.b
        (self.project / ".research/experiments/raw").mkdir(parents=True)
        sources = {path: b"# synthetic test-only identity\n" for path in b.SCOPED}
        sources[b.CONFIG] = b.encoded(b.FIXED)
        sources[b.SCRIPT + "synthetic_temperature_demo.py"] = b"source_marker = 'captured-P'\n"
        sources[b.SCRIPT + "synthetic_models.py"] = b"source_marker = 'captured-M'\n"
        for path, data in sources.items():
            target = self.project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)  # NEW test temp fixtures, never E004/E005
        adapter_path = self.project / b.SCRIPT / "synthetic_stage_adapter_v0.1.py"
        return {"project": str(self.project), "checkpoint": checkpoint, "persist_resource_receipt": Mock(),
                "sample": Mock(), "origin": Mock(), "writer_limits": self.limits(),
                "dispatch": {k: "test" for k in ("operation_ref", "owner", "approval_reference", "prestart_record", "quota_record", "postexit_record_locator")},
                "resource_receipt": {"test_only": True},
                "provenance": {k: None for k in ("runtime", "OS", "CPU", "RAM", "compiler", "repo_revision", "dirty_state", "secret_free_environment", "commands")},
                "frozen_hashes": {p: b.digest(data) for p, data in sources.items()},
                "adapter_loading": {"path": str(adapter_path), "sha256": b.digest(sources[b.SCRIPT + "synthetic_stage_adapter_v0.1.py"]), "mode": "captured-source-no-cache"}}

    def test_preloaded_names_stop_before_callbacks_or_source_use(self):
        callback = Mock(side_effect=AssertionError("must not be called"))
        for name in self.b.COMPUTATIONAL:
            with self.subTest(name=name), patch.dict(sys.modules, {name: ModuleType(name)}):
                with self.assertRaisesRegex(ValueError, "preloaded"):
                    self.b.Session({"checkpoint": callback}, "E005")
        callback.assert_not_called()

    def test_checkpoint_preload_rechecked_before_binding(self):
        def checkpoint(*_):
            sys.modules["synthetic_models"] = ModuleType("synthetic_models")
            return {"operation_ref": "test"}
        c = self.context_stub(checkpoint)
        with patch.object(self.b, "__file__", c["adapter_loading"]["path"]), patch.object(self.b, "bound_source") as loader:
            with self.assertRaisesRegex(ValueError, "preloaded"):
                self.b.Session(c, "E005")
        loader.assert_not_called()
        self.assertFalse((self.project / ".research/experiments/raw/E005").exists())

    def test_bad_frozen_bytes_stop_before_source_exec(self):
        checkpoint = Mock()
        c = self.context_stub(checkpoint)
        c["frozen_hashes"][self.b.SCRIPT + "synthetic_models.py"] = "0" * 64
        with patch.object(self.b, "__file__", c["adapter_loading"]["path"]), patch.object(self.b, "bound_source") as loader:
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                self.b.Session(c, "E005")
        checkpoint.assert_not_called()
        loader.assert_not_called()

    def test_bad_adapter_path_and_missing_caller_contract_stop(self):
        c = self.context_stub(Mock())
        with patch.object(self.b, "__file__", str(self.project / "wrong.py")):
            with self.assertRaisesRegex(ValueError, "adapter exact path"):
                self.b.Session(c, "E005")
        c.pop("adapter_loading")
        with patch.object(self.b, "__file__", str(self.project / self.b.SCRIPT / "synthetic_stage_adapter_v0.1.py")):
            with self.assertRaisesRegex(ValueError, "caller loading contract"):
                self.b.Session(c, "E005")

    def test_bound_captured_source_not_disk_or_pycache_and_provenance(self):
        name = "synthetic_models"
        path = self.project / self.b.COMPUTATIONAL[name]
        path.parent.mkdir(parents=True)
        path.write_bytes(b"raise AssertionError('disk must not execute')\n")
        m = self.b.bound_source(self.project, name, b"marker = 'captured-approved-test-bytes'\n")
        self.assertEqual((m.marker, m.__file__), ("captured-approved-test-bytes", str(path)))
        with self.assertRaisesRegex(ValueError, "preloaded"):
            self.b.bound_source(self.project, name, b"raise AssertionError('stale cache')\n")
        with self.assertRaisesRegex(ValueError, "provenance changed"):
            self.b.bound_source(self.project, "synthetic_temperature_demo", b"__file__ = '/wrong/import/path.py'\n")

    def test_e005_binding_never_captures_or_loads_oracle_tests(self):
        c = self.context_stub(lambda *_: {"operation_ref": "test"})
        with patch.object(self.b, "__file__", c["adapter_loading"]["path"]):
            s = self.b.Session(c, "E005")
        self.assertEqual(s.p.source_marker, "captured-P")
        self.assertEqual(s.m.source_marker, "captured-M")
        for name in tuple(self.b.COMPUTATIONAL)[2:]:
            self.assertNotIn(self.b.COMPUTATIONAL[name], s.sources)
            self.assertNotIn(name, sys.modules)

    def test_fresh_receipt_links_and_duplicate_point_stop(self):
        s = self.session_stub(lambda w, stage, point, receipt: w.put(point + ".json", self.b.encoded(receipt)))
        s.record("first")
        s.record("second")
        self.assertEqual(s.receipt_links, {"first": "first.json", "second": "second.json"})
        with self.assertRaisesRegex(ValueError, "duplicate receipt point"):
            s.record("first")

    def test_no_write_reused_and_failed_receipts_rejected(self):
        s = self.session_stub(lambda *_: "missing.json")
        with self.assertRaisesRegex(ValueError, "fresh successful"):
            s.record("no_write")
        s.writer.put("old.json", b"{}")
        s.c["persist_resource_receipt"] = lambda *_: "old.json"
        with self.assertRaisesRegex(ValueError, "fresh successful"):
            s.record("reuse")
        def failed_write(w, *_):
            try:
                w.put("partial.json", b"{}")
            except OSError:
                return "partial.json"
        s.c["persist_resource_receipt"] = failed_write
        with patch.object(self.b.os, "fsync", side_effect=OSError("test-only fsync failure")):
            with self.assertRaisesRegex(ValueError, "fresh successful"):
                s.record("failed_write")
        self.assertIn("partial.json", s.writer.attempted)
        self.assertNotIn("partial.json", s.writer.outputs)
        self.assertEqual(s.receipt_links, {})

    def test_reserved_names_slots_reject_before_charge_attempt_open(self):
        s = self.session_stub()
        for name, slot in (("manifest.json", None), ("failure-001.json", None),
                           ("ordinary.json", "manifest"), ("manifest.json", "failure"), ("failure-001.json", "manifest")):
            before = (s.writer.used, set(s.writer.attempted), dict(s.writer.outputs))
            with self.subTest(name=name, slot=slot), self.assertRaisesRegex(ValueError, "name/slot mismatch"):
                s.writer.put(name, b"{}", slot)
            self.assertEqual((s.writer.used, s.writer.attempted, s.writer.outputs), before)
            self.assertFalse((s.writer.root / name).exists())
        s.writer.put("manifest.json", b"{}", "manifest")
        s.writer.put("failure-001.json", b"{}", "failure")
        with self.assertRaisesRegex(ValueError, "repeated output"):
            s.writer.put("failure-001.json", b"{}", "failure")

    def assert_primary_survives(self, s, primary):
        try:
            try:
                raise primary
            except BaseException as error:
                s.report_failure(error)
                raise
        except BaseException as caught:
            self.assertIs(caught, primary)
            return caught
        self.fail("primary not re-raised")

    def test_primary_survives_reporting_io_and_reserve_failure(self):
        s = self.session_stub()
        secondary = OSError("secondary reporting failure")
        primary = ValueError("primary failure")
        with patch.object(s, "fail", side_effect=secondary):
            caught = self.assert_primary_survives(s, primary)
        self.assertIs(caught.failure_reporting_error, secondary)
        self.assertIsNone(caught.external_failure_pointer)
        if hasattr(caught, "__notes__"):
            self.assertIn("secondary reporting failure", caught.__notes__[0])
        s.writer.limits["failure_reserve"] = 1
        self.assert_primary_survives(s, ValueError("reserve case"))
        self.assertIsInstance(s.failure_reporting_error, ValueError)

    def test_owned_mkdir_sync_window_and_existing_directory_no_writes(self):
        s = self.session_stub()
        s.c["writer_limits"], s.initial = self.limits(), {"operation_ref": "test"}
        s.writer = None
        primary = OSError("primary mkdir-sync failure")
        with patch.object(self.b, "sync_dir", side_effect=primary):
            with self.assertRaises(OSError) as caught:
                s.open_writer()
        self.assertIs(caught.exception, primary)
        self.assertTrue(s.writer.created)
        self.assert_primary_survives(s, primary)  # sync now restored: best-effort failure artifact
        self.assertTrue((s.writer.root / "failure-001.json").exists())
        occupied = self.b.Writer(s.writer.root, self.limits())
        with self.assertRaises(FileExistsError):
            occupied.create()
        self.assertFalse(occupied.created)
        s.writer = occupied
        s.fail(ValueError("must not write into somebody else's directory"))
        self.assertEqual(occupied.attempted, set())


if __name__ == "__main__":
    raise SystemExit("STOP: UNRUN negative specifications need separate runtime permission/budget; not E004 checklist")
