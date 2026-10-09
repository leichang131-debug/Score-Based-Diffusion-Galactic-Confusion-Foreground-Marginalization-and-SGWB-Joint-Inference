"""Four batch-one original EMA samples from update 200; no training updates."""
import os
import sys
import json
import time
import hashlib
import math
import importlib.util
import resource
import logging
import statistics
import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/score-sde/original-200-sampling'
RESULTS=ROOT/'results/score-sde/original-200-sampling'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'report.json').exists(),'Preserve/rename existing sampling output before repeating.'
os.environ['JAX_PLATFORMS']='cpu'
os.environ['MPLCONFIGDIR']=str(OUT/'matplotlib')
sys.path.insert(0,str(ROOT/'external/score-sde-reproduction'))
from score_sde_bootstrap import prepare
prepare()
import run_train
import jax
import numpy as np
import flax
from flax import serialization
from flax.training import checkpoints
from models import utils as mutils
import losses
import sampling
import sde_lib
import datasets
from PIL import Image
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',force=True)
spec=importlib.util.spec_from_file_location('sampling_config',ROOT/'configs/local/score-sde/cifar10-original-200-updates.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
config=module.get_config()
started=time.perf_counter()
report={'status':'running','date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'pid':os.getpid(),
    'purpose':'Original EMA sampling functionality and preliminary warm-call timing; not sample-quality or convergence validation',
    'configuration':config.to_dict(),'checkpoint':'runs/score-sde/original-200-updates/checkpoints/checkpoint_200',
    'seeds':[1001,1002,1003,1004],'batch_size':1,'reverse_iterations':1000,
    'sampler':'pc / Euler-Maruyama predictor / no corrector / noise_removal=True',
    'timing_method':'Full sampler pmap invocation with all outputs blocked until ready; excludes NPY/PNG encoding and saving',
    'counter_note':'Upstream reports N*(n_steps_each+1)=2000 even for a no-op corrector. Actual score evaluations are 1000: one predictor per reverse iteration, zero corrector evaluations. Noise removal returns the final predictor mean, without an extra model call.',
    'records':[]}

def digest(x):
    h=hashlib.sha256()
    def visit(v):
        if isinstance(v,dict):
            for k in sorted(v):h.update(str(k).encode());visit(v[k])
        else:
            a=np.asarray(v);assert np.isfinite(a).all()
            h.update(str(a.shape).encode());h.update(str(a.dtype).encode());h.update(a.tobytes())
    visit(x);return h.hexdigest()

def state_hashes(state):
    return {k:digest(v) for k,v in serialization.to_state_dict(state).items()}

def write_report():
    report['elapsed_seconds']=time.perf_counter()-started
    report['peak_process_rss_gib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**3
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')

try:
    rng,model_rng=jax.random.split(jax.random.PRNGKey(config.seed))
    model,model_state,params=mutils.init_model(model_rng,config)
    template=mutils.State(step=0,optimizer=losses.get_optimizer(config).create(params),lr=config.optim.lr,
        model_state=model_state,ema_rate=config.model.ema_rate,params_ema=params,rng=rng)
    state=checkpoints.restore_checkpoint(str(ROOT/report['checkpoint']),template)
    expected=json.loads((ROOT/'docs/reproduction/score-sde/original-200-updates-validation.json').read_text())['final_saved_state']['field_sha256']
    assert int(state.step)==200 and state_hashes(state)==expected
    report['initial_state_hashes']=expected
    print('RESTORE VERIFIED: complete typed update-200 state; sampler uses params_ema',flush=True)
    del template,params,model_state
    sde=sde_lib.VPSDE(beta_min=config.model.beta_min,beta_max=config.model.beta_max,N=config.model.num_scales)
    assert sde.N==1000 and config.sampling.predictor=='euler_maruyama' and config.sampling.corrector=='none'
    sampler=sampling.get_sampling_fn(config,sde,model,(1,32,32,3),datasets.get_data_inverse_scaler(config),1e-3)
    pstate=flax.jax_utils.replicate(state)
    previews=[]
    for index,seed in enumerate(report['seeds']):
        print(f'SAMPLE START: index={index+1}, seed={seed}',flush=True)
        keys=jax.random.split(jax.random.PRNGKey(seed),jax.local_device_count())
        before=time.perf_counter()
        samples,reported_nfe=sampler(keys,pstate)
        jax.block_until_ready((samples,reported_nfe))
        seconds=time.perf_counter()-before
        raw=np.asarray(samples)
        assert raw.shape==(1,1,32,32,3) and raw.dtype==np.float32 and np.isfinite(raw).all()
        assert int(np.asarray(reported_nfe).flat[0])==2000
        name=f'sample-{index+1:02d}-seed-{seed}'
        np.save(OUT/f'{name}.npy',raw)
        image=(np.clip(raw[0,0],0,1)*255).astype(np.uint8)
        Image.fromarray(image).save(OUT/f'{name}.png')
        with Image.open(OUT/f'{name}.png') as saved:
            assert saved.mode=='RGB' and saved.size==(32,32)
        previews.append(image)
        record={'index':index+1,'seed':seed,'seconds':seconds,'includes_first_call_compilation':index==0,
            'shape':list(raw.shape),'dtype':str(raw.dtype),'all_finite':True,
            'raw_inverse_scaled_min':float(raw.min()),'raw_inverse_scaled_max':float(raw.max()),
            'raw_mean':float(raw.mean()),'raw_std':float(raw.std()),
            'below_zero_fraction':float(np.mean(raw<0)),'above_one_fraction':float(np.mean(raw>1)),
            'display_clipping_fraction':float(np.mean((raw<0)|(raw>1))),
            'upstream_reported_counter':2000,'actual_score_evaluations':1000,
            'raw_file':str((OUT/f'{name}.npy').relative_to(ROOT)),
            'png_file':str((OUT/f'{name}.png').relative_to(ROOT)),
            'cumulative_peak_process_rss_gib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**3}
        report['records'].append(record);write_report()
        print('SAMPLE DONE: '+json.dumps(record),flush=True)
    assert state_hashes(flax.jax_utils.unreplicate(pstate))==expected
    report['state_unchanged']=True;report['actual_updates_after_sampling']=200
    warm=[x['seconds'] for x in report['records'][1:]]
    report['warm_sampling_timing']={'count':3,'mean_seconds':statistics.mean(warm),'median_seconds':statistics.median(warm),
        'min_seconds':min(warm),'max_seconds':max(warm),
        'note':'Three full warm calls provide a preliminary estimate, not a sustained-speed benchmark or a precise tail distribution.'}
    report['status']='passed'
    write_report()
    RESULTS.mkdir(parents=True,exist_ok=True)
    # Raw arrays are only 12 KiB per image and useful for checking clipping.
    for p in OUT.glob('sample-*'):
        if p.suffix in ['.npy','.png']:shutil.copy2(p,RESULTS/p.name)
    sheet=Image.new('RGB',(64,64))
    for i,image in enumerate(previews):sheet.paste(Image.fromarray(image),((i%2)*32,(i//2)*32))
    sheet.save(RESULTS/'contact-sheet.png')
    report['artifact_files']=[]
    for p in sorted(RESULTS.glob('*')):
        report['artifact_files'].append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    write_report()
    (RESULTS/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
except BaseException as exc:
    report.update(status='failed',error=repr(exc));write_report();raise
