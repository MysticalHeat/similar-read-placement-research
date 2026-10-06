import gzip
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

import numpy as np

from read_prediction.checks.mae_source_audit import scan_source_prefix
from read_prediction.extended import EVENT_DTYPE, make_compact_samples
from read_prediction.pipeline import Event, TICKS_PER_SECOND


ORIGIN = 128166372010520299
MEMBER = "MSR-Cambridge/usr_1.csv.gz"


def event(seconds, kind, offset):
    return Event(ORIGIN + int(seconds * TICKS_PER_SECOND), kind, offset, 4096)


def compact(events):
    return np.asarray(
        [(item.timestamp, item.offset, item.size, item.kind == "Read") for item in events],
        dtype=EVENT_DTYPE,
    )


def line(item):
    return (f"{item.timestamp},usr,1,{item.kind},{item.offset},{item.size},0\n").encode("ascii")


def sample_examples(events):
    samples = make_compact_samples(compact(events), features_path=None)
    rows = {int(index): row for row, index in enumerate(samples["write_indices"])}
    expected_reads = {0: 1, 2: 4, 3: 4, 5: 8, 6: 7, 9: 14, 10: 15, 11: 14, 12: 14, 13: 16}
    examples = {}
    for write_index, read_index in expected_reads.items():
        row = rows[write_index]
        # Confirm the compact sample identifies these hand-checked source reads.
        if int(samples["next_read_indices"][row]) != read_index:
            raise AssertionError(f"Unexpected compact read index for write {write_index}")
        target = (events[read_index].timestamp - events[write_index].timestamp) / TICKS_PER_SECOND
        examples[write_index] = {
            "offset": events[write_index].offset,
            "next_read_event_index": read_index,
            "target_seconds": target,
        }
    return samples, examples


def make_archive(directory, events, excluded=None):
    prefix = b"".join(line(item) for item in events)
    following = b"" if excluded is None else line(excluded)
    compressed = gzip.compress(prefix + following)
    archive_path = Path(directory) / "trace.tar"
    with tarfile.open(archive_path, "w") as archive:
        info = tarfile.TarInfo(MEMBER)
        info.size = len(compressed)
        archive.addfile(info, io.BytesIO(compressed))
    source = {
        "archive": str(archive_path), "member": MEMBER,
        "loaded_events": len(events), "first_timestamp": events[0].timestamp,
        "last_timestamp": events[-1].timestamp,
        "first_excluded_timestamp": None if excluded is None else excluded.timestamp,
        "prefix_sha256": hashlib.sha256(prefix).hexdigest(),
        "volume": ["usr", 1],
        "stop_reason": "end_of_trace" if excluded is None else "duration_reached",
    }
    return archive_path, source


class MaeSourceAuditTests(unittest.TestCase):
    def setUp(self):
        # Tied reads/writes deliberately exercise source-row ordering. Writes 2
        # and 3 both resolve at read 4; write 17 remains censored at EOF.
        self.events = [
            event(0, "Write", 11), event(1, "Read", 11), event(1, "Write", 11),
            event(2, "Write", 11), event(2, "Read", 11), event(2, "Write", 11),
            event(2, "Write", 22), event(3, "Read", 22), event(4, "Read", 11),
            event(4, "Write", 11), event(4, "Write", 22), event(5, "Write", 11),
            event(5, "Write", 11), event(5, "Write", 33), event(6, "Read", 11),
            event(6, "Read", 22), event(6, "Read", 33), event(6.5, "Write", 11),
        ]

    def test_forward_walk_rebuilds_features_ties_targets_and_eof_hash(self):
        samples, examples = sample_examples(self.events)
        with tempfile.TemporaryDirectory() as directory:
            archive, source = make_archive(directory, self.events)
            walked = scan_source_prefix(archive, source, examples)

        features = walked["features"]
        self.assertTrue(walked["eof_verified"])
        self.assertFalse(walked["first_excluded_timestamp_verified"])
        self.assertEqual(walked["source_events_scanned"], len(self.events))
        self.assertEqual(walked["source_prefix_sha256"], source["prefix_sha256"])
        self.assertEqual(walked["resolved"][2]["read_index"], 4)
        self.assertEqual(walked["resolved"][3]["read_index"], 4)
        self.assertEqual(walked["resolved"][3]["target"], 0.0)

        def raw_base(write_index):
            item = self.events[write_index]
            return features[write_index][:7]

        # Write 2 follows a same-time read and sees write 0's completed target.
        np.testing.assert_allclose(
            raw_base(2), np.log1p([11, 4096, 1, 1, 0, 1, np.nan]),
            rtol=1e-12, atol=1e-12, equal_nan=True,
        )
        self.assertAlmostEqual(features[2][7], np.log1p(1.0))
        # Write 3 precedes the same-time read at row 4, so its target is not history yet.
        self.assertAlmostEqual(features[3][7], np.log1p(1.0))
        # Write 5 follows that read and sees the zero-second completed target.
        self.assertAlmostEqual(features[5][7], np.log1p(0.0))
        self.assertAlmostEqual(features[5][8], np.log1p(1.0))
        self.assertTrue(np.isnan(features[6][7]))  # first write for offset 22
        self.assertTrue(np.isnan(features[13][8]))  # first write for offset 33

        # The time-cycle terms use the raw FILETIME day phase.
        phase = 2 * np.pi * (self.events[2].timestamp % (86400 * TICKS_PER_SECOND)) / (86400 * TICKS_PER_SECOND)
        np.testing.assert_allclose(features[2][9:], [np.sin(phase), np.cos(phase)], rtol=1e-12, atol=1e-12)

        write_row = {int(index): row for row, index in enumerate(samples["write_indices"])}
        self.assertEqual(int(samples["next_read_indices"][write_row[17]]), -1)
        self.assertTrue(np.isnan(samples["targets"][write_row[17]]))
        self.assertNotIn(17, examples)  # a censored write is not a scored audit example

    def test_first_excluded_timestamp_is_checked_after_exact_prefix(self):
        _, examples = sample_examples(self.events)
        excluded = event(7, "Read", 11)
        with tempfile.TemporaryDirectory() as directory:
            archive, source = make_archive(directory, self.events, excluded)
            walked = scan_source_prefix(archive, source, examples)

        self.assertTrue(walked["first_excluded_timestamp_verified"])
        self.assertFalse(walked["eof_verified"])
        self.assertEqual(walked["source_events_scanned"], len(self.events))


if __name__ == "__main__":
    unittest.main()
