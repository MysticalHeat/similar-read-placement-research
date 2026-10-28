import unittest

import numpy as np

from pipeline import EVENT_DTYPE, history, labels, transform


class PipelineTest(unittest.TestCase):
    def test_causal_history_across_segments(self):
        events = np.array([(0, 10, 4, 0), (1, 10, 4, 1), (2, 20, 4, 0),
                           (3, 10, 4, 0), (4, 10, 4, 0), (5, 10, 4, 1),
                           (6, 10, 4, 0)], dtype=EVENT_DTYPE)
        _, state = history(events[:3])
        segmented, _ = history(events[3:], base=3, state=state, anchors=(3, 7))
        whole, _ = history(events, anchors=(3, 7))
        np.testing.assert_array_equal(segmented['integer'], whole['integer'])
        np.testing.assert_array_equal(whole['integer'][0], [3, -1, -1, 4, 10, 1, 1, 2])
        np.testing.assert_array_equal(whole['integer'][-1], [2, 1, 3, 4, 10, 3, 2, 1])

    def test_labels_include_endpoint_and_no_overwrite(self):
        events = np.array([(i, 10 if i in (0, 3) else i + 100, 4, 0)
                           for i in range(8)], dtype=EVENT_DTYPE)
        classes, truth = labels(events, 0, np.array([0, 1]), horizon=5)
        np.testing.assert_array_equal(classes, [0, 4])
        np.testing.assert_array_equal(truth, [[True] * 4, [False] * 4])
        with self.assertRaises(ValueError):
            labels(events, 0, np.array([3]), horizon=5)

    def test_feature_transform_and_missing_validation(self):
        x = transform(np.array([[-1, -1, -1, 4096, 0, 0, 0, -1]]))
        self.assertTrue(np.isnan(x[0, 0]))
        self.assertEqual(float(x[0, 4]), 0.0)
        with self.assertRaises(ValueError):
            transform(np.array([[0, -1, -1, 4096, 0, 0, 0, -1]]))


if __name__ == '__main__':
    unittest.main()
