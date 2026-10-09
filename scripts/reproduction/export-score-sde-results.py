"""Publish portable local evidence and regenerate plots from committed events.

--publish-local-evidence copies the three completed TensorBoard streams byte
for byte and publishes path-normalized text logs with original/normalized hashes.
Default plotting needs only the published event files and unchanged teacher
plot_loss.extract_losses, not datasets or checkpoints. No training or sampling.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/score-sde/final-summary'
os.environ['MPLCONFIGDIR']=str(ROOT/'runs/score-sde/matplotlib')
parser=argparse.ArgumentParser();parser.add_argument('--publish-local-evidence',action='store_true');args=parser.parse_args()
OUT.mkdir(parents=True,exist_ok=True)
STAGES=[('original-20-updates','original-20-updates-validation.json'),('resume-check','resume-validation.json'),
        ('original-200-updates','original-200-updates-validation.json')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if args.publish_local_evidence:
    index={'normalization':'Text logs replace repository/workspace/home paths and hostname; original local logs are unchanged. TensorBoard files are byte-identical copies with portable names.',
           'text_logs':[],'tensorboard_files':[]}
    for name,_ in STAGES:
        events=sorted((ROOT/'runs/score-sde'/name/'tensorboard').glob('events.out.tfevents.*'))
        assert len(events)==1
        src=events[0];dst=OUT/'evidence'/name/'tensorboard'/'events.out.tfevents.published'
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        assert sha(src)==sha(dst)
        index['tensorboard_files'].append({'stage':name,'original_path':str(src.relative_to(ROOT)),
            'published_path':str(dst.relative_to(ROOT)),'bytes':dst.stat().st_size,'sha256':sha(dst),'byte_identical':True})
    logs=sorted((ROOT/'runs/score-sde').glob('*.log'))
    logs += [ROOT/'runs/score-sde/resume-check-attempt-1.log',ROOT/'runs/score-sde/resume-check-attempt-2.log']
    # Failed-attempt reports exist, but their original console files were overwritten;
    # extract documented exception evidence from history separately, without inventing logs.
    for src in logs:
        if not src.exists():continue
        text=src.read_text()
        substitutions=[(str(ROOT),'<REPOSITORY_ROOT>'),(str(ROOT.parent),'<WORKSPACE_ROOT>'),
                       (str(Path.home()),'<USER_HOME>'),(platform.node(),'<HOST>'),('leideMacBook-Air.local','<HOST>')]
        for old,new in substitutions:
            if old:text=text.replace(old,new)
        dst=OUT/'logs'/(src.stem+'.txt');dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(text)
        index['text_logs'].append({'original_path':str(src.relative_to(ROOT)),'published_path':str(dst.relative_to(ROOT)),
            'original_sha256':sha(src),'normalized_sha256':sha(dst),'original_bytes':src.stat().st_size,
            'normalized_bytes':dst.stat().st_size})
    (OUT/'evidence-index.json').write_text(json.dumps(index,indent=2)+'\n')
index=json.loads((OUT/'evidence-index.json').read_text())
for item in index['tensorboard_files']:assert sha(ROOT/item['published_path'])==item['sha256']
for item in index['text_logs']:assert sha(ROOT/item['published_path'])==item['normalized_sha256']
spec=importlib.util.spec_from_file_location('teacher_plot',ROOT/'external/score-sde-reproduction/plot_loss.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=[];train=[];evaluate=[]
for name,report in STAGES:
    t,e=module.extract_losses(str(OUT/'evidence'/name))
    published=json.loads((ROOT/'docs/reproduction/score-sde'/report).read_text())
    for kind,values in [('training_loss',t),('eval_loss',e)]:
        expected=[r for r in published['loss_records'] if r['kind']==kind]
        assert [s for s,v in values]==[r['loop_step'] for r in expected]
        assert all(abs(v-r['loss'])<.000006 for (s,v),r in zip(values,expected))
        for step,value in values:
            assert np.isfinite(value) and value>0
            rows.append({'stage':name,'kind':kind,'loop_step':step,'actual_update':step+1,'loss':value})
    train+=t;evaluate+=e
assert [s for s,v in train]==list(range(200)) and len(evaluate)==14
train_steps=np.array([s for s,v in train],dtype=np.int64);train_values=np.array([v for s,v in train])
eval_steps=np.array([s for s,v in evaluate],dtype=np.int64);eval_values=np.array([v for s,v in evaluate])
# Preserve the teacher's four NPZ field names and zero-based loop labels.
np.savez(OUT/'loss_history.npz',train_steps=train_steps,train_losses=train_values,eval_steps=eval_steps,eval_losses=eval_values)
with (OUT/'loss_history.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['stage','kind','loop_step','actual_update','loss'],lineterminator='\n')
    w.writeheader();w.writerows(sorted(rows,key=lambda x:(x['actual_update'],x['kind'])))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.labelsize':10})
x=train_steps+1;ex=eval_steps+1
smooth=np.convolve(train_values,np.ones(20)/20,mode='valid');sx=x[19:]
def panel(ax,late=False):
    lo=100 if late else 1
    mask=x>=lo;em=ex>=lo;sm=sx>=lo
    ax.plot(x[mask],train_values[mask],color='#3069b4',alpha=.35,lw=.8,label='Train (raw, current params)')
    ax.plot(sx[sm],smooth[sm],color='#164b94',lw=1.8,label='Train (MA-20 records)')
    ax.plot(ex[em],eval_values[em],'o--',color='#b33d32',ms=4,lw=1,label='Eval (EMA, batch 1)')
    ax.set(xlabel='Completed optimizer updates',ylabel='Loss (log scale)',yscale='log',xlim=(lo,201),
           title='Later warmup: updates 100–200 (log scale)' if late else 'Full run: updates 1–200 (log scale)')
    if not late:
        for pos in [20.5,22.5]:ax.axvline(pos,color='#777777',lw=.7,ls=':')
    ax.grid(alpha=.2,which='both');ax.legend(fontsize=8,loc='lower left')
fig,axes=plt.subplots(1,2,figsize=(12,4.2),layout='constrained')
for ax,late in zip(axes,[False,True]):panel(ax,late)
fig.suptitle('Original VP-SDE / DDPM++: batch 1, 200 updates\nMA-20 covers 20 updates; restarts after updates 20 and 22. No convergence claim.',fontsize=11)
fig.savefig(OUT/'loss_curve.png',dpi=180);plt.close(fig)
for late,name in [(False,'loss-full.png'),(True,'loss-late.png')]:
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained');panel(ax,late)
    fig.savefig(OUT/name,dpi=180);plt.close(fig)
summary={'status':'passed','training_entries':200,'validation_entries':14,
    'step_semantics':'NPZ *_steps are original zero-based loop labels; plots/CSV actual_update = loop_step + 1.',
    'smoothing':'Trailing mean over 20 training records computed on the full sequence; no validation smoothing.',
    'min_train_loss':float(train_values.min()),'min_train_actual_update':int(x[train_values.argmin()]),
    'min_eval_loss':float(eval_values.min()),'min_eval_actual_update':int(ex[eval_values.argmin()]),
    'final_train_loss':float(train_values[-1]),'final_train_actual_update':200,
    'last_eval_loss':float(eval_values[-1]),'last_eval_actual_update':int(ex[-1]),
    'same_update_final_ratio':'not available; final train and last eval are at different updates',
    'interpretation':'Small-scale functionality reproduction only; still within 5000-update warmup; no overfitting/convergence assessment or standard image metrics.',
    'original_teacher_extraction_function':'external/score-sde-reproduction/plot_loss.py:extract_losses',
    'published_tensorboard_readback':'step/value comparison to all three stage reports passed',
    'parameter_semantics':'Training uses current optimizer parameters with train=True; evaluation and sampling use params_ema with train=False. The curves are not losses from the same parameter set.',
    'teacher_plot_difference':'Uses our actual 1–200 and 100–200 ranges; does not run the teacher 5k+ panel or heuristic overfitting classifier.'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# Verify the portable binary export itself before delivery.
with np.load(OUT/'loss_history.npz',allow_pickle=False) as z:
    assert set(z.files)=={'train_steps','train_losses','eval_steps','eval_losses'}
    np.testing.assert_array_equal(z['train_steps'],train_steps)
    np.testing.assert_array_equal(z['train_losses'],train_values)
    np.testing.assert_array_equal(z['eval_steps'],eval_steps)
    np.testing.assert_array_equal(z['eval_losses'],eval_values)
print(json.dumps(summary,indent=2))
