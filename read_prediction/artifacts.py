"""Record artifact fingerprints and verify the Git-sized model bundle."""

import argparse
import hashlib
import json

from read_prediction.paths import PROJECT_ROOT


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"size_bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def build_manifest(root):
    files = {}
    for path in sorted((root / "dataset").rglob("*")):
        if path.is_file() and path.name != "README.md":
            files[path.relative_to(root).as_posix()] = {"storage": "external", **fingerprint(path)}
    for path in sorted((root / "results").rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".lightgbm.txt") or path.suffix == ".json":
            storage = "git"
        elif path.suffix in {".npz", ".npy", ".csv", ".bin"}:
            storage = "external"
        else:
            continue
        files[path.relative_to(root).as_posix()] = {"storage": storage, **fingerprint(path)}
    selected = {}
    for workload in ("usr_1", "prxy_1"):
        relative = f"results/final-study/{workload}/frozen.json"
        selection = json.loads((root / relative).read_text())["selection"]
        if files[selection["model_path"]]["storage"] != "git":
            raise ValueError(f"Selected model must be versioned: {workload}")
        selected[workload] = {"frozen_path": relative, **selection}
    return {"schema_version": 1, "selected_models": selected, "files": files}


def verify_manifest(manifest, root, include_external=False):
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported artifact manifest version")
    checked = 0
    for relative, entry in manifest["files"].items():
        if entry["storage"] == "external" and not include_external:
            continue
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Missing artifact: {relative}")
        if path.stat().st_size != entry["size_bytes"] or fingerprint(path)["sha256"] != entry["sha256"]:
            raise ValueError(f"Artifact fingerprint mismatch: {relative}")
        checked += 1
    for workload, recorded in manifest["selected_models"].items():
        selection = json.loads((root / recorded["frozen_path"]).read_text())["selection"]
        if {"frozen_path": recorded["frozen_path"], **selection} != recorded:
            raise ValueError(f"Frozen selection mismatch: {workload}")
        if manifest["files"][selection["model_path"]]["storage"] != "git":
            raise ValueError(f"Selected model must be versioned: {workload}")
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("record", "verify"))
    parser.add_argument("--include-external", action="store_true", help="Also verify local traces and prediction arrays")
    args = parser.parse_args()
    manifest_path = PROJECT_ROOT / "artifacts/manifest.json"
    if args.command == "record":
        manifest = build_manifest(PROJECT_ROOT)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"Recorded {len(manifest['files'])} artifact fingerprints in artifacts/manifest.json")
    else:
        manifest = json.loads(manifest_path.read_text())
        try:
            checked = verify_manifest(manifest, PROJECT_ROOT, args.include_external)
        except ValueError as error:
            parser.exit(1, f"{error}\n")
        print(f"Verified {checked} artifacts and both frozen model selections.")


if __name__ == "__main__":
    main()
