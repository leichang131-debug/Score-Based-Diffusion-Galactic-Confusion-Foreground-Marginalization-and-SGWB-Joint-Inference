#!/usr/bin/env python3
"""Prepare input aliases and record actual local validation commands/timings."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Retrieve/check official inputs before validating.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Official input preparation and full data scan; no complete preprocessing, response grid or inference.", "commands": []}
    commands = []
    if args.download:
        commands.append((["python3", "scripts/reproduction/download-taiji-sgwb-data.py"], "download-execution.txt"))
    commands += [(["python3", "scripts/reproduction/prepare-taiji-sgwb-paths.py"], "path-execution.txt"),
        (["bash", "scripts/reproduction/run-taiji-sgwb-python.sh", "scripts/reproduction/check-taiji-sgwb-data.py"], "validation-execution.txt")]
    started = time.perf_counter()
    success = True
    for argv, log in commands:
        before = time.perf_counter()
        print("RUN", log, flush=True)
        with (OUT / log).open("w") as stream:
            proc = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        report["commands"].append({"argv": argv, "returncode": proc.returncode,
                                   "seconds": time.perf_counter()-before, "log": log})
        print((OUT / log).read_text(), flush=True)
        if proc.returncode:
            success = False
            break
    report["wall_seconds"] = time.perf_counter() - started
    report["success"] = success
    (OUT / "run.json").write_text(json.dumps(report, indent=2) + "\n")
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
