"""Readable training functions embedded in the standalone submission notebook."""

from array import array
import gzip
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory

import lightgbm as lgb
import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.pipeline import FEATURE_NAMES, TICKS_PER_SECOND, TRACE_SOURCES


def load_events(dataset_directory, workload, event_limit, cache_path):
    archive_name, member_name = TRACE_SOURCES[workload]
    archive_path = dataset_directory / archive_name
    event_buffer = array("q")
    event_count = 0
    first_timestamp = None
    previous_timestamp = None
    expected_volume = None

    if event_buffer.itemsize != 8 or not np.little_endian:
        raise RuntimeError("The event cache requires little-endian 64-bit integers")

    with tarfile.open(archive_path) as archive, cache_path.open("wb") as cache:
        compressed_trace = archive.extractfile(member_name)
        if compressed_trace is None:
            raise ValueError(f"Missing trace: {member_name}")

        with compressed_trace, gzip.GzipFile(fileobj=compressed_trace) as trace:
            for line in trace:
                fields = line.strip().split(b",")
                if len(fields) != 7:
                    raise ValueError(f"Invalid source row: {event_count + 1}")

                timestamp, hostname, disk, operation, offset, size, response = fields
                timestamp = int(timestamp)
                offset = int(offset)
                size = int(size)
                volume = (hostname.decode("ascii"), int(disk))

                if first_timestamp is None:
                    first_timestamp = timestamp
                    expected_volume = volume
                if previous_timestamp is not None and timestamp < previous_timestamp:
                    raise ValueError("Source timestamps are not chronological")
                if volume != expected_volume:
                    raise ValueError("The trace contains multiple logical volumes")

                window_end = first_timestamp + 24 * 3600 * TICKS_PER_SECOND
                if timestamp >= window_end or event_count >= event_limit:
                    break
                if operation not in (b"Read", b"Write"):
                    raise ValueError("Unknown I/O operation")
                if offset < 0 or size <= 0 or int(response) < 0:
                    raise ValueError("Invalid offset, size or response time")

                event_buffer.extend((timestamp, offset, size, int(operation == b"Read")))
                event_count += 1
                previous_timestamp = timestamp

                if event_count % 250_000 == 0:
                    event_buffer.tofile(cache)
                    event_buffer = array("q")
                if event_count % 2_000_000 == 0:
                    print(f"{workload}: {event_count:,} events", flush=True)

            event_buffer.tofile(cache)

    if event_count != event_limit:
        raise ValueError(f"{workload}: incomplete source prefix")
    return np.memmap(cache_path, mode="r", dtype=EVENT_DTYPE, shape=(event_count,))


