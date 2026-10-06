import copy
import unittest

from read_prediction.submission_overwrite import combine_metrics


class SubmissionOverwriteTests(unittest.TestCase):
    def setUp(self):
        self.mean = {"observed_reads": 100, "all_writes": 200, "paired_n": 80,
                     "censored_n": 20, "methods": {"model": {
                         "observed_read": {"mae_seconds": 10.}, "paired": None}}}
        self.passes = {"observed_reads": 100, "all_writes": 200,
                       "metrics": {"mae_seconds": 10.},
                       "confirmed_pass_count": 50, "unknown_pass_count": 5,
                       "pass_lower": .5, "pass_upper": .55}

    def combine(self, passes=None):
        return combine_metrics(self.mean, passes or self.passes,
                               "trace", "range", "pooled", "model")

    def test_rejects_different_cohorts_and_mae(self):
        for field, value in (("observed_reads", 99), ("all_writes", 201),
                             ("metrics", {"mae_seconds": 11.})):
            passes = copy.deepcopy(self.passes)
            passes[field] = value
            with self.assertRaises(ValueError):
                self.combine(passes)

    def test_ninety_percent_uses_bounds_and_includes_equality(self):
        self.assertEqual(self.combine()["ninety_percent_status"], "failed")
        passes = copy.deepcopy(self.passes)
        passes.update(confirmed_pass_count=85, unknown_pass_count=5,
                      pass_lower=.85, pass_upper=.90)
        self.assertEqual(self.combine(passes)["ninety_percent_status"], "undetermined")
        passes.update(confirmed_pass_count=90, unknown_pass_count=0,
                      pass_lower=.90, pass_upper=.90)
        self.assertEqual(self.combine(passes)["ninety_percent_status"], "passed")


if __name__ == "__main__":
    unittest.main()
