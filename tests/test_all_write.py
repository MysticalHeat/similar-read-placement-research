import tempfile
import unittest
from pathlib import Path

import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.all_write import prepare, snapshot, quality, choose
from read_prediction.checks.all_write import reference


class AllWriteTests(unittest.TestCase):
    def events(self):
        rows = [(0, 4096, 4, 0), (0, 4096, 8, 0), (10, 4096, 4, 1),
                (10, 4096, 4, 0), (11, 8192, 8, 0), (12, 4096, 16, 0),
                (13, 4096, 4, 1), (14, 4096, 8, 0), (16, 8192, 8, 1)]
        return np.array([(t*10_000_000, off, size, read) for t, off, size, read in rows], dtype=EVENT_DTYPE)

    def test_all_features_match_direct_source_history_and_include_unread_writes(self):
        events = self.events()
        with tempfile.TemporaryDirectory() as tmp:
            features, meta = prepare(events, Path(tmp), start_seconds=0)
            reopened = np.load(Path(tmp) / "meta.npy", mmap_mode="r")
            for field in meta.dtype.names:
                np.testing.assert_allclose(reopened[field], meta[field], rtol=0, atol=0, equal_nan=True)
            np.testing.assert_allclose(np.load(Path(tmp) / "features.npy", mmap_mode="r"), features, equal_nan=True)
            for row, index in enumerate(meta["write"]):
                indices = np.flatnonzero(events["offset"] == events["offset"][index])
                expected, r, w = reference(events, index, indices)
                np.testing.assert_allclose(features[row], expected, rtol=1e-12, atol=1e-12, equal_nan=True)
                self.assertEqual(meta["read"][row], r)
                self.assertEqual(meta["overwrite"][row], w)
            state, observed, known_write = snapshot(meta, 8)
            np.testing.assert_array_equal(state, [0, 1, 0, -1, 1, -1])
            self.assertFalse(observed[3])
            self.assertFalse(known_write[-1])

    def test_future_mutation_does_not_change_past_features(self):
        events = self.events()
        changed = events.copy()
        changed[8]["offset"] = 4096
        changed[8]["is_read"] = 0
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            before, meta = prepare(events, Path(a), 0)
            after, other = prepare(changed, Path(b), 0)
            rows = np.searchsorted(other["write"], meta["write"])
            np.testing.assert_allclose(before, after[rows], equal_nan=True)

    def test_censoring_and_unobserved_targets_are_not_false_successes(self):
        events = self.events()
        with tempfile.TemporaryDirectory() as tmp:
            _, meta = prepare(events, Path(tmp), 0)
            metric = quality(meta, np.zeros(len(meta)), np.ones(len(meta)), .5, 8, 14*10_000_000)
            self.assertEqual(metric["selected_n"], 6)
            self.assertEqual(metric["selected_censored"], 2)
            self.assertLess(metric["read_first_lower"], metric["read_first_upper"])
            self.assertFalse(metric["qualifies"])

    def test_fallback_respects_minimum_coverage(self):
        candidates = {"tiny": {"qualifies": False, "coverage": .001, "read_first_lower": 1., "confirmed_error_lt_overwrite_lower": 1.},
                      "broad": {"qualifies": False, "coverage": .3, "read_first_lower": .85, "confirmed_error_lt_overwrite_lower": .8}}
        self.assertEqual(choose(candidates), "broad")


if __name__ == "__main__":
    unittest.main()
