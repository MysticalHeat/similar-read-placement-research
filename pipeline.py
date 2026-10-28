"""Train and evaluate the request-count overwrite models."""
import argparse
import csv
from pathlib import Path

import lightgbm as lgb
import numpy as np

ROOT = Path(__file__).resolve().parent
EVENT_DTYPE = np.dtype([(name, '<i8') for name in ('timestamp', 'offset', 'size', 'is_read')])
KEY_DTYPE = np.dtype([('key', '<i8'), ('i', '<i8')])
HORIZONS = np.array([100, 1000, 10000, 100000])
SEGMENT = 2_000_000
DATASET_PARAMS = dict(max_bin=63, bin_construct_sample_cnt=200000, data_random_seed=42,
                      min_data_in_bin=3, feature_pre_filter=False, enable_bundle=False,
                      is_enable_sparse=False, use_missing=True, zero_as_missing=False)
TRAIN_PARAMS = dict(objective='multiclass', num_class=5, metric='None', boosting='gbdt',
                    learning_rate=0.05, num_leaves=15, max_depth=4, min_data_in_leaf=100,
                    feature_fraction=1, feature_fraction_bynode=1, bagging_fraction=1,
                    bagging_freq=0, extra_trees=False, data_sample_strategy='bagging',
                    lambda_l1=0, lambda_l2=0, min_gain_to_split=0,
                    min_sum_hessian_in_leaf=0.001, max_delta_step=0, path_smooth=0,
                    linear_tree=False, use_quantized_grad=False, device_type='cpu',
                    num_threads=1, deterministic=True, force_col_wise=True,
                    force_row_wise=False, seed=42, feature_fraction_seed=42,
                    bagging_seed=42, verbosity=0)


def keyed(offsets, indices):
    result = np.empty(len(indices), dtype=KEY_DTYPE)
    result['key'], result['i'] = offsets, indices
    return result


def transform(integer):
    integer = np.asarray(integer, dtype=np.int64)
    if integer.ndim != 2 or integer.shape[1] != 8:
        raise ValueError('Expected eight features per row')
    missing_allowed = np.zeros(integer.shape, dtype=bool)
    missing_allowed[:, [0, 1, 2, 7]] = True
    if np.any((integer < 0) & ~((integer == -1) & missing_allowed)):
        raise ValueError('Invalid feature value')
    if np.any((integer[:, [0, 1, 2, 7]] == 0)):
        raise ValueError('History distances must be positive or -1')
    result = np.log1p(np.maximum(integer, 0).astype(np.float64)).astype(np.float32)
    result[integer == -1] = np.nan
    return result


def history(events, base=0, state=None, anchors=None):
    """Build features from prior events and carry sufficient history to the next segment."""
    streams = []
    for op in (0, 1):
        index = np.flatnonzero(events['is_read'] == op).astype(np.int64) + base
        current = keyed(events['offset'][index - base], index)
        combined = np.concatenate((state[op], current)) if state is not None else current
        streams.append(combined[np.argsort(combined, order=['key', 'i'], kind='stable')])
    outgoing = []
    for op, stream in enumerate(streams):
        if not len(stream):
            outgoing.append(stream.copy())
            continue
        ends = np.r_[np.flatnonzero(stream['key'][1:] != stream['key'][:-1]) + 1, len(stream)]
        starts = np.r_[0, ends[:-1]]
        tail_start = np.repeat(ends - (3 if op == 0 else 1), ends - starts)
        keep = (np.arange(len(stream)) >= tail_start) | (stream['i'] >= base + len(events) - 100000)
        outgoing.append(stream[keep].copy())
    if anchors is None:
        return None, outgoing
    writes = np.flatnonzero(events['is_read'] == 0).astype(np.int64) + base
    a = writes[(writes >= anchors[0]) & (writes < anchors[1])]
    offsets = events['offset'][a - base].copy()
    query, left = keyed(offsets, a), keyed(offsets, np.maximum(0, a - 100000))
    previous = np.full((len(a), 4), -1, dtype=np.int64)
    integer = np.full((len(a), 8), -1, dtype=np.int64)
    integer[:, 3], integer[:, 4] = events['size'][a - base], offsets
    for op, stream in enumerate(streams):
        upper = np.searchsorted(stream, query, side='left')
        lower = np.searchsorted(stream, left, side='left')
        integer[:, 5 + op] = upper - lower
        for number in range(3 if op == 0 else 1):
            ix = upper - 1 - number
            safe = np.maximum(0, ix)
            valid = ((ix >= 0) & (stream['key'][safe] == offsets)
                     if len(stream) else np.zeros(len(a), dtype=bool))
            previous[valid, number if op == 0 else 3] = stream['i'][ix[valid]]
    for col in range(3):
        valid = previous[:, col] >= 0
        integer[valid, col] = (a[valid] - previous[valid, 0] if col == 0
                               else previous[valid, col - 1] - previous[valid, col])
    valid = previous[:, 3] >= 0
    integer[valid, 7] = a[valid] - previous[valid, 3]
    bins = np.zeros(len(a), dtype=np.int8)
    known = integer[:, 0] >= 0
    bins[known] = np.searchsorted(HORIZONS, integer[known, 0], side='left') + 1
    return {'a': a, 'offset': offsets, 'integer': integer, 'b': bins, 'X': transform(integer)}, outgoing


