# Score-SDE: macOS ARM64 CPU environment

Dedicated CPython 3.12.14 virtual environment: `.venv/` in this directory.
The existing Python installations and Downloads/Python library environment are unchanged.

Core versions: JAX/jaxlib 0.4.30, Flax 0.8.5, Optax 0.2.2, Chex 0.1.86,
Orbax Checkpoint 0.5.15, TensorFlow 2.21.0, NumPy 1.26.4.
`requirements.txt` records the selected baseline; `requirements-lock.txt` records all installed packages.
This is a macOS CPU environment, not a validated Linux/CUDA lock.

From the repository root:

```bash
git submodule update --init --recursive
bash scripts/reproduction/setup-score-sde.sh
environments/score-sde/.venv/bin/python scripts/reproduction/check-score-sde.py
bash scripts/reproduction/run-score-sde.sh --helpfull
```

The smoke check uses synthetic data and a reduced network. It is not a real-data training run or a quality benchmark.

A small-batch run of the original network (not automatically executed):

```bash
bash scripts/reproduction/run-score-sde.sh \
  --config=score_sde/configs/vp/cifar10_ddpmpp_continuous.py \
  --workdir="$PWD/runs/score-sde/original-network-local" \
  --mode=train \
  --config.training.batch_size=1 \
  --config.eval.batch_size=1 \
  --config.training.n_iters=20 \
  --config.training.n_jitted_steps=1 \
  --config.training.log_freq=1 \
  --config.training.eval_freq=10 \
  --config.training.snapshot_freq=10 \
  --config.training.snapshot_freq_for_preemption=10 \
  --config.training.snapshot_sampling=False
```

This preserves the original model architecture and its 5000-step warmup. It only checks execution; 20 configured iterations cannot establish learning quality. The upstream loop includes the final index, so this configuration performs 21 updates from a fresh state. Extend the budget after measuring local speed.
The launcher stores TFDS data under `data/raw/tensorflow_datasets/`, and outputs belong under `runs/`; both are ignored by Git.
Do not mix checkpoints created with different model architectures.

Upstream source is unchanged. Its license remains applicable. Environments, interpreter binaries, datasets, checkpoints and credentials are not committed.

## Compatibility decisions

- Setuptools 80.9.0 supplies `pkg_resources`, required by TF Hub 0.16.1.
- ML Collections 1.1.0 avoids the removed Python 3.12 `imp` module.
- `score_sde_bootstrap.py` skips the unused TF-GAN legacy Estimator import, as suggested by the upstream reproduction guide. Real TF-GAN evaluation functions remain available. The upstream wrapper supplies its own Estimator stubs; Estimator-based GAN training is not supported here.
- Run the provided launcher rather than invoking upstream `run_train.py` directly. No upstream source or installed package source was edited.

See [validation record](../../docs/reproduction/score-sde/environment-validation.json). CIFAR-10 is downloaded on the first real-data run; that download and real-data training have not yet been executed. Full FID/IS/KID evaluation is not validated by the synthetic smoke check.
