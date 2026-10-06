"""Standalone inference for validation-selected mixtures, regressors and medians."""

import hashlib
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np


class SelectedPredictor:
    """Accept seven raw causal features; return nonnegative seconds to Read."""

    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else Path(__file__).resolve().parent
        self.metadata = json.loads((self.directory / "models.json").read_text())
        for name, expected in self.metadata["files"].items():
            path = self.directory / name
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
                raise ValueError(f"Model fingerprint mismatch: {name}")
        self.models, self.addresses = {}, {}
        for workload, rules in self.metadata["predictors"].items():
            for rule, recipe in rules.items():
                key = (workload, rule)
                if recipe["method"] in ("log_l2", "raw_l1", "mix_log25", "mix_log50", "mix_log75"):
                    self.models[key] = {
                        method: lgb.Booster(model_file=str(self.directory / name))
                        for method, name in recipe["models"].items()}
                elif recipe["method"] == "address_median":
                    saved = json.loads((self.directory / recipe["address_medians"]).read_text())
                    self.addresses[key] = {int(address): value for address, value in saved.items()}
                else:
                    raise ValueError(f"Unsupported selected method: {recipe['method']}")

    def predict_seconds(self, workload, rule, raw_features):
        values = np.atleast_2d(np.asarray(raw_features, dtype=np.float64))
        if values.ndim != 2 or values.shape[1] != 7:
            raise ValueError("Expected (n, 7) raw features in the order documented in models.json")
        key = (workload, rule)
        recipe = self.metadata["predictors"][workload][rule]
        if recipe["method"] == "address_median":
            addresses = self.addresses[key]
            return np.asarray([addresses.get(int(offset), recipe["global_median_seconds"])
                               for offset in values[:, 0]], dtype=float)
        features = np.log1p(values)
        models = self.models[key]
        if recipe["method"] == "log_l2":
            return np.maximum(0, np.expm1(models["log_l2"].predict(features, num_threads=2)))
        if recipe["method"] == "raw_l1":
            return np.maximum(0, models["raw_l1"].predict(features, num_threads=2))
        log_seconds = np.maximum(0, np.expm1(models["log_l2"].predict(features, num_threads=2)))
        raw_seconds = np.maximum(0, models["raw_l1"].predict(features, num_threads=2))
        weight = recipe["weight_log_l2"]
        return weight * log_seconds + (1 - weight) * raw_seconds
