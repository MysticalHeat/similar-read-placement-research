"""PREPARATION / UNRUN. Bootstrap only; approval references are NOT permission.
No computational imports/compile/exec, subprocesses, threads, or network.
Soft worker observations only; no OS containment or complete-tail certificate.
"""
import time
FIRST_WALL = time.monotonic()  # interpreter/import-time startup before this UNKNOWN
INITIAL_CPU = time.process_time()  # includes preclock CPU; charged ONCE below
import sys
import os
import signal
import resource
import stat
import json
import hashlib
from pathlib import Path

PROJECT = Path("/home/nomli/workspace/bdss_lab/research1")
SCRIPTS = ".research/experiments/scripts/"
CALLER = SCRIPTS + "synthetic_practical_caller_v0.1.py"
AMENDMENT = ".research/protocol/synthetic-practical-runtime-amendment-v0.2.md"
CONFIG = ".research/experiments/configs/synthetic-temperature-demo-v0.1.json"
SCOPED = (CONFIG, ".research/protocol/synthetic-temperature-demo-v0.1.md",
          ".research/protocol/synthetic-preparation-approval-2026-10-01.md",
          ".research/protocol/synthetic-runtime-contract-v0.1.md",
          ".research/protocol/synthetic-controlled-launch-plan-v0.2.md",
          SCRIPTS + "synthetic_temperature_demo.py", SCRIPTS + "synthetic_models.py",
          SCRIPTS + "synthetic_stage_adapter_v0.1.py")
E004_EXTRA = (SCRIPTS + "synthetic_expectations.py",
              SCRIPTS + "test_synthetic_temperature_demo.py")
CONTROL = ".research/experiments/control"
PRACTICAL = CONTROL + "/synthetic-practical-v0.2"
BOOT = PRACTICAL + "/bootstrap-001"
TARGETS = {"inventory": 15, "E004_preparation": 35, "E005_fits": 40,
           "prediction_metrics": 15, "finalization": 15}
DISK, PER_FILE, ENTRY_CAP = 5242880, 2097152, 256
NORMAL, FAILURE, ROUNDING, META = 65536, 8192, 4096, 512
STDOUT_CAP = 2048
UNKNOWN = {"startup_wall": None, "own_exit_tail": None, "last_write_tail": None,
           "tool_control_cpu_wall_ram": None, "tool_capture_actual_disk": None,
           "whole_domain_RAM": None, "hard_metadata_bound": None,
           "exit_code_observed": None, "thread_count_observed": None}


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def alarm(signum, frame):
    raise RuntimeError("soft wall alarm; scheduling/I/O/exit latency NOT bounded")


class Budget:
    def __init__(self):
        self.finishing, self.latest = False, None
        signal.signal(signal.SIGALRM, alarm)
        self.arm()

    def arm(self):
        # Absolute first-marker deadlines: switching to finish NEVER resets time.
        remaining = (15 if self.finishing else 12) - (time.monotonic() - FIRST_WALL)
        require(remaining > 0, "inventory wall exhausted; no reserve extension")
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def sample(self):
        wall, cpu = time.monotonic() - FIRST_WALL, time.process_time()
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        self.latest = {"wall": wall, "cpu": cpu, "worker_peak_RSS_bytes": rss}
        return self.latest

    def check(self):
        s = self.sample()
        cap = 15 if self.finishing else 12
        require(s["wall"] < cap and s["cpu"] < cap, "inventory work/finish target")
        require(s["wall"] < 120 and s["cpu"] < 120, "global target")
        require(s["worker_peak_RSS_bytes"] < 1073741824, "worker RSS concern")

    def ledger(self, status):
        s = self.sample()
        phases = {p: {"wall": 0, "cpu": 0} for p in TARGETS}
        phases["inventory"] = {k: s[k] for k in ("wall", "cpu")}
        return {"id": "bootstrap-001", "previous": None, "status": status,
                "global_observed": phases["inventory"], "phase_cumulative": phases,
                "phase_current": "inventory", "phase_targets_wall_cpu": TARGETS,
                "origin": [0, 0], "totals_at_phase_entry": [0, 0], "prior_phase_used": [0, 0],
                "origin_rule": "totals_at_entry - prior_phase_used; NOT fresh phase budget",
                "fit_origin": None, "benchmark_fits_dispatched": 0,
                "initial_process_time": INITIAL_CPU, "cpu_charge": "absolute process_time once",
                "first_monotonic": FIRST_WALL, "sample": s,
                "remaining_measured_estimate": None, "tail": UNKNOWN,
                "human_wait": "only between exited invocations; no live waiting worker",
                "next_stage": "BLOCKED: immutable ledger pre-exit; tail/review/plumbing unresolved"}


