"""UNRUN unittest specifications; synthetic fixtures/toy fits are not evidence.

Manual feature/count expectations below share no production counting helpers.
Full recipe oracle is imported only here, never by the model/production module.
"""
import unittest
from dataclasses import replace
from fractions import Fraction

import synthetic_temperature_demo as prod
from synthetic_expectations import EXPECTED_GRIDS, EXPECTED_MASKS, recipe_expectations
from synthetic_models import BudgetGuard, Cart, gini, prediction_payload


def check():
    pass  # Explicit test-only no-op; not a resource enforcement implementation.


def events(spec, endpoint=1200):
    rows = tuple(prod.Event(f"fixture:{i}", t, "fixture", op, off, size)
                 for i, (t, op, off, size) in enumerate(spec))
    return prod.validate(rows, endpoint, check)


class Fixtures(unittest.TestCase):
    def assert_window(self, rows, features, counts, endpoint=1200, start=0, t=600):
        data = events(rows, endpoint)
        self.assertIsNone(prod.mask_reason(t, start, endpoint, endpoint))
        self.assertEqual(prod.past_features(data, t, start, check), features)
        self.assertEqual(prod.future_counts(data, t, check), counts)
        return data

    def test_F0_Fk_and_threshold_two(self):
        for k, expected_label in ((0, 0), (1, 1), (2, 1), (3, 2), (4, 2)):
            rows = [(1, "WRITE", 0, 4096)] + [(600, "READ", 0, 4096)] * k
            data = self.assert_window(rows, {("fixture", 0): (0, 0, 600, 1)},
                                      {("fixture", 0): k} if k else {})
            truth, _ = prod.truth_and_audit(prod.future_counts(data, 600, check), {("fixture", 0)})
            self.assertEqual(truth, {("fixture", 0): expected_label})
            self.assertEqual(prod.count_label(k), expected_label)

    def test_Fcross_Faligned(self):
        features = {("fixture", 0): (0, 0, 600, 1), ("fixture", 1): (0, 0, 600, 1)}
        self.assert_window([(1, "WRITE", 0, 8192), (600, "READ", 4095, 2)], features,
                           {("fixture", 0): 1, ("fixture", 1): 1})
        data = self.assert_window([(1, "WRITE", 0, 8192), (600, "READ", 4096, 4096)],
                                 features, {("fixture", 1): 1})
        self.assertEqual(prod.truth_and_audit(prod.future_counts(data, 600, check), features)[0],
                         {("fixture", 0): 0, ("fixture", 1): 1})

    def test_Fties_Fmutation_no_refit(self):
        rows = [(1, "WRITE", 0, 4096), (300, "READ", 0, 4096), (599, "READ", 0, 4096),
                (600, "READ", 0, 4096), (600, "READ", 0, 4096), (1200, "READ", 0, 4096)]
        data = self.assert_window(rows, {("fixture", 0): (2, 2, 1, 1)},
                                 {("fixture", 0): 2}, endpoint=1201)
        reordered = prod.validate((*data[:3], data[4], data[3], data[5]), 1201, check)
        mutated = tuple(replace(e, op="WRITE", offset_bytes=8192) if e.timestamp >= 600 else e
                        for e in data)
        prod.validate(mutated, 1201, check)
        features = prod.past_features(data, 600, 0, check)
        for other in (reordered, mutated):
            self.assertEqual(prod.past_features(other, 600, 0, check), features)
        self.assertEqual(prod.future_counts(reordered, 600, check), {("fixture", 0): 2})
        self.assertEqual(prod.future_counts(mutated, 600, check), {})
        xrows = [(0, 0, 600, 1)] * 50 + [(2, 2, 1, 1)] * 50
        labels = [0] * 50 + [1] * 50  # toy fits, not benchmark fits
        a = Cart().fit([(r[0],) for r in xrows], labels, check)
        x = Cart().fit(xrows, labels, check)
        frozen = (a.tree, x.tree)
        key = ("toy", "val", "fixture", 0, 600)
        before = prediction_payload({key: features["fixture", 0]}, a, x, check)
        for other in (reordered, mutated):
            after = prediction_payload({key: prod.past_features(other, 600, 0, check)["fixture", 0]}, a, x, check)
            self.assertEqual(before, after)
            self.assertEqual((a.tree, x.tree), frozen)
        with self.assertRaises(ValueError):
            x.fit(xrows, labels, check)

    def test_Funseen_FboundaryU_Fcensor_Freset(self):
        data = self.assert_window([(600, "READ", 4096, 4096)], {}, {("fixture", 1): 1})
        truth, audit = prod.truth_and_audit(prod.future_counts(data, 600, check), {})
        self.assertEqual(truth, {})
        self.assertEqual(audit["unseen_labels"], {("fixture", 1): 1})
        self.assertEqual((audit["unseen_cold_errors"], audit["coverage"]), (1, 0))
        data = self.assert_window([(600, "WRITE", 0, 4096)], {}, {})
        self.assertIsNone(prod.truth_and_audit(prod.future_counts(data, 600, check), {})[1]["coverage"])
        events([(1, "WRITE", 0, 4096)], endpoint=1199)
        self.assertEqual(prod.mask_reason(600, 0, 1200, 1199), "incomplete_recording_future")
        self.assert_window([(1, "WRITE", 0, 4096), (11400, "READ", 0, 4096),
                            (12001, "WRITE", 4096, 4096)],
                           {("fixture", 1): (0, 0, 600, 1)}, {},
                           endpoint=13200, start=12000, t=12600)

    def test_R006_direct_Event_recording_bounds(self):
        zero = prod.Event("at-zero", 0, "fixture", "WRITE", 0, 4096)
        same_time = replace(zero, request_id="distinct-at-zero")
        self.assertEqual(prod.validate((zero, same_time), 1200, check), (zero, same_time))
        for timestamp in (-1, -2, 1200, 1201, True, False, 0.0, "0"):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(ValueError):
                    prod.validate((replace(zero, timestamp=timestamp),), 1200, check)
        with self.assertRaises(ValueError):
            prod.validate((replace(zero, request_id=""),), 1200, check)
        for endpoint in (0, -1, True, 1200.0):
            with self.assertRaises(ValueError):
                prod.validate((zero,), endpoint, check)
        header = ",".join(prod.FIELDS) + "\n"
        self.assertEqual(prod.parse_csv(header + "at-zero,0,fixture,WRITE,0,4096\n", 1200, check),
                         (zero,))
        for timestamp in ("-1", "-2", "1200", "True", "0.0"):
            with self.assertRaises(ValueError):
                prod.parse_csv(header + f"id,{timestamp},fixture,WRITE,0,4096\n", 1200, check)

    def test_STOP_domains_and_distinct_tuple_retention(self):
        base = prod.Event("id", 1, "fixture", "WRITE", 0, 4096)
        bad = ((base, base), (replace(base, size_bytes=0),),
               (replace(base, size_bytes=-1),), (replace(base, op="R"),),
               (replace(base, timestamp=True),), (replace(base, offset_bytes=-1),),
               (replace(base, namespace=""),), (replace(base, timestamp=2), replace(base, request_id="b")))
        for data in bad:
            with self.assertRaises(ValueError):
                prod.validate(data, 1200, check)
        data = prod.validate((base, replace(base, request_id="other")), 1200, check)
        self.assertEqual(prod.past_features(data, 600, 0, check)["fixture", 0], (0, 0, 600, 2))
        for text in ("wrong\n", ",".join(prod.FIELDS) + "\nid,1,fixture,READ,0,no\n",
                     ",".join(prod.FIELDS) + "\nid,1,fixture,READ,0,0\n"):
            with self.assertRaises(ValueError):
                prod.parse_csv(text, 1200, check)


