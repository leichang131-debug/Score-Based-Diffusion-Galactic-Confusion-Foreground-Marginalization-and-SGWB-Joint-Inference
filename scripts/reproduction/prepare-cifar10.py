"""Prepare CIFAR-10 and validate the unmodified Score-SDE input pipeline.

Does not initialize the model or execute training. Downloads are verified by TFDS.
"""
import os
from pathlib import Path
import sys
import json
import hashlib
import platform
import shutil
import time
import subprocess
import importlib.util
import importlib.metadata as metadata
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/raw/tensorflow_datasets'
OUT = ROOT / 'runs/score-sde/data-preparation'
for p in (DATA, OUT): p.mkdir(parents=True, exist_ok=True)
os.environ['JAX_PLATFORMS'] = 'cpu'
os.environ['TFDS_DATA_DIR'] = str(DATA)
os.environ['MPLCONFIGDIR'] = str(OUT / 'matplotlib')
UPSTREAM = ROOT / 'external/score-sde-reproduction'
sys.path.insert(0, str(UPSTREAM))
from score_sde_bootstrap import prepare
prepare()
import run_train  # Apply the real upstream compatibility layer.
import numpy as np
import jax
import tensorflow as tf
import tensorflow_datasets as tfds
import datasets
spec = importlib.util.spec_from_file_location('reference_config', UPSTREAM / 'score_sde/configs/vp/cifar10_ddpmpp_continuous.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.get_config()
config.training.batch_size = 1
config.eval.batch_size = 1
config.training.n_jitted_steps = 1
# Avoid optional GCS metadata probing; download the official archive instead.
from tensorflow_datasets.core.utils import gcs_utils
gcs_utils._is_gcs_disabled = True
builder = tfds.builder('cifar10', data_dir=str(DATA))
start = time.perf_counter()
builder.download_and_prepare(download_config=tfds.download.DownloadConfig(try_download_gcs=False, force_checksums_validation=True))
print('Download/preparation finished', flush=True)
raw_checks = {}
for split, expected_count in [('train',50000),('test',10000)]:
    assert builder.info.splits[split].num_examples == expected_count
    count = 0
    low, high = 255, 0
    label_low, label_high = 9, 0
    class_counts = np.zeros(10, dtype=np.int64)
    for batch in tfds.as_numpy(builder.as_dataset(split=split).batch(512)):
        images, labels = batch['image'], batch['label']
        assert images.dtype == np.uint8 and images.shape[1:] == (32,32,3)
        assert np.issubdtype(labels.dtype,np.integer)
        low, high = min(low,int(images.min())),max(high,int(images.max()))
        label_low,label_high=min(label_low,int(labels.min())),max(label_high,int(labels.max()))
        class_counts += np.bincount(labels, minlength=10)
        count += len(images)
    assert count == expected_count and 0 <= label_low <= label_high <= 9
    assert np.all(class_counts == expected_count // 10)
    raw_checks[split]={'class_counts':class_counts.tolist(),'count':count,'image_shape':[32,32,3],'image_dtype':'uint8',
                       'pixel_range':[low,high],'label_range':[label_low,label_high]}
    print('Checked raw split:',split,count,flush=True)
# Exactly the train-mode dataset construction used by upstream run_lib.py.
train_ds, eval_ds, pipeline_builder = datasets.get_dataset(config,additional_dim=config.training.n_jitted_steps,
                                    uniform_dequantization=config.data.uniform_dequantization)
expected_shape=(jax.local_device_count(),1,1,32,32,3)
pipeline_checks={}
for name,ds in [('train',train_ds),('eval',eval_ds)]:
    image=next(iter(ds))['image'].numpy()
    assert image.shape==expected_shape and image.dtype==np.float32
    assert np.isfinite(image).all() and image.min()>=0 and image.max()<=1
    scaled=np.asarray(datasets.get_data_scaler(config)(image))
    assert np.isfinite(scaled).all() and scaled.min()>=-1 and scaled.max()<=1
    # lax.scan removes device and scanned-step axes: network receives B,H,W,C.
    assert scaled[0,0].shape==(1,32,32,3)
    pipeline_checks[name]={'tensor_shape':list(image.shape),'dtype':str(image.dtype),
                          'pre_scaler_range':[float(image.min()),float(image.max())],
                          'centered_range':[float(scaled.min()),float(scaled.max())],
                          'network_input_shape':list(scaled[0,0].shape)}
files=[]
for p in sorted(Path(builder.data_dir).rglob('*')):
    if p.is_file():
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        files.append({'path':str(p.relative_to(DATA)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
report={'status':'passed','purpose':'real CIFAR-10 preparation and input validation; no training',
        'date':datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),'platform':platform.platform(),'python':sys.version.split()[0],
        'versions':{n:metadata.version(n) for n in ['jax','jaxlib','flax','tensorflow','tensorflow-datasets','numpy','protobuf']},
        'devices':[str(d) for d in jax.devices()], 'tfds_dataset':'cifar10','tfds_version':str(builder.info.version),
        'data_directory_relative_to_repository':'data/raw/tensorflow_datasets',
        'upstream_commit':subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip(),
        'original_commit':subprocess.check_output(['git','-C',str(UPSTREAM/'score_sde'),'rev-parse','HEAD'],text=True).strip(),
        'raw_splits':raw_checks,'pipeline':pipeline_checks,
        'configuration_overrides':{'training.batch_size':1,'eval.batch_size':1,'training.n_jitted_steps':1},
        'model_training_configuration':'original; no network/loss/optimizer/warmup/EMA changes',
        'eval_split_note':'Upstream train-mode evaluation uses CIFAR-10 test split with its original preprocessing, including random flip. This is not an independent final test set.',
        'official_archive':{'url':'https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz','bytes':170052171,'expected_sha256':'c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd','verification':'TFDS forced checksum validation'},
        'prepared_files':files,'timing_scope':'this preparation/reuse and validation invocation; excludes optional ranged downloading',
        'elapsed_seconds':time.perf_counter()-start,
        'free_disk_gib_after_preparation':shutil.disk_usage(ROOT).free/(1024**3)}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='prepared_files'},indent=2),flush=True)
