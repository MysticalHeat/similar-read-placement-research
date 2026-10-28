"""Shared result and follow-up helpers for the count experiment."""
import hashlib
import json
from pathlib import Path

import numpy as np

from count_pipeline import count_labels, evaluate_predictions
from pipeline import EVENT_DTYPE, ROOT


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')


def sha256(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def summarize(predictions, lower, observed):
    result = evaluate_predictions(predictions, lower, observed)
    actual = lower[observed]
    errors = np.abs(predictions[observed] - actual)
    count = max(1, int(np.ceil(.01 * len(errors))))
    tail = np.partition(errors, len(errors) - count)[-count:].sum()
    result.update(observed_fraction=float(observed.mean()),
                  actual_mean=float(actual.mean()), actual_median=float(np.median(actual)),
                  mae_over_actual_mean=float(result['mae'] / actual.mean()),
                  p99_absolute_error=float(np.quantile(errors, .99)),
                  max_prediction=float(np.max(predictions)),
                  top_1_percent_error_share=float(tail / errors.sum()) if errors.sum() else 0.)
    return result


def extended_labels(trace, events, anchors, expected_end):
    metadata = json.loads((ROOT / 'dataset' / 'followup' / f'{trace}.json').read_text())
    path = ROOT / 'dataset' / 'followup' / f'{trace}.bin'
    if metadata['events'] != [11_000_000, expected_end] or sha256(path) != metadata['sha256']:
        raise ValueError('Follow-up identity mismatch')
    tail = np.memmap(path, mode='r', dtype=EVENT_DTYPE)
    segment = np.concatenate((events[10_000_000:11_000_000], tail))
    return count_labels(segment, 10_000_000, anchors), metadata


def prepare_followup(trace, source, end):
    source = Path(source)
    prepared = ROOT / 'dataset' / 'prepared' / f'{trace}.bin'
    output = ROOT / 'dataset' / 'followup'
    output.mkdir(exist_ok=True)
    path, metadata_path = output / f'{trace}.bin', output / f'{trace}.json'
    if path.exists() or metadata_path.exists():
        raise FileExistsError(path)
    prefix_bytes = 11_000_000 * EVENT_DTYPE.itemsize
    if prepared.stat().st_size != prefix_bytes or source.stat().st_size < end * EVENT_DTYPE.itemsize:
        raise ValueError('Unexpected prepared input size or insufficient follow-up')
    prefix_hash = hashlib.sha256()
    with source.open('rb') as raw:
        remaining = prefix_bytes
        while remaining:
            chunk = raw.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise ValueError('Truncated source')
            prefix_hash.update(chunk)
            remaining -= len(chunk)
        if prefix_hash.hexdigest() != sha256(prepared):
            raise ValueError('Full source does not match the prepared event prefix')
        tail = raw.read((end - 11_000_000) * EVENT_DTYPE.itemsize)
    if len(tail) != (end - 11_000_000) * EVENT_DTYPE.itemsize:
        raise ValueError('Truncated follow-up')
    with path.open('xb') as file:
        file.write(tail)
    metadata = {'trace': trace, 'source': str(source.resolve()),
                'events': [11_000_000, end], 'prefix_sha256': prefix_hash.hexdigest(),
                'sha256': sha256(path), 'bytes': len(tail)}
    write_json(metadata_path, metadata)
    print(json.dumps(metadata, indent=2))
