"""Independently audit sampled MAE-experiment predictions against the raw trace."""

import argparse
from collections import defaultdict, deque
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import tarfile

import numpy as np

from read_prediction.checks.mae_improvement import verify_hashes
from read_prediction.paths import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "results/mae-improvement"
TICKS_PER_SECOND = 10_000_000
DAY_TICKS = 86400 * TICKS_PER_SECOND
PREDICTION_TOLERANCE = {"rtol": 1e-10, "atol": 1e-8}


def resolve_archive(source, root=PROJECT_ROOT):
    recorded = Path(source["archive"])
    candidates = [recorded if recorded.is_absolute() else root / recorded,
                  root / "dataset" / recorded.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find recorded trace archive {source['archive']!r}")


def _file_fields(line, event_index):
    try:
        fields = next(csv.reader([line.decode("ascii")]))
        assert len(fields) == 7
        timestamp, host, disk, kind, offset, size = (
            int(fields[0]), fields[1], int(fields[2]), fields[3], int(fields[4]), int(fields[5]),
        )
        assert kind in {"Read", "Write"} and offset >= 0 and size > 0
        return timestamp, host, disk, kind, offset, size
    except (UnicodeDecodeError, ValueError, StopIteration, AssertionError) as error:
        raise AssertionError(f"Invalid trace row {event_index}") from error


def scan_source_prefix(archive_path, source, examples):
    """Rebuild base/history features and next reads by a source-order event walk.

    ``examples`` maps write event indices to ``offset``, ``next_read_event_index``
    and ``target_seconds`` recorded in prediction artifacts. No sample-building or
    causal-feature helper is used here.
    """
    loaded_events = int(source["loaded_events"])
    wanted_offsets = {int(record["offset"]) for record in examples.values()}
    states = {offset: {"reads": 0, "writes": 0, "last_read": None,
                       "last_write": None, "last_read_gap": None}
              for offset in wanted_offsets}
    pending_history = {offset: deque(maxlen=5) for offset in wanted_offsets}
    completed_history = {offset: deque(maxlen=5) for offset in wanted_offsets}
    pending_examples = defaultdict(list)
    features = {}
    resolved = {}
    prefix_digest = hashlib.sha256()
    first_timestamp = last_timestamp = previous_timestamp = None
    volume = None

    with tarfile.open(archive_path) as archive:
        raw = archive.extractfile(source["member"])
        assert raw is not None, f"Trace member is missing: {source['member']}"
        with raw, gzip.GzipFile(fileobj=raw) as stream:
            for event_index in range(loaded_events):
                line = stream.readline()
                assert line, f"Trace ended before loaded_events={loaded_events} at row {event_index}"
                prefix_digest.update(line)
                timestamp, host, disk, kind, offset, size = _file_fields(line, event_index)
                if first_timestamp is None:
                    first_timestamp = timestamp
                    volume = (host, disk)
                assert previous_timestamp is None or timestamp >= previous_timestamp, (
                    f"Nonchronological source at row {event_index}"
                )
                assert (host, disk) == volume, f"Volume changed at row {event_index}"
                previous_timestamp = last_timestamp = timestamp
                if offset not in wanted_offsets:
                    continue

                state = states[offset]
                if kind == "Read":
                    read_pending = pending_history[offset]
                    for write_timestamp in read_pending:
                        completed_history[offset].append(
                            (timestamp - write_timestamp) / TICKS_PER_SECOND
                        )
                    read_pending.clear()

                    for write_index, write_timestamp in pending_examples.pop(offset, []):
                        record = examples[write_index]
                        target = (timestamp - write_timestamp) / TICKS_PER_SECOND
                        assert event_index == int(record["next_read_event_index"]), (
                            f"First-read index mismatch for write {write_index}"
                        )
                        assert math.isclose(target, float(record["target_seconds"]),
                                            rel_tol=1e-10, abs_tol=1e-9), (
                            f"Target mismatch for write {write_index}"
                        )
                        resolved[write_index] = {"read_index": event_index, "target": target}

                    if state["last_read"] is not None:
                        state["last_read_gap"] = (timestamp - state["last_read"]) / TICKS_PER_SECOND
                    state["last_read"] = timestamp
                    state["reads"] += 1
                    continue

                if event_index in examples:
                    base = [offset, size, state["reads"], state["writes"],
                            np.nan if state["last_read"] is None else
                            (timestamp - state["last_read"]) / TICKS_PER_SECOND,
                            np.nan if state["last_write"] is None else
                            (timestamp - state["last_write"]) / TICKS_PER_SECOND,
                            np.nan if state["last_read_gap"] is None else state["last_read_gap"]]
                    history = completed_history[offset]
                    extra = [np.log1p(history[-1]) if history else np.nan,
                             np.log1p(float(np.median(history))) if history else np.nan]
                    phase = 2 * np.pi * (timestamp % DAY_TICKS) / DAY_TICKS
                    feature = np.log1p(np.asarray(base, dtype=np.float64))
                    assert int(examples[event_index]["offset"]) == offset
                    features[event_index] = np.r_[feature, extra, np.sin(phase), np.cos(phase)]
                    pending_examples[offset].append((event_index, timestamp))
                pending_history[offset].append(timestamp)
                state["writes"] += 1
                state["last_write"] = timestamp

            excluded_line = stream.readline()

    assert set(features) == set(examples), "Some sampled writes were absent from the source prefix"
    assert set(resolved) == set(examples), "Some sampled writes had no observed next read"
    assert first_timestamp == source["first_timestamp"]
    assert last_timestamp == source["last_timestamp"]
    assert prefix_digest.hexdigest() == source["prefix_sha256"], "Raw source-prefix SHA256 mismatch"
    if source.get("volume") is not None:
        assert tuple(source["volume"]) == volume

    first_excluded = source.get("first_excluded_timestamp")
    if first_excluded is None:
        assert excluded_line == b"", "Expected EOF immediately after the recorded source prefix"
        assert source.get("stop_reason") == "end_of_trace"
        excluded_verified, eof_verified = False, True
    else:
        assert excluded_line, "Expected the first excluded source row"
        excluded_timestamp = _file_fields(excluded_line, loaded_events)[0]
        assert excluded_timestamp == first_excluded
        excluded_verified, eof_verified = True, False

    return {
        "features": features,
        "resolved": resolved,
        "source_events_scanned": loaded_events,
        "source_prefix_sha256": prefix_digest.hexdigest(),
        "first_excluded_timestamp_verified": excluded_verified,
        "eof_verified": eof_verified,
    }


def collect_examples(output, selection):
    examples = {}
    selected_method = selection["selected_method"]
    for day in (2, 3, 4, 5, 6, 7):
        development = day < 5
        filename = (f"day{day}.predictions.npz" if development
                    else f"holdout-day{day}.predictions.npz")
        selected_key = selected_method if development else "selected"
        with np.load(output / filename, allow_pickle=False) as data:
            fields = ("write_event_index", "offset_bytes", "next_read_event_index", "target_seconds",
                      "current", "address_median", selected_key)
            arrays = {field: data[field] for field in fields}
            component = data["selected_model_prediction"] if "selected_model_prediction" in data.files else None
            count = len(arrays["write_event_index"])
            rows = (np.unique(np.linspace(0, count - 1, min(64, count), dtype=int))
                    if count else np.empty(0, dtype=int))
            for row in rows:
                write_index = int(arrays["write_event_index"][row])
                assert write_index not in examples, f"Duplicate sampled write index {write_index}"
                examples[write_index] = {
                    "day": day,
                    "offset": int(arrays["offset_bytes"][row]),
                    "next_read_event_index": int(arrays["next_read_event_index"][row]),
                    "target_seconds": float(arrays["target_seconds"][row]),
                    "current": float(arrays["current"][row]),
                    "address_median": float(arrays["address_median"][row]),
                    "selected": float(arrays[selected_key][row]),
                    "selected_model_prediction": float(component[row]) if component is not None else None,
                }
    return examples


def _model_features(examples, walked, columns):
    assert columns and all(isinstance(column, int) and 0 <= column < 11 for column in columns)
    indices = list(examples)
    if not indices:
        return indices, np.empty((0, len(columns)), dtype=np.float64)
    matrix = np.asarray([walked["features"][index] for index in indices], dtype=np.float64)
    return indices, matrix[:, columns]


def _model_seconds(model, examples, walked, columns):
    indices, matrix = _model_features(examples, walked, columns)
    if not indices:
        return np.empty(0, dtype=np.float64)
    return np.maximum(0, np.expm1(model.predict(matrix, num_threads=2)))


def _assert_saved_prediction(examples, indices, expected, field):
    saved = np.asarray([examples[index][field] for index in indices], dtype=np.float64)
    assert np.isfinite(saved).all() and np.all(saved >= 0), f"Invalid saved {field} predictions"
    np.testing.assert_allclose(expected, saved, err_msg=f"Raw-source {field} prediction mismatch",
                               **PREDICTION_TOLERANCE)


def _load_model(root, definition, frozen_hashes, cache):
    relative = Path(definition["model_path"]).as_posix()
    assert relative in frozen_hashes, f"Model is not covered by frozen hashes: {relative}"
    if relative not in cache:
        import lightgbm as lgb

        path = root / relative
        cache[relative] = lgb.Booster(model_file=str(path))
    return relative, cache[relative]


def verify_samples(root, output, selection, frozen, baselines, examples, walked):
    definitions = selection["definitions"]
    methods = selection["selected_method"]
    current_definition = definitions["current"]
    model_cache = {}
    current_path, current_model = _load_model(root, current_definition, frozen["hashes"], model_cache)
    indices = list(examples)
    current_predictions = _model_seconds(current_model, examples, walked, current_definition["columns"])
    _assert_saved_prediction(examples, indices, current_predictions, "current")

    median = baselines["global_median_seconds"]
    address_medians = baselines["address_medians_seconds"]
    address_predictions = np.asarray([
        address_medians.get(str(examples[index]["offset"]), median) for index in indices
    ], dtype=np.float64)
    _assert_saved_prediction(examples, indices, address_predictions, "address_median")

    selected_definition = definitions[methods]
    selected_model_predictions = None
    model_hashes = {current_path: hashlib.sha256((root / current_path).read_bytes()).hexdigest()}
    if selected_definition["kind"] == "address_median":
        selected_predictions = address_predictions
    else:
        model_method = (selected_definition["model_method"]
                        if selected_definition["kind"] == "blend" else methods)
        model_definition = definitions[model_method]
        selected_path, selected_model = _load_model(root, model_definition, frozen["hashes"], model_cache)
        model_hashes[selected_path] = hashlib.sha256((root / selected_path).read_bytes()).hexdigest()
        selected_model_predictions = _model_seconds(
            selected_model, examples, walked, model_definition["columns"],
        )
        if selected_definition["kind"] == "blend":
            selected_predictions = (
                selected_definition["model_weight"] * selected_model_predictions
                + (1 - selected_definition["model_weight"]) * address_predictions
            )
            component_positions = [
                position for position, index in enumerate(indices)
                if examples[index]["selected_model_prediction"] is not None
            ]
            if component_positions:
                saved_component = np.asarray([
                    examples[indices[position]]["selected_model_prediction"]
                    for position in component_positions
                ], dtype=np.float64)
                np.testing.assert_allclose(selected_model_predictions[component_positions], saved_component,
                                           err_msg="Saved selected model component mismatch",
                                           **PREDICTION_TOLERANCE)
        else:
            selected_predictions = selected_model_predictions

    _assert_saved_prediction(examples, indices, selected_predictions, "selected")
    return model_hashes


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_workload(workload, root=PROJECT_ROOT):
    assert workload in {"usr_1", "prxy_1"}
    output = root / "results/mae-improvement" / workload
    selection = json.loads((output / "selection.json").read_text())
    frozen = json.loads((output / "frozen.json").read_text())
    holdout = json.loads((output / "holdout.json").read_text())
    baselines = json.loads((output / "baselines.json").read_text())
    verification_path = output / "verification.json"
    assert verification_path.is_file(), "Run the artifact checker before the source audit"

    frozen_hash_count = verify_hashes(root, frozen["hashes"])
    examples = collect_examples(output, selection)
    source = holdout["source"]
    walked = scan_source_prefix(resolve_archive(source, root), source, examples)
    model_hashes = verify_samples(root, output, selection, frozen, baselines, examples, walked)

    code_hash = _sha256(Path(__file__))
    source_verification = {
        "workload": workload,
        "source_samples_audited": len(examples),
        "source_events_scanned": walked["source_events_scanned"],
        "source_prefix_hash_independently_verified": True,
        "source_prefix_sha256_expected": source["prefix_sha256"],
        "source_prefix_sha256_actual": walked["source_prefix_sha256"],
        "first_excluded_timestamp_verified": walked["first_excluded_timestamp_verified"],
        "eof_verified": walked["eof_verified"],
        "frozen_hashes_verified": frozen_hash_count,
        "model_sha256": model_hashes,
        "auditor_code_sha256": code_hash,
        "selected_prediction_reconstruction_verified": True,
        "new_fits": 0,
    }
    (output / "source-verification.json").write_text(
        json.dumps(source_verification, indent=2, allow_nan=False) + "\n"
    )

    verification = json.loads(verification_path.read_text())
    verification.update({
        "source_samples_audited": len(examples),
        "source_audit_skipped_reason": None,
        "selected_prediction_reconstruction_verified": True,
        "source_prefix_hash_independently_verified": True,
    })
    verification_path.write_text(json.dumps(verification, indent=2, allow_nan=False) + "\n")
    return source_verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True, choices=("usr_1", "prxy_1"))
    args = parser.parse_args(argv)
    print(json.dumps(audit_workload(args.workload), indent=2))


if __name__ == "__main__":
    main()
