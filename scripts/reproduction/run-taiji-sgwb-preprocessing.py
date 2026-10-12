#!/usr/bin/env python3
"""Run both original Stage 5 prefixes and retain timings/resources/parity."""
import csv
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/preprocessing"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = time.perf_counter()
    result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Two separate local executions of original full-scale preprocessing; no response computation or sampling.", "runs": []}
    cases = []
    for entry in ["template_nofg_28t.py", "rj_nofg_28t.py"]:
        case = Path(entry).stem
        case_out = OUT / case
        case_out.mkdir(parents=True, exist_ok=True)
        command = ["bash", "scripts/reproduction/run-taiji-sgwb-python.sh", "scripts/reproduction/check-taiji-sgwb-preprocessing.py", "--entry", entry]
        print("RUN", entry, flush=True)
        started = time.perf_counter()
        samples = []
        monitoring_error = None
        with (case_out / "execution.txt").open("w") as log:
            proc = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            while proc.poll() is None:
                try:
                    raw = subprocess.check_output(["ps", "-o", "rss=", "-p", str(proc.pid)]).decode().strip()
                    if raw:
                        samples.append((time.perf_counter()-started, int(raw)))
                except PermissionError as exc:
                    monitoring_error = repr(exc)
                except subprocess.CalledProcessError:
                    pass
                time.sleep(.1)
        seconds = time.perf_counter()-started
        with (case_out / "resources.csv").open("w") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["seconds", "worker_rss_kib"])
            writer.writerows(samples)
        run = {"entry": entry, "argv": command, "pid": proc.pid, "returncode": proc.returncode,
            "wall_seconds": seconds, "peak_sampled_worker_rss_kib": max((r for _,r in samples), default=0),
            "monitoring_error": monitoring_error,
            "resource_note": "RSS of the single worker sampled approximately every 0.1 seconds; may miss shorter peaks; not system total memory."}
        (case_out / "run.json").write_text(json.dumps(run, indent=2) + "\n")
        result["runs"].append(run)
        print((case_out / "execution.txt").read_text(), flush=True)
        if proc.returncode:
            result["success"] = False
            (OUT / "run.json").write_text(json.dumps(result, indent=2) + "\n")
            raise SystemExit(proc.returncode)
        cases.append(json.loads((case_out / "validation.json").read_text()))
    array_parity = {name: cases[0]["arrays"][name] == cases[1]["arrays"][name] for name in ["frequency", "CSD", "STFT"]}
    result["array_hash_parity"] = array_parity
    result["success"] = all(array_parity.values()) and all(c["all_checks_pass"] for c in cases)
    result["wall_seconds"] = time.perf_counter() - before
    (OUT / "run.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Independent original demo preprocessing parity:", array_parity, flush=True)
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
