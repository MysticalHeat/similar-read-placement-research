import unittest

import numpy as np

from read_prediction.experiments.all_write import META
from read_prediction.experiments.window_outcome import labels, matrix


class WindowOutcomeTests(unittest.TestCase):
    def test_no_event_before_deadline_is_not_write_first(self):
        meta = np.zeros(3, dtype=META)
        meta["read"] = [20, 80, -1]
        meta["overwrite"] = [30, 90, 25]
        np.testing.assert_array_equal(labels(meta, 50), [1, 2, 0])
        np.testing.assert_array_equal(labels(meta, 100), [1, 1, 0])

    def test_deadline_is_birth_window_and_not_future_trace_end(self):
        meta = np.zeros(2, dtype=META)
        meta["timestamp"] = np.asarray([119., 121.])*3600*10_000_000
        values = matrix(np.zeros((2, 17)), meta, 0)
        np.testing.assert_allclose(values[:, -1], np.log1p(np.asarray([1., 23.])*3600), rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
