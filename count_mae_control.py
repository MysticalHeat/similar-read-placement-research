"""Observed-overwrite control: direct raw-count MAE regression and causal baselines."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import lightgbm as lgb
import numpy as np
from count_metrics import extended_labels, prepare_followup, sha256, summarize, write_json
from count_pipeline import window
from pipeline import DATASET_PARAMS, ROOT, SEGMENT, history, open_events
from predict import FEATURES, TRACES, prepare_records

PROTOCOL_PATH = ROOT / 'count_mae_protocol.json'
SCOPE = 'Conditional control trained on observed overwrites; quality on censored outcomes is unknown'
BASELINES = ('previous_gap', 'median_three_gaps', 'training_median')


def round_counts(predictions):
    predictions = np.asarray(predictions, dtype=np.float64)
    if predictions.ndim != 1 or not np.all(np.isfinite(predictions)):
        raise ValueError('Expected finite scalar predictions')
    return np.maximum(1, np.rint(predictions))


def exact_training_rows(X, lower, observed):
    X, lower = np.asarray(X), np.asarray(lower, dtype=np.float64)
    observed = np.asarray(observed, dtype=bool)
    if X.ndim != 2 or lower.shape != observed.shape or len(X) != len(lower) or not observed.any():
        raise ValueError('Expected matching data and observed exact targets')
    target = lower[observed]
    if not np.all(np.isfinite(target)) or np.any(target <= 0):
        raise ValueError('Exact request counts must be finite and positive')
    return X[observed], target


def median_three_gaps(integer, fallback):
    gaps = np.asarray(integer)[:, :3]
    counts = (gaps > 0).sum(axis=1)
    ordered = np.sort(np.where(gaps > 0, gaps, np.inf), axis=1)
    known = np.flatnonzero(counts)
    prediction = np.full(len(gaps), fallback, dtype=np.float64)
    prediction[known] = (ordered[known, (counts[known] - 1) // 2]
                         + ordered[known, counts[known] // 2]) / 2
    return round_counts(prediction)


def select_checkpoint(candidates):
    return min(candidates, key=lambda candidate: (candidate['validation_mae'], candidate['rounds']))


def training_and_validation(events, protocol):
    start, end = protocol['training']['events']
    state = None
    for base in range(0, start, SEGMENT):
        _, state = history(events[base:base + SEGMENT], base, state)
    train, lower, _, observed, state = window(events, start, end, state)
    train_X, train_y = exact_training_rows(train['X'], lower, observed)
    stats = {'total_writes': len(observed), 'observed_count': int(observed.sum()),
             'censored_count': int((~observed).sum()), 'observed_fraction': float(observed.mean()),
             'target_min': float(train_y.min()), 'target_max': float(train_y.max()),
             'target_median': float(np.median(train_y)), 'target_mean': float(train_y.mean())}
    del train, lower, observed
    start, end = protocol['validation']['events']
    validation = window(events, start, end, state)
    return train_X, train_y, stats, validation


def predictions_for(features, model, fallback):
    gaps = features['integer'][:, 0]
    return {'direct_mae': round_counts(model.predict(features['X'], num_threads=1)),
            'previous_gap': round_counts(np.where(gaps > 0, gaps, fallback)),
            'median_three_gaps': median_three_gaps(features['integer'], fallback),
            'training_median': round_counts(np.full(len(gaps), fallback))}


def metric_group(predictions, lower, observed):
    return {name: summarize(values, lower, observed) for name, values in predictions.items()}


def score_view(features, predictions, lower, observed, observation_end, subblocks, protocol):
    result = {'observation_end': observation_end, 'methods': metric_group(predictions, lower, observed),
              'subblocks': [], 'distance_groups': [], 'short_long': {}}
    for start, end in subblocks:
        selected = (features['a'] >= start) & (features['a'] < end)
        values = {name: value[selected] for name, value in predictions.items()}
        result['subblocks'].append({'anchors': [start, end],
                                   'methods': metric_group(values, lower[selected], observed[selected])})

    def score_known(mask):
        count = int(mask.sum())
        values = {name: value[mask] for name, value in predictions.items()}
        metrics = metric_group(values, lower[mask], np.ones(count, dtype=bool)) if count else {}
        return {'observed_count': count, 'methods': metrics}

    for start, end in protocol['distance_groups']:
        mask = observed & (lower >= start)
        if end is not None:
            mask &= lower <= end
        result['distance_groups'].append({'range': [start, end], **score_known(mask)})
    boundary = protocol['short_long_boundary']
    result['short_long']['short'] = score_known(observed & (lower <= boundary))
    result['short_long']['long'] = score_known(observed & (lower > boundary))
    return result


def beats_references(methods):
    return methods['direct_mae']['mae'] < min(methods[name]['mae'] for name in BASELINES)


def conditional_success(windows):
    return beats_references(windows['validation']['methods']) and all(
        beats_references(block['methods']) for value in windows.values() for block in value['subblocks'])


def evaluate(trace, events, validation, model, fallback, protocol):
    val, lower, _, observed, state = validation
    predictions = predictions_for(val, model, fallback)
    results = {'validation': score_view(val, predictions, lower, observed,
                                        protocol['validation']['events'][1],
                                        protocol['subblocks']['validation'], protocol)}
    del val, lower, observed, predictions
    start, end = protocol['evaluation']['events']
    test, lower, _, observed, _ = window(events, start, end, state)
    predictions = predictions_for(test, model, fallback)
    (extended_lower, _, extended_observed), metadata = extended_labels(
        trace, events, test['a'], protocol['extended_observation_end'][trace])
    for name, target, known, observation_end in (
            ('evaluation', lower, observed, end),
            ('evaluation_extended', extended_lower, extended_observed,
             protocol['extended_observation_end'][trace])):
        if name == 'evaluation_extended' and metadata['events'][1] != observation_end:
            raise ValueError('Extended observation endpoint changed')
        results[name] = score_view(test, predictions, target, known, observation_end,
                                   protocol['subblocks']['evaluation'], protocol)
    examples = [{'event_index': int(test['a'][i]), 'integer_features': test['integer'][i].tolist(),
                 'actual': int(extended_lower[i]),
                 'predictions': {name: int(value[i]) for name, value in predictions.items()}}
                for i in np.flatnonzero(extended_observed)[:5]]
    return results, metadata, examples


def run(trace, output):
    output = Path(output).resolve()
    output.mkdir(exist_ok=True)
    if any(output.glob(f'{trace}*')):
        raise FileExistsError(f'Control artifacts already exist for {trace}')
    protocol_hash = sha256(PROTOCOL_PATH)
    protocol = json.loads(PROTOCOL_PATH.read_text())
    protocol_copy = output / 'protocol.json'
    if protocol_copy.exists():
        if sha256(protocol_copy) != protocol_hash:
            raise ValueError('Output directory contains another protocol')
    else:
        shutil.copy2(PROTOCOL_PATH, protocol_copy)
    events = open_events(trace)
    prefix_hash = sha256(ROOT / 'dataset' / 'prepared' / f'{trace}.bin')
    sidecar = json.loads((ROOT / 'dataset' / 'followup' / f'{trace}.json').read_text())
    if prefix_hash != sidecar['prefix_sha256']:
        raise ValueError('Prepared prefix identity mismatch')
    train_X, train_y, training, validation = training_and_validation(events, protocol)
    val, lower, _, observed, _ = validation
    dataset = lgb.Dataset(train_X, label=train_y, params=DATASET_PARAMS, feature_name=list(FEATURES))
    params = DATASET_PARAMS | protocol['lightgbm']
    fitted = lgb.train(params, dataset, num_boost_round=max(protocol['checkpoints']))
    candidates = []
    for rounds in protocol['checkpoints']:
        prediction = round_counts(fitted.predict(val['X'][observed], num_iteration=rounds, num_threads=1))
        score = {'rounds': rounds, 'validation_mae': float(np.abs(prediction - lower[observed]).mean())}
        candidates.append(score)
        print(f"{trace}: rounds={rounds}, validation MAE={score['validation_mae']:,.2f}", flush=True)
    chosen = select_checkpoint(candidates)
    model_path = output / f'{trace}.lightgbm.txt'
    fitted.save_model(str(model_path), num_iteration=chosen['rounds'])
    model = lgb.Booster(model_file=str(model_path))
    selection = {'trace': trace, 'scope': SCOPE, 'protocol_sha256': protocol_hash,
                 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                 'rounds': chosen['rounds'], 'validation_mae': chosen['validation_mae'],
                 'model_sha256': sha256(model_path)}
    # Freeze checkpoint before computing evaluation labels or reference scores.
    write_json(output / f'{trace}-selection.json', selection)
    del train_X, train_y, dataset, fitted, val, lower, observed
    windows, followup, examples = evaluate(trace, events, validation, model,
                                          training['target_median'], protocol)
    success = conditional_success(windows)
    result = {'schema': 'observed-overwrite-mae-control-result-v1', 'trace': trace, 'scope': SCOPE,
              'protocol_sha256': protocol_hash, 'selection': selection, 'training': training,
              'runtime': {'lightgbm': lgb.__version__, 'numpy': np.__version__},
              'dataset_params': DATASET_PARAMS, 'train_params': params, 'candidates': candidates,
              'followup': followup, 'windows': windows, 'examples': examples,
              'internal_conditional_criterion_passed': success,
              'all_writes_quality_established': False, 'deployment': 'control_only'}
    if sha256(PROTOCOL_PATH) != protocol_hash:
        raise ValueError('Protocol changed during training')
    write_json(output / f'{trace}.json', result)
    print(f'{trace}: selected {chosen["rounds"]} rounds; conditional criterion={success}', flush=True)
    return result


def load_model(trace, output):
    if trace not in TRACES:
        raise ValueError('Unknown trace model')
    output = Path(output)
    selection = json.loads((output / f'{trace}-selection.json').read_text())
    path = output / f'{trace}.lightgbm.txt'
    if selection['trace'] != trace or sha256(path) != selection['model_sha256']:
        raise ValueError('Control model identity mismatch')
    if sha256(output / 'protocol.json') != selection['protocol_sha256']:
        raise ValueError('Control protocol identity mismatch')
    model = lgb.Booster(model_file=str(path))
    if model.feature_name() != list(FEATURES) or model.current_iteration() != selection['rounds']:
        raise ValueError('Unexpected model feature order or checkpoint')
    return model


def predict_records(trace, records, output):
    _, X = prepare_records(records)
    model = load_model(trace, output)
    prediction = round_counts(model.predict(X, num_threads=1))
    return {'trace_model': trace, 'scope': SCOPE,
            'rows': [{'row': i, 'predicted_request_count': int(value)} for i, value in enumerate(prediction)]}


def require_same(actual, expected, location='result'):
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError(f'{location}: field names changed')
        for name in expected:
            require_same(actual[name], expected[name], f'{location}.{name}')
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f'{location}: list length changed')
        for i, (left, right) in enumerate(zip(actual, expected)):
            require_same(left, right, f'{location}[{i}]')
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if not np.isclose(actual, expected, rtol=1e-12, atol=1e-8):
            raise ValueError(f'{location}: {actual} != {expected}')
    elif actual != expected:
        raise ValueError(f'{location}: {actual} != {expected}')


def verify(trace, output):
    output = Path(output)
    saved = json.loads((output / f'{trace}.json').read_text())
    protocol = json.loads((output / 'protocol.json').read_text())
    if saved['selection'] != json.loads((output / f'{trace}-selection.json').read_text()):
        raise ValueError('Frozen selection changed')
    if sha256(ROOT / 'dataset' / 'prepared' / f'{trace}.bin') != saved['followup']['prefix_sha256']:
        raise ValueError('Prepared input changed')
    model = load_model(trace, output)
    events = open_events(trace)
    train_X, train_y, stats, validation = training_and_validation(events, protocol)
    del train_X, train_y
    require_same(stats, saved['training'], 'training')
    windows, metadata, examples = evaluate(trace, events, validation, model,
                                           stats['target_median'], protocol)
    require_same(windows, saved['windows'], 'windows')
    require_same(metadata, saved['followup'], 'followup')
    require_same(examples, saved['examples'], 'examples')
    require_same(conditional_success(windows), saved['internal_conditional_criterion_passed'], 'criterion')
    require_same(select_checkpoint(saved['candidates'])['rounds'], saved['selection']['rounds'], 'checkpoint')
    require_same(windows['validation']['methods']['direct_mae']['mae'],
                 saved['selection']['validation_mae'], 'selected validation MAE')
    print(f'{trace}: frozen models, all views, subblocks, distance groups and examples verified', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    for command in ('run', 'verify', 'predict', 'prepare-followup'):
        sub = subparsers.add_parser(command)
        sub.add_argument('trace', choices=TRACES)
        sub.add_argument('--output-dir', type=Path, default=ROOT / 'mae_control')
        if command == 'predict':
            sub.add_argument('--input', type=Path, required=True)
        if command == 'prepare-followup':
            sub.add_argument('--source-events', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'run':
        run(args.trace, args.output_dir)
    elif args.command == 'verify':
        verify(args.trace, args.output_dir)
    elif args.command == 'prepare-followup':
        protocol = json.loads(PROTOCOL_PATH.read_text())
        prepare_followup(args.trace, args.source_events, protocol['extended_observation_end'][args.trace])
    else:
        records = json.loads(args.input.read_text())
        print(json.dumps(predict_records(args.trace, records, args.output_dir), indent=2))


if __name__ == '__main__':
    main()
