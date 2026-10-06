"""Independently verify cohort sums, censoring and validation MAE selection."""

import json

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.checks.new_workloads import compare
from read_prediction.paths import PROJECT_ROOT


def main():
    folder = PROJECT_ROOT / "results/mean-overwrite"
    provenance = json.loads((folder / "provenance.json").read_text())
    for path, expected in provenance["hashes"].items():
        assert fingerprint(PROJECT_ROOT / path) == expected, path
    published = json.loads((folder / "metrics.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    checked = 0
    for workload, rules in published.items():
        for rule, record in rules.items():
            parts = []
            for window in ("validation", "day5", "day6", "day7", "pooled"):
                metric = record["windows"][window]
                if window == "pooled":
                    data = {key: np.concatenate([part[key] for part in parts]) for key in parts[0]}
                else:
                    with np.load(PROJECT_ROOT / f"results/long-history/{workload}/{rule}.{window}.npz") as saved:
                        data = {key: saved[key].copy() for key in saved.files}
                    if workload == "prn_1":
                        with np.load(PROJECT_ROOT / f"results/mixture/prn_1/{rule}.{window}.npz") as saved:
                            for name, weight in (("mix_log75", .75), ("mix_log50", .5), ("mix_log25", .25)):
                                compare(saved[name], weight * data["log_l2"] + (1 - weight) * data["raw_l1"])
                                data[name] = saved[name].copy()
                    if window != "validation":
                        parts.append(data)
                seen = data["read"] >= 0
                known = seen & (data["overwrite"] >= 0)
                unknown = seen & ~known
                np.testing.assert_array_equal(np.isfinite(data["lifetime"]), data["overwrite"] >= 0)
                n, paired_n = int(seen.sum()), int(known.sum())
                assert n > 0 and metric["observed_reads"] == n
                assert metric["all_writes"] == len(seen) and metric["paired_n"] == paired_n
                assert metric["censored_n"] == int(unknown.sum())
                compare(metric["coverage"], n / len(seen))
                lower = float((data["lifetime"][known].sum() + data["remaining"][unknown].sum()) / n)
                compare(metric["bounds"]["mean_lower_bound_seconds"], lower)
                for method, result in metric["methods"].items():
                    error = np.abs(data[method] - data["target"])
                    mae = float(error[seen].sum() / n)
                    observed = result["observed_read"]
                    compare(observed["mae_seconds"], mae)
                    compare(observed["mean_overwrite_lower_seconds"], lower)
                    compare(observed["ratio_upper_bound"], mae / lower if lower > 0 else None)
                    compare(observed["margin_lower_seconds"], lower - mae)
                    if mae < lower:
                        expected_status = "passed"
                    elif unknown.any():
                        expected_status = "undetermined"
                    else:
                        expected_status = "failed"
                    assert observed["status"] == expected_status
                    if paired_n:
                        paired_mae = float(error[known].sum() / paired_n)
                        mean = float(data["lifetime"][known].sum() / paired_n)
                        compare(result["paired"], {"mae_seconds": paired_mae, "mean_overwrite_seconds": mean,
                                "ratio": paired_mae / mean if mean > 0 else None,
                                "margin_seconds": mean - paired_mae, "passed": paired_mae < mean})
                    else:
                        assert result["paired"] is None
                checked += 1
            candidates = ["log_l2", "raw_l1", "address_median"]
            if workload == "prn_1":
                candidates += ["mix_log75", "mix_log50", "mix_log25"]
            assert frozen[workload][rule]["candidates"] == candidates
            validation = record["windows"]["validation"]["methods"]
            selected = min(candidates, key=lambda name: (validation[name]["observed_read"]["mae_seconds"], name))
            assert selected == record["selected"] == frozen[workload][rule]["selected"]
    result = {"passed": True, "verified_windows": checked, "selection_metric": "validation observed_read MAE",
              "checker_fingerprint": fingerprint(PROJECT_ROOT / "read_prediction/checks/mean_overwrite.py"),
              "metrics_fingerprint": fingerprint(folder / "metrics.json")}
    (folder / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Mean-overwrite verification passed:", checked, "windows")


if __name__ == "__main__":
    main()