def labels(events, base, anchors, horizon=100000):
    """Find the next same-start write; require complete follow-up for every anchor."""
    if np.any(anchors + horizon >= base + len(events)):
        raise ValueError('Incomplete follow-up')
    writes = np.flatnonzero(events['is_read'] == 0).astype(np.int64) + base
    offsets = events['offset'][writes - base]
    order = np.argsort(offsets, kind='stable')
    left, right = order[:-1], order[1:]
    same = offsets[left] == offsets[right]
    next_write = np.full(len(writes), -1, dtype=np.int64)
    next_write[left[same]] = writes[right[same]]
    index = np.searchsorted(writes, anchors)
    if np.any(index >= len(writes)) or not np.array_equal(writes[index], anchors):
        raise ValueError('Anchors must be writes in this segment')
    end = next_write[index]
    observed = (end > anchors) & (end <= anchors + horizon)
    classes = np.full(len(anchors), 4, dtype=np.int32)
    classes[observed] = np.searchsorted(HORIZONS, end[observed] - anchors[observed], side='left')
    return classes, classes[:, None] <= np.arange(4)[None, :]


def fit_baselines(features, truth):
    keys, inv, counts = np.unique(features['offset'], return_inverse=True, return_counts=True)
    successes = np.column_stack([np.bincount(inv[truth[:, h]], minlength=len(keys)) for h in range(4)])
    bins = features['b']
    counts_by_bin = np.bincount(bins, minlength=6)
    bin_success = np.column_stack([np.bincount(bins[truth[:, h]], minlength=6) for h in range(4)])
    cells = inv * 6 + bins
    joint_counts = np.bincount(cells, minlength=len(keys) * 6)
    joint_success = np.column_stack([np.bincount(cells[truth[:, h]], minlength=len(keys) * 6) for h in range(4)])
    global_cdf = truth.mean(axis=0)
    gap_cdf = np.tile(global_cdf, (6, 1))
    known = counts_by_bin > 0
    gap_cdf[known] = bin_success[known] / counts_by_bin[known, None]
    return keys, counts, successes, global_cdf, gap_cdf, joint_counts, joint_success


