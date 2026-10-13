#!/usr/bin/env python3
"""Sequential benchmark, capped sampling and fresh-process restart evidence."""
import csv
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/taiji-sgwb/template-mini'


def phase(mode):
    out=OUT/mode;out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat();samples=[]
    command=['bash','scripts/reproduction/run-taiji-sgwb-python.sh','scripts/reproduction/run-taiji-sgwb-mini-worker.py','--mode',mode]
    with (out/'execution.txt').open('w') as log:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        while proc.poll() is None:
            raw=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=']).decode();entries=[tuple(map(int,line.split())) for line in raw.splitlines() if len(line.split())==3];family={proc.pid}
            for _ in range(3):family.update(p for p,ppid,rss in entries if ppid in family)
            values=[(p,rss) for p,ppid,rss in entries if p in family];samples.append((time.perf_counter()-start,next((rss for p,rss in values if p==proc.pid),0),sum(rss for p,rss in values),len(values)));time.sleep(1)
    with (out/'resources.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['seconds','parent_rss_kib','family_rss_sum_kib','family_process_count']);w.writerows(samples)
    value={'started_utc':started_utc,'argv':command,'pid':proc.pid,'returncode':proc.returncode,'wall_seconds':time.perf_counter()-start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'peak_parent_rss_kib':max((x[1] for x in samples),default=0),'peak_family_rss_sum_kib':max((x[2] for x in samples),default=0),'resource_note':'~1 s sampled RSS; fork-shared pages double-counted in sum; no actual physical-RAM claim.'};(out/'run.json').write_text(json.dumps(value,indent=2)+'\n')
    print(f'{mode}: rc={proc.returncode}, {value["wall_seconds"]:.3f} s',flush=True)
    if proc.returncode:print((out/'execution.txt').read_text(),flush=True);raise SystemExit(proc.returncode)
    return json.loads((out/'worker.json').read_text())


def main():
    start=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True)
    phase('benchmark');speed=json.loads((OUT/'speed-check.json').read_text());print(json.dumps(speed,indent=2),flush=True)
    if not speed['budget_fit']:raise RuntimeError('Measured schedule exceeds approved small-run budget; stopped at benchmark checkpoint')
    for mode in ['first','resume']:
        w=phase(mode)
        if w['status']=='BUDGET_OR_USER_STOP':raise RuntimeError('Small-run budget reached; checkpoint preserved')
    (OUT/'sampling-run.json').write_text(json.dumps({'wall_seconds':time.perf_counter()-start,'scope':'20 real warmup-speed-check updates, continuation to burn300/production500, exit and fresh-process continuation to production1000.'},indent=2)+'\n')

if __name__=='__main__':main()
