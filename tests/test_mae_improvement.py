import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import lightgbm as lgb
import numpy as np

from read_prediction.checks.mae_improvement import verify_frozen, verify_hashes
from read_prediction.experiments.mae_improvement import (
    blend, causal_history_features, choose_candidate, seconds_mae,
)
from read_prediction.extended import EVENT_DTYPE, make_compact_samples
from read_prediction.pipeline import Event, TICKS_PER_SECOND


ORIGIN = 128166372010520299


def event(seconds, kind, offset):
    return Event(ORIGIN + int(seconds * TICKS_PER_SECOND), kind, offset, 4096)


def compact(events):
    return np.asarray(
        [(item.timestamp, item.offset, item.size, item.kind == "Read") for item in events],
        dtype=EVENT_DTYPE,
    )


def independent_causal_history(events, samples):
    """Reference the label history by walking source events in row order."""
    write_rows = {int(index): row for row, index in enumerate(samples["write_indices"])}
    features = np.full((len(write_rows), 4), np.nan)
    completed, pending = {}, {}
    period = 86400 * TICKS_PER_SECOND

    for event_index, item in enumerate(events):
        if item.kind == "Read":
            for write_index in pending.pop(item.offset, []):
                target = (item.timestamp - events[write_index].timestamp) / TICKS_PER_SECOND
                completed.setdefault(item.offset, []).append(target)
            continue

        row = write_rows[event_index]
        targets = completed.get(item.offset, [])
        if targets:
            features[row, 0] = np.log1p(targets[-1])
            features[row, 1] = np.log1p(np.median(targets[-5:]))
        phase = 2 * np.pi * (item.timestamp % period) / period
        features[row, 2:] = np.sin(phase), np.cos(phase)
        pending.setdefault(item.offset, []).append(event_index)

    return features


class MaeImprovementContractTests(unittest.TestCase):
    def test_seconds_mae_inverts_log_values_and_clamps_negative_predictions(self):
        metric, value, greater_is_better = seconds_mae(
            np.log1p([10.0, 0.0]), np.asarray([np.log1p(13.0), -2.0]),
        )

        self.assertEqual(metric, "mae_seconds")
        self.assertAlmostEqual(value, 1.5)
        self.assertFalse(greater_is_better)

    def test_blend_is_convex_and_weight_is_model_fraction(self):
        model = np.asarray([10.0, 20.0])
        baseline = np.asarray([2.0, 4.0])

        np.testing.assert_array_equal(blend(model, baseline, 0), baseline)
        np.testing.assert_array_equal(blend(model, baseline, 1), model)
        np.testing.assert_allclose(blend(model, baseline, 0.25), [4.0, 8.0])

    def test_blend_rejects_weights_outside_unit_interval_and_nonfinite_weights(self):
        for weight in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                blend([1.0], [2.0], weight)

    def test_candidate_selection_uses_pooled_not_macro_daily_mae(self):
        development = {
            "few_bad_rows": {
                "2": {"n": 1, "mae_seconds": 100.0},
                "3": {"n": 999, "mae_seconds": 0.0},
                "4": {"n": 1000, "mae_seconds": 0.0},
            },
            "steady": {
                "2": {"n": 1, "mae_seconds": 2.0},
                "3": {"n": 999, "mae_seconds": 2.0},
                "4": {"n": 1000, "mae_seconds": 2.0},
            },
        }
        macro_winner = min(
            development,
            key=lambda method: sum(day["mae_seconds"] for day in development[method].values()) / 3,
        )

        self.assertEqual(macro_winner, "steady")
        self.assertEqual(choose_candidate(development), "few_bad_rows")

    def test_causal_history_features_match_independent_event_walk(self):
        events = [
            event(0, "Write", 11),
            event(1, "Read", 11),
            event(1, "Write", 11),
            event(2, "Write", 11),
            event(2, "Read", 11),
            event(2, "Write", 11),
            event(2, "Write", 22),
            event(3, "Read", 22),
            event(4, "Read", 11),
            event(4, "Write", 11),
            event(4, "Write", 22),
            event(5, "Write", 11),
            event(5, "Write", 11),
            event(5, "Write", 33),
        ]
        samples = make_compact_samples(compact(events), features_path=None)
        expected = independent_causal_history(events, samples)
        actual = causal_history_features(samples, compact(events), path=None)

        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12, equal_nan=True)
        rows = {int(index): row for row, index in enumerate(samples["write_indices"])}
        # Read-before-write at t=1 is history; write-before-read at t=2 is not.
        self.assertAlmostEqual(actual[rows[2], 0], np.log1p(1.0))
        self.assertAlmostEqual(actual[rows[3], 0], np.log1p(1.0))
        # Both writes at events 2 and 3 complete on read event 4 (one read).
        self.assertAlmostEqual(actual[rows[5], 0], np.log1p(0.0))
        self.assertTrue(np.isnan(actual[rows[0], 0]))
        self.assertTrue(np.isnan(actual[rows[6], 0]))
        self.assertTrue(np.isnan(actual[rows[13], 1]))
        self.assertEqual(samples["next_read_indices"][rows[11]], -1)
        self.assertTrue(np.isnan(samples["targets"][rows[11]]))

    def test_future_target_mutation_does_not_change_prefix_features(self):
        events = [
            event(0, "Read", 7), event(1, "Write", 7), event(2, "Write", 7),
            event(4, "Read", 7), event(5, "Write", 7), event(7, "Read", 7),
        ]
        changed = list(events)
        changed[3] = event(4.5, "Read", 7)
        before_samples = make_compact_samples(compact(events), features_path=None)
        after_samples = make_compact_samples(compact(changed), features_path=None)
        before = causal_history_features(before_samples, compact(events), path=None)
        after = causal_history_features(after_samples, compact(changed), path=None)
        before_rows = {int(index): row for row, index in enumerate(before_samples["write_indices"])}
        after_rows = {int(index): row for row, index in enumerate(after_samples["write_indices"])}

        np.testing.assert_array_equal(before_samples["features"][:2], after_samples["features"][:2])
        np.testing.assert_allclose(before[:2], after[:2], rtol=0, atol=0, equal_nan=True)
        self.assertNotEqual(before_samples["targets"][before_rows[1]], after_samples["targets"][after_rows[1]])
        np.testing.assert_allclose(before[before_rows[1]], after[after_rows[1]], rtol=0, atol=0, equal_nan=True)
        self.assertNotEqual(before[before_rows[4], 0], after[after_rows[4], 0])

    def test_best_iteration_model_is_trimmed_and_reload_predictions_match(self):
        train_x = np.linspace(0, 1, 160).reshape(-1, 1)
        val_x = np.linspace(0, 1, 80).reshape(-1, 1)
        train_y = np.log1p(10 + 90 * train_x[:, 0])
        val_y = np.log1p(10 + 90 * (1 - val_x[:, 0]))
        model = lgb.LGBMRegressor(
            objective="regression", metric="None", n_estimators=40,
            learning_rate=0.1, num_leaves=7, min_child_samples=3,
            random_state=19, n_jobs=2, deterministic=True, force_col_wise=True,
            verbosity=-1,
        )
        model.fit(
            train_x, train_y, eval_set=[(val_x, val_y)], eval_metric=seconds_mae,
            callbacks=[lgb.early_stopping(5, verbose=False), lgb.log_evaluation(0)],
        )
        best_iteration = model.best_iteration_
        self.assertGreater(best_iteration, 0)
        self.assertLess(best_iteration, model.n_estimators)

        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "trimmed.lightgbm.txt"
            model.booster_.save_model(str(model_path), num_iteration=best_iteration)
            reloaded = lgb.Booster(model_file=str(model_path))
            self.assertEqual(reloaded.num_trees(), best_iteration)
            expected = model.booster_.predict(val_x, num_iteration=best_iteration, num_threads=2)
            actual = reloaded.predict(val_x, num_threads=2)
            np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


