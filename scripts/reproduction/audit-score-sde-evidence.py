"""Use the unmodified teacher loss reader to cross-check local stage records."""
import os,sys,json,importlib.util,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
os.environ['MPLCONFIGDIR']=str(R/'runs/score-sde/matplotlib')
spec=importlib.util.spec_from_file_location('teacher_plot',R/'external/score-sde-reproduction/plot_loss.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
alltrain=[];alleval=[];result={}
for run,report in [('original-20-updates','original-20-updates-validation.json'),('resume-check','resume-validation.json'),('original-200-updates','original-200-updates-validation.json')]:
    t,e=m.extract_losses(str(R/'runs/score-sde'/run))
    doc=json.loads((R/'docs/reproduction/score-sde'/report).read_text())
    records=doc['loss_records']
    want_t=[x for x in records if x['kind']=='training_loss']
    want_e=[x for x in records if x['kind']=='eval_loss']
    assert [s for s,v in t]==[x['loop_step'] for x in want_t]
    assert [s for s,v in e]==[x['loop_step'] for x in want_e]
    errors=[abs(v-x['loss']) for (_,v),x in zip(t+e,want_t+want_e)]
    assert max(errors)<0.000006
    result[run]={'tensorboard_training_entries':len(t),'tensorboard_eval_entries':len(e),'training_loop_range':[t[0][0],t[-1][0]],'max_json_loss_rounding_difference':max(errors)}
    alltrain+=t;alleval+=e
assert [s for s,v in alltrain]==list(range(200))
a=np.load(R/'external/score-sde-reproduction/exp/vp_cifar10_ncsnpp/loss_history.npz')
result['teacher_npz']={'keys':a.files,'train_entries':len(a['train_steps']),'eval_entries':len(a['eval_steps']),
    'last_logged_train_step':int(a['train_steps'][-1]),'first_train_log_intervals':np.diff(a['train_steps'][:10]).tolist(),
    'min_train_loss':float(a['train_losses'].min()),'min_eval_loss':float(a['eval_losses'].min())}
result['combined_local']={'training_entries':len(alltrain),'eval_entries':len(alleval),'loop_step_range':[0,199],
    'actual_update_range':[1,200],'final_train_loss':alltrain[-1][1], 'last_eval_actual_update':alleval[-1][0]+1,
    'minimum_train':min(alltrain,key=lambda x:x[1]),'minimum_eval':min(alleval,key=lambda x:x[1])}
# Compare each project configuration to the teacher's original reference.
sys.path.insert(0,str(R/'external/score-sde-reproduction'))
from score_sde_bootstrap import prepare
prepare()
import run_train
reference=R/'external/score-sde-reproduction/score_sde/configs/vp/cifar10_ddpmpp_continuous.py'
def load_config(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.get_config().to_dict()
def flatten(d,prefix=''):
    flat={}
    for k,v in d.items():
        name=prefix+k
        if isinstance(v,dict):flat.update(flatten(v,name+'.'))
        else:flat[name]=v
    return flat
baseline=flatten(load_config(reference,'audit_reference'))
allowed={'training.batch_size','eval.batch_size','training.n_jitted_steps','training.n_iters',
    'training.log_freq','training.eval_freq','training.snapshot_freq','training.snapshot_freq_for_preemption',
    'training.snapshot_sampling'}
result['configuration_alignment']={}
for filename in ['cifar10-original-20-updates.py','cifar10-resume-check.py','cifar10-original-200-updates.py']:
    actual=flatten(load_config(R/'configs/local/score-sde'/filename,'audit_'+filename.replace('-','_').replace('.','_')))
    assert actual.keys()==baseline.keys()
    diff={k:{'reference':baseline[k],'local':actual[k]} for k in baseline if baseline[k]!=actual[k]}
    assert set(diff)<=allowed
    result['configuration_alignment'][filename]={'only_allowlisted_execution_overrides':True,
        'network_loss_optimizer_warmup_ema_and_sampler_preserved':True,'overrides':diff}
# Verify the already-published checkpoint and sample artifact checksums.
result['artifact_integrity']={}
for filename,key in [('original-200-updates-validation.json','final_artifact_files'),('sampling-validation.json','artifact_files')]:
    document=json.loads((R/'docs/reproduction/score-sde'/filename).read_text())
    matched=0
    for item in document[key]:
        path=R/item['path'];assert path.stat().st_size==item['bytes']
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        assert h.hexdigest()==item['sha256'];matched+=1
    result['artifact_integrity'][filename]={'matched_files':matched,'missing_or_modified':0}
canonical=R/'docs/reproduction/score-sde/sampling-validation.json'
mirror=R/'results/score-sde/original-200-sampling/summary.json'
assert canonical.read_bytes()==mirror.read_bytes()
result['duplicated_report']={'canonical':str(canonical.relative_to(R)),'mirror':str(mirror.relative_to(R)),'currently_identical':True}
result['status']='passed'
result['method']='Unmodified upstream plot_loss.extract_losses; TensorBoard step/value cross-check against each published stage JSON. Console-formatted JSON values may be rounded.'
result['log_files']=[]
for name in ['original-20-updates.log','resume-check.log','resume-second-restart.log','original-200-updates.log','original-200-analysis.log','original-200-sampling.log']:
    p=R/'runs/score-sde'/name
    raw=p.read_bytes()
    result['log_files'].append({'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
result['tensorboard_files']=[]
for run in ['original-20-updates','resume-check','original-200-updates']:
    for p in sorted((R/'runs/score-sde'/run/'tensorboard').glob('events.out.tfevents.*')):
        raw=p.read_bytes()
        result['tensorboard_files'].append({'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(R/'docs/reproduction/score-sde/evidence-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
