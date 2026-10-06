import unittest

import numpy as np

from read_prediction.experiments.overwrite90 import causal_history, metrics, select, snapshot_budget


class OverwriteGoalTests(unittest.TestCase):
    def test_history_uses_only_completed_reads_with_row_order_ties(self):
        data = {"offset_bytes": np.array([1, 1, 1, 1]),
                "write_event_index": np.array([0, 1, 4, 7]),
                "next_read_event_index": np.array([3, 3, 6, 8]),
                "target_seconds": np.array([5., 4., 2., 1.]),
                "write_seconds": np.array([0., 1., 5., 7.]),
                "next_read_seconds": np.array([5., 5., 7., 8.])}
        result = causal_history(data)
        self.assertTrue(np.isnan(result[1, 0]))
        np.testing.assert_allclose(result[2], [4., 4.5, 4.5, 0., 2.])
        np.testing.assert_allclose(result[3], [2., 4., 11/3, 0., 3.])
        data["target_seconds"][2:] = 10000
        np.testing.assert_allclose(causal_history(data)[:3], result[:3], equal_nan=True)

    def test_future_overwrite_is_not_available_for_training_weights(self):
        data = {"write_seconds": np.array([10., 15.])}
        annotation = {"next_write_event_index": np.array([30, 50]), "overwrite_seconds": np.array([2., 100.])}
        budget, known = snapshot_budget(data, slice(None), annotation, 20., 40)
        np.testing.assert_array_equal(budget, [2., 5.])
        np.testing.assert_array_equal(known, [True, False])

    def test_censoring_and_zero_intervals_remain_in_denominator(self):
        result = metrics(np.array([0., 4., 4.]), np.array([0., 3., 0.]), np.array([0., 2., 3.]), np.array([True, True, False]))
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["pass_lower_bound"], 1/3)
        self.assertEqual(result["pass_upper_bound"], 2/3)
        self.assertFalse(result["meets_90_percent"])

    def test_selection_prefers_pass_fraction_over_mae(self):
        candidates = {"low_mae": {"pass_lower_bound": .7, "mae_seconds": 1.},
                      "more_passes": {"pass_lower_bound": .8, "mae_seconds": 10.}}
        self.assertEqual(select(candidates), "more_passes")


if __name__ == "__main__":
    unittest.main()
