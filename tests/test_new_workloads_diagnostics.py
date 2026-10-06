import unittest

import numpy as np

from read_prediction.experiments.new_workloads_diagnostics import budget_groups, metrics
from read_prediction.experiments.new_workloads_horizon import WIDTH, restrict
from read_prediction.extended import EVENT_DTYPE
from read_prediction.range_label import TICKS


class DiagnosticTests(unittest.TestCase):
    def test_budget_boundaries_and_unknown_are_separate(self):
        values = np.array([0, .0005, .001, .01, .1, 1, 10, 60, 600, 3600, np.nan])
        np.testing.assert_array_equal(budget_groups(values), np.arange(11))

    def test_strict_pass_and_unknown_overwrite(self):
        result = metrics(np.array([0., 2., 3., 4.]), np.zeros(4),
                         np.array([0., 2., np.nan, np.nan]), np.array([9., 9., 4., 1.]))
        self.assertEqual(result["confirmed_pass_count"], 1)
        self.assertEqual(result["unknown_pass_count"], 1)
        self.assertEqual(result["pass_lower"], .25)
        self.assertEqual(result["pass_upper"], .5)

    def test_signed_errors_partition_mae(self):
        result = metrics(np.array([2., 2., 2.]), np.array([5., 0., 2.]),
                         np.full(3, 10.), np.full(3, 10.))
        self.assertAlmostEqual(result["over_share"], 1 / 3)
        self.assertAlmostEqual(result["under_share"], 1 / 3)
        self.assertAlmostEqual(result["exact_share"], 1 / 3)
        self.assertAlmostEqual(result["mae_seconds"], result["over_mae_contribution_seconds"]
                               + result["under_mae_contribution_seconds"])
        self.assertAlmostEqual(result["bias_seconds"], 1 / 3)

    def test_horizon_excludes_boundary_read_and_censors_later_overwrite(self):
        events = np.zeros(4, dtype=EVENT_DTYPE)
        events["timestamp"] = [WIDTH - 2 * TICKS, WIDTH - TICKS, WIDTH + TICKS, WIDTH + 2 * TICKS]
        rows = np.array([0, 2])
        labels = {"read": np.array([1, 3]), "overwrite": np.array([2, -1]),
                  "target": np.array([1., 1.]), "lifetime": np.array([3., np.nan])}
        keep, target, lifetime, remaining = restrict(events, rows, labels, 0, 2 * WIDTH)
        np.testing.assert_array_equal(keep, [True, True])
        np.testing.assert_array_equal(target, [1., 1.])
        self.assertTrue(np.isnan(lifetime).all())
        np.testing.assert_array_equal(remaining, [2., WIDTH / TICKS - 1])
        events["timestamp"][1] = WIDTH
        keep, _, _, _ = restrict(events, rows, labels, 0, 2 * WIDTH)
        np.testing.assert_array_equal(keep, [False, True])


if __name__ == "__main__":
    unittest.main()
