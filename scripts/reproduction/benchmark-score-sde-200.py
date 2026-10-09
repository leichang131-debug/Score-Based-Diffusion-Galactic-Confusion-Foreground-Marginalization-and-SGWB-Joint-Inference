"""Time unmodified original training, continuing update 22 through update 200.

External instrumentation synchronizes pmap outputs to measure completed calls.
Checkpoint names use actual state.step to avoid a final-save index collision.
No model, loss, optimizer or upstream source edits are made.
"""
import os
import sys
import json
import math
import time
import re
import logging
import shutil
import resource
import importlib.util
import statistics
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/score-sde/original-200-updates'
SOURCE=ROOT/'runs/score-sde/resume-check/checkpoints-meta'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'checkpoints-meta').exists(),'Preserve/rename an existing run before repeating this experiment.'
os.environ['JAX_PLATFORMS']='cpu'
os.environ['TFDS_DATA_DIR']=str(ROOT/'data/raw/tensorflow_datasets')
os.environ['MPLCONFIGDIR']=str(OUT/'matplotlib')
sys.path.insert(0,str(ROOT/'external/score-sde-reproduction'))
from score_sde_bootstrap import prepare
prepare()
import run_train
import jax
import numpy as np
from flax import serialization
from flax.training import checkpoints
from tensorflow_datasets.core.utils import gcs_utils
gcs_utils._is_gcs_disabled=True
spec=importlib.util.spec_from_file_location('benchmark_config',ROOT/'configs/local/score-sde/cifar10-original-200-updates.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
config=module.get_config()
shutil.copytree(SOURCE,OUT/'checkpoints-meta')
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',force=True)
started=time.perf_counter()
report={'status':'running','date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'pid':os.getpid(),
        'start_update':22,'target_update':200,'configuration':config.to_dict(),
        'source':'runs/score-sde/resume-check/checkpoints-meta',
        'timing_method':'Wall-clock pmap call with all outputs blocked until ready; training excludes input fetching, validation, checkpoint saving and logging.',
        'cycle_timing_method':'Time between successive training log records; includes intervening validation, checkpoint and input/host overhead.',
        'periodic_schedule_note':'Unmodified loop triggers at zero-based labels: validation at actual updates 41,61,...,181; periodic checkpoints at 51,101,151. Final state 200 is saved to both checkpoint directories.'}
records=[];calls=[];saves=[];factories=0
last_state=None

def write_progress():
    (OUT/'progress.json').write_text(json.dumps({'status':report['status'],'elapsed_seconds':time.perf_counter()-started,
        'last_update':records[-1]['actual_update'] if records else 22,'records':records[-5:],
        'training_calls_completed':sum(c['kind']=='train' for c in calls)},indent=2)+'\n')

def state_description(state):
    d=serialization.to_state_dict(state)
    hashes={}
    def digest(x):
        h=hashlib.sha256()
        def visit(v):
            if isinstance(v,dict):
                for k in sorted(v):h.update(str(k).encode());visit(v[k])
            else:
                a=np.asarray(v);assert np.isfinite(a).all()
                h.update(str(a.shape).encode());h.update(str(a.dtype).encode());h.update(a.tobytes())
        visit(x);return h.hexdigest()
    for k,v in d.items():hashes[k]=digest(v)
    counts=[]
    def scan(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k=='count':counts.append(int(v))
                else:scan(v)
    scan(d['optimizer']['state'])
    return {'state_step':int(state.step),'adam_counts':counts,'field_sha256':hashes,'all_state_values_finite':True}

original_restore=checkpoints.restore_checkpoint
original_save=checkpoints.save_checkpoint
original_pmap=jax.pmap

def measured_restore(path,target,*args,**kwargs):
    state=original_restore(path,target,*args,**kwargs)
    desc=state_description(state)
    expected=json.loads((ROOT/'docs/reproduction/score-sde/resume-validation.json').read_text())['preemption_restart']
    assert desc['state_step']==22 and desc['adam_counts']==[22]
    assert desc['field_sha256']==expected['field_sha256']
    report['restored_state']=desc
    print('RESTORE VERIFIED: update 22; full typed state matches verified source',flush=True)
    return state

def measured_save(path,state,*args,**kwargs):
    global last_state
    # Original calls supply step by keyword. Preserve retention behavior.
    actual=int(state.step)
    kwargs['step']=actual
    before=time.perf_counter()
    result=original_save(path,state,*args,**kwargs)
    saves.append({'directory':Path(path).name,'actual_update':actual,'seconds':time.perf_counter()-before})
    last_state=state
    return result

def measured_pmap(*args,**kwargs):
    global factories
    kind=['train','eval'][factories]
    factories+=1
    compiled=original_pmap(*args,**kwargs)
    def invoke(*call_args,**call_kwargs):
        before=time.perf_counter()
        output=compiled(*call_args,**call_kwargs)
        jax.block_until_ready(output)
        elapsed=time.perf_counter()-before
        update=int(np.asarray(output[0][1].step).flat[0])
        loss=float(np.asarray(output[1]).mean());assert math.isfinite(loss)
        calls.append({'kind':kind,'actual_update':update,'seconds':elapsed,'loss':loss,
                      'elapsed_seconds':time.perf_counter()-started})
        return output
    return invoke

class Recorder(logging.Handler):
    def emit(self,record):
        match=re.search(r'step: (\d+), (training_loss|eval_loss): (\S+)',record.getMessage())
        if match:
            value=float(match[3]);assert math.isfinite(value)
            records.append({'loop_step':int(match[1]),'actual_update':int(match[1])+1,
                'kind':match[2],'loss':value,'elapsed_seconds':time.perf_counter()-started})
            write_progress()
logging.getLogger().addHandler(Recorder())
checkpoints.restore_checkpoint=measured_restore
checkpoints.save_checkpoint=measured_save
jax.pmap=measured_pmap
try:
    run_train.run_lib.train(config,str(OUT))
    train=[x for x in calls if x['kind']=='train'];evaluate=[x for x in calls if x['kind']=='eval']
    assert factories==2 and [x['actual_update'] for x in train]==list(range(23,201))
    assert [x['actual_update'] for x in evaluate]==list(range(41,182,20))
    desc=state_description(last_state)
    assert desc['state_step']==200 and desc['adam_counts']==[200]
    # Ensure automatic continuation starts at the final update, not at 151.
    measured_save(str(OUT/'checkpoints-meta'),last_state,step=200,keep=1)
    report.update(status='trained_pending_checkpoint_readback',additional_updates=178,actual_updates=200,
                  final_saved_state=desc,validation_batches=len(evaluate))
except BaseException as exc:
    report.update(status='failed',error=repr(exc));raise
finally:
    report.update(calls=calls,loss_records=records,checkpoint_saves=saves,
                  training_invocation_seconds=time.perf_counter()-started,
                  peak_process_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**3)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    write_progress()
