"""Request-count labels and observed-outcome metrics."""
import numpy as np

from pipeline import history


def count_labels(events, base, anchors):
    """Exact distance when observed; otherwise a right-censored lower bound."""
    anchors = np.asarray(anchors, dtype=np.int64)
    if np.any(anchors < base) or np.any(anchors >= base + len(events) - 1):
        raise ValueError('Every anchor needs at least one later event in the window')
    writes = np.flatnonzero(events['is_read'] == 0).astype(np.int64) + base
    positions = np.searchsorted(writes, anchors)
    if np.any(positions >= len(writes)) or not np.array_equal(writes[positions], anchors):
        raise ValueError('Anchors must be writes in this window')
    offsets = events['offset'][writes - base]
    order = np.argsort(offsets, kind='stable')
    left, right = order[:-1], order[1:]
    same = offsets[left] == offsets[right]
    next_write = np.full(len(writes), -1, dtype=np.int64)
    next_write[left[same]] = writes[right[same]]
    ends = next_write[positions]
    observed = ends >= 0
    lower = np.where(observed, ends - anchors, base + len(events) - 1 - anchors).astype(np.float64)
    return lower, np.where(observed, lower, np.inf), observed


def evaluate_predictions(predictions, lower, observed):
    predictions, lower, observed = map(np.asarray, (predictions, lower, observed))
    if predictions.shape != lower.shape or observed.shape != lower.shape or not observed.any():
        raise ValueError('Expected matching predictions and at least one observed target')
    pred, actual = predictions[observed], lower[observed]
    if np.any(~np.isfinite(pred)) or np.any(pred <= 0) or np.any(actual <= 0):
        raise ValueError('Counts must be finite and positive')
    error = np.abs(pred - actual)
    return {'observed_count': int(observed.sum()), 'censored_count': int((~observed).sum()),
            'mae': float(error.mean()), 'median_absolute_error': float(np.median(error)),
            'within_factor_2': float(np.mean((pred >= actual / 2) & (pred <= actual * 2)))}


def window(events, base, end, state):
    segment = events[base:end]
    features, state = history(segment, base, state, (base, end - 100_000))
    if features is None:
        raise ValueError('Feature extraction must return anchor features')
    lower, upper, observed = count_labels(segment, base, features['a'])
    return features, lower, upper, observed, state
