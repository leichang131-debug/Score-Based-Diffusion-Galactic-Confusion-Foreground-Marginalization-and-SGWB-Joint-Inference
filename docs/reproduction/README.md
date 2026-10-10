# Reproduction roadmap

Score-SDE small-scale workflow and final evidence export are complete. See [the final report](score-sde/final-report.md). Full numerical image-generation reproduction remains pending.

Triangle-Simulator shared environment is prepared separately from full tutorial execution. See [setup and evidence](tdc/environment-setup.md). Tutorials 1–4 original-default reproductions are complete: see [Tutorial 1](tdc/tutorial-1.md), [Tutorial 2](tdc/tutorial-2.md) and [Tutorial 3](tdc/tutorial-3.md). Tutorial 4 is complete; Tutorial 5 is excluded following teacher guidance.

## Planned order

1. Score-SDE: verify imports and devices, inspect a batch, run a small training configuration, save and resume, and generate a few samples.
2. TDC: run documented tutorials, inspect separate components, and verify output conventions.
3. TaijiSGWB: read inputs, reproduce a minimal inference case, and inspect sampling diagnostics before claiming numerical reproduction.

Each component uses a separate environment. Pin the upstream commit before execution. A smoke test is not a full training or inference reproduction.

## Report template

- Scientific or software objective.
- Upstream URL and commit; local patch commit.
- Platform and environment lock.
- Data source, checksum, and split.
- Exact command, configuration, and random seed.
- Runtime and resource use.
- Logs, figures, checkpoints, and artifact manifest.
- Validation outcome, convergence status, and unresolved limitations.
