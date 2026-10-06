"""Copy selected predictors and their verified inference recipe into submission."""

import json
import shutil

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT

RAW_FEATURES = ["offset_bytes", "size_bytes", "prior_read_count", "prior_write_count",
                "seconds_since_read", "seconds_since_write", "last_read_read_interval_seconds"]


def package_models(folder):
    frozen = json.loads((PROJECT_ROOT / "results/mean-overwrite/frozen.json").read_text())
    metadata = {"raw_feature_order": RAW_FEATURES, "input_transform": "log1p for prn_1; raw offset for proj_1",
                "missing_history": "NaN", "output": "seconds from Write to first subsequent Read",
                "history_key": "same starting Offset for both labeling rules; features before current Write",
                "train_window": "days 1–3", "selection_window": "day 4 observed-Read MAE",
                "predictors": {}, "files": {}, "sources": {}}
    for workload, rules in frozen.items():
        parent = PROJECT_ROOT / "results/long-history" / workload
        provenance = json.loads((parent / "provenance.json").read_text())
        parent_frozen = json.loads((parent / "frozen.json").read_text())
        metadata["predictors"][workload] = {}
        for rule, selection in rules.items():
            method = selection["selected"]
            if method == "mix_log25":
                recipe = {"method": method, "weight_log_l2": .25, "models": {}}
                source_names = [f"{rule}.{component}.lightgbm.txt" for component in ("log_l2", "raw_l1")]
                recipe["models"] = {component: f"{workload}.{rule}.{component}.lightgbm.txt"
                                    for component in ("log_l2", "raw_l1")}
            elif method == "address_median":
                recipe = {"method": method, "global_median_seconds": parent_frozen[rule]["global_median"],
                          "address_medians": f"{workload}.{rule}.address_medians.json"}
                source_names = [f"{rule}.address_medians.json"]
            else:
                raise ValueError(f"Unsupported selected method: {workload}/{rule}/{method}")
            for name in source_names:
                source = parent / name
                relative = str(source.relative_to(PROJECT_ROOT))
                expected = provenance["hashes"][relative]
                if fingerprint(source) != expected:
                    raise ValueError(f"Predictor fingerprint mismatch: {relative}")
                destination = f"{workload}.{name}"
                shutil.copyfile(source, folder / destination)
                metadata["files"][destination] = expected
                metadata["sources"][destination] = relative
            metadata["predictors"][workload][rule] = recipe
    source = PROJECT_ROOT / "read_prediction/submission_predict.py"
    shutil.copyfile(source, folder / "predict.py")
    metadata["files"]["predict.py"] = fingerprint(source)
    (folder / "models.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata
