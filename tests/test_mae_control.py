import unittest
import json
from pathlib import Path

import numpy as np

from count_mae_control import (
    conditional_success,
    exact_training_rows,
    median_three_gaps,
    round_counts,
    select_checkpoint,
    predict_records,
)
from predict import FEATURES


class MaeControlTest(unittest.TestCase):
    def test_median_uses_only_available_prior_gaps_and_has_no_upper_cap(self):
        integer = np.array([[10, 1000, 20], [10, 20, -1], [7, -1, -1],
                            [-1, -1, -1], [2_000_000, 3_000_000, 9_000_000]])
        np.testing.assert_array_equal(median_three_gaps(integer, 51),
                                      [20, 15, 7, 51, 3_000_000])

    def test_training_uses_raw_exact_targets_and_excludes_censored_bounds(self):
        X = np.array([[1., np.nan], [2., 0.], [3., 4.]], dtype=np.float32)
        lower = np.array([2., 700., 1_234_567.])
        rows, target = exact_training_rows(X, lower, np.array([True, False, True]))
        np.testing.assert_array_equal(target, [2., 1_234_567.])
        np.testing.assert_array_equal(rows, X[[0, 2]])
        with self.assertRaises(ValueError):
            exact_training_rows(X, lower, np.zeros(3, dtype=bool))

    def test_rounding_only_enforces_positive_counts_and_rejects_nonfinite(self):
        np.testing.assert_array_equal(round_counts(np.array([-2., .2, 17.7, 2e8])),
                                      [1, 1, 18, 200_000_000])
        with self.assertRaises(ValueError):
            round_counts(np.array([np.nan]))

    def test_checkpoint_is_chosen_by_validation_mae_with_earlier_tie(self):
        candidates = [{'rounds': 50, 'validation_mae': 10.},
                      {'rounds': 100, 'validation_mae': 8.},
                      {'rounds': 200, 'validation_mae': 8.}]
        self.assertEqual(select_checkpoint(candidates)['rounds'], 100)

    def test_conditional_criterion_requires_each_temporal_subblock(self):
        def methods(error):
            return {'direct_mae': {'mae': error},
                    'previous_gap': {'mae': 2}, 'median_three_gaps': {'mae': 2},
                    'training_median': {'mae': 2}}
        windows = {name: {'methods': methods(1), 'subblocks': [{'methods': methods(1)}]}
                   for name in ('validation', 'evaluation', 'evaluation_extended')}
        self.assertTrue(conditional_success(windows))
        windows['evaluation_extended']['subblocks'][0]['methods'] = methods(3)
        self.assertFalse(conditional_success(windows))

    def test_saved_control_models_replay_real_integer_predictions(self):
        output = Path(__file__).resolve().parents[1] / 'mae_control'
        for trace in ('prxy_1', 'prn_1'):
            saved = json.loads((output / f'{trace}.json').read_text())
            records = [dict(zip(FEATURES, row['integer_features'])) for row in saved['examples']]
            result = predict_records(trace, records, output)
            self.assertIn('censored', result['scope'])
            self.assertEqual([row['predicted_request_count'] for row in result['rows']],
                             [row['predictions']['direct_mae'] for row in saved['examples']])
            for row in result['rows']:
                self.assertIs(type(row['predicted_request_count']), int)
                self.assertGreater(row['predicted_request_count'], 0)


if __name__ == '__main__':
    unittest.main()
