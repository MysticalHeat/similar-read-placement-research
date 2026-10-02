"""UNRUN library adapter; injected checks are soft, not permission or OS isolation.

Only a separately approved, frozen, externally contained caller may use this API.
No launcher, environment discovery, subprocess, retry, or global COMPLETE claim.
"""
import csv
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CASES = ("phase_cycle", "independent_negative")
KEY = ("case", "split", "namespace", "page", "decision_seconds")
FEATURE = KEY + ("r600", "r300", "recency", "w600")
SCRIPT = ".research/experiments/scripts/"
CONFIG = ".research/experiments/configs/synthetic-temperature-demo-v0.1.json"
SCOPED = (CONFIG, ".research/protocol/synthetic-temperature-demo-v0.1.md",
          ".research/protocol/synthetic-preparation-approval-2026-10-01.md",
          ".research/protocol/synthetic-runtime-contract-v0.1.md",
          ".research/protocol/synthetic-controlled-launch-plan-v0.2.md",
          SCRIPT + "synthetic_temperature_demo.py", SCRIPT + "synthetic_models.py",
          SCRIPT + "synthetic_stage_adapter_v0.1.py")
TOYS = ("Fixtures.test_F0_Fk_and_threshold_two", "Fixtures.test_Fcross_Faligned",
        "Fixtures.test_Fties_Fmutation_no_refit", "Fixtures.test_Funseen_FboundaryU_Fcensor_Freset",
        "Fixtures.test_R006_direct_Event_recording_bounds", "Fixtures.test_STOP_domains_and_distinct_tuple_retention",
        "ModelAndMetrics.test_exact_CART_pure_no_gain_ties_minleaf_depth",
        "ModelAndMetrics.test_metrics_shared_keys_and_guards",
        "ModelAndMetrics.test_R007_origin_shape_domain_order_and_no_constructor_sample",
        "ModelAndMetrics.test_R007_current_domain_future_origins_and_monotonicity",
        "ModelAndMetrics.test_R007_wall_CPU_caps_and_valid_near_boundaries")
