import unittest

import numpy as np

from read_prediction.experiments.study import daily_mask, period_prediction
from read_prediction.pipeline import Event, TICKS_PER_SECOND, make_samples


class FinalBoundaryTests(unittest.TestCase):
    def test_read_at_next_midnight_is_censored_and_ties_follow_source(self):
        origin = 128166372010520299
        history = [(0, "Read", 9), (86399, "Write", 1), (86400, "Read", 1),
                   (86400, "Write", 2), (86400, "Read", 2),
                   (172799, "Write", 3), (172800, "Read", 3),
                   (172800, "Write", 4), (172801, "Read", 4)]
        samples = make_samples([Event(origin + t * TICKS_PER_SECOND, k, a, 4096) for t, k, a in history])
        eligible, observed, start, end = daily_mask(samples, 2)
        np.testing.assert_equal(eligible, [False, True, True, False])
        np.testing.assert_equal(observed, [False, True, False, False])
        self.assertEqual((start, end), (2, 6))
        _, day3, _, _ = daily_mask(samples, 3)
        np.testing.assert_equal(day3, [False, False, False, True])

    def test_period_rule_is_nonnegative_and_missing_history_falls_back(self):
        features = np.full((3, 7), np.nan)
        features[0, [4, 6]] = np.log1p([5, 20])
        features[1, [4, 6]] = np.log1p([30, 20])
        np.testing.assert_allclose(period_prediction(features, np.arange(3), 60), [15, 0, 60])


if __name__ == "__main__":
    unittest.main()
