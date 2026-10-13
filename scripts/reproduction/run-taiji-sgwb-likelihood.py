#!/usr/bin/env python3
"""Run the Stage 7 worker and record command/log/resource provenance."""
import csv
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"results/taiji-sgwb/likelihood"


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    command=["bash","scripts/reproduction/run-taiji-sgwb-python.sh","scripts/reproduction/check-taiji-sgwb-likelihood.py"]
    start=time.perf_counter();samples=[];monitoring_error=None
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (OUT/"execution.txt").open("w") as log:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        while proc.poll() is None:
            try:
                raw=subprocess.check_output(["ps","-o","rss=","-p",str(proc.pid)]).decode().strip()
                if raw:samples.append((time.perf_counter()-start,int(raw)))
            except PermissionError as e:monitoring_error=repr(e)
            except subprocess.CalledProcessError:pass
            time.sleep(.5)
    with (OUT/"resources.csv").open("w") as file:
        writer=csv.writer(file,lineterminator="\n");writer.writerow(["seconds","worker_rss_kib"]);writer.writerows(samples)
    report={"started_utc":started,"argv":command,"pid":proc.pid,"returncode":proc.returncode,
        "wall_seconds":time.perf_counter()-start,"peak_sampled_worker_rss_kib":max((r for _,r in samples),default=0),
        "monitoring_error":monitoring_error,"resource_note":"RSS of the single CPU worker sampled approximately every 0.5 seconds; may miss shorter peaks.",
        "scope":"Original spectral models and likelihood numerical checks; no MCMC updates or posterior sampling."}
    (OUT/"run.json").write_text(json.dumps(report,indent=2)+"\n")
    print((OUT/"execution.txt").read_text(),flush=True)
    print(json.dumps(report,indent=2),flush=True)
    if proc.returncode:raise SystemExit(proc.returncode)


if __name__=="__main__":main()
