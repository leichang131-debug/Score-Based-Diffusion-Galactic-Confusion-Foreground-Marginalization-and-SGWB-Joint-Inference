"""Inspect saved smoke state without running any additional training updates."""
import os
import sys
import json
import hashlib
import statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/score-sde/original-20-updates'
os.environ['JAX_PLATFORMS'] = 'cpu'
os.environ['MPLCONFIGDIR'] = str(OUT/'matplotlib')
sys.path.insert(0, str(ROOT/'external/score-sde-reproduction'))
from score_sde_bootstrap import prepare
prepare()
import run_train
import numpy as np
import jax
from flax.training import checkpoints
report = json.loads((OUT/'report.json').read_text())
for folder in ['checkpoints','checkpoints-meta']:
    restored = checkpoints.restore_checkpoint(str(OUT/folder), target=None)
    assert int(restored['step']) == 20
    leaves = jax.tree_util.tree_leaves(restored)
    assert all(np.isfinite(np.asarray(x)).all() for x in leaves)
    report.setdefault('checkpoint_validation',{})[folder] = {
        'restored_state_step':int(restored['step']), 'all_state_leaves_finite':True,
        'tensor_leaf_count':len(leaves)}
    del restored, leaves
records = report['loss_records']
train = [r for r in records if r['kind']=='training_loss']
# Exclude intervals containing validation: these are a short smoke estimate.
intervals = [b['elapsed_seconds']-a['elapsed_seconds'] for a,b in zip(train,train[1:]) if a['loop_step'] % 5 != 0]
report['timing']={'first_training_loss_elapsed_seconds':train[0]['elapsed_seconds'],
                  'training_interval_median_seconds_excluding_validation':statistics.median(intervals),
                  'training_interval_range_seconds_excluding_validation':[min(intervals),max(intervals)],
                  'note':'Short-run timing; not the planned 200-update sustained-speed benchmark. Includes host scheduling and synchronization.'}
report['artifact_files']=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name != 'report.json':
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        report['artifact_files'].append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checkpoint_validation':report['checkpoint_validation'],'timing':report['timing']},indent=2))