FIXED = json.loads(r'''{
"version":"0.1","status":"PREPARATION_ONLY_EXECUTION_BLOCKED","protocol":".research/protocol/synthetic-temperature-demo-v0.1.md",
"preparation_approval":".research/protocol/synthetic-preparation-approval-2026-10-01.md","runtime_contract":".research/protocol/synthetic-runtime-contract-v0.1.md","claim":"C037_UNVERIFIED",
"dataset":{"id":"SYN001_PROPOSED_NOT_GENERATED","provenance":"First-party artificial recipe; no downloaded source bytes or SSD simulation",
"namespace":"synthetic0","pages":96,"page_bytes":4096,"endpoint_seconds":21600,"bins":36,"bin_seconds":600,
"cases":["phase_cycle","independent_negative"],"counts":[0,1,4],"negative_rng":"random.Random","seed":42,
"rng_iteration":"j ascending, then p ascending; one randrange(3)","read_offsets_seconds":{"0":[],"1":[300],"4":[60,180,360,480]},
"registration_seconds":[1,12001,16801],"sort":["timestamp","WRITE-before-READ","offset_bytes"],"request_id":"case:ordinal, ordinal starts at zero",
"event_caps":{"per_case":14112,"fixtures":100,"total":30000}},
"windows":{"history_seconds":600,"future_seconds":600,"step_seconds":600,"past":"[t-600,t)","future":"[t,t+600)",
"universe":"R/W issue<t since segment reset; never union future pages","splits":{"train":[0,10800],"val":[12000,15600],"test":[16800,21600]},
"grid_counts_expected_not_observed":[17,5,7],"labels":{"cold":[0,0],"warm":[1,2],"hot_min":3},
"feature_order":["readcount600","readcount300","recency_clipped600","writecount600"],"unseen_prediction":"cold","sampling":null},
"models":{"method_order":["Z","D","A","X"],"release_order":["val","test"],"cart":{"max_depth":3,"root_depth":0,"min_samples_leaf":50,
"gini":"exact Fraction","threshold":"adjacent distinct midpoint Fraction","split_ties":"feature order then lowest threshold","class_ties":[0,1,2],
"positive_gain_only":true,"pruning":false,"class_weights":null},"benchmark_fits":4,"tuning_fits":0,"refit":false,
"evaluation_truth_access":"after exclusive durable commit of val AND test predictions","expectation_tables_allowed_in_E005":false},
"resources":{"global_active_wall_seconds":120,"global_cpu_seconds":120,"memory_max_bytes":1073741824,"memory_swap_max_bytes":0,
"python_workers":1,"worker_threads":1,"worker_children":0,"phase_wall_and_cpu_seconds":{"inventory":15,"E004_preparation":35,"E005_fits":40,"prediction_metrics":15,"finalization":15},
"per_fit_wall_and_cpu_seconds":10,"new_disk_logical_and_allocated_bytes":5242880,
"disk_includes":"prepared source/config/tests, fixtures, all raw/processed/partials/logs/receipts/enforcement","failure_reserve_bytes":null,
"warmup":"no performance benchmark; causal history warmup600s","network":false,"gpu":false,"installs":false,"retry":false},
"freeze":{"python_executable":null,"python_exact_version":null,"stdlib_environment":null,"third_party_dependency_lock":[],"protocol_sha256":null,"config_sha256":null,
"code_sha256":null,"repo_revision_and_dirty_state":null,"launcher_receipt":null,"remaining_active_ledger":null,"E004_execution_permission":null,
"E005_separate_G2_permission":null,"E004_complete_input_manifest_sha256_for_E005":null},
"artifacts_prospective_only":{"raw":[".research/experiments/raw/E004",".research/experiments/raw/E005"],"reserved_do_not_reuse":["E002","E003"],
"creation":"exclusive new directory; existing=>STOP","writes":"exclusive bounded writes once; final manifest once; preserve partials on failure",
"checksums":"SHA256 of actual protocol/config/code/inputs/outputs; not calculated during preparation","processed":"separate new processed/E-ID with raw input hashes and script version",
"manifest_required":["run_id","protocol_version","commands","exit_code","status","timestamps","hashes","runtime","OS","CPU","RAM","compiler","secret_free_environment","ledger","cgroup_domain","phase_usage","final_external_accounting","splits_masks","checks","failures","deviations"]}
}''')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def csv_bytes(header, rows):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue().encode()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Writer:
    """Logical allowance only; no allocated-block, quota, RAM, or tail guarantee."""
    def __init__(self, root, limits):
        self.root, self.limits, self.used, self.outputs, self.attempted = root, limits, 0, {}, set()
        root.mkdir(mode=0o700)  # exclusive, no parents; occupied run ID => STOP
        sync_dir(root.parent)
        sync_dir(root)

    def put(self, name, data, slot=None):
        require(Path(name).name == name and name not in self.attempted, "unsafe/repeated output")
        require(slot in (None, "manifest", "failure"), "reservation slot")
        reserve = self.limits["manifest_reserve"] + self.limits["failure_reserve"]
        if slot:
            require(name == ("manifest.json" if slot == "manifest" else "failure-001.json"), "reserved path")
            require(len(data) <= self.limits[slot + "_reserve"], "reserved payload overflow")
        else:
            require(len(data) <= self.limits["per_file"] and self.used + len(data) + reserve <= self.limits["total"], "logical allowance")
            self.used += len(data)  # charge full attempted payload; never refund partials
        self.attempted.add(name)
        with (self.root / name).open("xb") as file:
            require(file.write(data) == len(data), "short write")
            file.flush()
            os.fsync(file.fileno())
        sync_dir(self.root)
        self.outputs[name] = {"sha256": digest(data), "bytes": len(data)}
        return name