class RecipeChecks(unittest.TestCase):
    def test_independent_bins_labels_keys_grids_and_gap_isolation(self):
        for args, expected in EXPECTED_MASKS.items():
            self.assertEqual(prod.mask_reason(*args), expected)
        for case in ("phase_cycle", "independent_negative"):
            # Serialization precedes the production scan; oracle never sees CSV/events.
            data = prod.parse_csv(prod.generate_csv(case, check), 21600, check)
            bins, expected_truth = recipe_expectations(case)
            for j in range(36):
                observed = prod.future_counts(data, j * 600, check)
                self.assertEqual({p: observed.get(("synthetic0", p), 0) for p in range(96)},
                                 {p: bins[p, j] for p in range(96)})
            id_sets, all_keys = [], set()
            for split, start, end in prod.SPLITS:
                self.assertEqual(prod.grid(start, end), EXPECTED_GRIDS[split])
                features, masks = prod.feature_table(data, case, split, start, end, 21600, check)
                wanted = {k: y for k, y in expected_truth.items() if k[1] == split}
                self.assertEqual(set(features), set(wanted))
                self.assertTrue(all(v is None for v in masks.values()))
                self.assertEqual(prod.label_table(data, features, check), wanted)
                segment = tuple(e for e in data if start <= e.timestamp < end)
                id_sets.append({e.request_id for e in segment})
                self.assertEqual(prod.feature_table(segment, case, split, start, end, 21600, check)[0], features)
                self.assertEqual(prod.label_table(segment, features, check), wanted)
                self.assertTrue(all(v[0] >= v[1] and 0 <= v[2] <= 600 for v in features.values()))
                all_keys.update(features)
            self.assertEqual(all_keys, set(expected_truth))
            self.assertFalse(id_sets[0] & id_sets[1] or id_sets[1] & id_sets[2] or id_sets[0] & id_sets[2])