def checked(path, missing=False):
    """Project root MUST exist; any missing component BELOW it may return None."""
    require((path == PROJECT or PROJECT in path.parents) and ".." not in path.parts, "path outside project")
    root = PROJECT.lstat()  # never stat PROJECT.parent, including for the root census
    require(stat.S_ISDIR(root.st_mode) and not stat.S_ISLNK(root.st_mode), "unsafe project root")
    if path == PROJECT:
        return root
    parts = [p for p in reversed(path.parents) if PROJECT in p.parents] + [path]
    for p in parts:
        try:
            s = p.lstat()
        except FileNotFoundError:
            if missing:
                return None
            raise
        require(not stat.S_ISLNK(s.st_mode), "scoped symlink rejected")
        require(p == path or stat.S_ISDIR(s.st_mode), "non-directory ancestor")
    return s


def signature(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_blocks)


def read_data(path, expected):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as f:
        before = os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode) and signature(before) == signature(expected), "input race/type")
        data = f.read(PER_FILE + 1)
        require(len(data) <= PER_FILE and signature(before) == signature(os.fstat(f.fileno())), "input bound/race")
    require(signature(checked(path)) == signature(before), "input replaced")
    return data


def census(budget):
    records, stats, seen, scanned = {}, {}, set(), [0]

    def add(path, recursive=False):
        budget.check()
        s = checked(path, missing=True)
        if s is None:
            return
        rel = str(path.relative_to(PROJECT)) if path != PROJECT else "."
        if rel in records:
            return
        require(len(records) < ENTRY_CAP, "bounded scope entry count")
        directory = stat.S_ISDIR(s.st_mode)
        require(directory or stat.S_ISREG(s.st_mode), "unclear scope file type")
        require(directory or s.st_size <= PER_FILE, "scoped file exceeds 2MiB")
        identity = (s.st_dev, s.st_ino)
        duplicate = identity in seen
        seen.add(identity)
        records[rel] = {"kind": "dir" if directory else "file", "nlink": s.st_nlink,
                        "logical": 0 if directory or duplicate else s.st_size,
                        "allocated": 0 if duplicate else s.st_blocks * 512,
                        "hardlink_counted_elsewhere": duplicate}
        stats[rel] = s
        if recursive and directory:
            for child in children(path):
                add(child, True)

    def children(path):
        with os.scandir(path) as entries:
            selected = []
            for entry in entries:
                budget.check()
                scanned[0] += 1
                require(scanned[0] <= ENTRY_CAP, "bounded directory enumeration")
                selected.append(path / entry.name)
        return sorted(selected)

    for rel in (".", ".research", ".research/experiments", ".research/experiments/raw",
                ".research/experiments/processed", CONTROL):
        add(PROJECT / rel)
    for rel in (".research/README.md", ".research/brief.md", ".research/claims"):
        add(PROJECT / rel, True)
    for rel, prefixes, suffix in (
        (SCRIPTS.rstrip("/"), ("synthetic", "test_synthetic"), None),
        (".research/experiments/configs", ("synthetic-",), ".json"),
        (".research/protocol", ("synthetic-",), ".md"),
        (".research/experiments", ("synthetic", "test_synthetic"), None),
        (".research/reviews", ("synthetic-",), ".md"),
        (CONTROL, ("synthetic", "test_synthetic"), None)):
        base = PROJECT / rel
        add(base)
        base_stat = checked(base, missing=True)
        if base_stat is not None:
            require(stat.S_ISDIR(base_stat.st_mode), "non-directory census base")
            for path in children(base):
                if path.name.startswith(prefixes) and (suffix is None or path.name.endswith(suffix)):
                    add(path, True)
    for rel in (".research/experiments/raw/E004", ".research/experiments/raw/E005",
                ".research/experiments/processed/E005"):
        add(PROJECT / rel, True)
    totals = {k: sum(r[k] for r in records.values()) for k in ("logical", "allocated")}
    totals["metadata_estimate"] = META * len(records)
    return records, stats, totals


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Writer:
    def __init__(self, budget):
        self.budget, self.owned, self.created = budget, False, []
        self.attempted, self.outputs, self.normal = set(), {}, 0

    def space(self):
        records, stats, totals = census(self.budget)
        dirs = sum(1 for rel in (CONTROL, PRACTICAL, BOOT) if rel not in records)
        normal_files = 3 - len(self.attempted - {"failure.json"})
        failure = "failure.json" not in self.attempted
        future = NORMAL - self.normal + (FAILURE if failure else 0)
        entries = dirs + normal_files + int(failure) + 1  # stdout capture estimate
        metadata = totals["metadata_estimate"] + entries * META
        logical = totals["logical"] + future + 2048 + metadata
        allocated = (totals["allocated"] + future + (dirs + normal_files + int(failure) + 1) * ROUNDING + metadata)
        require(len(records) + entries <= ENTRY_CAP, "future entry reservation")
        require(logical <= DISK and allocated <= DISK, "5MiB used + future reserves estimate")
        return {"entries": records, "totals": totals, "future_payload": future,
                "future_entries": entries, "directory_rounding_estimate": ROUNDING,
                "logical_with_reserves": logical, "allocated_with_reserves": allocated}

    def create(self):
        for rel in (CONTROL, PRACTICAL, BOOT):
            path = PROJECT / rel
            parent_stat = checked(path, missing=True) if rel == CONTROL else None
            if parent_stat is not None:
                require(stat.S_ISDIR(parent_stat.st_mode), "control parent type")
                continue
            checked(path.parent)
            path.mkdir(mode=0o700)  # exclusive; ownership AFTER mkdir, BEFORE fsync
            self.created.append(rel)
            if rel == BOOT:
                self.owned = True
            sync_dir(path.parent)
            sync_dir(path)

    def put(self, name, value):
        require(self.owned and name in ("freeze.json", "receipt.json", "ledger.json", "failure.json")
                and name not in self.attempted, "unowned/reserved/repeated output")
        data = encoded(value)
        require(len(data) <= (FAILURE if name == "failure.json" else NORMAL - self.normal), "output allowance")
        self.budget.check()
        self.space()  # full census only at write batches, NOT each cooperative sample
        self.attempted.add(name)
        if name != "failure.json":
            self.normal += len(data)  # attempted payload charged, including partial writes
        with (PROJECT / BOOT / name).open("xb") as f:
            require(f.write(data) == len(data), "short write")
            f.flush()
            os.fsync(f.fileno())
        sync_dir(PROJECT / BOOT)
        self.outputs[name] = {"sha256": digest(data), "bytes": len(data)}
        self.space()
        self.budget.check()


