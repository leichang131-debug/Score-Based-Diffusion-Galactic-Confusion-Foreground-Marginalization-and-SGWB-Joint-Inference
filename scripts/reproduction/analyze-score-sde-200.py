"""Fresh-process checkpoint readback and short-run CPU timing analysis."""
import os
import sys
import json
import importlib.util
import statistics
import hashlib
import platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/score-sde/original-200-updates'
os.environ['JAX_PLATFORMS']='cpu'
os.environ['MPLCONFIGDIR']=str(OUT/'matplotlib')
sys.path.insert(0,str(ROOT/'external/score-sde-reproduction'))
from score_sde_bootstrap import prepare
prepare()
import run_train
import jax
import numpy as np
from flax import serialization
from flax.training import checkpoints
from models import utils as mutils
import losses
spec=importlib.util.spec_from_file_location('benchmark_config',ROOT/'configs/local/score-sde/cifar10-original-200-updates.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
config=module.get_config()
r=json.loads((OUT/'report.json').read_text())
assert r['status']=='trained_pending_checkpoint_readback'
rng,model_rng=jax.random.split(jax.random.PRNGKey(config.seed))
_,model_state,params=mutils.init_model(model_rng,config)
template=mutils.State(step=0,optimizer=losses.get_optimizer(config).create(params),lr=config.optim.lr,
    model_state=model_state,ema_rate=config.model.ema_rate,params_ema=params,rng=rng)

def digest(tree):
    h=hashlib.sha256()
    def visit(v):
        if isinstance(v,dict):
            for k in sorted(v):h.update(str(k).encode());visit(v[k])
        else:
            a=np.asarray(v);assert np.isfinite(a).all()
            h.update(str(a.shape).encode());h.update(str(a.dtype).encode());h.update(a.tobytes())
    visit(tree);return h.hexdigest()

r['checkpoint_readback']={}
for folder in ['checkpoints','checkpoints-meta']:
    restored=checkpoints.restore_checkpoint(str(OUT/folder),template)
    d=serialization.to_state_dict(restored)
    assert int(restored.step)==200
    hashes={k:digest(v) for k,v in d.items()}
    assert hashes==r['final_saved_state']['field_sha256']
    r['checkpoint_readback'][folder]={'state_step':200,'all_fields_match_saved_state':True,'all_state_values_finite':True}
    del restored,d

def stats(values):
    a=np.asarray(values,dtype=float)
    return {'count':len(a),'mean_seconds':float(a.mean()),'median_seconds':float(np.median(a)),
        'p10_seconds':float(np.quantile(a,.1)),'p90_seconds':float(np.quantile(a,.9)),
        'min_seconds':float(a.min()),'max_seconds':float(a.max())}
train=[x for x in r['calls'] if x['kind']=='train']
evaluate=[x for x in r['calls'] if x['kind']=='eval']
# First five training calls excluded conservatively for compile/warm-up effects.
steady=train[5:]
windows={}
for lo,hi in [(50,99),(100,149),(150,200)]:
    windows[f'{lo}-{hi}']=stats([x['seconds'] for x in train if lo<=x['actual_update']<=hi])
logs=[x for x in r['loss_records'] if x['kind']=='training_loss']
cycles=[b['elapsed_seconds']-a['elapsed_seconds'] for a,b in zip(logs,logs[1:])]
r['speed_analysis']={'first_training_call_seconds':train[0]['seconds'],
    'first_validation_call_seconds':evaluate[0]['seconds'],
    'steady_training_excluding_first_five_calls':stats([x['seconds'] for x in steady]),
    'last_100_training_updates':stats([x['seconds'] for x in train if x['actual_update']>=101]),
    'training_windows':windows,'training_log_intervals_including_other_work':stats(cycles),
    'validation_after_first_call':stats([x['seconds'] for x in evaluate[1:]]),
    'sum_training_call_seconds':sum(x['seconds'] for x in train),
    'sum_validation_call_seconds':sum(x['seconds'] for x in evaluate),
    'sum_checkpoint_call_seconds':sum(x['seconds'] for x in r['checkpoint_saves']),
    'last_window_to_first_window_median_ratio':windows['150-200']['median_seconds']/windows['50-99']['median_seconds'],
    'interpretation':'A single short CPU run with explicit output synchronization. A timing trend cannot by itself establish thermal throttling; no temperature or clock telemetry was collected.'}
r['loss_summary']={'train_min':min(x['loss'] for x in train),'train_max':max(x['loss'] for x in train),
    'train_final':train[-1]['loss'],'eval_min':min(x['loss'] for x in evaluate),'eval_max':max(x['loss'] for x in evaluate),
    'all_finite':True,'note':'Batch-one noisy losses and 5000-update warmup; no convergence or image-quality claim.'}
r['verification_process_pid']=os.getpid();assert os.getpid()!=r['pid']
r['platform']=platform.platform();r['status']='passed'
base=json.loads((ROOT/'docs/reproduction/score-sde/original-20-updates-validation.json').read_text())
r['source_commits']={k:base[k] for k in ['upstream_commit','original_commit']}
(OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n')
progress=json.loads((OUT/'progress.json').read_text())
progress.update(status='passed',last_update=200)
(OUT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
# Small, shareable scientific records; raw checkpoints remain local.
import csv
results=ROOT/'results/score-sde/original-200-updates'
results.mkdir(parents=True,exist_ok=True)
with (results/'timings.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['kind','actual_update','seconds','loss','elapsed_seconds'],lineterminator='\n')
    writer.writeheader();writer.writerows(r['calls'])
summary={k:r[k] for k in ['status','start_update','actual_updates','additional_updates','validation_batches',
    'speed_analysis','loss_summary','peak_process_rss_gib','training_invocation_seconds','checkpoint_readback']}
(results/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
x=[c['actual_update'] for c in steady];y=[c['seconds'] for c in steady]
rolling=[statistics.median(y[max(0,i-9):i+1]) for i in range(len(y))]
fig,ax=plt.subplots(figsize=(8,3.5),layout='constrained')
ax.scatter(x,y,s=9,alpha=.5,label='Synchronized training calls')
ax.plot(x,rolling,color='#b34a21',linewidth=1.8,label='Trailing 10-call median')
ax.set(xlabel='Cumulative optimizer updates',ylabel='Seconds per training call',
       title='Original Score-SDE: batch 1, macOS CPU')
ax.text(.01,.98,'First five calls excluded; validation and saving timed separately',
        transform=ax.transAxes,va='top',fontsize=8)
ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=8)
fig.savefig(results/'training-speed.png',dpi=180)
plt.close(fig)
print(json.dumps({k:r[k] for k in ['status','actual_updates','speed_analysis','loss_summary','peak_process_rss_gib','training_invocation_seconds','checkpoint_readback']},indent=2),flush=True)
