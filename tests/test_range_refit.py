"""Synthetic cases for full-prefix range labeling used by the refit stage."""

import unittest

import numpy as np

from read_prediction.range_label import TICKS, label_writes

EVENT_DTYPE = [("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")]


def make_events(rows):
    array = np.array(rows, dtype=EVENT_DTYPE)
    return array


class LabelWritesTests(unittest.TestCase):
    def test_intersect_read_and_overwrite_with_targets(self):
        events = make_events([
            (0, 1024, 1024, 0),            # W0, query
            (10 * TICKS, 1024, 1024, 1),   # R1 intersects -> target 10s
            (20 * TICKS, 1536, 512, 0),    # W2 intersects -> lifetime 20s
        ])
        labels = label_writes(events, np.array([0]), begin=0)
        self.assertEqual(labels["read"][0], 1)
        self.assertEqual(labels["overwrite"][0], 2)
        self.assertEqual(labels["target"][0], 10.0)
        self.assertEqual(labels["lifetime"][0], 20.0)

    def test_no_future_events_is_censored(self):
        events = make_events([(0, 1024, 1024, 0)])
        labels = label_writes(events, np.array([0]), begin=0)
        self.assertEqual(labels["read"][0], -1)
        self.assertEqual(labels["overwrite"][0], -1)
        self.assertTrue(np.isnan(labels["target"][0]))
        self.assertTrue(np.isnan(labels["lifetime"][0]))

    def test_equal_timestamps_follow_row_order(self):
        events = make_events([
            (5 * TICKS, 1024, 1024, 0),
            (5 * TICKS, 1024, 1024, 1),
            (5 * TICKS, 1024, 1024, 0),
        ])
        labels = label_writes(events, np.array([0]), begin=0)
        self.assertEqual(labels["read"][0], 1)
        self.assertEqual(labels["overwrite"][0], 2)

    def test_query_rows_must_not_precede_begin(self):
        events = make_events([
            (0, 1024, 1024, 0),
            (10 * TICKS, 1024, 1024, 1),
        ])
        with self.assertRaises(ValueError):
            label_writes(events, np.array([0]), begin=1)

    def test_later_begin_excludes_earlier_candidates(self):
        events = make_events([
            (0, 1024, 1024, 1),              # R0 before begin -> not a candidate
            (10 * TICKS, 1024, 1024, 0),     # W1, query
            (20 * TICKS, 1024, 1024, 1),     # R2 intersects
        ])
        labels = label_writes(events, np.array([1]), begin=1)
        self.assertEqual(labels["read"][0], 2)

    def test_multiple_queries_and_write_first(self):
        events = make_events([
            (0, 1024, 2048, 0),            # W0 query
            (1 * TICKS, 1280, 512, 0),     # W1 intersects W0 interior -> W0 write-first
            (2 * TICKS, 2048, 512, 0),     # W2 query, intersects nothing later
            (3 * TICKS, 4096, 512, 1),     # R3 intersects nothing
        ])
        labels = label_writes(events, np.array([0, 2]), begin=0)
        self.assertEqual(labels["overwrite"][0], 1)
        self.assertEqual(labels["read"][0], -1)
        self.assertEqual(labels["read"][1], -1)
        self.assertEqual(labels["overwrite"][1], -1)

    def test_targets_use_event_timestamps(self):
        events = make_events([
            (100 * TICKS, 1024, 512, 0),
            (350 * TICKS, 1024, 512, 1),
        ])
        labels = label_writes(events, np.array([0]), begin=0)
        self.assertEqual(labels["target"][0], 250.0)

    def test_full_array_indexing_with_nonzero_begin(self):
        """Regression: candidates before `begin` must not shift query assembly."""
        events = make_events([
            (0 * TICKS, 8192, 512, 1),      # R0 before begin, different offset
            (10 * TICKS, 1024, 512, 0),     # W1, query
            (20 * TICKS, 1024, 512, 1),     # R2 intersects the query
            (30 * TICKS, 8192, 512, 1),     # R3 would match only a shifted query
        ])
        labels = label_writes(events, np.array([1]), begin=1)
        self.assertEqual(labels["read"][0], 2)
        self.assertEqual(labels["overwrite"][0], -1)


if __name__ == "__main__":
    unittest.main()