class ModelAndMetrics(unittest.TestCase):
    def test_exact_CART_pure_no_gain_ties_minleaf_depth(self):
        self.assertEqual(gini([50, 50, 0]), Fraction(1, 2))
        pure = Cart().fit([(0,)] * 100, [2] * 100, check)
        self.assertEqual(pure.tree.label, 2)
        tie = Cart().fit([(0,)] * 100, [1] * 50 + [0] * 50, check)
        self.assertEqual((tie.tree.label, tie.tree.feature), (0, None))
        no_gain = Cart().fit([(0,)] * 100 + [(1,)] * 100, [0, 1] * 100, check)
        self.assertIsNone(no_gain.tree.feature)
        small = Cart().fit([(0,)] * 49 + [(1,)] * 51, [0] * 49 + [1] * 51, check)
        self.assertIsNone(small.tree.feature)
        rows = [(v, v, v, v) for v in (0, 1, 2) for _ in range(50)]
        tree = Cart().fit(rows, [0] * 50 + [1] * 50 + [0] * 50, check)
        self.assertEqual((tree.tree.feature, tree.tree.threshold), (0, Fraction(1, 2)))
        self.assertEqual(tree.predict([(0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2)], check), (0, 1, 0))
        rows = [(v,) for v in range(16) for _ in range(50)]
        tree = Cart().fit(rows, [v % 2 for v in range(16) for _ in range(50)], check)
        def bounds(node, subset, depth):
            self.assertLessEqual(depth, 3)
            if node.feature is not None:
                left = [r for r in subset if r[node.feature] <= node.threshold]
                right = [r for r in subset if r[node.feature] > node.threshold]
                self.assertGreaterEqual(min(len(left), len(right)), 50)
                bounds(node.left, left, depth + 1)
                bounds(node.right, right, depth + 1)
        bounds(tree.tree, rows, 0)

    def test_metrics_shared_keys_and_guards(self):
        result = prod.metrics([0, 1, 2], [0, 0, 2])
        self.assertEqual(result["confusion"], [[1, 0, 0], [1, 0, 0], [0, 0, 1]])
        self.assertAlmostEqual(result["macro_f1"], (2 / 3 + 0 + 1) / 3)
        empty = prod.metrics([], [])
        self.assertEqual(empty["f1_zero_denominator"], [True] * 3)
        self.assertEqual(empty["absent_class"], [True] * 3)
        self.assertIsNone(empty["hot_precision"])
        self.assertIsNone(empty["hot_recall"])
        k = ("toy", "val", "fixture", 0, 600)
        preds = {m: {k: 0} for m in ("Z", "D", "A", "X")}
        report = prod.score_release({k: (0, 0, 600, 1)}, preds, {k: 0})
        self.assertEqual(report["all"]["paired_delta"]["X-Z"], 0)
        with self.assertRaises(ValueError):
            prod.score_release({k: (0, 0, 600, 1)}, preds, {})
        BudgetGuard(lambda: (1, 1), (0, 0), 35).check()
        for sample, origin, cap, fit in (((120, 1), (0, 0), 35, None),
                                          ((35, 1), (0, 0), 35, None),
                                          ((10, 1), (0, 0), 40, (0, 0)),
                                          ((-1, 0), (0, 0), 15, None)):
            with self.assertRaises(RuntimeError):
                BudgetGuard(lambda: sample, origin, cap, fit).check()
    def test_R007_origin_shape_domain_order_and_no_constructor_sample(self):
        invalid = ((0,), (0, 0, 0), (), None, "00", ("0", 0),
                   (float("nan"), 0), (0, float("inf")), (float("-inf"), 0),
                   (-1, 0), (0, -1), (True, 0), (0, False), (120, 0), (0, 120))
        for origin in invalid:
            with self.subTest(origin=origin):
                with self.assertRaises(ValueError):
                    BudgetGuard(check, origin, 35)
                if origin is not None:  # None is the explicitly allowed absence of fit origin.
                    with self.assertRaises(ValueError):
                        BudgetGuard(check, (0, 0), 40, origin)
        for fit in ((1, 2), (2, 1)):
            with self.assertRaises(ValueError):
                BudgetGuard(check, (2, 2), 40, fit)
        for sampler in (None, 0, (1, 1)):
            with self.assertRaises(ValueError):
                BudgetGuard(sampler, (0, 0), 35)
        for cap in (14, 41, True, 35.0, "35"):
            with self.assertRaises(ValueError):
                BudgetGuard(check, (0, 0), cap)
        BudgetGuard(lambda: self.fail("constructor sampled"), (0, 0), 40, (119, 119))

    def test_R007_current_domain_future_origins_and_monotonicity(self):
        invalid = ((1,), (1, 1, 1), (), None, "11", ("1", 1),
                   (float("nan"), 1), (1, float("inf")), (float("-inf"), 1),
                   (-1, 1), (1, -1), (True, 1), (1, False), (120, 1), (1, 120))
        for current in invalid:
            with self.subTest(current=current):
                with self.assertRaises(RuntimeError):
                    BudgetGuard(lambda: current, (0, 0), 35).check()
        for current, phase, fit in (((1, 2), (2, 2), None), ((2, 1), (2, 2), None),
                                     ((11, 11), (0, 0), (20, 20)),
                                     ((2, 3), (0, 0), (3, 3)), ((3, 2), (0, 0), (3, 3))):
            with self.assertRaisesRegex(RuntimeError, "precedes accounting origin"):
                BudgetGuard(lambda: current, phase, 40, fit).check()
        for later in ((2, 3), (3, 2)):
            samples = iter(((3, 3), later))
            guard = BudgetGuard(lambda: next(samples), (0, 0), 35)
            guard.check()
            with self.assertRaisesRegex(RuntimeError, "nonmonotonic accounting"):
                guard.check()
            self.assertEqual(guard.previous, (3, 3))

    def test_R007_wall_CPU_caps_and_valid_near_boundaries(self):
        for cap in (15, 35, 40):
            BudgetGuard(lambda: (cap - 0.001, cap - 0.001), (0, 0), cap).check()
            for current in ((cap, 1), (1, cap)):
                with self.assertRaisesRegex(RuntimeError, "phase cap"):
                    BudgetGuard(lambda: current, (0, 0), cap).check()
        for current in ((10, 1), (1, 10)):
            with self.assertRaisesRegex(RuntimeError, "per-fit cap"):
                BudgetGuard(lambda: current, (0, 0), 40, (0, 0)).check()
        BudgetGuard(lambda: (9.999, 9.999), (0, 0), 40, (0, 0)).check()
        BudgetGuard(lambda: (119.999, 119.999), (110, 110), 15, (110, 110)).check()
        BudgetGuard(lambda: (5, 5), [5, 5], 40, [5, 5]).check()
        origin = [0, 0]
        guard = BudgetGuard(lambda: (1, 1), origin, 35, origin)
        origin[:] = [119, 119]
        guard.check()
        self.assertEqual((guard.origin, guard.fit_origin), ((0, 0), (0, 0)))


if __name__ == "__main__":
    unittest.main()
