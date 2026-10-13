# Reproduction roadmap

Score-SDE small-scale workflow and final evidence export are complete. See [the final report](score-sde/final-report.md). Full numerical image-generation reproduction remains pending.

Triangle-Simulator shared environment is prepared separately from full tutorial execution. See [setup and evidence](tdc/environment-setup.md). Tutorials 1–4 original-default reproductions are complete: see [Tutorial 1](tdc/tutorial-1.md), [Tutorial 2](tdc/tutorial-2.md) and [Tutorial 3](tdc/tutorial-3.md). Tutorial 4 is complete; Tutorial 5 is excluded following teacher guidance.

## Planned order

1. Score-SDE: verify imports and devices, inspect a batch, run a small training configuration, save and resume, and generate a few samples.
2. TDC: run documented tutorials, inspect separate components, and verify output conventions.
3. Triangle-GB: source integration and independent environment setup are complete. Examples 1/2 public data are downloaded and checked; a strict orbit-coverage gap remains, documented in [data preparation](triangle-gb/data-preparation.md). Sangria and network Fisher prerequisites are now prepared; see [completion report](triangle-gb/prerequisites-completion.md). Full example execution remains pending. See [environment scope](triangle-gb/environment-setup.md). See [source report](triangle-gb/source-integration.md).
4. TaijiSGWB: Stages 1–8 are complete through original spectral likelihood verification ([Stage 7](taiji-sgwb/likelihood.md)) and an exact same-seed template short-chain save/exit/restart comparison ([Stage 8](taiji-sgwb/template-short-chain.md)). Stage 9 original formal template inference is intentionally paused after 108 burn-in transitions; cluster migration is planned ([schedule and live-status instructions](taiji-sgwb/template-formal.md)); completion, posterior diagnostic assessment, RJ inference and paper comparison remain pending.

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

A separate TaijiSGWB selected-data mini experiment has completed the real sampling, restart and analysis workflow ([report](taiji-sgwb/template-mini.md)). Its numerical checks pass while convergence is not confirmed. This does not resume or complete the paused full-data formal inference.
