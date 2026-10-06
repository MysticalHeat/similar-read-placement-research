import unittest

import numpy as np

from read_prediction.experiments.overwrite_comparison import summarize, next_overwrite
from read_prediction.extended import EVENT_DTYPE
from read_prediction.pipeline import TICKS_PER_SECOND


def compact(rows):
    return np.asarray(
        [(int(seconds * TICKS_PER_SECOND), offset, 4096, kind == "Read")
         for seconds, kind, offset in rows],
        dtype=EVENT_DTYPE,
    )


def brute_next_overwrite(events, write_indices):
    result = []
    for write_index in write_indices:
        offset = events[write_index]["offset"]
        next_index = -1
        for candidate in range(int(write_index) + 1, len(events)):
            if not events[candidate]["is_read"] and events[candidate]["offset"] == offset:
                next_index = candidate
                break
        result.append(next_index)
    return np.asarray(result, dtype=np.int64)


class NextOverwriteTests(unittest.TestCase):
    def test_all_writes_and_subsets_match_chronological_reference(self):
        events = compact([
            (86398, "Write", 11), (86398, "Write", 22), (86398, "Read", 11),
            (86401, "Write", 11), (86401, "Write", 11), (86401, "Read", 11),
            (86402, "Write", 22), (86402, "Write", 22), (86402, "Read", 22),
            (86403, "Write", 22), (86404, "Read", 22), (86405, "Write", 33),
        ])
        writes = np.flatnonzero(events["is_read"] == 0).astype(np.int64)
        expected = brute_next_overwrite(events, writes)

        actual = next_overwrite(events, writes)

        self.assertEqual(actual.dtype, np.dtype(np.int64))
        np.testing.assert_array_equal(actual, expected)
        np.testing.assert_array_equal(actual, [3, 6, 4, -1, 7, 9, -1, -1])
        subset = np.asarray([4, 7, 11, 0], dtype=np.int64)
        np.testing.assert_array_equal(next_overwrite(events, subset), brute_next_overwrite(events, subset))


class OverwriteSummaryTests(unittest.TestCase):
    def test_known_censored_and_zero_overwrites_keep_correct_denominators(self):
        data = {
            "write_event_index": np.asarray([10, 20, 30, 40, 50], dtype=np.int64),
            "next_read_event_index": np.asarray([12, 25, 32, 48, 55], dtype=np.int64),
            "target_seconds": np.asarray([5.0, 8.0, 2.0, 10.0, 4.0]),
            "current": np.asarray([4.0, 11.0, 4.0, 8.0, 2.0]),
            "address_median": np.asarray([5.0, 7.0, 3.0, 12.0, 4.0]),
            "selected": np.asarray([6.0, 8.0, 2.0, 9.0, 5.0]),
        }
        annotations = {
            "write_event_index": data["write_event_index"].copy(),
            "next_write_event_index": np.asarray([13, -1, 35, 45, -1], dtype=np.int64),
            "overwrite_seconds": np.asarray([0.0, np.nan, 4.0, 0.0, np.nan]),
            "overwrite_censor_lower_bound_seconds": np.asarray([6.0, 5.0, 7.0, 0.0, 1.0]),
            # Event indices decide order even when timestamps tie.
            "read_before_overwrite": np.asarray([True, True, True, False, True]),
        }

        result = summarize(data, annotations)

        self.assertEqual(result["n"], 5)
        self.assertEqual(result["overwrite_observed_n"], 3)
        self.assertEqual(result["overwrite_censored_n"], 2)
        self.assertEqual(result["zero_overwrite_n"], 2)
        self.assertEqual(result["read_before_overwrite_n"], 4)
        self.assertEqual(result["overwrite_before_read_n"], 1)
        self.assertAlmostEqual(result["fraction_read_before_overwrite"], 0.8)
        self.assertEqual(result["overwrite_distribution"]["n"], 3)
        self.assertAlmostEqual(result["overwrite_distribution"]["mean_seconds"], 4 / 3)
        self.assertAlmostEqual(result["overwrite_distribution"]["median_seconds"], 0.0)
        self.assertEqual(result["read_first_overwrite_distribution"]["n"], 2)

        current = result["methods"]["current"]
        self.assertAlmostEqual(current["all_mae_seconds"], 2.0)
        self.assertEqual(current["paired"]["n"], 3)
        self.assertAlmostEqual(current["paired"]["mae_seconds"], 5 / 3)
        # The two zero-duration cases fail the strict pass comparison but remain
        # in its denominator; only the positive-duration row contributes a ratio.
        self.assertAlmostEqual(current["paired"]["fraction_error_lt_overwrite"], 1 / 3)
        self.assertAlmostEqual(current["paired"]["median_error_to_overwrite_ratio"], 0.5)
        self.assertAlmostEqual(current["paired"]["p90_error_to_overwrite_ratio"], 0.5)
        self.assertAlmostEqual(current["read_first_mae_seconds"], 2.0)
        self.assertEqual(current["read_first_paired"]["n"], 2)
        self.assertAlmostEqual(current["read_first_paired"]["fraction_error_lt_overwrite"], 0.5)
        self.assertEqual(current["censored_definitely_error_lt_overwrite_n"], 1)
        self.assertAlmostEqual(current["fraction_error_lt_overwrite_lower_bound"], 0.4)
        self.assertAlmostEqual(current["fraction_error_lt_overwrite_upper_bound"], 0.6)
        errors = np.abs(data["target_seconds"] - data["current"])
        known = np.isfinite(annotations["overwrite_seconds"])
        lower = current["fraction_error_lt_overwrite_lower_bound"]
        upper = current["fraction_error_lt_overwrite_upper_bound"]
        self.assertGreaterEqual(upper, lower)
        for possible_censored_durations in ([6.0, 1.5], [6.0, 3.0]):
            possible = np.asarray(possible_censored_durations)
            self.assertTrue(np.all(possible > annotations["overwrite_censor_lower_bound_seconds"][~known]))
            true_fraction = (
                np.count_nonzero(errors[known] < annotations["overwrite_seconds"][known])
                + np.count_nonzero(errors[~known] < possible)
            ) / len(errors)
            self.assertLessEqual(lower, true_fraction)
            self.assertLessEqual(true_fraction, upper)
        self.assertTrue(np.isnan(annotations["overwrite_seconds"][1]))
        self.assertTrue(np.isnan(annotations["overwrite_seconds"][4]))


if __name__ == "__main__":
    unittest.main()
