#!/usr/bin/env python3
"""Verify input checksums, aliases and evidence without executing demos."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/data"


def main():
    download = json.loads((OUT / "download.json").read_text())
    validation = json.loads((OUT / "validation.json").read_text())
    run = json.loads((OUT / "run.json").read_text())
    paths = json.loads((OUT / "path-map.json").read_text())
    checks = {"all_validation_checks_pass": validation["all_checks_pass"] and all(validation["checks"].values()),
              "successful_execution": run["success"] and all(c["returncode"] == 0 for c in run["commands"]),
              "official_filename_preserved": download["data"]["official_filename"] == "TDCII2.8.h5",
              "original_orbit_filename_preserved": download["orbit"]["official_filename"] == "MicroSateOrbit.hdf5",
              "both_original_read_interfaces_pass": len(validation["original_read_interfaces"]) == 2 and all(r["all_AET_finite"] for r in validation["original_read_interfaces"]),
              "official_md5_and_orbit_git_blob_verified": download["data"]["official_checksum_passed"] and download["orbit"]["matches_pinned_official_git_blob"]}
    for kind in ["data", "orbit"]:
        entry = download[kind]
        file = ROOT / entry["path"]
        md5, sha = hashlib.md5(), hashlib.sha256()
        with file.open("rb") as stream:
            while block := stream.read(8*1024*1024):
                md5.update(block)
                sha.update(block)
        checks[kind + "_size_and_hashes_reverified"] = file.stat().st_size == entry["bytes"] and sha.hexdigest() == entry["sha256"] and md5.hexdigest() == entry["md5"]
        checks[kind + "_ignored_by_git"] = subprocess.run(["git", "check-ignore", "--quiet", entry["path"]], cwd=ROOT).returncode == 0
    checks["all_runtime_aliases_resolve"] = all((ROOT / m["link"]).is_symlink() and (ROOT / m["link"]).resolve() == (ROOT / m["target"]).resolve() for m in paths["links"])
    checks["runtime_aliases_ignored"] = all(subprocess.run(["git", "check-ignore", "--quiet", m["link"]], cwd=ROOT).returncode == 0 for m in paths["links"])
    source = ROOT / "external/taiji-sgwb"
    manifest = json.loads((ROOT / "results/taiji-sgwb/source/manifest.json").read_text())
    checks["original_TaijiSGWB_files_unchanged"] = all(hashlib.sha256((source / f["path"]).read_bytes()).hexdigest() == f["sha256"] for f in manifest["files"])
    report = {"scope": "Input/evidence integrity only; does not run full preprocessing, response grids or parameter inference.",
              "checks": checks, "all_checks_pass": all(checks.values())}
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    files = [p for p in OUT.rglob("*") if p.is_file() and p.name != "manifest.json"]
    files += [ROOT / "scripts/reproduction" / n for n in ["download-taiji-sgwb-data.py", "prepare-taiji-sgwb-paths.py", "check-taiji-sgwb-data.py", "run-taiji-sgwb-data-check.py", "audit-taiji-sgwb-data.py"]]
    files += [ROOT / "configs/reproduction/taiji-sgwb/data-paths.json", ROOT / "docs/reproduction/taiji-sgwb/data-preparation.md"]
    entries = [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
    (OUT / "manifest.json").write_text(json.dumps({"schema_version": 1, "files": entries}, indent=2) + "\n")
    print(f"TaijiSGWB data audit: {sum(checks.values())}/{len(checks)} passed; {len(entries)} hashed artifacts.")
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
