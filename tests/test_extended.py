import gzip
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

import numpy as np

from read_prediction.pipeline import Event, TICKS_PER_SECOND, make_samples, split_masks
from read_prediction.extended import EVENT_DTYPE, load_duration, make_compact_samples


def compact(events):
    return np.array([(e.timestamp, e.offset, e.size, e.kind == "Read") for e in events], dtype=EVENT_DTYPE)


class CompactPreparationTests(unittest.TestCase):
    def compare(self, events):
        expected = make_samples(events)
        actual = make_compact_samples(compact(events), block_size=3)
        for key in expected:
            np.testing.assert_allclose(actual[key], expected[key], rtol=1e-12, atol=1e-12, err_msg=key)

    def test_manual_histories_and_source_order_ties(self):
        specifications = [
            (1, "Read", 1), (1, "Write", 1), (1, "Read", 1),
            (2, "Write", 2), (3, "Write", 2), (4, "Read", 3),
            (5, "Read", 2), (6, "Write", 1), (7, "Read", 1),
            (8, "Write", 4), (9, "Write", 1),
        ]
        self.compare([Event(t * TICKS_PER_SECOND, kind, offset, 4096) for t, kind, offset in specifications])

    def test_read_only_write_only_and_unread_addresses(self):
        for kind in ("Read", "Write"):
            self.compare([Event(i, kind, i % 3, 4096) for i in range(20)])

    def test_random_histories_match_reference_and_split_masks(self):
        rng = np.random.default_rng(17)
        events = [Event(128166372010520299 + i // 3, "Read" if rng.random() < .6 else "Write", int(rng.integers(0, 20)), 4096) for i in range(1000)]
        self.compare(events)
        expected, actual = make_samples(events), make_compact_samples(compact(events))
        expected_masks, expected_coverage = split_masks(expected)
        actual_masks, actual_coverage = split_masks(actual)
        self.assertEqual(expected_coverage, actual_coverage)
        for key in expected_masks:
            np.testing.assert_equal(expected_masks[key], actual_masks[key])

    def test_disk_features_equal_in_memory_features(self):
        events = compact([Event(i, "Read" if i % 3 else "Write", i % 5, 4096) for i in range(20)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.npy"
            disk = make_compact_samples(events, path, block_size=2)
            memory = make_compact_samples(events)
            np.testing.assert_equal(disk["features"], memory["features"])
            np.testing.assert_equal(np.load(path, mmap_mode="r"), memory["features"])

    def test_half_open_duration_and_event_cap(self):
        origin = 128166372010520299
        lines = [f"{origin + i * TICKS_PER_SECOND},usr,1,{'Read' if i % 2 else 'Write'},4096,4096,0\n".encode() for i in range(401)]
        data = gzip.compress(b"".join(lines))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with tarfile.open(root / "msr-cambridge2.tar", "w") as tar:
                info = tarfile.TarInfo("MSR-Cambridge/usr_1.csv.gz")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
            events, metadata = load_duration(root, "usr_1", 300 / 3600, 1000, root / "events.bin")
            self.assertEqual(len(events), 300)
            self.assertEqual(metadata["stop_reason"], "duration_reached")
            self.assertEqual(metadata["first_excluded_timestamp"], origin + 300 * TICKS_PER_SECOND)
            self.assertEqual(metadata["prefix_sha256"], hashlib.sha256(b"".join(lines[:300])).hexdigest())
            _, capped = load_duration(root, "usr_1", 1, 250, root / "capped.bin")
            self.assertEqual(capped["stop_reason"], "event_cap_reached")
            self.assertEqual(capped["loaded_events"], 250)


if __name__ == "__main__":
    unittest.main()