class Session:
    def __init__(self, context, stage):
        self.c, self.stage, self.writer, self.previous = context, stage, None, None
        for name in ("checkpoint", "persist_resource_receipt", "sample", "origin"):
            require(callable(context.get(name)), "mandatory callable: " + name)
        for name in ("dispatch", "resource_receipt", "provenance", "frozen_hashes", "writer_limits"):
            require(isinstance(context.get(name), dict) and context[name], "missing external object: " + name)
        for name in ("operation_ref", "owner", "approval_reference", "prestart_record", "quota_record", "postexit_record_locator"):
            require(context["dispatch"].get(name), "missing dispatch reference: " + name)
        for name in ("runtime", "OS", "CPU", "RAM", "compiler", "repo_revision", "dirty_state", "secret_free_environment", "commands"):
            require(name in context["provenance"], "missing provenance field: " + name)
        limits = context["writer_limits"]
        require(set(limits) == {"per_file", "total", "manifest_reserve", "failure_reserve"}, "writer fields")
        require(all(type(v) is int and v > 0 for v in limits.values()) and limits["total"] <= 5242880
                and limits["manifest_reserve"] + limits["failure_reserve"] < limits["total"], "logical reservations")
        self.project = Path(context["project"])
        require(self.project.is_absolute(), "absolute project required")
        self.raw = self.project / ".research/experiments/raw"
        require(self.raw.is_dir() and not self.raw.is_symlink(), "existing raw parent required")
        require(not (self.raw / stage).exists() and not (self.raw / stage).is_symlink(), "occupied run ID")
        self.started = datetime.now(timezone.utc).isoformat()
        self.initial = self.receipt("before_writes")  # absent callback/receipt rejects before mkdir
        paths = SCOPED + ((SCRIPT + "synthetic_expectations.py", SCRIPT + "test_synthetic_temperature_demo.py") if stage == "E004" else ())
        require(set(context["frozen_hashes"]) == set(paths), "freeze must match approved scoped paths")
        self.identities = {p: digest(self.read(self.project / p)) for p in paths}
        require(self.identities == context["frozen_hashes"], "frozen identity mismatch")
        self.config_bytes = self.read(self.project / CONFIG)
        require(encoded(json.loads(self.config_bytes)) == encoded(FIXED), "config drift: no adaptation")

    def read(self, path, expected=None):
        require(not path.is_symlink(), "symlink input")
        with path.open("rb") as file:
            data = file.read(self.c["writer_limits"]["per_file"] + 1)
        require(len(data) <= self.c["writer_limits"]["per_file"], "bounded input")
        if expected is not None:
            require(digest(data) == expected, "input checksum mismatch: " + path.name)
        return data

    def receipt(self, point):
        value = self.c["checkpoint"](self.stage, point)
        require(isinstance(value, dict) and value.get("operation_ref") == self.c["dispatch"]["operation_ref"], "checkpoint receipt missing/mismatched")
        return value

    def record(self, point, receipt=None):
        name = self.c["persist_resource_receipt"](self.writer, self.stage, point,
                                                 self.receipt(point) if receipt is None else receipt)
        require(name in self.writer.outputs and name not in ("manifest.json", "failure-001.json"), "receipt not durably persisted via writer")

    def sample(self):
        from synthetic_models import BudgetGuard
        value = BudgetGuard._coordinates(self.c["sample"](), RuntimeError, "external ledger malformed")
        require(self.previous is None or all(value[i] >= self.previous[i] for i in range(2)), "ledger regressed")
        self.previous = value
        return value

    def guard(self, phase, cap, fit=None):
        from synthetic_models import BudgetGuard
        origin = self.c["origin"](phase, None)
        guard = BudgetGuard(self.sample, origin, cap, None if fit is None else self.c["origin"](phase, fit))
        guard.check()
        return guard.check

    def open_writer(self):
        self.writer = Writer(self.raw / self.stage, self.c["writer_limits"])
        self.record("start", self.initial)
        self.writer.put("config.json", self.config_bytes)

    def finish(self, checks, inputs=None):
        check = self.guard("finalization", 15)
        self.record("local_finalization")
        check()
        manifest = {"run_id": self.stage, "experiment_id": self.stage, "status": "LOCAL_WORKER_COMPLETE",
                    "protocol_version": "synthetic-temperature-demo-v0.1", "claim": "C037",
                    "started_at": self.started, "local_completed_at": datetime.now(timezone.utc).isoformat(),
                    "exit_code": None, "local_return_code": 0, "checks": checks, "inputs": inputs,
                    "identities": self.identities, "config_hash": digest(self.config_bytes), "outputs": dict(self.writer.outputs),
                    "provenance": self.c["provenance"], "dispatch": self.c["dispatch"], "resource_receipt": self.c["resource_receipt"],
                    "final_external_accounting": None, "global_resource_certification": None,
                    "seed": 42, "warmup": "causal history600s; no performance benchmark", "concurrency": "worker1/thread1/no children REQUIRED_EXTERNALLY",
                    "independent_unit": "whole engineered case; cases not iid", "repetitions": 1,
                    "dependency_lock": [], "environment_spec": "exact runtime/stdlib supplied in provenance; no third-party dependencies",
                    "deviations": [], "failure_handling": "STOP; retain partials/negatives; no retry/delete/overwrite"}
        self.writer.put("manifest.json", encoded(manifest), "manifest")
        return {"run_id": self.stage, "manifest": manifest, "manifest_sha256": self.writer.outputs["manifest.json"]["sha256"]}

    def fail(self, error):
        if self.writer is not None:
            self.writer.put("failure-001.json", encoded({"status": "LOCAL_WORKER_FAILED", "run_id": self.stage,
                            "error_type": type(error).__name__, "reason": str(error)[:1024],
                            "attempted": sorted(self.writer.attempted), "outputs": self.writer.outputs,
                            "exit_code": None, "final_external_accounting": None}), "failure")