def error_record(error):
    record = {"type": type(error).__name__, "reason": None}
    try:
        record["reason"] = str(error)  # FULL detail for the single reserved failure write
    except BaseException:
        record["reason_status"] = "UNAVAILABLE: exception string conversion failed"
    return record


def emit_summary(code, primary, secondary, writer):
    """Byte guard + explicit omission fallback; no traceback or second stdout write."""
    try:
        pointer = BOOT + "/failure.json" if writer and "failure.json" in writer.outputs else None
        def short(value):
            if value is None:
                return None
            reason = value["reason"]
            return {"type": value["type"][:24], "type_truncated": len(value["type"]) > 24,
                    "reason": reason[:64] if reason is not None else None,
                    "reason_omitted": reason is None or len(reason) > 64}
        summary = {"local_return_intended": code, "primary": short(primary), "secondary": short(secondary),
                   "owned_directory": BOOT if writer and writer.owned else None,
                   "created": writer.created if writer else [], "outputs": writer.outputs if writer else {},
                   "durable_failure_pointer": pointer, "full_reason_location": pointer or "UNKNOWN",
                   "tail": "UNKNOWN; pre-exit only; missing receipt forbids next stage"}
        output = encoded(summary)
        if len(output) > STDOUT_CAP:
            # Only two <=24-character types (<=576 escaped bytes together), fixed paths/fields.
            output = encoded({"local_return_intended": code, "primary_type": primary["type"][:24] if primary else None,
                              "secondary_type": secondary["type"][:24] if secondary else None,
                              "details": "OMITTED: stdout byte cap; types limited to24 characters",
                              "owned_directory": BOOT if writer and writer.owned else None,
                              "durable_failure_pointer": pointer, "full_reason_location": pointer or "UNKNOWN",
                              "tail": "UNKNOWN; no resource/persistence certificate"})
        if len(output) > STDOUT_CAP:
            raise ValueError("fallback byte bound")  # caught below, never escapes formatter
    except BaseException:
        code = 2  # never replace an existing failure with success or an uncaught formatter error
        output = b'{"local_return_intended":2,"details":"OMITTED: formatter failure; primary retained in memory","external_pointer":"UNKNOWN","tail":"UNKNOWN"}\n'
    try:
        # Fixed emergency literal <256 bytes; runtime guard also checks every chosen payload.
        if len(output) > STDOUT_CAP:
            return 2
        return code if os.write(1, output) == len(output) else 2  # ONE unbuffered write, no flush/retry
    except BaseException:
        return 2  # primary remains retained; external delivery pointer UNKNOWN, no stderr fallback


