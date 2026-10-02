"""Preparation-only trace/causal functions. No filesystem writer or stage runner.

Production counting uses event timestamps and byte overlap, never recipe tables.
Callers must validate a complete trace before counting. Checks are injected so a
future approved adapter can stop within loops; they are NOT external enforcement.
"""
import csv
import io
import random
from collections import Counter
from dataclasses import dataclass

PAGE = 4096
H = 600
CASES = ("phase_cycle", "independent_negative")
SPLITS = (("train", 0, 10800), ("val", 12000, 15600),
          ("test", 16800, 21600))
FIELDS = ("request_id", "timestamp", "namespace", "op", "offset_bytes", "size_bytes")


@dataclass(frozen=True)
class Event:
    request_id: str
    timestamp: int
    namespace: str
    op: str
    offset_bytes: int
    size_bytes: int


def validate(events, endpoint, check):
    if type(endpoint) is not int or endpoint <= 0 or len(events) > 30000:
        raise ValueError("endpoint/event cap")
    ids, previous = set(), -1
    for e in events:
        check()
        if (not isinstance(e, Event) or type(e.request_id) is not str
                or not e.request_id or e.request_id in ids
                or type(e.namespace) is not str or not e.namespace
                or e.op not in ("READ", "WRITE")
                or any(type(v) is not int for v in
                       (e.timestamp, e.offset_bytes, e.size_bytes))
                or e.timestamp < 0 or not previous <= e.timestamp < endpoint
                or e.offset_bytes < 0 or e.size_bytes <= 0):
            raise ValueError("malformed/duplicate ID/nonmonotonic/outside recording")
        ids.add(e.request_id)
        previous = e.timestamp
    return tuple(events)  # identical tuples with distinct IDs remain distinct


