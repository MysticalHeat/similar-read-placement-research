"""Pin existing baseline values before final evaluation and record period roles."""

import argparse
import hashlib
import json
from pathlib import Path

from final_study import OUTPUT, ROOT, dump, evaluate, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload", choices=["usr_1", "prxy_1"])
    args = parser.parse_args()
    workload = args.workload
    if (OUTPUT / workload).exists():
        raise ValueError("Evaluation output already exists")
    baseline_path = (OUTPUT / "usr-selection/baselines.json" if workload == "usr_1" else
                     ROOT / "results/prxy-day2/frozen-baselines.json")
    baseline = json.loads(baseline_path.read_text())
    pin = {"baseline_path": str(baseline_path.relative_to(ROOT)),
           "baseline_file_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
           "baseline_values_sha256": hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest(),
           "code_hashes": fingerprint([Path(__file__), ROOT / "final_study.py"])}
    pin_path = OUTPUT / f"{workload}.baseline-pin.json"
    if pin_path.exists():
        raise ValueError("Baseline pin already exists")
    dump(pin_path, pin)
    evaluate(workload)
    actual = json.loads((OUTPUT / workload / "baselines.json").read_text())
    assert actual == baseline
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == pin["baseline_file_sha256"]
    path = OUTPUT / workload / "results.json"
    result = json.loads(path.read_text())
    result["baseline_pin"] = pin
    result["baseline_frozen_before_evaluation"] = True
    for day, data in result["days"].items():
        data["evaluation_role"] = "previously_evaluated_replication" if workload == "prxy_1" and day == "2" else "new_future_period"
    dump(path, result)
    print(f"{workload}: baseline pin verified; period roles recorded", flush=True)


if __name__ == "__main__":
    main()
