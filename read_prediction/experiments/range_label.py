"""Day-7 diagnostic: byte-range labeling versus exact-start-offset labeling."""

import argparse
import json
from pathlib import Path

import numpy as np

from read_prediction.experiments.overwrite90 import dump, hashes
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import (
    BLOCK,
    first_future_intersecting,
    first_future_same_start,
    grid_is_noop,
    outcome_state,
    overlap_category,
    require_grid,
)

TICKS = 10_000_000
REGIONS = 16


def slice_events(events, cutoffs):
    begin, end = int(cutoffs[6]), int(cutoffs[7])
    part = events[begin:end]
    rows = np.arange(begin, end, dtype=np.int64)
    writes = part["is_read"] == 0
    reads = ~writes
    return {
        "rows": rows, "timestamp": part["timestamp"], "offset": part["offset"], "size": part["size"],
        "write_rows": rows[writes], "write_ts": part["timestamp"][writes],
        "write_offset": part["offset"][writes], "write_size": part["size"][writes],
        "read_rows": rows[reads], "read_ts": part["timestamp"][reads],
        "read_offset": part["offset"][reads], "read_size": part["size"][reads],
    }


def masked_share(mask, values):
    """Share of `values` among rows satisfying `mask`; None when the mask is empty."""
    if not len(values) or np.count_nonzero(mask) == 0:
        return None
    return float(np.count_nonzero(values & mask) / np.count_nonzero(mask))


def counts(state):
    return {"read_first": int((state == 1).sum()), "write_first": int((state == 0).sum()),
            "censored": int((state < 0).sum()), "all_writes": int(len(state))}


def lookup_rows(part, rows, begin):
    """Positions of absolute event rows inside the contiguous day-7 slice."""
    return rows - begin


