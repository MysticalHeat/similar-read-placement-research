"""R005 expectation-only oracle: direct recipe, NO production imports.

Never an E005 input. Seed replay here is independent of generated events.
Literal grids do not call/repeat the production mask or reset implementation.
"""
import random

EXPECTED_GRIDS = {
    "train": (600, 1200, 1800, 2400, 3000, 3600, 4200, 4800, 5400,
              6000, 6600, 7200, 7800, 8400, 9000, 9600, 10200),
    "val": (12600, 13200, 13800, 14400, 15000),
    "test": (17400, 18000, 18600, 19200, 19800, 20400, 21000),
}
EXPECTED_MASKS = {
    (0, 0, 10800, 21600): "incomplete_history_reset",
    (600, 0, 10800, 21600): None,
    (10200, 0, 10800, 21600): None,
    (10800, 0, 10800, 21600): "outside_segment_or_gap",
    (10500, 0, 10800, 21600): "future_crosses_segment_or_gap",
    (12000, 12000, 15600, 21600): "incomplete_history_reset",
    (12600, 12000, 15600, 21600): None,
    (16800, 16800, 21600, 21600): "incomplete_history_reset",
    (21000, 16800, 21600, 21600): None,
    (21300, 16800, 21600, 21600): "incomplete_recording_future",
    (600, 0, 1200, 1199): "incomplete_recording_future",
}


def recipe_expectations(case):
    if case not in ("phase_cycle", "independent_negative"):
        raise ValueError("unregistered recipe")
    rng = random.Random(42)
    bins = {}
    for j in range(36):
        for p in range(96):
            # Separate formula and random stream: no events/window/overlap helpers.
            code = (p + j) % 3 if case == "phase_cycle" else rng.randrange(3)
            bins[p, j] = (0, 1, 4)[code]
    decisions = {}
    for split, times in EXPECTED_GRIDS.items():
        for t in times:
            for p in range(96):
                n = bins[p, t // 600]
                decisions[case, split, "synthetic0", p, t] = (0 if n == 0 else 1 if n <= 2 else 2)
    return bins, decisions
