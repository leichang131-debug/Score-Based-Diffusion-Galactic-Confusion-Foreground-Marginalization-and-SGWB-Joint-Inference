"""Fresh-process typed restore and two original upstream updates, then restart QA.

Run without arguments to resume; run with --verify to load the final state in
another interpreter. Upstream sources are not edited. Checkpoint interception
only records equality diagnostics around the original restore/save calls.
"""
import os
import sys
import json
import math
import re
import hashlib
import logging
import shutil
import importlib.util
import time
import resource
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'runs/score-sde/original-20-updates/checkpoints-meta'
OUT = ROOT/'runs/score-sde/resume-check'
VERIFY = '--verify' in sys.argv
OUT.mkdir(parents=True, exist_ok=True)
os.environ['JAX_PLATFORMS'] = 'cpu'
os.environ['TFDS_DATA_DIR'] = str(ROOT/'data/raw/tensorflow_datasets')
os.environ['MPLCONFIGDIR'] = str(OUT/'matplotlib')
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
from tensorflow_datasets.core.utils import gcs_utils
gcs_utils._is_gcs_disabled = True
spec=importlib.util.spec_from_file_location('resume_config',ROOT/'configs/local/score-sde/cifar10-resume-check.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config=module.get_config()
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',force=True)

def digest(tree):
    h=hashlib.sha256()
    def visit(x):
        if isinstance(x,dict):
            for key in sorted(x):
                h.update(str(key).encode());visit(x[key])
        else:
            a=np.asarray(x)
            assert np.isfinite(a).all()
            h.update(str(a.shape).encode());h.update(str(a.dtype).encode());h.update(a.tobytes())
    visit(tree)
    return h.hexdigest()

def describe(raw):
    counts=[]
    def scan(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k=='count':counts.append(int(v))
                else:scan(v)
    scan(raw['optimizer']['state'])
    return {'state_step':int(raw['step']), 'adam_counts':counts,
            'field_sha256':{k:digest(v) for k,v in raw.items()},
            'optimizer_parameter_sha256':digest(raw['optimizer']['target']),
            'adam_state_sha256':digest(raw['optimizer']['state']),
            'ema_sha256':digest(raw['params_ema']), 'all_state_values_finite':True}

if VERIFY:
    report=json.loads((OUT/'report.json').read_text())
    rng,model_rng=jax.random.split(jax.random.PRNGKey(config.seed))
    _,model_state,params=mutils.init_model(model_rng,config)
    template=mutils.State(step=0,optimizer=losses.get_optimizer(config).create(params),lr=config.optim.lr,
                         model_state=model_state,ema_rate=config.model.ema_rate,params_ema=params,rng=rng)
    restored=checkpoints.restore_checkpoint(str(OUT/'checkpoints'),template)
    desc=describe(serialization.to_state_dict(restored))
    if desc!=report['last_saved_state']:
        print(json.dumps({'restored':desc,'saved':report['last_saved_state']},indent=2),flush=True)
    assert desc==report['last_saved_state']
    assert desc['state_step']==22 and desc['adam_counts']==[22]
    report['second_restart']={'pid':os.getpid(),'directory':'checkpoints','typed_restore_exactly_equals_saved_state':True,**desc}
    meta=checkpoints.restore_checkpoint(str(OUT/'checkpoints-meta'),template)
    meta_desc=describe(serialization.to_state_dict(meta))
    for key,value in desc['field_sha256'].items():
        if key!='rng': assert meta_desc['field_sha256'][key]==value
    assert meta_desc['state_step']==22 and meta_desc['adam_counts']==[22]
    report['preemption_restart']={'directory':'checkpoints-meta','parameters_optimizer_ema_match_final':True,
        'rng_note':'Upstream saves preemption state before validation and final state after validation; RNG keys may differ legitimately.',**meta_desc}
    report['status']='passed'
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['second_restart'],indent=2),flush=True)
    sys.exit(0)

assert not (OUT/'checkpoints-meta').exists(),'Use a fresh resume-check work directory.'
shutil.copytree(SOURCE,OUT/'checkpoints-meta')
original_restore=checkpoints.restore_checkpoint
original_save=checkpoints.save_checkpoint
report={'status':'running','date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'pid':os.getpid(),'configuration':config.to_dict(),'source':'runs/score-sde/original-20-updates/checkpoints-meta',
        'scope':'State continuation; does not promise the same next batches as an uninterrupted TFDS iterator.'}
records=[]
started=time.perf_counter()

def recorded_restore(path,target,*args,**kwargs):
    before=describe(serialization.to_state_dict(target))
    raw=original_restore(path,None,*args,**kwargs)
    # Orbax target=None exposes custom optimizer pytree children as 0/1.
    if 'target' not in raw['optimizer']:
        raw['optimizer'] = {'target':raw['optimizer']['0'], 'state':raw['optimizer']['1']}
    # Orbax represents empty pytree containers as None; Flax serializes {}.
    def normalize_empty(x):
        if x is None: return {}
        if isinstance(x,dict): return {k:normalize_empty(v) for k,v in x.items()}
        return x
    expected=describe(normalize_empty(raw))
    del raw
    restored=original_restore(path,target,*args,**kwargs)
    actual=describe(serialization.to_state_dict(restored))
    assert actual==expected
    assert before['state_step']==0 and before['adam_counts']==[0]
    assert actual['state_step']==20 and actual['adam_counts']==[20]
    assert actual['adam_state_sha256']!=before['adam_state_sha256']
    assert actual['ema_sha256']!=before['ema_sha256']
    report['initial_restore']={'exact_match_to_checkpoint':True,'fresh_template':before,'restored':actual}
    print('RESTORE VERIFIED: state.step=20, Adam count=20; parameters, EMA, RNG and all fields exactly match checkpoint',flush=True)
    return restored

def recorded_save(path,target,*args,**kwargs):
    result=original_save(path,target,*args,**kwargs)
    report['last_saved_state']=describe(serialization.to_state_dict(target))
    return result

class Recorder(logging.Handler):
    def emit(self,record):
        match=re.search(r'step: (\d+), (training_loss|eval_loss): (\S+)',record.getMessage())
        if match:
            value=float(match[3]);assert math.isfinite(value)
            records.append({'loop_step':int(match[1]),'kind':match[2],'loss':value})
logging.getLogger().addHandler(Recorder())
checkpoints.restore_checkpoint=recorded_restore
checkpoints.save_checkpoint=recorded_save
try:
    run_train.run_lib.train(config,str(OUT))
    assert [x['loop_step'] for x in records if x['kind']=='training_loss']==[20,21]
    assert [x['loop_step'] for x in records if x['kind']=='eval_loss']==[20,21]
    final=report['last_saved_state'];initial=report['initial_restore']['restored']
    assert final['state_step']==22 and final['adam_counts']==[22]
    for key in ['optimizer_parameter_sha256','adam_state_sha256','ema_sha256']:
        assert final[key]!=initial[key]
    report.update(status='continued_pending_second_restart',additional_updates=2,loss_records=records)
except BaseException as exc:
    report.update(status='failed',error=repr(exc))
    raise
finally:
    report.update(elapsed_seconds=time.perf_counter()-started,
                  peak_process_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**3)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