def main(workload):
    folder = PROJECT_ROOT / "results/range-label" / workload
    folder.mkdir(parents=True, exist_ok=False)
    parent = PROJECT_ROOT / "results/all-write" / workload
    source = json.loads((parent / "source.json").read_text())
    events = np.memmap(parent / "events.bin", mode="r",
                       dtype=[("timestamp", "<i8"), ("offset", "<i8"), ("size", "<i8"), ("is_read", "<i8")],
                       shape=(source["loaded_events"],))
    origin = source["first_timestamp"]
    cutoffs = {day: int(np.searchsorted(events["timestamp"], origin + day * 86400 * TICKS)) for day in (6, 7)}
    begin = cutoffs[6]
    part = slice_events(events, cutoffs)
    del events
    require_grid(part["offset"], part["size"])
    if not grid_is_noop(part["offset"], part["size"]):
        raise ValueError("512-byte grid rounding is not a no-op on real data")
    end_timestamp = min(source["last_timestamp"], origin + 168 * 3600 * TICKS)
    w_off, w_size, w_ts = part["write_offset"], part["write_size"], part["write_ts"]

    new_read = first_future_intersecting(
        w_off, w_off + w_size, part["write_rows"],
        part["read_offset"], part["read_offset"] + part["read_size"], part["read_rows"], regions=REGIONS)
    new_write = first_future_intersecting(
        w_off, w_off + w_size, part["write_rows"], w_off, w_off + w_size, part["write_rows"], regions=REGIONS)
    old_read = first_future_same_start(part["write_offset"], part["write_rows"], part["read_offset"], part["read_rows"])
    old_write = first_future_same_start(part["write_offset"], part["write_rows"], part["write_offset"], part["write_rows"])
    old_state, new_state = outcome_state(old_read, old_write), outcome_state(new_read, new_write)
    published = json.loads((parent / "diagnostic.json").read_text())
    expected = {key: published["outcomes"][key] for key in ("read_first", "write_first", "censored", "all_writes")}
    if counts(old_state) != expected:
        raise ValueError(f"Old-rule outcomes {counts(old_state)} do not reproduce published {expected}")

    def delay(match_rows):
        present = match_rows >= 0
        seconds = np.full(len(match_rows), np.nan)
        if present.any():
            position = lookup_rows(part, match_rows[present], begin)
            seconds[present] = (part["timestamp"][position] - w_ts[present]) / TICKS
        return seconds

    old_target, new_target = delay(old_read), delay(new_read)
    old_life, new_life = delay(old_write), delay(new_write)
    remainder = (end_timestamp - w_ts) / TICKS
    old_budget = np.where(old_write >= 0, old_life, remainder)
    new_budget = np.where(new_write >= 0, new_life, remainder)

    meta = np.load(parent / "meta.npy", mmap_mode="r")
    meta_begin = int(np.searchsorted(meta["write"], begin))
    meta_end = int(np.searchsorted(meta["write"], cutoffs[7]))
    with np.load(parent / "day7.predictions.npz") as saved:
        if saved["current"].shape != (meta_end - meta_begin,):
            raise ValueError("Saved day-7 predictions do not match the slice length")
        np.testing.assert_array_equal(meta["write"][meta_begin:meta_end], part["write_rows"])
        current = saved["current"].copy()
    del meta

    old_seen, new_seen = old_read >= 0, new_read >= 0
    both_seen = old_seen & new_seen
    old_pass = np.zeros(len(w_off), dtype=bool)
    old_pass[old_seen] = np.abs(old_target[old_seen] - current[old_seen]) < old_budget[old_seen]
    new_pass = np.zeros(len(w_off), dtype=bool)
    new_pass[new_seen] = np.abs(new_target[new_seen] - current[new_seen]) < new_budget[new_seen]
    old_zero = np.zeros(len(w_off), dtype=bool)
    old_zero[old_seen] = old_target[old_seen] < old_budget[old_seen]
    new_zero = np.zeros(len(w_off), dtype=bool)
    new_zero[new_seen] = new_target[new_seen] < new_budget[new_seen]

    changed_read = (old_seen != new_seen) | (old_seen & new_seen & (old_read != new_read))
    old_has_w, new_has_w = old_write >= 0, new_write >= 0
    changed_overwrite = (old_has_w != new_has_w) | (old_has_w & new_has_w & (old_write != new_write))
    if abs(masked_share(old_seen, old_pass) - published["original_observed_current"]["pass_lower_bound"]) > 1e-9:
        raise ValueError("Old-rule criterion does not reproduce the published all-write result")

    matched = np.flatnonzero(new_seen)
    category = overlap_category(
        w_off[matched], w_size[matched],
        part["offset"][lookup_rows(part, new_read[matched], begin)],
        part["size"][lookup_rows(part, new_read[matched], begin)])
    category_counts = {int(value): int(np.count_nonzero(category == value)) for value in np.unique(category)}
    overwritten = np.flatnonzero(new_has_w)
    over_offset = part["offset"][lookup_rows(part, new_write[overwritten], begin)]
    over_size = part["size"][lookup_rows(part, new_write[overwritten], begin)]
    partial_overwrite = ~((over_offset <= w_off[overwritten]) & (over_offset + over_size >= w_off[overwritten] + w_size[overwritten]))

    result = {
        "workload": workload, "independent_holdout": False,
        "source": {"loaded_events": source["loaded_events"], "first_timestamp": source["first_timestamp"],
                   "last_timestamp": source["last_timestamp"], "stop_reason": source["stop_reason"]},
        "slice": {"begin_event": begin, "end_event": cutoffs[7], "end_timestamp": int(end_timestamp),
                  "block": BLOCK, "regions": REGIONS},
        "old_outcomes": counts(old_state), "range_outcomes": counts(new_state),
        "state_transitions": {f"old{a}_new{b}": int(np.count_nonzero((old_state == a) & (new_state == b)))
                              for a in (-1, 0, 1) for b in (-1, 0, 1)},
        "changed": {"read_match_changed": int(np.count_nonzero(changed_read)),
                    "read_match_changed_bytes": int(w_size[changed_read].sum()),
                    "overwrite_match_changed": int(np.count_nonzero(changed_overwrite)),
                    "overwrite_match_changed_bytes": int(w_size[changed_overwrite].sum()),
                    "total_write_request_bytes": int(w_size.sum())},
        "partiality": {"matched_reads": int(len(matched)), "matched_read_categories": category_counts,
                       "read_first_with_intersecting_overwrite": int(np.count_nonzero((new_state == 1) & new_has_w)),
                       "partial_overwrite_of_read_first": int(np.count_nonzero(partial_overwrite & (new_state[overwritten] == 1)))},
        "criteria": {
            "old_observed_n": int(np.count_nonzero(old_seen)),
            "old_observed_current_pass": masked_share(old_seen, old_pass),
            "old_observed_zero_pass": masked_share(old_seen, old_zero),
            "range_observed_n": int(np.count_nonzero(new_seen)),
            "range_observed_current_pass": masked_share(new_seen, new_pass),
            "range_observed_zero_pass": masked_share(new_seen, new_zero),
            "both_observed_n": int(np.count_nonzero(both_seen)),
            "both_current_pass_old_target": masked_share(both_seen, old_pass),
            "both_current_pass_new_target": masked_share(both_seen, new_pass),
            "both_zero_pass_old_target": masked_share(both_seen, old_zero),
            "both_zero_pass_new_target": masked_share(both_seen, new_zero),
            "changed_read_n": int(np.count_nonzero(changed_read)),
            "changed_current_pass_old_target": masked_share(changed_read, old_pass),
            "changed_current_pass_new_target": masked_share(changed_read, new_pass),
            "published_old_pass_lower_bound": published["original_observed_current"]["pass_lower_bound"],
        },
    }
    np.savez(folder / "labeling.npz", write_index=part["write_rows"], old_read=old_read, old_write=old_write,
             new_read=new_read, new_write=new_write, old_target=old_target, new_target=new_target,
             old_budget=old_budget, new_budget=new_budget)
    inputs = [parent / name for name in ("events.bin", "meta.npy", "source.json", "day7.predictions.npz", "diagnostic.json")]
    dump(folder / "labeling.json", {**result,
         "input_hashes": hashes(inputs),
         "code_hashes": hashes([Path(__file__), PROJECT_ROOT / "read_prediction/range_label.py",
                                PROJECT_ROOT / "read_prediction/checks/range_label.py",
                                PROJECT_ROOT / "docs/protocols/range-label-protocol.md"])})
    print(f"{workload}: old={counts(old_state)}", flush=True)
    print(f"{workload}: range={counts(new_state)}", flush=True)
    print(f"{workload}: criteria={json.dumps(result['criteria'])}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    main(parser.parse_args().workload)
