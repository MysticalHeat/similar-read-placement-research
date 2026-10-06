"""Screen same-start training labels without inspecting future-day performance."""

import gzip
import hashlib
import json
import tarfile
from collections import Counter

import numpy as np

from read_prediction.artifacts import fingerprint
from read_prediction.paths import PROJECT_ROOT
from read_prediction.pipeline import Event, TICKS_PER_SECOND, make_samples


class WindowCounter:
    """Count observed labels and competing first events within one closed window."""

    def __init__(self):
        self.reads = self.writes = self.read_first = self.write_first = 0
        self.target_reads = 0
        self.pending = Counter()
        self.unresolved = set()
        self.labelled = Counter()

    def add(self, kind, offset):
        if kind == b"Write":
            self.writes += 1
            self.pending[offset] += 1
            if offset in self.unresolved:
                self.write_first += 1
            self.unresolved.add(offset)
        else:
            self.reads += 1
            waiting = self.pending.pop(offset, 0)
            if waiting:
                self.labelled[offset] += waiting
                self.target_reads += 1
            if offset in self.unresolved:
                self.read_first += 1
                self.unresolved.remove(offset)

    def summary(self):
        n = sum(self.labelled.values())
        assert self.read_first + self.write_first + len(self.unresolved) == self.writes
        return {
            "events": self.reads + self.writes, "reads": self.reads, "writes": self.writes,
            "observed_labels": n, "unobserved_labels": self.writes - n,
            "coverage": n / self.writes if self.writes else None,
            "distinct_labelled_offsets": len(self.labelled),
            "distinct_target_reads": self.target_reads,
            "largest_address_label_share": max(self.labelled.values()) / n if n else None,
            "effective_address_count": n * n / sum(v * v for v in self.labelled.values()) if n else 0,
            "read_first": self.read_first, "write_first": self.write_first,
            "unresolved_first_event": len(self.unresolved),
        }


def eligibility(train, validation, full_window):
    reasons = []
    if not full_window:
        reasons.append("incomplete_19.2h_window")
    for name, metrics, labels, offsets in (
        ("train", train, 10_000, 100), ("validation", validation, 2_000, 50)
    ):
        if metrics["observed_labels"] < labels:
            reasons.append(f"{name}_too_few_labels")
        if metrics["distinct_labelled_offsets"] < offsets:
            reasons.append(f"{name}_too_few_labelled_offsets")
    independent_targets = (train["distinct_target_reads"] >= 1000
                           and validation["distinct_target_reads"] >= 200)
    return {
        "basic_eligible": not reasons, "basic_failure_reasons": reasons,
        "target_event_support": independent_targets,
        "recommended_for_next_check": not reasons and independent_targets,
        "read_first_support": train["read_first"] >= 1000 and validation["read_first"] >= 200,
    }


def verify_prefix(prefix, origin):
    boundaries = [origin, origin + round(14.4 * 3600 * TICKS_PER_SECOND),
                  origin + round(19.2 * 3600 * TICKS_PER_SECOND)]
    for begin, end in zip(boundaries, boundaries[1:]):
        part = [e for e in prefix if begin <= e.timestamp < end]
        if not part:
            continue
        reference = make_samples(part)
        counter = WindowCounter()
        for event in part:
            counter.add(event.kind.encode(), event.offset)
        assert counter.summary()["observed_labels"] == int((reference["next_read_indices"] >= 0).sum())
        assert counter.summary()["distinct_target_reads"] == len(
            np.unique(reference["next_read_indices"][reference["next_read_indices"] >= 0]))


def screen(archive, member):
    counters = [WindowCounter(), WindowCounter()]
    digest = hashlib.sha256()
    origin = previous = volume = None
    full_window = False
    prefix = []
    with archive.extractfile(member) as raw, gzip.GzipFile(fileobj=raw) as stream:
        for line in stream:
            fields = line.strip().split(b",")
            if len(fields) != 7:
                raise ValueError(f"Invalid source row in {member.name}")
            ts, host, disk, kind, offset, size, response = fields
            ts, offset, size = int(ts), int(offset), int(size)
            row_volume = (host.decode(), int(disk))
            if origin is None:
                origin, volume = ts, row_volume
            if previous is not None and ts < previous:
                raise ValueError(f"Nonchronological trace: {member.name}")
            if row_volume != volume:
                raise ValueError(f"Multiple volumes: {member.name}")
            if ts >= origin + round(19.2 * 3600 * TICKS_PER_SECOND):
                full_window = True
                break
            if (kind not in (b"Read", b"Write") or offset < 0 or size <= 0
                    or offset % 512 or size % 512 or int(response) < 0):
                raise ValueError(f"Invalid I/O fields: {member.name}")
            window = int(ts >= origin + round(14.4 * 3600 * TICKS_PER_SECOND))
            counters[window].add(kind, offset)
            digest.update(line)
            if len(prefix) < 2000:
                prefix.append(Event(ts, kind.decode(), offset, size))
            previous = ts
    if origin is None:
        raise ValueError(f"Empty source: {member.name}")
    verify_prefix(prefix, origin)
    train, validation = [c.summary() for c in counters]
    n = validation["observed_labels"]
    shared = sum(count for offset, count in counters[1].labelled.items()
                 if offset in counters[0].labelled)
    return {
        "workload": member.name.split("/")[-1].removesuffix(".csv.gz"),
        "volume": volume, "source_member": member.name,
        "first_timestamp": origin, "last_included_timestamp": previous,
        "full_window": full_window, "prefix_sha256": digest.hexdigest(),
        "verified_prefix_events": len(prefix), "train": train, "validation": validation,
        "validation_labels_on_training_labelled_offsets_share": shared / n if n else None,
        **eligibility(train, validation, full_window),
    }


def main():
    folder = PROJECT_ROOT / "results/data-sufficiency"
    folder.mkdir(exist_ok=False)
    results = []
    for name in ("msr-cambridge1.tar", "msr-cambridge2.tar"):
        with tarfile.open(PROJECT_ROOT / "dataset" / name) as archive:
            members = sorted((m for m in archive.getmembers() if m.name.endswith(".csv.gz")),
                             key=lambda m: m.name)
            for member in members:
                result = screen(archive, member)
                result["source_archive"] = name
                results.append(result)
                (folder / f"{result['workload']}.json").write_text(
                    json.dumps(result, indent=2, ensure_ascii=False) + "\n")
                print(result["workload"], "train", result["train"]["observed_labels"],
                      "validation", result["validation"]["observed_labels"],
                      "target_reads", result["train"]["distinct_target_reads"],
                      result["validation"]["distinct_target_reads"],
                      "recommended", result["recommended_for_next_check"], flush=True)
    candidates = sorted((r for r in results if r["recommended_for_next_check"]
                         and r["workload"] not in ("usr_1", "prxy_1", "prxy_0")),
                        key=lambda r: (r["validation"]["distinct_target_reads"],
                                       r["train"]["distinct_target_reads"]), reverse=True)
    summary = {"traces": len(results), "recommended_new_workloads": [r["workload"] for r in candidates],
               "results": results, "hashes": {str(p.relative_to(PROJECT_ROOT)): fingerprint(p) for p in (
                   PROJECT_ROOT / "docs/protocols/data-sufficiency-protocol.md",
                   PROJECT_ROOT / "read_prediction/experiments/data_sufficiency.py")}}
    (folder / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print("Recommended new workloads:", summary["recommended_new_workloads"], flush=True)


if __name__ == "__main__":
    main()