def toy_checklist(check):
    import unittest
    import test_synthetic_temperature_demo as tests  # E004 ONLY; never RecipeChecks
    from synthetic_models import Cart
    count = [0]
    class CountedCart(Cart):
        def fit(self, matrix, labels, ignored_check):
            check()
            if self.tree is None:
                count[0] += 1
                require(count[0] <= 8, "toy fit budget")
            return super().fit(matrix, labels, check)
    tests.check, tests.Cart = check, CountedCart  # replace test-only no-op before calls
    for item in TOYS:
        check()
        cls, method = item.split(".")
        result = unittest.TestResult()
        getattr(tests, cls)(method).run(result)
        require(result.testsRun == 1 and result.wasSuccessful() and not result.skipped, "fixture/toy failure: " + item)
    require(count[0] == 8, "frozen toy count mismatch")
    return {"checklist": TOYS, "toy_fits": count[0], "benchmark_fits": 0, "status": "LOCAL_CHECKS_PASSED"}


def prepare_e004(context):
    s = Session(context, "E004")
    try:
        check = s.guard("E004_preparation", 35)
        import synthetic_temperature_demo as p
        from synthetic_expectations import EXPECTED_GRIDS, EXPECTED_MASKS, recipe_expectations
        s.open_writer()
        checks = toy_checklist(check)
        for args, wanted in EXPECTED_MASKS.items():
            check()
            require(p.mask_reason(*args) == wanted, "mask invariant")
        total, cases = 0, {}
        for case in CASES:
            check()
            name = case + ".trace.csv"
            s.writer.put(name, p.generate_csv(case, check).encode())  # EXACTLY ONCE/case
            data = p.parse_csv(s.read(s.writer.root / name, s.writer.outputs[name]["sha256"]).decode(), 21600, check)
            total += len(data)
            require(len(data) <= 14112 and total + 100 <= 30000, "aggregate event cap including fixture bound")
            bins, expected = recipe_expectations(case)
            comparison = []
            for j in range(36):
                observed = p.future_counts(data, j * 600, check)
                require(set(observed) <= {("synthetic0", page) for page in range(96)}, "unexpected bin key")
                for page in range(96):
                    check()
                    n = observed.get(("synthetic0", page), 0)
                    require(n == bins[page, j], "independent recipe/bin disagreement")
                    comparison.append((page, j, bins[page, j], n))
            s.writer.put(case + ".recipe.csv", csv_bytes(("page", "bin", "expected", "observed"), comparison))
            all_features, ids, masks_out = {}, [], {}
            for split, start, end in p.SPLITS:
                features, masks = p.feature_table(data, case, split, start, end, 21600, check)
                truth = p.label_table(data, features, check)
                wanted = {k: y for k, y in expected.items() if k[1] == split}
                require(p.grid(start, end) == EXPECTED_GRIDS[split] and all(v is None for v in masks.values()), "grid/censor invariant")
                require(set(features) == set(truth) == set(wanted) and truth == wanted, "decision/shared keys disagreement")
                require(all(v[0] >= v[1] and 0 <= v[2] <= 600 for v in features.values()), "feature invariant")
                segment = tuple(e for e in data if start <= e.timestamp < end)
                ids.append({e.request_id for e in segment})
                require(p.feature_table(segment, case, split, start, end, 21600, check)[0] == features
                        and p.label_table(segment, features, check) == truth, "reset/gap isolation")
                all_features.update(features)
                masks_out[split] = masks
                s.writer.put(case + "." + ("trainlabels" if split == "train" else split + ".truth") + ".csv",
                             csv_bytes(KEY + ("y",), ((*k, truth[k]) for k in sorted(truth))))
                audits = []
                for t in EXPECTED_GRIDS[split]:
                    check()
                    eligible = {(k[2], k[3]) for k in features if k[4] == t}
                    _, audit = p.truth_and_audit(p.future_counts(data, t, check), eligible)
                    unseen = [[ns, page, y] for (ns, page), y in audit["unseen_labels"].items()]
                    audits.append((t, audit["seen_incidences"], audit["all_incidences"], json.dumps(unseen, separators=(",", ":"))))
                s.writer.put(case + "." + split + ".audit.csv", csv_bytes(("decision", "seen", "all", "unseen"), audits))
            require(not (ids[0] & ids[1] or ids[1] & ids[2] or ids[0] & ids[2]) and set(all_features) == set(expected), "split disjointness")
            s.writer.put(case + ".features.csv", csv_bytes(FEATURE, ((*k, *all_features[k]) for k in sorted(all_features))))
            cases[case] = {"events": len(data), "bin_comparisons": 3456, "decision_comparisons": len(expected), "masks": masks_out}
        checks.update({"cases": cases, "events": total, "fixture_event_bound": 100, "invariants": "LOCAL_CHECKS_PASSED"})
        check()
        s.writer.put("checks.json", encoded(checks))
        return s.finish(checks)
    except BaseException as error:
        s.fail(error)
        raise


