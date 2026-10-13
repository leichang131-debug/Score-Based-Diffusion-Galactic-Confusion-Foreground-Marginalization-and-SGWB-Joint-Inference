#!/usr/bin/env python3
"""Fresh-process initial/resume/continuous runs with provenance and pool RSS."""
import csv
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/taiji-sgwb/template-short-chain'


def run_phase(mode):
    out=OUT/mode;out.mkdir(parents=True,exist_ok=True)
    argv=['bash','scripts/reproduction/run-taiji-sgwb-python.sh','scripts/reproduction/run-taiji-sgwb-template-worker.py','--mode',mode]
    start=time.perf_counter();started=datetime.datetime.now(datetime.timezone.utc).isoformat();samples=[];error=None;pool_pids=set()
    with (out/'execution.txt').open('w') as log:
        proc=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        while proc.poll() is None:
            try:
                raw=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=']).decode()
                entries=[tuple(map(int,line.split())) for line in raw.splitlines() if len(line.split())==3]
                family={proc.pid};changed=True
                while changed:
                    before=len(family);family.update(pid for pid,ppid,rss in entries if ppid in family);changed=len(family)!=before
                members=[(pid,rss) for pid,ppid,rss in entries if pid in family]
                pool_pids.update(pid for pid,rss in members if pid!=proc.pid)
                parent_rss=next((rss for pid,rss in members if pid==proc.pid),0)
                samples.append((time.perf_counter()-start,parent_rss,sum(rss for pid,rss in members),len(members)))
            except (PermissionError,subprocess.CalledProcessError) as e:error=repr(e)
            time.sleep(1)
    with (out/'resources.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['seconds','parent_rss_kib','family_rss_sum_kib','family_process_count']);w.writerows(samples)
    result={'mode':mode,'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'pid':proc.pid,'observed_child_pids':sorted(pool_pids),'returncode':proc.returncode,'wall_seconds':time.perf_counter()-start,'process_exited_and_reaped':proc.poll() is not None,'monitoring_error':error,'peak_parent_rss_kib':max((x[1] for x in samples),default=0),'peak_family_rss_sum_kib':max((x[2] for x in samples),default=0),'resource_note':'Parent and descendant RSS sampled every ~1 s. Sum double-counts fork-shared memory and is not physical memory usage; shorter peaks can be missed.'}
    (out/'run.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{mode}: returncode={proc.returncode}, wall={result["wall_seconds"]:.3f} s, PID={proc.pid}',flush=True)
    if proc.returncode:
        print((out/'execution.txt').read_text(),flush=True);raise SystemExit(proc.returncode)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--start-at',choices=['initial','resume','continuous'],default='initial');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);start=time.perf_counter();phases=[]
    modes=('initial','resume','continuous');offset=modes.index(args.start_at)
    for mode in modes[:offset]:
        saved=json.loads((OUT/mode/'run.json').read_text());assert saved['returncode']==0;phases.append(saved)
    for mode in modes[offset:]:phases.append(run_phase(mode))
    (OUT/'run.json').write_text(json.dumps({'phases':phases,'current_invocation_seconds':time.perf_counter()-start,'sum_successful_phase_wall_seconds':sum(p['wall_seconds'] for p in phases),'start_at':args.start_at,'scope':'Initial 4 steps, terminated process, restored 4 steps, separate same-seed continuous 8-step control. No posterior convergence claim.'},indent=2)+'\n')
    command=['bash','scripts/reproduction/run-taiji-sgwb-python.sh','scripts/reproduction/check-taiji-sgwb-template-short-chain.py']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    (OUT/'validation-execution.txt').write_text(result.stdout+result.stderr);print(result.stdout+result.stderr,flush=True)
    if result.returncode:raise SystemExit(result.returncode)

if __name__=='__main__':main()
