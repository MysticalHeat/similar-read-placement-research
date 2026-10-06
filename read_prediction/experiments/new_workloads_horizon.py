"""Compare observed labels at matched 4.8-hour horizons, without refitting."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.extended import EVENT_DTYPE
from read_prediction.experiments.new_workloads_diagnostics import distribution, metrics
from read_prediction.experiments.prxy0_check import dump, local_labels
from read_prediction.paths import PROJECT_ROOT
from read_prediction.range_label import TICKS

WIDTH = round(4.8 * 3600 * TICKS)


def restrict(events, rows, labels, origin, last_timestamp):
    write_ts = events["timestamp"][rows]
    ends = np.minimum(origin + ((write_ts - origin) // WIDTH + 1) * WIDTH, last_timestamp)
    seen = labels["read"] >= 0
    keep = np.zeros(len(rows), dtype=bool)
    keep[seen] = events["timestamp"][labels["read"][seen]] < ends[seen]
    lifetime = labels["lifetime"][keep].copy()
    overwritten = labels["overwrite"][keep] >= 0
    within = np.zeros(len(lifetime), dtype=bool)
    within[overwritten] = events["timestamp"][labels["overwrite"][keep][overwritten]] < ends[keep][overwritten]
    lifetime[~within] = np.nan
    target = labels["target"][keep]
    assert np.all(target < WIDTH / TICKS)
    return keep, target, lifetime, (ends[keep] - write_ts[keep]) / TICKS


def main():
    output = PROJECT_ROOT / "results/new-workloads-horizon"
    output.mkdir(exist_ok=False)
    for workload in ("proj_1", "prn_1"):
        folder = PROJECT_ROOT / "results/new-workloads" / workload
        source = json.loads((folder / "source.json").read_text())
        frozen = json.loads((folder / "frozen.json").read_text())
        original = json.loads((PROJECT_ROOT / "results/new-workloads-diagnostics" / f"{workload}.json").read_text())
        events = np.memmap(folder / "events.bin", mode="r", dtype=EVENT_DTYPE)
        origin = source["first_timestamp"]
        train_end = int(np.searchsorted(events["timestamp"], origin + 3 * WIDTH))
        result = {}
        for rule in ("same_start", "range"):
            rows, labels = local_labels(events, 0, train_end, rule)
            _, train_target, _, _ = restrict(events, rows, labels, origin, source["last_timestamp"])
            arrays = {key: [] for key in ("target", "lifetime", "remaining", "model", "address_median")}
            for day in range(2, 8):
                with np.load(folder / f"{rule}.day{day}.npz") as saved:
                    keep, target, lifetime, remaining = restrict(events, saved["write_rows"], saved,
                                                               origin, source["last_timestamp"])
                    for key, values in (("target", target), ("lifetime", lifetime), ("remaining", remaining),
                                        ("model", saved[frozen[rule]["selected"]][keep]),
                                        ("address_median", saved["address_median"][keep])):
                        arrays[key].append(values)
            arrays = {key: np.concatenate(parts) for key, parts in arrays.items()}
            n = len(arrays["target"])
            prior = original["rules"][rule]["windows"]["future"]
            assert n <= prior["n"]
            result[rule] = {"train_target_distribution_4_8h": distribution(train_target),
                            "validation_target_distribution_4_8h": original["rules"][rule]["windows"]["validation"]["target_distribution"],
                            "future_target_distribution_4_8h": distribution(arrays["target"]),
                            "retained_observed_fraction": n / prior["n"],
                            "future_metrics_4_8h": {method: metrics(arrays["target"], arrays[method],
                                                                   arrays["lifetime"], arrays["remaining"])
                                                     for method in ("model", "address_median")}}
        dump(output / f"{workload}.json", result)
        print(workload, json.dumps(result), flush=True)
    paths = [PROJECT_ROOT / "docs/protocols/new-workloads-horizon-protocol.md",
             PROJECT_ROOT / "read_prediction/experiments/new_workloads_horizon.py",
             PROJECT_ROOT / "read_prediction/experiments/new_workloads_diagnostics.py",
             output / "proj_1.json", output / "prn_1.json"]
    dump(output / "verification.json", {"passed": True,
         "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in paths}})


if __name__ == "__main__":
    main()