def table(s, manifest, name, header, check):
    data = s.read(s.raw / "E004" / name, manifest["outputs"][name]["sha256"])
    reader = csv.reader(io.StringIO(data.decode(), newline=""))
    require(next(reader, None) == list(header), "table schema")
    result = {}
    for row in reader:
        check()
        require(len(row) == len(header), "table width")
        key = (*row[:3], int(row[3]), int(row[4]))
        value = tuple(int(v) for v in row[5:])
        require(key not in result, "duplicate table key")
        result[key] = value
    return result


def tree_record(node):
    if node.feature is None:
        return {"label": node.label}
    return {"label": node.label, "feature": node.feature,
            "threshold": [node.threshold.numerator, node.threshold.denominator],
            "left": tree_record(node.left), "right": tree_record(node.right)}


def frozen_mutation(p, m, a, x, check):
    spec = ((1, "WRITE"), (300, "READ"), (599, "READ"), (600, "READ"), (600, "READ"), (1200, "READ"))
    original = tuple(p.Event(str(i), t, "fixture", op, 0, 4096) for i, (t, op) in enumerate(spec))
    mutated = tuple(p.Event(e.request_id, e.timestamp, e.namespace, "WRITE", 8192, e.size_bytes)
                    if e.timestamp >= 600 else e for e in original)
    before = p.past_features(p.validate(original, 1201, check), 600, 0, check)
    after = p.past_features(p.validate(mutated, 1201, check), 600, 0, check)
    require(before == after == {("fixture", 0): (2, 2, 1, 1)}, "Fmutation features")
    key, trees = ("toy", "val", "fixture", 0, 600), (a.tree, x.tree)
    require(m.prediction_payload({key: before["fixture", 0]}, a, x, check) ==
            m.prediction_payload({key: after["fixture", 0]}, a, x, check) and trees == (a.tree, x.tree), "frozen prediction mutation")


