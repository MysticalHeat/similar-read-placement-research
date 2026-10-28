"""Predict a numerical I/O-request count from prepared causal features."""
import argparse
import json
from pathlib import Path

import numpy as np
from pipeline import ROOT, transform

FEATURES = ('gap1', 'gap2', 'gap3', 'current_size', 'current_offset',
            'past_W_100k', 'past_R_100k', 'read_age')
MISSING = {'gap1', 'gap2', 'gap3', 'read_age'}
TRACES = ('prxy_1', 'prn_1')


def prepare_records(records):
    if not isinstance(records, list) or not 1 <= len(records) <= 10000:
        raise ValueError('Expected 1..10000 feature objects')
    rows = []
    for record in records:
        if not isinstance(record, dict) or set(record) != set(FEATURES):
            raise ValueError('Each record must have exactly the eight named features')
        row = []
        for name in FEATURES:
            value = record[name]
            if value is None and name in MISSING:
                value = -1
            if type(value) is not int or not -1 <= value <= np.iinfo(np.int64).max:
                raise ValueError(f'{name} must be an int64 integer or allowed missing value')
            row.append(value)
        rows.append(row)
    integer = np.array(rows, dtype=np.int64)
    return integer, transform(integer)


def predict_records(trace, records):
    from count_mae_control import predict_records as predict
    return predict(trace, records, ROOT / 'mae_control')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', choices=TRACES, required=True)
    parser.add_argument('--input', type=Path, required=True, help='JSON list of prepared features')
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding='utf-8'))
    print(json.dumps(predict_records(args.trace, records), indent=2))


if __name__ == '__main__':
    main()
