import unittest

import numpy as np

from read_prediction.pipeline import Event, TICKS_PER_SECOND, fit_baselines, make_samples, split_masks


def event(seconds, kind, offset=4096):
    return Event(int(seconds * TICKS_PER_SECOND), kind, offset, 4096)


class TargetTests(unittest.TestCase):
    def test_write_trigger_multiple_writes_and_missing_future(self):
        samples = make_samples([
            event(10, "Read"), event(15, "Write"), event(17, "Write"),
            event(18, "Read", 8192), event(20, "Read"), event(25, "Write"),
        ])
        np.testing.assert_equal(samples["targets"], [5, 3, np.nan])
        np.testing.assert_equal(samples["next_read_indices"], [4, 4, -1])

    def test_same_timestamp_uses_source_order(self):
        samples = make_samples([event(10, "Write"), event(10, "Read"), event(10, "Write")])
        np.testing.assert_equal(samples["targets"], [0, np.nan])

    def test_features_do_not_change_when_future_changes(self):
        prefix = [event(1, "Read"), event(2, "Read"), event(3, "Write")]
        early = make_samples(prefix + [event(4, "Read")])
        late = make_samples(prefix + [event(100, "Read")])
        np.testing.assert_equal(early["features"], late["features"])
        self.assertNotEqual(early["targets"][0], late["targets"][0])
        np.testing.assert_allclose(early["features"][0, [2, 3, 4, 6]], np.log1p([2, 0, 1, 1]))
        self.assertTrue(np.isnan(early["features"][0, 5]))

    def test_labels_do_not_cross_split_boundary(self):
        events = [event(i, "Read", 8192) for i in range(20)]
        events[10] = event(10, "Write")
        events[13] = event(13, "Read")
        events[14] = event(14, "Write")
        events[17] = event(17, "Read")
        events[18] = event(18, "Write")
        events[19] = event(19, "Read")
        masks, coverage = split_masks(make_samples(events), split_by="events")
        np.testing.assert_equal(masks["train"], [False, False, False])
        np.testing.assert_equal(masks["validation"], [False, False, False])
        np.testing.assert_equal(masks["test"], [False, False, True])
        self.assertEqual(coverage["train"]["right_censored"], 1)
        self.assertEqual(coverage["validation"]["right_censored"], 1)

    def test_timestamp_ties_stay_in_one_split(self):
        events = [event(i // 3, "Read") for i in range(20)]
        _, coverage = split_masks(make_samples(events), split_by="events")
        for name in ["validation", "test"]:
            start = coverage[name]["start_event"]
            self.assertLess(events[start - 1].timestamp, events[start].timestamp)

    def test_baseline_medians_and_new_address_fallback(self):
        global_median, addresses = fit_baselines([1, 1, 2], [2, 6, 20])
        self.assertEqual(global_median, 6)
        self.assertEqual(addresses[1], 4)
        self.assertEqual(addresses.get(3, global_median), 6)

    def test_duration_split_with_bursty_arrivals(self):
        events = [event(i, "Read", 8192) for i in range(11)]
        events[1] = event(1, "Write")
        events[2] = event(2, "Read")
        events[5] = event(5, "Write")
        events[7] = event(7, "Read")
        events[8] = event(8, "Write")
        events[9] = event(9, "Read")
        # Many arrivals at t=9 must not move the 60%/80% time cutoffs.
        events[10:10] = [event(9, "Read", 8192)] * 100
        masks, coverage = split_masks(make_samples(events))
        np.testing.assert_equal(masks["train"], [True, False, False])
        np.testing.assert_equal(masks["test"], [False, False, True])
        self.assertEqual(coverage["validation"]["observed_targets"], 0)
        self.assertEqual(coverage["train"]["right_censored"], 1)
        self.assertEqual(coverage["validation"]["start_seconds"], 6)
        self.assertEqual(coverage["test"]["start_seconds"], 8)


if __name__ == "__main__":
    unittest.main()
