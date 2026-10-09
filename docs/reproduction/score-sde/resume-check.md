# Fresh-process checkpoint continuation

Executed on 2026-10-09 after the original-network 20-update process had exited. The teacher wrapper and original Score-SDE submodule remain unmodified.

## Verified sequence

1. Copy the original update-20 preemption checkpoint into a separate `runs/score-sde/resume-check/checkpoints-meta` directory. Preserve the original run.
2. Start a new Python interpreter. Initialize the original network and an empty typed Adam state using the original configuration.
3. Let the original training function restore the copied checkpoint into this typed state. Compare hashes of every serialized field against the stored checkpoint, normalizing only Orbax's custom-pytree field numbering and empty-container representation.
4. Confirm that the fresh template started at update zero with Adam count zero, while the restored state has update count 20 and Adam count 20. Parameters, both Adam moment trees and counter, EMA parameters, model state, learning rate, EMA rate, and saved RNG match the checkpoint exactly.
5. Execute upstream loop labels 20 and 21, adding exactly two updates and two finite validation batches. Save state at update 22. Verify that parameters, Adam state and EMA all changed rather than being reset or left unused.
6. Exit this interpreter. Start another interpreter and reconstruct the typed model/optimizer state. Restore the final checkpoint and confirm that all field hashes exactly match the state supplied to the preceding save call. Separately restore the preemption checkpoint and confirm the same update count, optimizer count, model parameters and EMA.

Both restarts passed. The two resumed training losses were 0.945921 and 1.001740; validation losses were 0.971441 and 0.997999. All inspected state values were finite.

## Checkpoint locations and numbering

The original run remains at update 20. The continuation is stored separately:

- `runs/score-sde/resume-check/checkpoints-meta/checkpoint_21`: update count **22**, used by the original training function for automatic continuation.
- `runs/score-sde/resume-check/checkpoints/checkpoint_21`: update count **22**, final checkpoint after validation.

Directory numbers are based on the upstream loop label and snapshot frequency; inspect `state.step` to determine the actual completed update count. Do not infer it from a folder name.

Upstream writes the preemption checkpoint before that iteration's validation and the final checkpoint afterwards. Validation consumes RNG keys, so these two checkpoints legitimately store different keys even though their parameters, Adam state and EMA are identical. The final checkpoint was compared against the matching final save call, including its RNG.

## Reproduce

With the prepared dataset and environment, from the repository root:

```bash
environments/score-sde/.venv/bin/python -u scripts/reproduction/check-score-sde-resume.py \
  > runs/score-sde/resume-check.log 2>&1
environments/score-sde/.venv/bin/python -u scripts/reproduction/check-score-sde-resume.py --verify \
  > runs/score-sde/resume-second-restart.log 2>&1
```

The first command refuses to reuse its experiment directory. Preserve or rename an existing directory before repeating. The second command executes no training updates. Inspection wraps checkpoint calls in project-owned code; it does not change the original training, loss or optimizer implementation.

- [Configuration](../../../configs/local/score-sde/cifar10-resume-check.py)
- [Validation script](../../../scripts/reproduction/check-score-sde-resume.py)
- [Full diagnostic record and state hashes](resume-validation.json)

## Limits

This check establishes state restoration and usable continuation, not converged training or an identical uninterrupted trajectory. Upstream does not checkpoint the TFDS iterator position, shuffle or augmentation state, and folds the saved RNG by host index again when restarting. Consequently, the next batches and subsequent keys can differ from an uninterrupted process despite correct checkpoint restoration. Exact replay would require a separate, explicitly designed data/RNG persistence solution.

The network, denoising objective, Adam, 5,000-step warmup and EMA 0.9999 were retained. The warmup continues from the restored update count. Snapshot sampling remains disabled. No 200-update benchmark was run.
