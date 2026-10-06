"""Exact byte-range labeling of Write outcomes on the 512-byte grid.

All MSR Cambridge offsets and sizes are divisible by 512, so half-open byte
ranges [offset, offset + size) are unions of complete 512-byte blocks and
byte-level intersection is identical to intersection on the 512-byte grid.
The first later event (source row order) whose range intersects the written
range decides the outcome; ties follow trace row order exactly like every
previous stage. See docs/protocols/range-label-protocol.md.
"""

import numpy as np

BLOCK = 512
_INDEX_BITS = 31
_INDEX_MASK = (1 << _INDEX_BITS) - 1
_INDEX_MOD = 1 << _INDEX_BITS


def require_grid(offsets, sizes):
    offsets = np.asarray(offsets, dtype=np.int64)
    sizes = np.asarray(sizes, dtype=np.int64)
    if (offsets < 0).any() or (sizes <= 0).any() or (offsets % BLOCK).any() or (sizes % BLOCK).any():
        raise ValueError("Events must have nonnegative 512-byte aligned offsets and positive aligned sizes")


def grid_is_noop(offsets, sizes):
    """Rounding endpoints to the 512-byte grid must not change any range."""
    offsets = np.asarray(offsets, dtype=np.int64)
    sizes = np.asarray(sizes, dtype=np.int64)
    return bool(
        np.array_equal(offsets // BLOCK * BLOCK, offsets)
        and np.array_equal((offsets + sizes + BLOCK - 1) // BLOCK * BLOCK, offsets + sizes)
    )


def _expand_blocks(starts, ends, indices):
    """Per-event half-open block spans to flat (block, index) pairs."""
    counts = np.maximum(ends - starts, 0)
    total = int(counts.sum())
    if not total:
        empty_i = np.empty(0, dtype=np.int64)
        return empty_i, empty_i
    block = np.repeat(starts - np.cumsum(counts, dtype=np.int64) + counts, counts) + np.arange(total, dtype=np.int64)
    pair_index = np.repeat(indices, counts)
    return block, pair_index


def _keys(blocks, indices):
    return (blocks.astype(np.int64) << _INDEX_BITS) | (_INDEX_MOD - 1 - indices)


def first_future_intersecting(query_starts, query_ends, query_indices,
                              candidate_starts, candidate_ends, candidate_indices,
                              regions=16):
    """For each query range, the smallest candidate row index greater than the
    query's own index whose byte range intersects the query range; -1 if none.

    Exact on the 512-byte grid: candidates are expanded to per-block pairs and
    processed region by region to bound memory. Key packing assumes more than
    2**31 events and fewer than 2**32 blocks (both hold for these traces).
    """
    query_starts = np.asarray(query_starts, dtype=np.int64)
    query_ends = np.asarray(query_ends, dtype=np.int64)
    query_indices = np.asarray(query_indices, dtype=np.int64)
    candidate_starts = np.asarray(candidate_starts, dtype=np.int64)
    candidate_ends = np.asarray(candidate_ends, dtype=np.int64)
    candidate_indices = np.asarray(candidate_indices, dtype=np.int64)
    if (query_indices >= _INDEX_MOD - 1).any() or (candidate_indices >= _INDEX_MOD - 1).any():
        raise ValueError("Row indices must fit the packed key width")
    result = np.full(len(query_indices), np.iinfo(np.int64).max, dtype=np.int64)
    if not len(candidate_indices) or not len(query_indices):
        return np.where(result == np.iinfo(np.int64).max, -1, result)
    q_begin, q_end = query_starts // BLOCK, query_ends // BLOCK
    c_begin, c_end = candidate_starts // BLOCK, candidate_ends // BLOCK
    span = max(int(c_end.max()), int(q_end.max()))
    c_total = int((c_end - c_begin).sum())
    needed = 1
    while needed * 30_000_000 < c_total:
        needed *= 2
    regions = max(regions, needed)
    region_size = -(-span // regions)
    for lo in range(0, span, region_size):
        hi = lo + region_size
        csel = np.flatnonzero((c_begin < hi) & (c_end > lo))
        qsel = np.flatnonzero((q_begin < hi) & (q_end > lo))
        if not len(csel) or not len(qsel):
            continue
        cblocks, cindex = _expand_blocks(
            np.maximum(c_begin[csel], lo), np.minimum(c_end[csel], hi), candidate_indices[csel])
        ckeys = _keys(cblocks, cindex)
        ckeys.sort()
        if int(ckeys.nbytes) > 6_400_000_000:
            raise ValueError("Region pair budget exceeded; increase regions")
        qblocks, qindex = _expand_blocks(
            np.maximum(q_begin[qsel], lo), np.minimum(q_end[qsel], hi), query_indices[qsel])
        qkeys = _keys(qblocks, qindex)
        position = np.searchsorted(ckeys, qkeys, side="left")
        previous = position - 1
        valid = (previous >= 0) & (ckeys[np.maximum(previous, 0)] >> _INDEX_BITS == qblocks)
        found = np.where(valid, _INDEX_MOD - 1 - (ckeys[np.maximum(previous, 0)] & _INDEX_MASK),
                         np.iinfo(np.int64).max)
        boundaries = np.zeros(len(qsel) + 1, dtype=np.int64)
        np.cumsum(np.minimum(q_end[qsel], hi) - np.maximum(q_begin[qsel], lo), out=boundaries[1:])
        per_query = np.minimum.reduceat(found, boundaries[:-1])
        result[qsel] = np.minimum(result[qsel], per_query)
    return np.where(result == np.iinfo(np.int64).max, -1, result)


def first_future_same_start(query_offsets, query_indices, candidate_offsets, candidate_indices):
    """Previous-stage rule: first later candidate with the identical start offset."""
    query_offsets = np.asarray(query_offsets, dtype=np.int64)
    query_indices = np.asarray(query_indices, dtype=np.int64)
    candidate_offsets = np.asarray(candidate_offsets, dtype=np.int64)
    candidate_indices = np.asarray(candidate_indices, dtype=np.int64)
    result = np.full(len(query_offsets), -1, dtype=np.int64)
    if not len(candidate_indices) or not len(query_offsets):
        return result
    unique = np.unique(candidate_offsets)
    rank = np.searchsorted(unique, candidate_offsets)
    keys = (rank.astype(np.int64) << _INDEX_BITS) | candidate_indices
    order = np.argsort(keys, kind="stable")
    keys = keys[order]
    sorted_candidates = candidate_indices[order]
    qrank = np.searchsorted(unique, query_offsets)
    present = (qrank < len(unique)) & (unique[np.minimum(qrank, len(unique) - 1)] == query_offsets)
    qkeys = (qrank.astype(np.int64) << _INDEX_BITS) | (query_indices + 1)
    position = np.searchsorted(keys, qkeys, side="left")
    valid = present & (position < len(keys))
    safe = np.minimum(position, len(keys) - 1)
    same = valid & (keys[safe] >> _INDEX_BITS == qrank)
    result[same] = sorted_candidates[safe[same]]
    return result


def outcome_state(read_index, overwrite_index):
    """1 = Read-first, 0 = Write-first, -1 = unresolved before the boundary."""
    state = np.full(len(read_index), -1, dtype=np.int8)
    read = np.where(read_index >= 0, read_index, np.iinfo(np.int64).max)
    write = np.where(overwrite_index >= 0, overwrite_index, np.iinfo(np.int64).max)
    resolved = np.minimum(read, write) < np.iinfo(np.int64).max
    state[resolved] = (read[resolved] < write[resolved]).astype(np.int8)
    return state


def overlap_category(write_offset, write_size, read_offset, read_size):
    """Mutually exclusive shape of the first matched read against the write."""
    write_end = write_offset + write_size
    read_end = read_offset + read_size
    same_start = read_offset == write_offset
    covering = (read_offset < write_offset) & (read_end >= write_end)
    category = np.full(len(write_offset), -1, dtype=np.int8)
    category[covering] = 5
    interior = (~covering) & (read_offset > write_offset) & (read_offset < write_end)
    category[interior] = 4
    before = (~covering) & (read_offset < write_offset)
    category[before] = 3
    same_larger = same_start & (read_size > write_size)
    category[same_larger] = 2
    same_smaller = same_start & (read_size < write_size)
    category[same_smaller] = 1
    category[same_start & (read_size == write_size)] = 0
    return category


TICKS = 10_000_000


def label_writes(events, write_rows, begin, regions=16):
    """Range labels for query rows against every later event from `begin` on.

    Returns read/overwrite absolute row indices (-1 if none) and issue-to-issue
    target/lifetime in seconds (NaN when unmatched). Exact on the 512-byte grid.
    The event array is used as a read-only view; only needed columns are copied.
    """
    write_rows = np.asarray(write_rows, dtype=np.int64)
    if (write_rows < begin).any():
        raise ValueError("Query rows must not precede the candidate begin")
    offset = np.asarray(events["offset"][write_rows])
    size = np.asarray(events["size"][write_rows])
    timestamp = np.asarray(events["timestamp"][write_rows])
    is_read = np.asarray(events["is_read"][begin:]) == 1
    read_rows = np.flatnonzero(is_read) + begin
    write_candidate_rows = np.flatnonzero(~is_read) + begin
    read_off = np.asarray(events["offset"][read_rows])
    read_size = np.asarray(events["size"][read_rows])
    write_off = np.asarray(events["offset"][write_candidate_rows])
    write_size = np.asarray(events["size"][write_candidate_rows])
    read_idx = first_future_intersecting(offset, offset + size, write_rows, read_off, read_off + read_size, read_rows, regions=regions)
    write_idx = first_future_intersecting(offset, offset + size, write_rows, write_off, write_off + write_size, write_candidate_rows, regions=regions)

    def delay(match_rows):
        seconds = np.full(len(match_rows), np.nan)
        present = match_rows >= 0
        if present.any():
            seconds[present] = (np.asarray(events["timestamp"][match_rows[present]]) - timestamp[present]) / TICKS
        return seconds

    return {"read": read_idx, "overwrite": write_idx, "target": delay(read_idx), "lifetime": delay(write_idx)}