class MaeImprovementFreezeTests(unittest.TestCase):
    def make_frozen_bundle(self, root):
        workload = "usr_1"
        output = root / "results/mae-improvement" / workload
        model_path = root / "results/next-read-24h/usr_1.lightgbm.txt"
        model_path.parent.mkdir(parents=True)
        model_path.write_bytes(b"frozen model bytes")
        output.mkdir(parents=True)

        definitions = {
            "current": {
                "kind": "model", "model_path": model_path.relative_to(root).as_posix(),
                "columns": list(range(7)),
            },
            "address_median": {"kind": "address_median", "model_path": None, "columns": []},
        }
        selection = {"selected_method": "current", "definitions": definitions}
        selection_file = output / "selection.json"
        selection_file.write_text(json.dumps(selection))
        baseline_file = output / "baselines.json"
        baseline_file.write_text(json.dumps({"global_median_seconds": 1.0, "address_medians_seconds": {}}))

        hash_paths = (selection_file, baseline_file, model_path)
        hashes = {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in hash_paths
        }
        frozen = {
            "selection": {**definitions["current"], "method": "current"},
            "selection_path": selection_file.relative_to(root).as_posix(),
            "hashes": hashes,
            "development_days": [2, 3, 4],
            "test_days": [5, 6, 7],
            "new_fits": 0,
        }
        return workload, output, selection, frozen

    def test_frozen_hashes_are_verified_at_exact_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workload, output, selection, frozen = self.make_frozen_bundle(root)

            self.assertEqual(verify_frozen(root, workload, selection, frozen, output), 3)

            (root / "results/next-read-24h/usr_1.lightgbm.txt").write_bytes(b"changed model")
            with self.assertRaisesRegex(AssertionError, "SHA256 mismatch"):
                verify_frozen(root, workload, selection, frozen, output)

    def test_hash_check_does_not_fall_back_to_historical_archive_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archived = root / "archive/code-before-restructure/old-model.txt"
            archived.parent.mkdir(parents=True)
            archived.write_bytes(b"historical bytes")
            digest = hashlib.sha256(archived.read_bytes()).hexdigest()

            with self.assertRaisesRegex(AssertionError, "Missing frozen artifact"):
                verify_hashes(root, {"old-model.txt": digest})

    def test_frozen_evaluation_rejects_any_new_fit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workload, output, selection, frozen = self.make_frozen_bundle(root)
            frozen["new_fits"] = 1

            with self.assertRaisesRegex(AssertionError, "must not fit new models"):
                verify_frozen(root, workload, selection, frozen, output)


if __name__ == "__main__":
    unittest.main()
