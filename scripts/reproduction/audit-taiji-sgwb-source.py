#!/usr/bin/env python3
"""Audit the complete pinned TaijiSGWB tree without importing upstream code."""
import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from taiji_sgwb_source import source_lock, source_is_pristine, file_records, actual_tree_oid

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "external/taiji-sgwb"
OUTPUT = ROOT / "results/taiji-sgwb/source"
PIN = "4afaad4044b08721e7f1ce29cba3b0d912636dce"
URL = "https://github.com/DrizzleatDusk/TaijiSGWB.git"
EXPECTED = sorted([
    ".gitignore", "LICENSE", "README.md", "pyproject.toml",
    "demos/template_nofg_28t.py", "demos/rj_nofg_28t.py",
    "src/taijisgwb/__init__.py", "src/taijisgwb/analyorf.py",
    "src/taijisgwb/constants.py", "src/taijisgwb/plotlib.py",
    "src/taijisgwb/utils.py", "src/taijisgwb/waveform.py",
    "src/taijisgwb/detector/__init__.py", "src/taijisgwb/detector/constants.py",
    "src/taijisgwb/detector/data.py", "src/taijisgwb/detector/interferometer.py",
    "src/taijisgwb/detector/noise.py", "src/taijisgwb/detector/orbit.py",
    "src/taijisgwb/detector/tdi.py",
])


def git(*args, cwd=SOURCE):
    return subprocess.check_output(["git", "-C", str(cwd), *args])


def audit(offline=False, output=OUTPUT):
    lock = source_lock()
    checks = {}
    checks["pinned_commit"] = lock["pinned_commit"] == PIN
    checks["origin_url"] = lock["upstream_url"] == URL
    checks["fixed_source_snapshot"] = lock["integration"] == "fixed-source-snapshot"
    checks["no_nested_git_pointer"] = not (SOURCE/".git").exists()
    module = subprocess.run(["git", "config", "-f", str(ROOT/".gitmodules"), "--get",
        "submodule.external/taiji-sgwb.path"], capture_output=True)
    checks["submodule_registration_removed"] = module.returncode == 1
    indexed = git("ls-files", "--stage", "--", "external/taiji-sgwb", cwd=ROOT).decode().splitlines()
    expected_index = {"external/taiji-sgwb/"+f["path"]:(f["git_mode"],f["git_blob"]) for f in lock["files"]}
    actual_index = {}
    for line in indexed:
        meta, name = line.split("\t",1)
        mode, oid, stage = meta.split()
        actual_index[name] = (mode,oid)
    checks["parent_tracks_all_original_files_directly"] = actual_index == expected_index
    checks["parent_gitlink_removed"] = all(not line.startswith("160000 ") for line in indexed)
    paths = sorted(f["path"] for f in lock["files"])
    checks["complete_expected_tree"] = paths == EXPECTED
    actual_paths = sorted(str(p.relative_to(SOURCE)) for p in SOURCE.rglob("*") if p.is_file() and p.name != ".DS_Store")
    checks["no_missing_or_extra_checkout_files"] = actual_paths == paths
    files = file_records()
    checks["every_file_byte_identical"] = all(f["matches_pinned_blob"] and f["sha256"]==e["sha256"] for f,e in zip(files,lock["files"]))
    checks["every_file_mode_matches"] = all(f["matches_git_mode"] for f in files)
    checks["original_git_tree_reconstructed_exactly"] = actual_tree_oid() == lock["tree_oid"]
    checks["clean_source_including_untracked"] = source_is_pristine() and actual_paths == paths
    python_paths = [name for name in paths if name.endswith(".py")]
    for name in python_paths:
        ast.parse((SOURCE / name).read_text(), filename=name)
    checks["all_python_files_parse_without_execution"] = True
    checks["original_gpl3_license"] = "Version 3, 29 June 2007" in (SOURCE / "LICENSE").read_text()
    checks["declared_gpl3_or_later"] = 'license = "GPL-3.0-or-later"' in (SOURCE / "pyproject.toml").read_text()
    remote = {"checked": not offline, "url": URL}
    if not offline:
        raw = git("ls-remote", URL, "HEAD", "refs/heads/main").decode()
        refs = {line.split()[1]: line.split()[0] for line in raw.splitlines()}
        remote["refs"] = refs
        checks["upstream_head_matches_pin"] = refs.get("HEAD") == PIN
        checks["upstream_main_matches_pin"] = refs.get("refs/heads/main") == PIN
    report = {"schema_version": 2, "integration": "fixed-source-snapshot", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Source preservation only; no package import, environment installation, data preparation or inference execution.",
              "upstream_url": URL, "pinned_commit": PIN,
              "tree_oid": actual_tree_oid(),
              "commit_date": lock["commit_date"],
              "tracked_files": len(files), "python_files": len(python_paths),
              "demo_files": [name for name in paths if name.startswith("demos/")],
              "remote": remote, "checks": checks, "all_checks_pass": all(checks.values())}
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps({"schema_version": 1,
        "upstream_url": URL, "pinned_commit": PIN, "files": files}, indent=2) + "\n")
    (output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "file-list.txt").write_text("\n".join(paths) + "\n")
    print(f"TaijiSGWB source audit: {sum(checks.values())}/{len(checks)} checks passed; "
          f"{len(files)} files, {len(python_paths)} Python files, 2 demos.")
    if not report["all_checks_pass"]:
        raise SystemExit("FAILED: " + ", ".join(k for k, passed in checks.items() if not passed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Skip current upstream remote HEAD verification.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT, help="Evidence destination; defaults to the Stage 1 source directory.")
    args = parser.parse_args()
    audit(args.offline, args.output_dir)
