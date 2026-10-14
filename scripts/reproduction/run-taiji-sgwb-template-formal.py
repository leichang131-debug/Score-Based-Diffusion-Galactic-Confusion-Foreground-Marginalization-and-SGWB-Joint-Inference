#!/usr/bin/env python3
"""Persistent supervisor: resume original formal schedule, analyze, sync evidence."""
import argparse
import csv
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import time
import os

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'runs/taiji-sgwb/template-formal'
OUT=ROOT/'results/taiji-sgwb/template-formal'


def write(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def python(script):return ['bash','scripts/reproduction/run-taiji-sgwb-python.sh','scripts/reproduction/'+script]


def sync_evidence(message):
    # User explicitly authorized stage evidence pushes. Stage only owned paths.
    subprocess.run(python('audit-taiji-sgwb-template-formal.py'),cwd=ROOT,check=True)
    for cmd in [['git','add','results/taiji-sgwb/template-formal'],['git','diff','--cached','--check','--','results/taiji-sgwb/template-formal']]:subprocess.run(cmd,cwd=ROOT,check=True)
    changed=subprocess.run(['git','diff','--cached','--quiet','--','results/taiji-sgwb/template-formal'],cwd=ROOT).returncode
    if changed==1:subprocess.run(['git','commit','--only','-m',message,'--','results/taiji-sgwb/template-formal'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True,timeout=120)


def snapshot():
    if (WORK/'progress.json').exists():shutil.copyfile(WORK/'progress.json',OUT/'progress-snapshot.json')
    if (WORK/'source-execution.json').exists():shutil.copyfile(WORK/'source-execution.json',OUT/'source-execution.json')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sync',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    lock=WORK/'supervisor.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise RuntimeError('Supervisor lock exists; verify saved PID before recovery')
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    start=time.perf_counter();samples=[];last_sync=start
    session=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    history=OUT/'sessions'/session;history.mkdir(parents=True,exist_ok=False)
    for name in ['launch.json','run.json','resources.csv','status.json','progress-snapshot.json','execution.txt']:
        if (OUT/name).exists():shutil.copyfile(OUT/name,history/('previous-'+name))
    prior=json.loads((WORK/'progress.json').read_text())
    command=python('run-taiji-sgwb-template-formal-worker.py')+['--resume']
    write(WORK/'supervisor.json',{'pid':os.getpid(),'argv':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Original full formal inference. Live outputs ignored; portable progress/evidence snapshots synced hourly and on completion.'})
    caffeinate=None
    try:
        with (WORK/'formal-execution.log').open('a') as log:
            proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:caffeinate=subprocess.Popen(['caffeinate','-is','-w',str(proc.pid)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            except FileNotFoundError:pass
            write(OUT/'launch.json',{'supervisor_pid':os.getpid(),'worker_pid':proc.pid,'argv':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'resume_from_burn':prior['burn_done'],'resume_from_production':prior['production_saved'],'target_burn':1000,'target_saved_samples':350,'thin_by':12,'idle_sleep_inhibited':caffeinate is not None})
            shutil.copyfile(OUT/'launch.json',history/'launch.json')
            write(OUT/'status.json',{'status':'RUNNING','sampling_complete':False,'note':'Resumed original full-data schedule; no posterior verdict yet.'})
            while proc.poll() is None:
                raw=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=']).decode()
                entries=[tuple(map(int,x.split())) for x in raw.splitlines() if len(x.split())==3];family={proc.pid}
                for _ in range(4):family.update(pid for pid,ppid,rss in entries if ppid in family)
                rss=[(pid,rss) for pid,ppid,rss in entries if pid in family]
                samples.append([time.perf_counter()-start,next((r for pid,r in rss if pid==proc.pid),0),sum(r for pid,r in rss),len(rss)])
                pointer=WORK/'latest-checkpoint.json'
                if pointer.exists() and not (WORK/'burn-exit-state.json').exists():
                    ref=json.loads(pointer.read_text());record_path=WORK/ref['directory']/'state.json'
                    state_record=json.loads(record_path.read_text())
                    if state_record['burn_done']==1000 and state_record['production_done']==0:shutil.copyfile(record_path,WORK/'burn-exit-state.json')
                if not args.no_sync and time.perf_counter()-last_sync>=3600:
                    snapshot()
                    try:sync_evidence('Record TaijiSGWB formal template inference progress')
                    except Exception as e:write(OUT/'sync-error.json',{'error':repr(e),'note':'Sampling continues; retry next snapshot.'})
                    last_sync=time.perf_counter()
                time.sleep(30)
        snapshot()
        shutil.copyfile(WORK/'formal-execution.log',OUT/'execution.txt')
        with (OUT/'resources.csv').open('w') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['seconds','parent_rss_kib','family_rss_sum_kib','family_count']);w.writerows(samples)
        write(OUT/'run.json',{'returncode':proc.returncode,'worker_pid':proc.pid,'wall_seconds':time.perf_counter()-start,'peak_parent_rss_kib':max((s[1] for s in samples),default=0),'peak_family_rss_sum_kib':max((s[2] for s in samples),default=0),'resource_note':'RSS sums double-count fork-shared pages; ~30-second sampling may miss peaks.'})
        if proc.returncode:
            write(OUT/'status.json',{'status':'SAMPLING_FAILED','note':'See execution log and last immutable checkpoint. No completed posterior.'})
        else:
            progress=json.loads((WORK/'progress.json').read_text())
            if progress['status']=='SAMPLING_COMPLETE':
                shutil.copyfile(WORK/'template_AET_nofg.h5',OUT/'template_AET_nofg.h5')
                cp=json.loads((WORK/'latest-checkpoint.json').read_text());p=WORK/cp['directory']
                shutil.copyfile(p/'state.json',OUT/'final-state.json');shutil.copyfile(p/'state.npz',OUT/'final-state.npz')
                if (WORK/'burn-exit-state.json').exists():shutil.copyfile(WORK/'burn-exit-state.json',OUT/'burn-exit-state.json')
                result=subprocess.run(python('analyze-taiji-sgwb-template-formal.py'),cwd=ROOT,capture_output=True,text=True)
                (OUT/'analysis-execution.txt').write_text(result.stdout+result.stderr)
                if result.returncode:write(OUT/'status.json',{'status':'ANALYSIS_FAILED','sampling_complete':True,'note':'Read analysis-execution.txt; no convergence claim.'})
            else:write(OUT/'status.json',{'status':progress['status'],'sampling_complete':False,'note':'Checkpoint saved; original schedule not finished.'})
        for name in ['run.json','resources.csv','status.json','progress-snapshot.json']:
            if (OUT/name).exists():shutil.copyfile(OUT/name,history/name)
        if not args.no_sync:sync_evidence('Record TaijiSGWB formal template sampling outcome and posterior diagnostics')
    finally:
        if caffeinate and caffeinate.poll() is None:caffeinate.terminate()
        lock.unlink(missing_ok=True)

if __name__=='__main__':main()
