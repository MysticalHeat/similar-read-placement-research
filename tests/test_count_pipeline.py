import unittest
import json
from pathlib import Path

import numpy as np

from pipeline import EVENT_DTYPE
from count_pipeline import count_labels, evaluate_predictions
from predict import FEATURES, predict_records


class CountPipelineTest(unittest.TestCase):
    def test_exact_and_censored_at_boundary_and_reads_count(self):
        events = np.array([(i, offset, 4, read) for i, offset, read in [
            (0, 10, 0), (1, 10, 1), (2, 20, 0), (3, 10, 0),
            (4, 20, 0), (5, 30, 0), (6, 20, 0), (7, 10, 0),
        ]], dtype=EVENT_DTYPE)
        # The event at index 6 is outside this window, despite existing in the trace.
        lower, upper, observed = count_labels(events[:6], 0, np.array([0, 2, 3, 4]))
        np.testing.assert_array_equal(lower, [3, 2, 2, 1])
        np.testing.assert_array_equal(upper[:2], [3, 2])
        self.assertTrue(np.all(np.isinf(upper[2:])))
        np.testing.assert_array_equal(observed, [True, True, False, False])

    def test_empty_followup_and_non_write_are_rejected(self):
        events = np.array([(0, 10, 4, 0), (1, 10, 4, 1)], dtype=EVENT_DTYPE)
        with self.assertRaises(ValueError):
            count_labels(events, 0, np.array([1]))
        with self.assertRaises(ValueError):
            count_labels(events[:1], 0, np.array([0]))

    def test_metrics_are_on_observed_cases_only(self):
        result = evaluate_predictions(np.array([2., 8., 99.]),
                                      np.array([2., 4., 20.]),
                                      np.array([True, True, False]))
        self.assertEqual(result['observed_count'], 2)
        self.assertEqual(result['censored_count'], 1)
        self.assertEqual(result['mae'], 2.0)
        self.assertEqual(result['median_absolute_error'], 2.0)
        self.assertEqual(result['within_factor_2'], 1.0)

    def test_saved_models_return_positive_integer_counts(self):
        examples = json.loads((Path(__file__).resolve().parents[1] / 'examples/features.json').read_text())
        for trace in ('prxy_1', 'prn_1'):
            result = predict_records(trace, examples)
            self.assertEqual(len(result['rows']), len(examples))
            for row in result['rows']:
                self.assertIs(type(row['predicted_request_count']), int)
                self.assertGreater(row['predicted_request_count'], 0)
        with self.assertRaises(ValueError):
            predict_records('prxy_1', [{'current_size': 42}])
        with self.assertRaises(ValueError):
            predict_records('unknown', examples)

    def test_exported_predictions_match_frozen_real_examples(self):
        root = Path(__file__).resolve().parents[1]
        for trace in ('prxy_1', 'prn_1'):
            saved = json.loads((root / 'mae_control' / f'{trace}.json').read_text())
            records = [dict(zip(FEATURES, example['integer_features']))
                       for example in saved['examples']]
            result = predict_records(trace, records)
            self.assertEqual([row['predicted_request_count'] for row in result['rows']],
                             [example['predictions']['direct_mae'] for example in saved['examples']])


if __name__ == '__main__':
    unittest.main()
