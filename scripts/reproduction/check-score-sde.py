"""Synthetic CPU smoke check; not a CIFAR-10 reproduction or quality result."""
import os
from pathlib import Path
import sys
import json
import importlib.metadata as metadata
import importlib.util
os.environ['JAX_PLATFORMS'] = 'cpu'
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/score-sde/environment-check'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(OUT / 'matplotlib')
UPSTREAM = ROOT / 'external/score-sde-reproduction'
sys.path.insert(0, str(UPSTREAM))
# Load the real wrapper, including its TensorFlow and compatibility patches.
from score_sde_bootstrap import prepare
prepare()
import run_train
import jax
import jax.numpy as jnp
import numpy as np
import flax
from flax.training import checkpoints
from models import utils as mutils
import losses
import sampling
import sde_lib
spec = importlib.util.spec_from_file_location('reference_config', UPSTREAM / 'score_sde/configs/vp/cifar10_ddpmpp_continuous.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.get_config()
# Explicitly reduced network for environment validation only.
config.model.nf = 32
config.model.num_res_blocks = 1
config.model.num_scales = 32
config.training.batch_size = 1
config.optim.warmup = 1
rng = jax.random.PRNGKey(42)
model, model_state, params = mutils.init_model(rng, config)
state = mutils.State(step=0, optimizer=losses.get_optimizer(config).create(params), lr=config.optim.lr,
                    model_state=model_state, ema_rate=config.model.ema_rate, params_ema=params, rng=rng)
initial = jax.tree_util.tree_leaves(params)
sde = sde_lib.VPSDE(beta_min=config.model.beta_min, beta_max=config.model.beta_max, N=config.model.num_scales)
step_fn = jax.pmap(losses.get_step_fn(sde, model, train=True, optimize_fn=losses.optimization_manager(config),
                    reduce_mean=config.training.reduce_mean, continuous=True, likelihood_weighting=False), axis_name='batch')
pstate = flax.jax_utils.replicate(state)
batch = {'image': jax.random.uniform(rng, (1, 1, 32, 32, 3), minval=-1., maxval=1.)}
loss_values = []
for i in range(2):
    keys = jax.random.split(jax.random.fold_in(rng, i), jax.local_device_count())
    (_, pstate), loss = step_fn((keys, pstate), batch)
    loss_values.append(float(np.asarray(loss).mean()))
assert np.isfinite(loss_values).all()
state = flax.jax_utils.unreplicate(pstate)
changes = [float(np.max(np.abs(np.asarray(a)-np.asarray(b)))) for a,b in zip(initial,jax.tree_util.tree_leaves(state.optimizer.target))]
assert max(changes) > 0
path = checkpoints.save_checkpoint(str(OUT / 'checkpoints'), state, step=int(state.step), overwrite=True)
restored = checkpoints.restore_checkpoint(str(OUT / 'checkpoints'), state)
assert int(restored.step) == int(state.step)
for a,b in zip(jax.tree_util.tree_leaves(state), jax.tree_util.tree_leaves(restored)):
    np.testing.assert_array_equal(np.asarray(a), np.asarray(b))
sampler = sampling.get_sampling_fn(config, sde, model, (1,32,32,3), lambda x: (x+1.)/2., 1e-3)
samples, evaluations = sampler(jax.random.split(rng, jax.local_device_count()), pstate)
samples = np.asarray(samples)
assert samples.shape == (1,1,32,32,3) and np.isfinite(samples).all()
np.save(OUT / 'synthetic-smoke-samples.npy', samples)
report = {'purpose':'synthetic environment validation; no real-data training or quality claim',
          'python':sys.version.split()[0], 'devices':[str(d) for d in jax.devices()],
          'versions':{n:metadata.version(n) for n in ['jax','jaxlib','flax','optax','tensorflow','tensorflow-gan','tensorflow-hub','tensorflow-probability','tf-keras','numpy']},
          'losses':loss_values,'updates':int(state.step),'max_parameter_change':max(changes),
          'checkpoint_roundtrip':'all state leaves exactly equal','sample_shape':list(samples.shape),
          'sampling_function_evaluations':int(np.asarray(evaluations).flat[0]),
          'reduced_config':{'nf':32,'num_res_blocks':1,'num_scales':32,'batch_size':1,'warmup':1}}
(OUT / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
