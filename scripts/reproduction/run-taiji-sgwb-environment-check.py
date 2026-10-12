#!/usr/bin/env python3
"""Install/check the independent environment and preserve execution evidence."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/environment"
PYTHON = ROOT / "environments/taiji-sgwb/.venv/bin/python"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true", help="Sync the locked environment before checking.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Environment verification only; no full upstream demos or scientific inference.", "commands": []}
    started = time.perf_counter()
    commands = []
    if args.setup:
        commands.append((["bash", "scripts/reproduction/setup-taiji-sgwb-macos.sh"], "setup-execution.txt"))
    commands.extend([
        (["uv", "pip", "check", "--python", str(PYTHON)], "dependency-check.txt"),
        ([str(PYTHON), "-B", "scripts/reproduction/check-taiji-sgwb-environment.py"], "execution.txt"),
        (["python3", "scripts/reproduction/audit-taiji-sgwb-source.py", "--offline", "--output-dir",
          "results/taiji-sgwb/environment/source-audit"], "source-check.txt"),
    ])
    success = True
    for command, logfile in commands:
        t0 = time.perf_counter()
        print("RUN", logfile, flush=True)
        with (OUT / logfile).open("w") as stream:
            proc = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        report["commands"].append({"argv": command, "returncode": proc.returncode,
                                   "seconds": time.perf_counter() - t0, "log": logfile})
        print((OUT / logfile).read_text(), flush=True)
        if proc.returncode:
            success = False
            break
    if success:
        checked = json.loads((OUT / "check.json").read_text())
        locked = dict(re.findall(r"^([\w-]+)==([^\s\\]+)", (ROOT / "environments/taiji-sgwb/requirements-macos-arm64-py311.txt").read_text(), re.M))
        normalize = lambda s: re.sub(r"[-_.]+", "-", s).lower()
        installed = {normalize(n): v for n, v in checked["versions"].items()}
        parity = {name: installed.get(normalize(name)) == version for name, version in locked.items()}
        assert all(parity.values()), parity
        assert set(installed) == {normalize(n) for n in locked} | {"taijisgwb"}
        report["locked_package_count"] = len(locked)
        report["all_locked_versions_match"] = all(parity.values())
        report["only_additional_distribution"] = "taijisgwb==0.1.0 (pinned editable source)"
        report["check_count"] = len(checked["checks"])
    report["elapsed_seconds"] = time.perf_counter() - started
    report["success"] = success
    (OUT / "run.json").write_text(json.dumps(report, indent=2) + "\n")
    files = []
    for file in sorted(OUT.rglob("*")):
        if file.is_file() and file.name != "manifest.json":
            content = file.read_bytes()
            files.append({"path": str(file.relative_to(ROOT)), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    (OUT / "manifest.json").write_text(json.dumps({"schema_version": 1, "files": files}, indent=2) + "\n")
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
