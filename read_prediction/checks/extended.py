"""Independent metrics and streamed source audit for the 24h experiment."""

import gzip
import hashlib
import json
import math
import tarfile

import lightgbm as lgb
import numpy as np

from read_prediction.paths import PROJECT_ROOT, recorded_archive_path
from read_prediction.provenance import check_recorded_hash


def verify_metrics(result, workload, output):
    selected, total = {}, 0
    for split in ("validation", "test"):
        coverage = result["split_coverage"][split]
        assert coverage["writes"] == coverage["observed_targets"] + coverage["right_censored"]
        with np.load(output / f"{workload}.{split}.predictions.npz") as data:
            writes, reads = data["write_event_index"], data["next_read_event_index"]
            write_times, read_times = data["write_seconds"], data["next_read_seconds"]
            targets = data["target_seconds"]
            assert len(writes) == coverage["observed_targets"]
            assert np.all(np.diff(writes) > 0)
            assert np.all((writes >= coverage["start_event"]) & (writes < coverage["end_event_exclusive"]))
            assert np.all((reads > writes) & (reads < coverage["end_event_exclusive"]))
            assert np.all((write_times >= coverage["start_seconds"]) & (read_times <= coverage["last_event_seconds"]))
            np.testing.assert_allclose(read_times - write_times, targets, rtol=1e-10, atol=1e-9)
            for method, metric in result["metrics"][split].items():
                predictions = data[method]
                assert np.isfinite(predictions).all() and np.all(predictions >= 0)
                errors = np.abs(targets - predictions)
                independently_calculated = {
                    "mae_seconds": math.fsum(errors) / len(errors),
                    "median_absolute_error_seconds": float(np.median(errors)),
                    "p90_absolute_error_seconds": float(np.quantile(errors, .9)),
                    "rmse_seconds": math.sqrt(math.fsum(errors ** 2) / len(errors)),
                    "mae_log1p_seconds": math.fsum(np.abs(np.log1p(targets) - np.log1p(predictions))) / len(errors),
                }
                assert metric["n"] == len(errors)
                for key, value in independently_calculated.items():
                    assert math.isclose(value, metric[key], rel_tol=1e-10, abs_tol=1e-10), (workload, split, method, key)
            offsets, model_predictions = data["offset_bytes"], data["lightgbm"]
            for row in np.unique(np.linspace(0, len(writes) - 1, min(64, len(writes)), dtype=int)):
                selected[int(writes[row])] = {
                    "offset": int(offsets[row]), "read_index": int(reads[row]),
                    "target": float(targets[row]), "prediction": float(model_predictions[row]),
                }
            total += len(writes)
    return selected, total


def audit_source(result, selected, model, columns=None):
    """For selected writes, recompute history and first read in source row order.

    No grouped preparation or reference pipeline helpers are used here.
    """
    source = result["source"]
    state = {record["offset"]: [0, 0, None, None, None] for record in selected.values()}
    pending, resolved, features, expected_predictions = {}, 0, [], []
    digest = hashlib.sha256()
    with tarfile.open(recorded_archive_path(source["archive"])) as tar:
        raw = tar.extractfile(source["member"])
        assert raw is not None
        with raw, gzip.GzipFile(fileobj=raw) as stream:
            for index in range(source["loaded_events"]):
                line = stream.readline()
                assert line
                digest.update(line)
                fields = line.strip().split(b",")
                timestamp, kind, offset, size = int(fields[0]), fields[3], int(fields[4]), int(fields[5])
                if index == 0:
                    assert timestamp == source["first_timestamp"]
                if offset not in state:
                    continue
                reads, writes, last_read, last_write, last_gap = state[offset]
                if kind == b"Write":
                    if index in selected:
                        truth = selected[index]
                        assert truth["offset"] == offset
                        values = [offset, size, reads, writes,
                                  np.nan if last_read is None else (timestamp - last_read) / 10_000_000,
                                  np.nan if last_write is None else (timestamp - last_write) / 10_000_000,
                                  np.nan if last_gap is None else last_gap]
                        features.append(np.log1p(np.asarray(values, dtype=float)))
                        expected_predictions.append(truth["prediction"])
                        pending.setdefault(offset, []).append((index, timestamp))
                    state[offset][1] += 1
                    state[offset][3] = timestamp
                elif kind == b"Read":
                    for write_index, write_timestamp in pending.pop(offset, []):
                        truth = selected[write_index]
                        assert index == truth["read_index"], (write_index, index, truth["read_index"])
                        assert math.isclose((timestamp - write_timestamp) / 10_000_000, truth["target"], abs_tol=1e-12)
                        resolved += 1
                    state[offset][0] += 1
                    state[offset][4] = None if last_read is None else (timestamp - last_read) / 10_000_000
                    state[offset][2] = timestamp
                else:
                    raise AssertionError("Invalid source operation")
            excluded_line = stream.readline()
            assert excluded_line
            assert int(excluded_line.split(b",", 1)[0]) == source["first_excluded_timestamp"]
    assert digest.hexdigest() == source["prefix_sha256"]
    assert not pending and resolved == len(selected)
    matrix = np.asarray(features)
    if columns is not None:
        matrix = matrix[:, columns]
    predictions = np.maximum(0, np.expm1(model.predict(matrix, num_threads=2)))
    np.testing.assert_allclose(predictions, expected_predictions, rtol=1e-10, atol=1e-9)
    return resolved


def main():
    root = PROJECT_ROOT
    output = root / "results/next-read-24h"
    record = json.loads((output / "results.json").read_text())
    for name, expected in record["code_sha256"].items():
        check_recorded_hash(name, expected)
    pilot = json.loads((root / "results/next-read-pilot/results.json").read_text())
    verification = {}
    for workload, result in record["results"].items():
        assert result["model_params"] == pilot["results"][workload]["model_params"]
        assert result["source"]["stop_reason"] == "duration_reached"
        model = lgb.Booster(model_file=str(output / f"{workload}.lightgbm.txt"))
        assert model.feature_name() == result["feature_names"]
        selected, n_rows = verify_metrics(result, workload, output)
        audited = audit_source(result, selected, model)
        verification[workload] = {"prediction_rows_verified": n_rows, "source_writes_audited": audited,
                                  "prefix_hash_independently_verified": True,
                                  "sample_features_predictions_and_first_reads_verified": True}
        print(f"{workload}: checked {n_rows:,} saved predictions and {audited} source histories", flush=True)
    (output / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print("All extended artifact checks passed; no retraining.")


if __name__ == "__main__":
    main()
