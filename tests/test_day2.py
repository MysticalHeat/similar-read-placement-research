import unittest

import numpy as np

from read_prediction.pipeline import Event, TICKS_PER_SECOND, make_samples
from read_prediction.experiments.day2 import window_masks


class DayTwoBoundaryTests(unittest.TestCase):
    def test_half_open_day_and_training_truth_cutoff(self):
        origin = 128166391023873138
        rows = [(0, "Write", 1), (1, "Read", 1), (2, "Write", 2),
                (3, "Read", 2), (86399, "Write", 3),
                (86400, "Write", 1), (86400, "Read", 1),
                (172799, "Write", 2), (172800, "Read", 2)]
        events = [Event(origin + t * TICKS_PER_SECOND, kind, offset, 4096) for t, kind, offset in rows]
        train, eligible, observed, start, end = window_masks(make_samples(events), train_end=3)
        np.testing.assert_equal(train, [True, False, False, False, False])
        np.testing.assert_equal(eligible, [False, False, False, True, True])
        np.testing.assert_equal(observed, [False, False, False, True, False])
        self.assertEqual((start, end), (5, 8))


if __name__ == "__main__":
    unittest.main()