def prepare_samples(events, features_path, batch_size=250_000):
    address_order = np.argsort(events["offset"], kind="stable")
    sorted_read_flags = events["is_read"][address_order].astype(bool)
    read_positions = np.flatnonzero(sorted_read_flags)
    write_positions = np.flatnonzero(~sorted_read_flags)
    read_event_indices = address_order[read_positions]
    write_event_indices = address_order[write_positions]
    del address_order, sorted_read_flags

    read_offsets = events["offset"][read_event_indices]
    write_offsets = events["offset"][write_event_indices]
    chronological_writes = np.flatnonzero(events["is_read"] == 0)
    write_count = len(chronological_writes)

    features = np.lib.format.open_memmap(
        features_path,
        mode="w+",
        dtype=np.float64,
        shape=(write_count, len(FEATURE_NAMES)),
    )
    next_read_indices = np.full(write_count, -1, dtype=np.int64)
    target_seconds = np.full(write_count, np.nan)

    for batch_start in range(0, write_count, batch_size):
        batch_end = min(batch_start + batch_size, write_count)
        sorted_write_rows = np.arange(batch_start, batch_end)
        write_indices = write_event_indices[batch_start:batch_end]
        offsets = write_offsets[batch_start:batch_end]
        write_timestamps = events["timestamp"][write_indices]
        feature_rows = np.searchsorted(chronological_writes, write_indices)

        next_read_slots = np.searchsorted(
            read_positions,
            write_positions[batch_start:batch_end],
            side="right",
        )
        prior_read_counts = next_read_slots - np.searchsorted(read_offsets, offsets)
        prior_write_counts = sorted_write_rows - np.searchsorted(write_offsets, offsets)

        raw_features = np.full((batch_end - batch_start, len(FEATURE_NAMES)), np.nan)
        raw_features[:, 0] = offsets
        raw_features[:, 1] = events["size"][write_indices]
        raw_features[:, 2] = prior_read_counts
        raw_features[:, 3] = prior_write_counts

        previous_writes = write_event_indices[np.maximum(sorted_write_rows - 1, 0)]
        has_previous_write = prior_write_counts > 0
        raw_features[has_previous_write, 5] = (
            write_timestamps[has_previous_write]
            - events["timestamp"][previous_writes[has_previous_write]]
        ) / TICKS_PER_SECOND

        if len(read_event_indices):
            last_read_slot = len(read_event_indices) - 1
            previous_reads = read_event_indices[np.clip(next_read_slots - 1, 0, last_read_slot)]
            earlier_reads = read_event_indices[np.clip(next_read_slots - 2, 0, last_read_slot)]
            has_previous_read = prior_read_counts > 0
            has_previous_interval = prior_read_counts > 1

            raw_features[has_previous_read, 4] = (
                write_timestamps[has_previous_read]
                - events["timestamp"][previous_reads[has_previous_read]]
            ) / TICKS_PER_SECOND
            raw_features[has_previous_interval, 6] = (
                events["timestamp"][previous_reads[has_previous_interval]]
                - events["timestamp"][earlier_reads[has_previous_interval]]
            ) / TICKS_PER_SECOND

            candidate_reads = read_event_indices[np.minimum(next_read_slots, last_read_slot)]
            has_next_read = (
                (next_read_slots < len(read_event_indices))
                & (events["offset"][candidate_reads] == offsets)
            )
            completed_rows = feature_rows[has_next_read]
            next_read_indices[completed_rows] = candidate_reads[has_next_read]
            target_seconds[completed_rows] = (
                events["timestamp"][candidate_reads[has_next_read]]
                - write_timestamps[has_next_read]
            ) / TICKS_PER_SECOND

        features[feature_rows] = np.log1p(raw_features)

    features.flush()
    return {
        "features": features,
        "write_indices": chronological_writes,
        "next_read_indices": next_read_indices,
        "targets": target_seconds,
    }


def make_split_masks(samples, training_end_index):
    write_indices = samples["write_indices"]
    next_read_indices = samples["next_read_indices"]
    has_observed_target = next_read_indices >= 0

    training_mask = (
        (write_indices < training_end_index)
        & has_observed_target
        & (next_read_indices < training_end_index)
    )
    validation_mask = (write_indices >= training_end_index) & has_observed_target
    return training_mask, validation_mask


def fit_model(samples, training_mask, configuration):
    feature_columns = configuration["columns"]
    training_features = samples["features"][training_mask][:, feature_columns]
    training_targets = np.log1p(samples["targets"][training_mask])
    feature_names = [FEATURE_NAMES[column] for column in feature_columns]

    model = lgb.LGBMRegressor(**configuration["params"])
    model.fit(training_features, training_targets, feature_name=feature_names)
    return model


def predict_validation(model, samples, validation_mask, feature_columns, batch_size=250_000):
    validation_rows = np.flatnonzero(validation_mask)
    predictions = np.empty(len(validation_rows))

    for batch_start in range(0, len(validation_rows), batch_size):
        batch_end = min(batch_start + batch_size, len(validation_rows))
        batch_rows = validation_rows[batch_start:batch_end]
        batch_features = samples["features"][batch_rows][:, feature_columns]
        log_predictions = model.booster_.predict(batch_features, num_threads=2)
        predictions[batch_start:batch_end] = np.maximum(0, np.expm1(log_predictions))

    return predictions


def train_workload(workload, configuration, dataset_directory, output_directory):
    with TemporaryDirectory() as temporary_directory:
        cache_directory = Path(temporary_directory)
        events = load_events(
            dataset_directory,
            workload,
            configuration["validation_end"],
            cache_directory / "events.bin",
        )
        samples = prepare_samples(events, cache_directory / "features.npy")
        training_mask, validation_mask = make_split_masks(samples, configuration["train_end"])

        model = fit_model(samples, training_mask, configuration)
        model_path = output_directory / f"{workload}.lightgbm.txt"
        model.booster_.save_model(str(model_path))

        predictions = predict_validation(model, samples, validation_mask, configuration["columns"])
        validation_targets = samples["targets"][validation_mask]
        validation_mae = float(np.abs(validation_targets - predictions).mean())
        result = {
            "workload": workload,
            "training_samples": int(training_mask.sum()),
            "validation_samples": int(validation_mask.sum()),
            "validation_mae_seconds": validation_mae,
        }
        del samples, events, model

    return result
