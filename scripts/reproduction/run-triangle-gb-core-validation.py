"""Measure full process runtimes and retain failures from the core verification suite."""
import datetime,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/core-validation';OUT.mkdir(parents=True,exist_ok=True)
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.node(),'machine':platform.machine(),'python_executable':sys.executable,'commands':[]};start=time.perf_counter()
for name,log in [('validate-triangle-gb-core.py','execution.txt'),('check-triangle-gb-core-impact.py','tutorial-impact-execution.txt')]:
 command=[sys.executable,str(ROOT/'scripts/reproduction'/name)];t=time.perf_counter()
 with (OUT/log).open('w') as f:result=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 report['commands'].append({'argv':command,'seconds_including_imports':time.perf_counter()-t,'exit_code':result.returncode,'log':log})
 if result.returncode:break
report['wall_seconds']=time.perf_counter()-start
report['execution_completed']=len(report['commands'])==2 and all(x['exit_code']==0 for x in report['commands'])
if report['execution_completed']:
 v=json.loads((OUT/'validation.json').read_text());report['package_acceptance_passed']=v['all_checks_passed'];report['failed_checks']=v['failed_count']
report['scope']='Command exit=0 means every check was recorded, not that all numerical checks passed. Failed original interfaces remain in validation.json.'
(OUT/'run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['execution_completed']
