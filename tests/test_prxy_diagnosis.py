import unittest

import numpy as np

from read_prediction.experiments.diagnosis import address_extrapolation


class ExtrapolationTests(unittest.TestCase):
    def test_per_address_limits_and_new_addresses(self):
        result = address_extrapolation(
            np.array([1, 1, 2]), np.log1p([1, 2, 4]),
            np.array([1, 2, 3]), np.log1p([3, 4, 2]),
        )
        self.assertAlmostEqual(result["known_address_fraction"], 2 / 3)
        self.assertAlmostEqual(result["above_own_address_train_max_fraction"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