def baseline_predict(baselines, features, method):
    keys, counts, successes, global_cdf, gap_cdf, joint_counts, joint_success = baselines
    offsets, bins = features['offset'], features['b']
    if method == 'G':
        return np.broadcast_to(global_cdf, (len(offsets), 4))
    if method == 'K':
        return gap_cdf[bins]
    if method not in ('A', 'J'):
        raise ValueError(method)
    ix = np.searchsorted(keys, offsets)
    safe = np.minimum(ix, len(keys) - 1)
    seen = (ix < len(keys)) & (keys[safe] == offsets)
    result = np.tile(global_cdf, (len(offsets), 1))
    result[seen] = successes[ix[seen]] / counts[ix[seen], None]
    if method == 'J':
        cells = safe * 6 + bins
        joint_n = np.zeros(len(offsets), dtype=np.int64)
        joint_n[seen] = joint_counts[cells[seen]]
        valid = joint_n > 0
        weight = joint_n[valid] / (joint_n[valid] + 20.0)
        joint = joint_success[cells[valid]] / joint_n[valid, None]
        result[valid] = weight[:, None] * joint + (1 - weight[:, None]) * result[valid]
    return result


def train_model(features, classes):
    if not np.all(np.bincount(classes, minlength=5) > 0):
        raise ValueError('Training data must contain all five classes')
    data = lgb.Dataset(features['X'], label=classes, params=DATASET_PARAMS, categorical_feature=[])
    return lgb.train(DATASET_PARAMS | TRAIN_PARAMS, data, num_boost_round=50)


def open_events(trace, data_dir=ROOT / 'dataset' / 'prepared'):
    path = Path(data_dir) / f'{trace}.bin'
    if path.stat().st_size < 11_000_000 * EVENT_DTYPE.itemsize:
        raise ValueError(f'{path} must contain at least 11 million events')
    return np.memmap(path, mode='r', dtype=EVENT_DTYPE, shape=(11_000_000,))


def run(trace, train=False, data_dir=ROOT / 'dataset' / 'prepared', output=None):
    """Use train [0,2M), evaluate [8M,10M) and [10M,11M)."""
    events = open_events(trace, data_dir)
    features, state = history(events[:SEGMENT], anchors=(0, 1_900_000))
    classes, truth = labels(events[:SEGMENT], 0, features['a'])
    controls = fit_baselines(features, truth)
    if train:
        if output is None:
            raise ValueError('Specify an output path for a newly trained model')
        output = Path(output)
        if output.exists():
            raise FileExistsError(output)
        model = train_model(features, classes)
        model.save_model(str(output))
    else:
        model = lgb.Booster(model_file=str(ROOT / 'models' / f'{trace}.lightgbm.txt'))
    del features, classes, truth
    scores = []
    for base in range(2_000_000, 10_000_001, SEGMENT):
        end = min(base + SEGMENT, 11_000_000)
        evaluation = base in (8_000_000, 10_000_000)
        features, state = history(events[base:end], base, state,
                                  (base, end - 100_000) if evaluation else None)
        if not evaluation:
            continue
        _, truth = labels(events[base:end], base, features['a'])
        for method in ('G', 'A', 'K', 'J', 'M'):
            if method == 'M':
                probabilities = model.predict(features['X'], num_threads=1)
                probabilities = probabilities / probabilities.sum(axis=1, keepdims=True)
                prediction = np.cumsum(probabilities, axis=1)[:, :4]
            else:
                prediction = baseline_predict(controls, features, method)
            brier = np.mean((prediction - truth) ** 2, axis=0)
            scores.append({'run': 'E013' if base == 8_000_000 else 'E014',
                           'trace': trace, 'N': len(truth), 'method': method,
                           **{f'brier_h{h}': float(value) for h, value in zip(HORIZONS, brier)},
                           'brier_mean4': float(brier.mean())})
        print(f'{trace}: evaluated {base:,}–{end:,}', flush=True)
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', choices=['prxy_1', 'prn_1'])
    parser.add_argument('--train', action='store_true')
    parser.add_argument('--model-output', type=Path)
    parser.add_argument('--scores-output', type=Path, required=True)
    args = parser.parse_args()
    if args.scores_output.exists():
        raise FileExistsError(args.scores_output)
    scores = run(args.trace, train=args.train, output=args.model_output)
    with args.scores_output.open('x', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=scores[0].keys())
        writer.writeheader()
        writer.writerows(scores)


if __name__ == '__main__':
    main()
