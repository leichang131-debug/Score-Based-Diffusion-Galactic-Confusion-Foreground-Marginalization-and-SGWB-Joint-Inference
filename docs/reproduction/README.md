# Reproduction roadmap

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