def main():
    budget, writer, primary, secondary, code = None, None, None, None, 2
    try:
        budget = Budget()
        require(len(sys.argv) == 5 and sys.argv[1] == "--stage" and sys.argv[3] == "--approval-ref", "exact stage/approval flags required")
        stage, ref = sys.argv[2], sys.argv[4]
        require(stage in ("bootstrap", "E004", "E005"), "unknown stage")
        require(0 < len(ref) <= 128 and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._:/" for c in ref)
                and not any(x in ref.upper() for x in ("PENDING", "PLACEHOLDER", "TODO", "UNAPPROVED", "NONE", "NULL")), "missing real approval reference; NO WRITES")
        require(stage == "bootstrap", "E004/E005 BLOCKED: separate G1/G2 and inspected plumbing absent")
        require(sys.executable == "/usr/bin/python3" and sys.flags.no_site and sys.flags.dont_write_bytecode, "exact /usr/bin/python3 -B -S required; NO FALLBACK")
        require(Path(__file__) == PROJECT / CALLER and os.uname().sysname == "Linux", "exact caller/Linux RSS semantics required")
        control_stat = checked(PROJECT / CONTROL, missing=True)
        require(control_stat is None or stat.S_ISDIR(control_stat.st_mode), "control parent unsafe")
        require(checked(PROJECT / PRACTICAL, missing=True) is None, "occupied/partial ledger namespace; NO RETRY")
        writer = Writer(budget)
        initial_disk = writer.space()
        # This initial ledger is allowed ONLY for a pristine, single-use bootstrap namespace.
        writer.create()
        records, stats, totals = census(budget)
        required = set(SCOPED + E004_EXTRA + (CALLER, AMENDMENT,))
        require(required <= set(records), "required prepared source missing")
        hashes, config_bytes = {}, None
        for rel in sorted(records):
            budget.check()
            if records[rel]["kind"] == "file" and not rel.startswith((CONTROL + "/", ".research/experiments/raw/", ".research/experiments/processed/")):
                data = read_data(PROJECT / rel, stats[rel])  # DATA ONLY, never executable
                hashes[rel] = digest(data)
                if rel == CONFIG:
                    config_bytes = data.decode("utf-8")
        current_records, current_stats, _ = census(budget)
        require(set(current_records) == set(records) and all(signature(current_stats[p]) == signature(s) for p, s in stats.items()), "inventory changed while capturing")
        environment = {"version": sys.version, "executable_actual": sys.executable, "OS": list(os.uname()),
                       "CPU_hardware": None, "RAM_hardware": None, "compiler": "embedded in sys.version",
                       "stdlib_origins": {m.__name__: getattr(m, "__file__", getattr(m.__spec__, "origin", None)) for m in (time, sys, os, signal, resource, stat, json, hashlib)},
                       "dependency_lock": [], "environment_spec": "single Linux stdlib worker, -B -S; installed runtime trusted externally",
                       "repo_revision": None, "dirty_state": None, "environment_dump": "NOT READ"}
        budget.check()
        budget.finishing = True  # bootstrap finish STAYS in inventory, never finalization
        budget.arm()
        writer.put("freeze.json", {"version": "0.1", "status": "BOOTSTRAP_OBSERVED_PRE_EXIT", "amendment": AMENDMENT,
                   "approval_ref": ref, "approval_is_authorization": False,
                   "command": ["/usr/bin/python3", "-B", "-S", str(PROJECT / CALLER), "--stage", stage, "--approval-ref", ref],
                   "hashes_as_data": hashes, "stage_SCOPED": {"E004": list(SCOPED + E004_EXTRA), "E005": list(SCOPED)},
                   "config_bytes_utf8": config_bytes, "original_config_unchanged": True, "environment": environment,
                   "initial_disk": initial_disk, "unknown": UNKNOWN, "syntax_importability": "UNKNOWN / UNTESTED",
                   "resource_mode": "NOT_ENFORCED_PRACTICAL_MODE", "claim": "C037_UNVERIFIED", "E004_E005": "BLOCKED"})
        writer.put("receipt.json", {"status": "BOOTSTRAP_OBSERVED_PRE_EXIT", "freeze": writer.outputs["freeze.json"],
                   "ledger_observation": budget.ledger("INCOMPLETE_PRE_EXIT"), "disk": writer.space(),
                   "started_unix_approx": time.time() - (time.monotonic() - FIRST_WALL), "warmup": "NONE; metadata only",
                   "concurrency": "same worker/thread; no children created; counts not OS-certified",
                   "errors": [], "exit_code": None, "intended_local_return": 0, "overhead": "OVERHEAD_UNKNOWN"})
        writer.put("ledger.json", {"ledger": budget.ledger("INCOMPLETE_PRE_EXIT"), "links": dict(writer.outputs),
                   "finish_phase": "inventory", "failure_handling": "retain all partials; no retry/overwrite/delete",
                   "success_is_not_complete": True, "output_checksums_self": None})
        code = 0
    except BaseException as error:
        code, primary = 2, error_record(error)
        if writer is not None and writer.owned:
            try:
                budget.finishing = True
                budget.arm()  # absolute 15s deadline; may fail, never renew reserve
                writer.put("failure.json", {"status": "FAILED", "primary": primary, "secondary": None,
                           "ledger": budget.ledger("FAILED_PRE_EXIT"), "links": dict(writer.outputs),
                           "attempted": sorted(writer.attempted), "created": writer.created, "exit_code": None})
            except BaseException as reporting:
                secondary = error_record(reporting)
    finally:
        if budget is not None:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)  # cancellation/report/exit tail UNKNOWN
            except BaseException as ending:
                code = 2
                if primary is None:
                    primary = error_record(ending)
                elif secondary is None:
                    secondary = error_record(ending)
    return emit_summary(code, primary, secondary, writer)


if __name__ == "__main__":
    raise SystemExit(main())
