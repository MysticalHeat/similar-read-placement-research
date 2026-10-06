"""Independent finite-window counts and deadline/probability replay."""

import argparse
import json

import lightgbm as lgb
import numpy as np

from read_prediction.paths import PROJECT_ROOT
from read_prediction.artifacts import fingerprint
from read_prediction.checks.all_write import counts, compare


def verify(workload):
    folder = PROJECT_ROOT / "results/window-outcome" / workload
    parent = PROJECT_ROOT / "results/all-write" / workload
    selection = json.loads((folder / "selection.json").read_text())
    frozen = json.loads((folder / "frozen.json").read_text())
    result = json.loads((folder / "diagnostic.json").read_text())
    for section in ("input_hashes", "code_hashes", "validation_hashes"):
        for path, expected in selection[section].items():
            assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected
    assert fingerprint(folder / "selection.json")["sha256"] == frozen["selection_sha256"]
    for path, expected in frozen["models"].items():
        assert fingerprint(PROJECT_ROOT / path)["sha256"] == expected
    source = json.loads((parent / "source.json").read_text())
    old = json.loads((parent / "selection.json").read_text())
    cuts = {int(day): value for day, value in old["cutoffs"].items()}
    meta = np.load(parent / "meta.npy", mmap_mode="r")
    features = np.load(parent / "features.npy", mmap_mode="r")
    slices = {day: slice(np.searchsorted(meta["write"], cuts[day-1]), np.searchsorted(meta["write"], cuts[day])) for day in (6, 7)}
    with np.load(folder / "validation.predictions.npz") as saved:
        validation = {key: saved[key] for key in saved.files}
    for name, expected in selection["validation"].items():
        gate, time, threshold = name.split("/")
        compare(expected, counts(meta[slices[6]], validation[time], validation[gate], float(threshold),
                                 cuts[6], source["first_timestamp"]+144*3600*10_000_000))
    values = selection["validation"]
    qualified = [name for name, value in values.items() if value["qualifies"]]
    broad = [name for name, value in values.items() if value["coverage"] >= .1]
    if qualified:
        chosen = min(qualified, key=lambda name: (-values[name]["coverage"], values[name]["observed_selected_mae_seconds"], name))
    elif broad:
        chosen = min(broad, key=lambda name: (-min(values[name]["read_first_lower"], values[name]["confirmed_error_lt_overwrite_lower"]), -values[name]["coverage"], name))
    else:
        chosen = min(values, key=lambda name: (-values[name]["coverage"], name))
    assert chosen == selection["chosen"] == result["chosen"]
    del validation
    with np.load(folder / "day7.predictions.npz") as saved:
        p, prediction, current = saved["probability"], saved["prediction"], saved["current"]
    gate_name, time_name, threshold = chosen.split("/")
    threshold = float(threshold)
    test = meta[slices[7]]
    end = min(source["last_timestamp"], source["first_timestamp"]+168*3600*10_000_000)
    compare(result["all_write_selective"], counts(test, prediction, p, threshold, cuts[7], end))
    assert np.isfinite(p).all() and np.all((p >= 0) & (p <= 1))
    assert np.isfinite(prediction).all() and np.all(prediction >= 0)
    observed = (test["read"] >= 0) & (test["read"] < cuts[7])
    known = (test["overwrite"] >= 0) & (test["overwrite"] < cuts[7])
    budget = (end-test["timestamp"])/10_000_000
    budget[known] = test["lifetime"][known]
    routed = np.where(p >= threshold, prediction, current)
    for key, pred in (("original_observed_current", current), ("original_observed_routed", routed)):
        error = np.abs(test["target"][observed]-pred[observed])
        passed = error < budget[observed]
        k = int(np.count_nonzero(passed & known[observed]))
        c = int(np.count_nonzero(passed & ~known[observed]))
        n = len(error)
        compare(result[key], {"n": n, "mae_seconds": float(error.mean()), "known_n": int(known[observed].sum()),
               "zero_interval_n": int(np.count_nonzero(known[observed] & (budget[observed]==0))),
               "known_passes": k, "censored_certified_passes": c,
               "pass_lower_bound": (k+c)/n, "pass_upper_bound": (k+int((~known[observed]).sum()))/n,
               "meets_90_percent": bool((k+c)/n >= .9)})
    samples = np.unique(np.linspace(0, len(test)-1, min(64, len(test)), dtype=int))
    remaining = []
    for row in samples:
        elapsed = (int(test["timestamp"][row])-source["first_timestamp"])/10_000_000
        next_boundary = (int(elapsed//86400)+1)*86400
        remaining.append(np.log1p(next_boundary-elapsed))
    x = np.column_stack((features[slices[7]][samples], remaining)).astype(np.float32)
    gate = lgb.Booster(model_file=str(folder / "gate.lightgbm.txt"))
    np.testing.assert_allclose(p[samples], gate.predict(x, num_threads=2)[:, 1], rtol=1e-12, atol=1e-12)
    if time_name == "current":
        np.testing.assert_array_equal(prediction, current)
    else:
        model = lgb.Booster(model_file=str(folder / "time.lightgbm.txt"))
        value = model.predict(features[slices[7]][samples], num_threads=2)
        if old["recipes"][time_name]["log"]:
            value = np.expm1(value)
        np.testing.assert_allclose(prediction[samples], np.maximum(0, value), rtol=1e-12, atol=1e-12)
    record = {"workload": workload, "validation_combinations_recounted": len(values),
              "all_write_day7_rows": len(test), "planned_deadline_and_prediction_samples": len(samples),
              "new_fits": 0, "independent_holdout": False}
    (folder / "verification.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=("usr_1", "prxy_1"))
    verify(parser.parse_args().workload)
