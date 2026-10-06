import unittest

import numpy as np

from read_prediction.overwrite_reporting import criterion, lifetime_bounds


class LifetimeBoundTests(unittest.TestCase):
    def test_completions_respect_mean_and_median_bounds(self):
        durations = np.asarray([1., 2., 4., np.nan])
        lower = np.asarray([0., 0., 0., 10.])
        bounds = lifetime_bounds(durations, lower)
        self.assertEqual(bounds["mean_lower_bound_seconds"], 4.25)
        self.assertIsNone(bounds["mean_upper_bound_seconds"])
        self.assertEqual(bounds["median_lower_bound_seconds"], 3.)
        self.assertEqual(bounds["median_upper_bound_seconds"], 3.)
        for lifetime in (10.01, 10000.):
            actual = np.asarray([1., 2., 4., lifetime])
            self.assertGreaterEqual(actual.mean(), bounds["mean_lower_bound_seconds"])
            self.assertGreaterEqual(np.median(actual), bounds["median_lower_bound_seconds"])
            self.assertLessEqual(np.median(actual), bounds["median_upper_bound_seconds"])

    def test_many_unknowns_do_not_produce_fake_finite_upper_bound(self):
        bounds = lifetime_bounds(np.asarray([1., np.nan, np.nan, np.nan]), np.asarray([0., .5, .5, .5]))
        self.assertIsNone(bounds["median_upper_bound_seconds"])
        self.assertEqual(criterion(100., .5, None), "не определено из-за неизвестных интервалов")


if __name__ == "__main__":
    unittest.main()
