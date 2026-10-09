"""Run unmodified upstream training on real CIFAR-10; record smoke diagnostics."""
import os
import sys
import time
import json
import logging
import math
import re
import resource
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/score-sde/original-20-updates'
OUT.mkdir(parents=True, exist_ok=True)
# Refuse accidental continuation of an earlier experiment.
assert not (OUT / 'checkpoints-meta').exists(), 'Use a fresh work directory for exactly 20 updates.'
os.environ['JAX_PLATFORMS'] = 'cpu'
os.environ['TFDS_DATA_DIR'] = str(ROOT / 'data/raw/tensorflow_datasets')
os.environ['MPLCONFIGDIR'] = str(OUT / 'matplotlib')
UPSTREAM = ROOT / 'external/score-sde-reproduction'
sys.path.insert(0, str(UPSTREAM))
from score_sde_bootstrap import prepare
prepare()
import run_train
import jax
from tensorflow_datasets.core.utils import gcs_utils
gcs_utils._is_gcs_disabled = True
spec = importlib.util.spec_from_file_location('smoke_config', ROOT / 'configs/local/score-sde/cifar10-original-20-updates.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.get_config()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', force=True)
started = time.perf_counter()
records = []
class LossRecorder(logging.Handler):
    def emit(self, record):
        match = re.search(r'step: (\d+), (training_loss|eval_loss): (\S+)', record.getMessage())
        if match:
            value = float(match[3])
            assert math.isfinite(value), f'Non-finite loss: {record.getMessage()}'
            records.append({'loop_step':int(match[1]), 'kind':match[2], 'loss':value,
                            'elapsed_seconds':time.perf_counter()-started})
logging.getLogger().addHandler(LossRecorder())
report = {'status':'running','date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
          'purpose':'original-network 20-update training/evaluation smoke check; not convergence or sample-quality validation',
          'devices':[str(x) for x in jax.devices()], 'configuration':config.to_dict(),
          'upstream_commit':subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip(),
          'original_commit':subprocess.check_output(['git','-C',str(UPSTREAM/'score_sde'),'rev-parse','HEAD'],text=True).strip()}
try:
    run_train.run_lib.train(config, str(OUT))
    train = [r for r in records if r['kind']=='training_loss']
    evaluate = [r for r in records if r['kind']=='eval_loss']
    assert [r['loop_step'] for r in train] == list(range(20))
    assert [r['loop_step'] for r in evaluate] == [0,5,10,15]
    assert any((OUT/'checkpoints').iterdir())
    assert any((OUT/'checkpoints-meta').iterdir())
    report.update(status='passed', actual_updates=20, validation_batches=4,
                  checkpoint_saved=True, observed_memory_error=False)
except BaseException as exc:
    report.update(status='failed', error=repr(exc))
    raise
finally:
    report.update(loss_records=records, elapsed_seconds=time.perf_counter()-started,
                  peak_process_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024**3),
                  memory_note='macOS process peak resident set; excludes other processes and does not measure total system pressure')
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='configuration'},indent=2),flush=True)
