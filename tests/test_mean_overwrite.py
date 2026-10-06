import unittest

import numpy as np

from read_prediction.experiments.mean_overwrite import mean_comparison, summarize


class MeanOverwriteTests(unittest.TestCase):
    def test_paired_and_censored_cohorts_use_matching_records(self):
        data = {"read": np.array([1, 2, -1]), "target": np.array([4., 20., np.nan]),
                "lifetime": np.array([10., np.nan, 1000.]), "remaining": np.array([12., 30., 40.]),
                "model": np.array([6., 8., 0.])}
        result = summarize(data, ("model",))
        self.assertEqual(result["paired_n"], 1)
        self.assertEqual(result["censored_n"], 1)
        paired = result["methods"]["model"]["paired"]
        self.assertEqual(paired["mae_seconds"], 2.)
        self.assertEqual(paired["mean_overwrite_seconds"], 10.)
        observed = result["methods"]["model"]["observed_read"]
        self.assertEqual(observed["mae_seconds"], 7.)
        self.assertEqual(observed["mean_overwrite_lower_seconds"], 20.)
        self.assertEqual(observed["status"], "passed")

    def test_unknown_intervals_do_not_imply_failure(self):
        data = {"read": np.array([1]), "target": np.array([100.]),
                "lifetime": np.array([np.nan]), "remaining": np.array([10.]),
                "model": np.array([0.])}
        metric = summarize(data, ("model",))["methods"]["model"]
        self.assertIsNone(metric["paired"])
        self.assertEqual(metric["observed_read"]["status"], "undetermined")

    def test_equality_and_zero_mean_are_not_success(self):
        self.assertFalse(mean_comparison(10., 10.)["passed"])
        comparison = mean_comparison(0., 0.)
        self.assertFalse(comparison["passed"])
        self.assertIsNone(comparison["ratio"])


if __name__ == "__main__":
    unittest.main()
