from pathlib import Path
import tempfile
import unittest

import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.notebook_training import make_split_masks, prepare_samples
from read_prediction.pipeline import Event, TICKS_PER_SECOND, make_samples


class NotebookPreparationTests(unittest.TestCase):
    def compare_with_reference(self, events):
        compact_events = np.array([
            (event.timestamp, event.offset, event.size, event.kind == "Read")
            for event in events
        ], dtype=EVENT_DTYPE)
        expected = make_samples(events)

        with tempfile.TemporaryDirectory() as directory:
            actual = prepare_samples(compact_events, Path(directory) / "features.npy", batch_size=3)
            for key in ("features", "targets", "write_indices", "next_read_indices"):
                np.testing.assert_array_equal(actual[key], expected[key])

            cutoff = len(events) // 2
            training_mask, validation_mask = make_split_masks(actual, cutoff)
            writes = expected["write_indices"]
            reads = expected["next_read_indices"]
            np.testing.assert_array_equal(training_mask, (writes < cutoff) & (reads >= 0) & (reads < cutoff))
            np.testing.assert_array_equal(validation_mask, (writes >= cutoff) & (reads >= 0))

    def test_ties_multiple_writes_and_missing_reads(self):
        events = [
            Event(0, "Read", 512, 4096),
            Event(TICKS_PER_SECOND, "Write", 512, 4096),
            Event(TICKS_PER_SECOND, "Write", 512, 8192),
            Event(TICKS_PER_SECOND, "Read", 512, 4096),
            Event(2 * TICKS_PER_SECOND, "Write", 1024, 4096),
            Event(3 * TICKS_PER_SECOND, "Write", 512, 4096),
            Event(4 * TICKS_PER_SECOND, "Read", 512, 4096),
        ]
        self.compare_with_reference(events)
        self.compare_with_reference([Event(index, "Write", 512, 4096) for index in range(20)])

    def test_random_history_matches_independent_reference(self):
        random = np.random.default_rng(42)
        timestamps = np.cumsum(random.integers(0, 4, size=500)) * TICKS_PER_SECOND
        events = [
            Event(int(timestamp), "Read" if random.random() < 0.6 else "Write",
                  int(random.integers(0, 8)) * 512, 4096)
            for timestamp in timestamps
        ]
        self.compare_with_reference(events)


if __name__ == "__main__":
    unittest.main()
