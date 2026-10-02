"""Bare-matrix exact CART, prospective guards and prediction-only interface.

No imports of trace code, config, filesystem, random or expectation tables.
"""
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction


class BudgetGuard:
    """Injected cumulative accounting samples, NOT a watchdog/cgroup verifier.

    sample() returns active aggregate wall/CPU seconds including prior E-stage
    and launcher overhead, from the externally agreed ledger. No human-wait time.
    phase_origin and fit_origin must be supplied by that domain, not reset here.
    """
    def __init__(self, sample, phase_origin, phase_cap, fit_origin=None):
        if phase_cap not in (15, 35, 40) or min(phase_origin) < 0:
            raise ValueError("unregistered phase")
        self.sample, self.origin, self.cap = sample, phase_origin, phase_cap
        self.fit_origin, self.previous = fit_origin, phase_origin

    def check(self):
        current = self.sample()
        if len(current) != 2 or any(not isinstance(x, (int, float)) or not 0 <= x < 120
                                    for x in current):
            raise RuntimeError("global wall/CPU cap or malformed ledger")
        if any(now < prev for now, prev in zip(current, self.previous)):
            raise RuntimeError("nonmonotonic accounting")
        if any(now - base >= self.cap for now, base in zip(current, self.origin)):
            raise RuntimeError("phase cap")
        if self.fit_origin is not None and any(now - base >= 10
                                              for now, base in zip(current, self.fit_origin)):
            raise RuntimeError("per-fit cap")
        self.previous = current


@dataclass(frozen=True)
class Node:
    label: int
    feature: int = None
    threshold: Fraction = None
    left: "Node" = None
    right: "Node" = None


def gini(counts):
    n = sum(counts)
    return Fraction(1) - sum((Fraction(c, n) ** 2 for c in counts), Fraction(0))


class Cart:
    """Root0/depth3/minleaf50, exact splits. fit is single-use; tree immutable."""
    def __init__(self):
        self.tree, self.width = None, None

    def fit(self, matrix, labels, check):
        check()
        if self.tree is not None:
            raise ValueError("refit prohibited")
        x, y = tuple(map(tuple, matrix)), tuple(labels)
        width = len(x[0]) if x else 0
        if (not x or len(x) != len(y) or width not in (1, 4)
                or any(len(r) != width or any(type(v) is not int or v < 0 for v in r) for r in x)
                or any(type(v) is not int or v not in (0, 1, 2) for v in y)):
            raise ValueError("bare integer matrix/labels required")

        def build(indices, depth):
            check()
            counts = [sum(y[i] == c for i in indices) for c in range(3)]
            label = max(range(3), key=lambda c: (counts[c], -c))
            if depth == 3 or max(counts) == len(indices) or len(indices) < 100:
                return Node(label)
            parent, best = gini(counts), None
            for f in range(width):
                check()
                ordered = sorted(indices, key=lambda i: (x[i][f], i))
                left = [0, 0, 0]
                for pos in range(1, len(ordered)):
                    check()
                    left[y[ordered[pos - 1]]] += 1
                    low, high = x[ordered[pos - 1]][f], x[ordered[pos]][f]
                    if low == high or pos < 50 or len(ordered) - pos < 50:
                        continue
                    right = [counts[c] - left[c] for c in range(3)]
                    gain = parent - (pos * gini(left) + (len(ordered) - pos) * gini(right)) / len(ordered)
                    threshold = Fraction(low + high, 2)
                    # Feature ascending/value ascending; strict gain preserves tie rule.
                    if gain > 0 and (best is None or gain > best[0]):
                        best = (gain, f, threshold)
            if best is None:
                return Node(label)
            _, f, threshold = best
            left_ids, right_ids = [], []
            for i in indices:
                check()
                (left_ids if x[i][f] <= threshold else right_ids).append(i)
            return Node(label, f, threshold, build(left_ids, depth + 1), build(right_ids, depth + 1))

        tree = build(tuple(range(len(x))), 0)
        check()
        self.width, self.tree = width, tree  # failure leaves model unfitted
        return self

    def predict(self, matrix, check):
        check()
        if self.tree is None:
            raise ValueError("unfitted")
        result = []
        for row in matrix:
            check()
            if len(row) != self.width or any(type(v) is not int or v < 0 for v in row):
                raise ValueError("feature matrix domain")
            node = self.tree
            while node.feature is not None:
                check()
                node = node.left if row[node.feature] <= node.threshold else node.right
            result.append(node.label)
        check()
        return tuple(result)


def train_case(train_matrix, train_labels, guard_a, guard_x):
    """Two benchmark fits/case. No case keys/config/recipe/eval truth passed."""
    a = Cart().fit([(r[0],) for r in train_matrix], train_labels, guard_a.check)
    x = Cart().fit(train_matrix, train_labels, guard_x.check)
    return a, x


def prediction_payload(features, a, x, check):
    """No truth argument; return payload for future exclusive durable commit.

    Caller must commit val AND test before opening either evaluation-label file.
    This function alone cannot enforce filesystem access order or four-fit count.
    """
    keys = sorted(features, key=lambda k: (k[4], k[3], k[2]))
    rows = [features[k] for k in keys]
    if any(len(r) != 4 or r[0] < r[1] or not 0 <= r[2] <= 600 for r in rows):
        raise ValueError("feature invariant")
    check()
    predictions = {"Z": tuple(0 if r[0] == 0 else 1 if r[0] < 3 else 2 for r in rows),
                   "D": (0,) * len(rows),
                   "A": a.predict([(r[0],) for r in rows], check),
                   "X": x.predict(rows, check)}
    check()
    return {m: dict(zip(keys, p)) for m, p in predictions.items()}
