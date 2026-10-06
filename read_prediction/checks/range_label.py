"""Independent verification of range-label day-7 diagnostics."""

import argparse
import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import outcome_state


def reference_first(events_slice, begin, query_row, query_offset, query_size):
    """Slow exact scan after the query row; one pass, four reference answers."""
    rows = np.arange(begin, begin + len(events_slice), dtype=np.int64)
    later = rows > query_row
    intersects = (events_slice["offset"] < query_offset + query_size) & \
                 (events_slice["offset"] + events_slice["size"] > query_offset) & later
    same_start = (events_slice["offset"] == query_offset) & later
    result = {}
    for shape, mask in (("intersect", intersects), ("same_start", same_start)):
        for kind, name in ((1, "read"), (0, "write")):
            candidates = np.flatnonzero(mask & (events_slice["is_read"] == kind))
            result[f"{shape}_{name}"] = int(rows[candidates[0]]) if len(candidates) else -1
    return result


def verify(workload):
    folder = PROJECT_ROOT / "results/range-label" / workload
    parent = PROJECT_ROOT / "results/all-write" / workload
    record = json.loads((folder / "labeling.json").read_text())
    for section in ("input_hashes", "code_hashes"):
        for path, expected in record[section].items():
            assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected, path
    source = json.loads((parent / "source.json").read_text())
    events = np.memmap(parent / "events.bin", mode="r",
                       dtype=[("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")],
                       shape=(source["loaded_events"],))
    origin = source["first_timestamp"]
    begin = int(np.searchsorted(events["timestamp"], origin + 6 * 86400 * 10_000_000))
    end = int(np.searchsorted(events["timestamp"], origin + 7 * 86400 * 10_000_000))
    part = events[begin:end]
    assert record["slice"]["begin_event"] == begin and record["slice"]["end_event"] == end
    assert (part["offset"] % 512 == 0).all() and (part["size"] % 512 == 0).all()

    saved = np.load(folder / "labeling.npz")
    write_rows = saved["write_index"]
    assert np.array_equal(write_rows, np.flatnonzero(part["is_read"] == 0) + begin)
    state_old = outcome_state(saved["old_read"], saved["old_write"])
    state_new = outcome_state(saved["new_read"], saved["new_write"])
    for name, state in (("old_outcomes", state_old), ("range_outcomes", state_new)):
        for key, value in record[name].items():
            actual = {"read_first": int((state == 1).sum()), "write_first": int((state == 0).sum()),
                      "censored": int((state < 0).sum()), "all_writes": int(len(state))}[key]
            assert actual == value, (name, key, actual, value)
    published = json.loads((parent / "diagnostic.json").read_text())["outcomes"]
    for key in ("read_first", "write_first", "censored", "all_writes"):
        assert record["old_outcomes"][key] == published[key], key

    rng = np.random.default_rng(42)
    sample = np.sort(rng.choice(len(write_rows), 64, replace=False))
    mismatches = 0
    for slot in sample:
        row = int(write_rows[slot])
        offset = int(part["offset"][row - begin])
        size = int(part["size"][row - begin])
        reference = reference_first(part, begin, row, offset, size)
        for saved_key, reference_key in (("new_read", "intersect_read"), ("new_write", "intersect_write"),
                                         ("old_read", "same_start_read"), ("old_write", "same_start_write")):
            if int(saved[saved_key][slot]) != reference[reference_key]:
                mismatches += 1
    assert mismatches == 0, f"{mismatches} reference mismatches"

    with np.load(parent / "day7.predictions.npz") as day7:
        meta = np.load(parent / "meta.npy", mmap_mode="r")
        meta_begin = int(np.searchsorted(meta["write"], begin))
        meta_end = int(np.searchsorted(meta["write"], end))
        assert np.array_equal(meta["write"][meta_begin:meta_end], write_rows)
        assert day7["current"].shape == (meta_end - meta_begin,)
        current = day7["current"].copy()
        del meta
    old_seen, new_seen = saved["old_read"] >= 0, saved["new_read"] >= 0
    old_pass = np.zeros(len(write_rows), dtype=bool)
    old_pass[old_seen] = np.abs(saved["old_target"][old_seen] - current[old_seen]) < saved["old_budget"][old_seen]
    new_pass = np.zeros(len(write_rows), dtype=bool)
    new_pass[new_seen] = np.abs(saved["new_target"][new_seen] - current[new_seen]) < saved["new_budget"][new_seen]
    criteria = record["criteria"]
    checks = {
        "old_observed_current_pass": float(np.count_nonzero(old_pass) / np.count_nonzero(old_seen)),
        "range_observed_current_pass": float(np.count_nonzero(new_pass) / np.count_nonzero(new_seen)),
    }
    for key, value in checks.items():
        assert abs(criteria[key] - value) < 1e-12, (key, criteria[key], value)
    assert abs(criteria["old_observed_current_pass"] - criteria["published_old_pass_lower_bound"]) < 1e-9
    np.testing.assert_array_equal(saved["old_read"] >= 0, np.isfinite(saved["old_target"]))
    np.testing.assert_array_equal(saved["new_read"] >= 0, np.isfinite(saved["new_target"]))
    (folder / "verification.json").write_text(json.dumps({
        "workload": workload, "verified": True, "reference_sample": 64, "reference_mismatches": mismatches,
        "criteria_recomputed": checks}, indent=2) + "\n")
    print(f"{workload}: range-label verification passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    verify(parser.parse_args().workload)
