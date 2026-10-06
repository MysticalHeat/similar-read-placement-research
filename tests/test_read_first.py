import unittest

import numpy as np

from read_prediction.experiments.read_first import outcome_history, gate_metrics, choose


class ReadFirstTests(unittest.TestCase):
    def test_outcome_does_not_enter_before_read_even_if_overwrite_was_earlier(self):
        writes = np.array([0, 1, 4, 7])
        reads = np.array([3, 3, 6, 8])
        labels = np.array([False, True, True, False])
        history = outcome_history(writes, reads, np.ones(4), labels)
        self.assertTrue(np.isnan(history[1, 0]))
        np.testing.assert_allclose(history[2], [1., .5, np.log1p(2)])
        labels[2:] = False
        np.testing.assert_allclose(outcome_history(writes, reads, np.ones(4), labels)[:3], history[:3], equal_nan=True)

    def test_gate_counts_false_positives_and_publishes_coverage(self):
        metric = gate_metrics(np.array([1., 8., 5.]), np.array([1., 1., 5.]),
                              np.array([2., 1., 10.]), np.ones(3, dtype=bool),
                              np.array([True, False, True]), np.array([.99, .98, .1]), .9)
        self.assertEqual(metric["coverage"], 2/3)
        self.assertEqual(metric["read_first_precision"], .5)
        self.assertEqual(metric["selected"]["pass_lower_bound"], .5)
        self.assertFalse(metric["qualifies_selective"])

    def test_empty_selection_is_not_success(self):
        metric = gate_metrics(np.array([1.]), np.array([1.]), np.array([2.]), np.array([True]),
                              np.array([True]), np.array([.1]), .9)
        self.assertIsNone(metric["selected"])
        self.assertFalse(metric["qualifies_selective"])


if __name__ == "__main__":
    unittest.main()