def compare_e005(context):
    require(not any(n in sys.modules for n in ("synthetic_expectations", "test_synthetic_temperature_demo")), "E005 requires fresh worker; oracle/tests must not be imported")
    s = Session(context, "E005")
    try:
        import synthetic_temperature_demo as p
        import synthetic_models as m
        check = s.guard("E005_fits", 40)
        manifest_bytes = s.read(s.raw / "E004/manifest.json", context["e004_manifest_sha256"])
        manifest = json.loads(manifest_bytes)
        require(manifest["run_id"] == "E004" and manifest["status"] == "LOCAL_WORKER_COMPLETE"
                and manifest["config_hash"] == digest(s.config_bytes), "E004 local completion/config required")
        require(manifest["checks"]["invariants"] == "LOCAL_CHECKS_PASSED" and manifest["checks"]["toy_fits"] == 8
                and manifest["checks"]["benchmark_fits"] == 0, "E004 incomplete invariant checklist")
        require(all(manifest["identities"].get(path) == value for path, value in s.identities.items()), "E004/E005 implementation drift")
        features, models, fits, input_hashes = {}, {}, 0, {}
        s.open_writer()
        for case in CASES:
            f = table(s, manifest, case + ".features.csv", FEATURE, check)
            labels = table(s, manifest, case + ".trainlabels.csv", KEY + ("y",), check)
            wanted = {(case, split, "synthetic0", page, t) for split, start, end in p.SPLITS for t in p.grid(start, end) for page in range(96)}
            require(set(f) == wanted and set(labels) == {k for k in f if k[1] == "train"}, "input keys/splits")
            require(all(len(v) == 4 and min(v) >= 0 and v[0] >= v[1] and v[2] <= 600 for v in f.values())
                    and all(v in ((0,), (1,), (2,)) for v in labels.values()), "input domains")
            ordered = sorted(labels, key=lambda k: (k[4], k[3]))
            rows, y = [f[k] for k in ordered], [labels[k][0] for k in ordered]
            pair = []
            for method in ("A", "X"):
                fits += 1
                fit_check = s.guard("E005_fits", 40, fits)
                pair.append(m.Cart().fit([(r[0],) for r in rows] if method == "A" else rows, y, fit_check))
                fit_check()
                s.record("fit_" + str(fits))
            features[case], models[case] = f, tuple(pair)
            for name in (case + ".features.csv", case + ".trainlabels.csv"):
                input_hashes[name] = manifest["outputs"][name]["sha256"]
        require(fits == 4, "registered benchmark fit count")
        check = s.guard("prediction_metrics", 15)
        predictions = {}
        for case in CASES:
            f = {k: v for k, v in features[case].items() if k[1] in ("val", "test")}
            payload = m.prediction_payload(f, *models[case], check)
            predictions[case] = payload
            s.writer.put(case + ".predictions.csv", csv_bytes(KEY + ("Z", "D", "A", "X"),
                         ((*k, *(payload[method][k] for method in ("Z", "D", "A", "X"))) for k in sorted(f))))
        s.writer.put("models.json", encoded({case: {method: tree_record(model.tree) for method, model in zip(("A", "X"), models[case])} for case in CASES}))
        committed = {n: v for n, v in s.writer.outputs.items() if n.endswith(".predictions.csv") or n == "models.json"}
        sync_dir(s.writer.root)
        sync_dir(s.raw)
        s.writer.put("prediction-commit.json", encoded({"status": "ALL_PREDICTIONS_DURABLE", "outputs": committed, "inputs": input_hashes,
                     "e004_manifest_sha256": digest(manifest_bytes), "evaluation_truth_opened": False}))
        s.read(s.writer.root / "prediction-commit.json", s.writer.outputs["prediction-commit.json"]["sha256"])
        s.record("prediction_commit_before_truth")  # ALL cases, val+test, files+dirs fsynced
        for case in CASES:
            frozen_mutation(p, m, *models[case], check)  # mandatory; no additional fits
        for split in ("val", "test"):
            for case in CASES:
                check()
                f = {k: v for k, v in features[case].items() if k[1] == split}
                truth = table(s, manifest, case + "." + split + ".truth.csv", KEY + ("y",), check)
                pred = {method: {k: values[k] for k in f} for method, values in predictions[case].items()}
                report = p.score_release(f, pred, {k: v[0] for k, v in truth.items()})
                name = case + "." + split + ".audit.csv"
                reader = csv.reader(io.StringIO(s.read(s.raw / "E004" / name, manifest["outputs"][name]["sha256"]).decode(), newline=""))
                require(next(reader, None) == ["decision", "seen", "all", "unseen"], "audit schema")
                audit = {}
                for row in reader:
                    check()
                    t, seen, total, unseen = int(row[0]), int(row[1]), int(row[2]), json.loads(row[3])
                    require(t not in audit and 0 <= seen <= total and all(len(v) == 3 and v[2] in (0, 1, 2) for v in unseen), "audit domain")
                    audit[t] = {"seen_incidences": seen, "all_incidences": total, "coverage": None if not total else seen / total,
                                "unseen": unseen, "unseen_cold_errors": sum(v[2] != 0 for v in unseen),
                                "unseen_methods_Z_D_A_X": p.metrics([v[2] for v in unseen], [0] * len(unseen))}
                require(set(audit) == {k[4] for k in f}, "audit/shared decision keys")
                s.writer.put(case + "." + split + ".score.json", encoded({"seen_strata": report, "unseen_coverage": audit, "censored_selected": 0}))
        check()
        return s.finish({"benchmark_fits": fits, "tuning_fits": 0, "frozen_mutation": "LOCAL_CHECKS_PASSED",
                         "release_order": ["val", "test"], "all_predictions_committed_before_truth": True},
                        {"e004_manifest_sha256": digest(manifest_bytes), "model_inputs": input_hashes})
    except BaseException as error:
        s.fail(error)
        raise


if __name__ == "__main__":
    raise SystemExit("STOP: library only; separate actual launch approval/freeze and all original hard accounting gates required")
