#!/usr/bin/env python3
"""Audit the complete pinned TaijiSGWB tree without importing upstream code."""
import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

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
    checks = {}
    checks["pinned_commit"] = git("rev-parse", "HEAD").decode().strip() == PIN
    checks["clean_source_including_untracked"] = not git("status", "--porcelain", "--untracked-files=all").strip()
    checks["origin_url"] = git("remote", "get-url", "origin").decode().strip() == URL
    checks["registered_submodule_url"] = git("config", "-f", ".gitmodules", "--get",
        "submodule.external/taiji-sgwb.url", cwd=ROOT).decode().strip() == URL
    checks["registered_submodule_path"] = git("config", "-f", ".gitmodules", "--get",
        "submodule.external/taiji-sgwb.path", cwd=ROOT).decode().strip() == "external/taiji-sgwb"
    checks["parent_index_gitlink"] = git("ls-files", "--stage", "external/taiji-sgwb", cwd=ROOT).decode().startswith("160000 " + PIN)
    entries = []
    for line in git("ls-tree", "-r", "-z", PIN).split(b"\0"):
        if not line:
            continue
        metadata, name = line.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        entries.append((name.decode(), mode, kind, oid))
    paths = sorted(e[0] for e in entries)
    checks["complete_expected_tree"] = paths == EXPECTED
    actual_paths = sorted(str(p.relative_to(SOURCE)) for p in SOURCE.rglob("*")
                          if p.is_file() and p.name != ".git")
    checks["no_missing_or_extra_checkout_files"] = actual_paths == paths
    files = []
    for name, mode, kind, oid in entries:
        p = SOURCE / name
        actual = p.read_bytes()
        original = git("cat-file", "blob", oid)
        matched = actual == original
        mode_matched = mode == ("100755" if p.stat().st_mode & 0o111 else "100644")
        files.append({"path": name, "repository_path": "external/taiji-sgwb/" + name,
                      "git_mode": mode, "git_blob": oid, "bytes": len(actual),
                      "sha256": hashlib.sha256(actual).hexdigest(),
                      "matches_pinned_blob": matched, "matches_git_mode": mode_matched})
    checks["every_file_byte_identical"] = all(f["matches_pinned_blob"] for f in files)
    checks["every_file_mode_matches"] = all(f["matches_git_mode"] for f in files)
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
    report = {"schema_version": 1, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Source preservation only; no package import, environment installation, data preparation or inference execution.",
              "upstream_url": URL, "pinned_commit": PIN,
              "tree_oid": git("rev-parse", PIN + "^{tree}").decode().strip(),
              "commit_date": git("show", "-s", "--format=%cI", PIN).decode().strip(),
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
