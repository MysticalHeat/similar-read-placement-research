"""Manual labeling cases fixed by docs/protocols/range-label-protocol.md."""

import unittest

import numpy as np

from read_prediction.range_label import (
    BLOCK,
    first_future_intersecting,
    first_future_same_start,
    grid_is_noop,
    outcome_state,
    overlap_category,
    require_grid,
)


def run_case(events, queries=None):
    """events: list of (timestamp_unused, kind, offset, size); row order = list order."""
    kinds = np.array([kind for _, kind, _, _ in events])
    offsets = np.array([offset for *_, offset, _ in events], dtype=np.int64)
    sizes = np.array([size for *_, size in events], dtype=np.int64)
    require_grid(offsets, sizes)
    assert grid_is_noop(offsets, sizes)
    rows = np.arange(len(events), dtype=np.int64)
    if queries is None:
        queries = np.flatnonzero(kinds == 0)
    write = queries
    read_candidates = np.flatnonzero(kinds == 1)
    write_candidates = np.flatnonzero(kinds == 0)
    matched_read = first_future_intersecting(
        offsets[write], offsets[write] + sizes[write], rows[write],
        offsets[read_candidates], offsets[read_candidates] + sizes[read_candidates], rows[read_candidates])
    matched_write = first_future_intersecting(
        offsets[write], offsets[write] + sizes[write], rows[write],
        offsets[write_candidates], offsets[write_candidates] + sizes[write_candidates], rows[write_candidates])
    old_read = first_future_same_start(offsets[write], rows[write], offsets[read_candidates], rows[read_candidates])
    old_write = first_future_same_start(offsets[write], rows[write], offsets[write_candidates], rows[write_candidates])
    return {
        "rows": rows[write],
        "range_read": matched_read, "range_write": matched_write,
        "old_read": old_read, "old_write": old_write,
        "range_state": outcome_state(matched_read, matched_write),
        "old_state": outcome_state(old_read, old_write),
    }


class RangeLabelTests(unittest.TestCase):
    def test_partial_interior_overlap_matches_range_but_not_old(self):
        events = [(0, 0, 1024, 1024), (10, 1, 1536, 512)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], 1)
        self.assertEqual(result["old_read"][0], -1)
        self.assertEqual(result["range_state"][0], 1)
        self.assertEqual(result["old_state"][0], -1)
        self.assertEqual(overlap_category(np.array([1024]), np.array([1024]),
                                          np.array([1536]), np.array([512]))[0], 4)

    def test_covering_large_read_from_before(self):
        events = [(0, 0, 1024, 1024), (10, 1, 512, 4096)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], 1)
        self.assertEqual(result["old_read"][0], -1)
        self.assertEqual(overlap_category(np.array([1024]), np.array([1024]),
                                          np.array([512]), np.array([4096]))[0], 5)

    def test_repeated_write_destroys_version_under_range_rule(self):
        events = [(0, 0, 1024, 1024), (10, 0, 1536, 512), (20, 1, 1024, 1024)]
        result = run_case(events, queries=np.array([0]))
        self.assertEqual(result["old_read"][0], 2)
        self.assertEqual(result["old_write"][0], -1)
        self.assertEqual(result["old_state"][0], 1)
        self.assertEqual(result["range_write"][0], 1)
        self.assertEqual(result["range_state"][0], 0)

    def test_same_start_rewrite_precedes_read_under_both_rules(self):
        events = [(0, 0, 1024, 1024), (10, 0, 1024, 1024), (20, 1, 1024, 1024)]
        result = run_case(events, queries=np.array([0]))
        self.assertEqual(result["old_state"][0], 0)
        self.assertEqual(result["range_state"][0], 0)

    def test_equal_timestamps_follow_row_order(self):
        events = [(5, 0, 1024, 1024), (5, 1, 1024, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], 1)
        events_reversed = [(5, 1, 1024, 1024), (5, 0, 1024, 1024)]
        result_reversed = run_case(events_reversed)
        self.assertEqual(result_reversed["range_read"][0], -1)
        self.assertEqual(result_reversed["range_write"][0], -1)

    def test_earlier_row_same_timestamp_does_not_consume(self):
        events = [(5, 1, 1024, 1024), (5, 0, 1024, 1024), (5, 1, 1024, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], 2)

    def test_adjacent_blocks_do_not_intersect(self):
        events = [(0, 0, 1024, 1024), (10, 1, 0, 1024), (20, 1, 2048, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], -1)
        self.assertEqual(result["old_read"][0], -1)
        self.assertEqual(result["range_state"][0], -1)

    def test_no_future_events_is_censored_not_negative(self):
        events = [(0, 0, 1024, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], -1)
        self.assertEqual(result["range_write"][0], -1)
        self.assertEqual(result["range_state"][0], -1)

    def test_nearest_row_order_wins_among_candidates(self):
        events = [(0, 0, 1024, 1024), (1, 1, 1024, 1024), (2, 1, 1024, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_read"][0], 1)

    def test_first_event_wins_between_read_and_write(self):
        events = [(0, 0, 1024, 1024), (10, 0, 1536, 512), (20, 1, 1024, 512)]
        result = run_case(events)
        self.assertEqual(result["range_state"][0], 0)
        self.assertEqual(result["range_write"][0], 1)

    def test_unaligned_input_rejected_and_grid_noop(self):
        with self.assertRaises(ValueError):
            require_grid(np.array([1024]), np.array([512 + 1]))
        with self.assertRaises(ValueError):
            require_grid(np.array([1023]), np.array([512]))
        self.assertTrue(grid_is_noop(np.array([0, 1024]), np.array([512, 1024])))

    def test_multiregion_consistency(self):
        offsets = np.array([0, 0, 1 << 40], dtype=np.int64)
        sizes = np.array([1024, 1024, 1024], dtype=np.int64)
        kinds = np.array([0, 1, 1])
        rows = np.arange(3, dtype=np.int64)
        reads = np.flatnonzero(kinds == 1)
        single = first_future_intersecting(
            offsets[:1], offsets[:1] + sizes[:1], rows[:1],
            offsets[reads], offsets[reads] + sizes[reads], rows[reads], regions=1)
        for regions in (2, 3, 7, 16):
            split = first_future_intersecting(
                offsets[:1], offsets[:1] + sizes[:1], rows[:1],
                offsets[reads], offsets[reads] + sizes[reads], rows[reads], regions=regions)
            np.testing.assert_array_equal(single, split)
        self.assertEqual(single[0], 1)

    def test_same_start_matches_old_rule_with_any_size(self):
        events = [(0, 0, 1024, 4096), (10, 1, 1024, 512)]
        result = run_case(events)
        self.assertEqual(result["old_read"][0], 1)
        self.assertEqual(result["range_read"][0], 1)

    def test_self_write_not_own_overwrite(self):
        events = [(0, 0, 1024, 1024)]
        result = run_case(events)
        self.assertEqual(result["range_write"][0], -1)


if __name__ == "__main__":
    unittest.main()