def pages(e):
    return range(e.offset_bytes // PAGE,
                 (e.offset_bytes + e.size_bytes - 1) // PAGE + 1)


def generate_csv(case, check):
    """Serialize the whole recording first; no counts/features returned."""
    if case not in CASES:
        raise ValueError("unregistered case")
    rng, rows = random.Random(42), []
    for j in range(36):
        for p in range(96):
            check()
            state = (p % 3 + j) % 3 if case == CASES[0] else rng.randrange(3)
            n = (0, 1, 4)[state]
            for delta in (() if n == 0 else (300,) if n == 1 else (60, 180, 360, 480)):
                rows.append((600 * j + delta, "READ", PAGE * p, PAGE))
    for s in (0, 12000, 16800):
        for p in range(96):
            check()
            rows.append((s + 1, "WRITE", PAGE * p, PAGE))
    rows.sort(key=lambda r: (r[0], 0 if r[1] == "WRITE" else 1, r[2]))
    if len(rows) > 14112:
        raise ValueError("case event cap")
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(FIELDS)
    for ordinal, (t, op, offset, size) in enumerate(rows):
        check()
        writer.writerow((f"{case}:{ordinal}", t, "synthetic0", op, offset, size))
    return out.getvalue()


def parse_csv(text, endpoint, check):
    reader = csv.reader(io.StringIO(text, newline=""))
    if next(reader, None) != list(FIELDS):
        raise ValueError("CSV schema")
    events = []
    for row in reader:
        check()
        if len(row) != 6 or any(not row[i].isascii() or not row[i].isdigit()
                                for i in (1, 4, 5)):
            raise ValueError("CSV malformed integer/row")
        events.append(Event(row[0], int(row[1]), row[2], row[3], int(row[4]), int(row[5])))
        if len(events) > 30000:
            raise ValueError("event cap")
    return validate(events, endpoint, check)


def mask_reason(t, start, end, endpoint):
    if t < start or t >= end:
        return "outside_segment_or_gap"
    if t - H < start:
        return "incomplete_history_reset"
    if t + H > endpoint:
        return "incomplete_recording_future"
    if t + H > end:
        return "future_crosses_segment_or_gap"
    return None


def grid(start, end):
    return tuple(range(start + H, end - H + 1, H))


def past_features(events, t, start, check):
    """U and feature matrix only: R/W since reset and strictly before t."""
    universe, r600, r300, writes, last = set(), Counter(), Counter(), Counter(), {}
    for e in events:
        check()
        if not start <= e.timestamp < t:
            continue
        for p in pages(e):
            check()
            key = (e.namespace, p)
            universe.add(key)
            if e.op == "READ":
                last[key] = max(last.get(key, e.timestamp), e.timestamp)
                r600[key] += int(e.timestamp >= t - H)
                r300[key] += int(e.timestamp >= t - 300)
            elif e.timestamp >= t - H:
                writes[key] += 1
    return {k: (r600[k], r300[k], min(t - last[k], H) if k in last else H,
                writes[k]) for k in sorted(universe)}


def future_counts(events, t, check):
    """Independent READ-only production scan, no generator/expectation access."""
    counts = Counter()
    for e in events:
        check()
        if e.op == "READ" and t <= e.timestamp < t + H:
            for p in pages(e):
                check()
                counts[e.namespace, p] += 1
    return dict(counts)


def count_label(n):
    if type(n) is not int or n < 0:
        raise ValueError("invalid count")
    return 0 if n == 0 else 1 if n < 3 else 2


def truth_and_audit(counts, eligible):
    """Separate truth output: caller supplies a past-only U, never unions it."""
    truth = {k: count_label(counts.get(k, 0)) for k in eligible}
    unseen = {k: count_label(n) for k, n in sorted(counts.items()) if k not in eligible}
    total = sum(counts.values())
    seen = sum(n for k, n in counts.items() if k in eligible)
    return truth, {"unseen_labels": unseen, "unseen_cold_errors": sum(v != 0 for v in unseen.values()),
                   "seen_incidences": seen, "all_incidences": total,
                   "coverage": None if not total else seen / total}


def feature_table(events, case, split, start, end, endpoint, check):
    rows, masks = {}, {}
    for t in grid(start, end):
        check()
        reason = mask_reason(t, start, end, endpoint)
        masks[t] = reason
        if reason is None:
            for (ns, p), values in past_features(events, t, start, check).items():
                rows[case, split, ns, p, t] = values
    return rows, masks


def label_table(events, keys, check):
    """Offline E004 label path; separate from feature_table and model interface."""
    windows, result = {}, {}
    for k in keys:
        check()
        t = k[4]
        if t not in windows:
            windows[t] = future_counts(events, t, check)
        result[k] = count_label(windows[t].get((k[2], k[3]), 0))
    return result


def metrics(truth, predicted):
    if len(truth) != len(predicted) or any(type(v) is not int or v not in (0, 1, 2)
                                         for v in (*truth, *predicted)):
        raise ValueError("label/prediction domain")
    cm = [[0] * 3 for _ in range(3)]
    for y, p in zip(truth, predicted):
        cm[y][p] += 1
    support = [sum(row) for row in cm]
    predicted_support = [sum(cm[r][c] for r in range(3)) for c in range(3)]
    den = [support[c] + predicted_support[c] for c in range(3)]
    f1 = [2 * cm[c][c] / den[c] if den[c] else 0.0 for c in range(3)]
    return {"confusion": cm, "true_support": support, "predicted_support": predicted_support,
            "f1": f1, "absent_class": [support[c] == 0 for c in range(3)],
            "f1_zero_denominator": [d == 0 for d in den], "macro_f1": sum(f1) / 3,
            "hot_precision": cm[2][2] / predicted_support[2] if predicted_support[2] else None,
            "hot_recall": cm[2][2] / support[2] if support[2] else None}


def score_release(features, committed_predictions, truth):
    """Use ONLY after a durable prediction commit and subsequent truth release.

    This pure function cannot certify durable commit timing; the adapter is absent.
    Reports one case/split, never a pooled winner. Unseen audits are separate.
    """
    keys = set(features)
    if keys != set(truth) or any(set(p) != keys for p in committed_predictions.values()):
        raise ValueError("shared key failure")
    if tuple(committed_predictions) != ("Z", "D", "A", "X"):
        raise ValueError("method order")
    if len({(k[0], k[1]) for k in keys}) != 1:
        raise ValueError("single case/split required")
    groups = {"all": keys, "zero_history": {k for k in keys if features[k][0] == 0},
              "write_only_history": {k for k in keys if features[k][0] == 0 and features[k][3] > 0}}
    groups.update({f"decision:{t}": {k for k in keys if k[4] == t} for t in sorted({k[4] for k in keys})})
    report = {}
    for name, subset in groups.items():
        ordered = sorted(subset, key=lambda k: (k[4], k[3], k[2]))
        scores = {m: metrics([truth[k] for k in ordered], [p[k] for k in ordered])
                  for m, p in committed_predictions.items()}
        report[name] = {"methods": scores, "paired_delta": {
            f"{a}-{b}": scores[a]["macro_f1"] - scores[b]["macro_f1"]
            for a, b in (("X", "Z"), ("X", "A"), ("A", "Z"))}}
    return report


if __name__ == "__main__":
    raise SystemExit("EXECUTION BLOCKED: preparation only; no verified launcher, freeze, G1/G2 or artifact adapter")
