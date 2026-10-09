# Original-network CIFAR-10: 20-update smoke check

Executed on 2026-10-09 on the local MacBook Air, using one JAX CPU device and the locked Score-SDE environment. This is a functionality check, not a numerical reproduction of published metrics or a convergence result.

## Outcome

- Exactly 20 optimizer updates completed (upstream loop labels 0 through 19).
- All 20 logged training losses were finite, approximately 0.950–1.054.
- Four validation batches executed at loop labels 0, 5, 10, and 15. Losses were 0.986175, 1.002560, 1.002490, and 1.030570.
- No memory allocation error or out-of-memory termination occurred.
- The training invocation took 198.81 seconds, including initialization, compilation, validation and checkpoint writing, but excluding interpreter imports and subsequent saved-state inspection.
- The first training loss was recorded after 108.35 seconds, including model initialization and initial compilation/execution. The median subsequent training interval excluding intervals containing validation was 4.08 seconds. This short run is not the planned 200-update sustained-speed measurement.
- Peak training-process resident memory was 5.63 GiB. This is process RSS on macOS, not total system memory pressure or a guarantee for larger batches.
- Final and preemption checkpoints were saved. Both restored dictionaries report `state.step = 20`; all 2,261 state tensor leaves were finite. This validates artifact readability, not yet a continued-training run with a reconstructed typed state.
- Local output occupies approximately 1.8 GiB, mainly the two checkpoints. Raw checkpoints and TensorBoard events remain outside Git.

## What was preserved

The pinned teacher wrapper and its pinned original Score-SDE submodule remain unmodified. Configuration derives from `configs/vp/cifar10_ddpmpp_continuous.py`: NCSN++/DDPM++, `nf=128`, four residual blocks per level, original attention and channel multipliers, continuous VP-SDE, original denoising score-matching objective, Adam, learning rate 0.0002, 5,000-step warmup, gradient clipping and EMA 0.9999. The SDE retains 1,000 discretization scales.

Project-owned overrides are batch size 1 for training/evaluation, one jitted step, `n_iters=19` for the inclusive upstream loop, per-update logging, evaluation every five steps, final/preemption checkpoint frequency 19, and disabled automatic snapshot sampling. Sampling settings themselves are unchanged; image generation and quality evaluation are outside this check.

## Reproduce and inspect

From the repository root, with prepared CIFAR-10 and the installed environment:

```bash
environments/score-sde/.venv/bin/python -u scripts/reproduction/check-original-20-updates.py \
  > runs/score-sde/original-20-updates.log 2>&1
environments/score-sde/.venv/bin/python -u scripts/reproduction/verify-original-20-checkpoint.py \
  > runs/score-sde/original-20-checkpoint-validation.log 2>&1
```

The training script intentionally refuses to reuse an existing checkpoint directory. To repeat, first preserve or rename `runs/score-sde/original-20-updates`; an existing run must not silently resume and be reported as a new 20-update run. The separate inspection script runs no optimizer updates. Optional GCS metadata probing is disabled in the runner; data are read from the verified local TFDS dataset.

- [Project configuration](../../../configs/local/score-sde/cifar10-original-20-updates.py)
- [Machine-readable report, configuration and artifact checksums](original-20-updates-validation.json)
- [Timestamped loss records](original-20-updates-losses.txt)

## Interpretation and next step

With batch size one, random diffusion times and a retained 5,000-step warmup, losses near one after 20 updates do not establish learning quality. Do not use these values to claim convergence, good denoising, or improved generative performance. Upstream train-mode validation uses the CIFAR-10 test split with its original preprocessing; this is not a separate untouched final scientific test.

The next stage is a separately authorized continuation to approximately 200 updates, checking typed-state restoration, longer-run timing and memory stability while preserving the original method. A fresh process may compile again. Do not change network size or warmup merely to produce visually appealing outputs during this smoke stage.
