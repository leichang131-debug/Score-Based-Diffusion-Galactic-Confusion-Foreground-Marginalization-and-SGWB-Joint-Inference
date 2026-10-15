# Reproduction roadmap

Score-SDE small-scale workflow and final evidence export are complete. See [the final report](score-sde/final-report.md). Full numerical image-generation reproduction remains pending.

Triangle-Simulator shared environment is prepared separately from full tutorial execution. See [setup and evidence](tdc/environment-setup.md). Tutorials 1–4 original-default reproductions are complete: see [Tutorial 1](tdc/tutorial-1.md), [Tutorial 2](tdc/tutorial-2.md) and [Tutorial 3](tdc/tutorial-3.md). Tutorial 4 is complete; Tutorial 5 is excluded following teacher guidance.

## Planned order

1. Score-SDE: verify imports and devices, inspect a batch, run a small training configuration, save and resume, and generate a few samples.
2. TDC: run documented tutorials, inspect separate components, and verify output conventions.
3. Triangle-GB: source integration and independent environment setup are complete. Examples 1/2 public data are downloaded and checked; a strict orbit-coverage gap remains, documented in [data preparation](triangle-gb/data-preparation.md). Sangria and network Fisher prerequisites are now prepared; see [completion report](triangle-gb/prerequisites-completion.md). All five examples have since completed fresh local execution; [current reports and six retained core-check failures](triangle-gb/README.md) define the present limits. See [environment scope](triangle-gb/environment-setup.md). See [source report](triangle-gb/source-integration.md).
4. TaijiSGWB: Stages 1–8 are complete through original spectral likelihood verification ([Stage 7](taiji-sgwb/likelihood.md)) and an exact same-seed template short-chain save/exit/restart comparison ([Stage 8](taiji-sgwb/template-short-chain.md)). Stage 9 completed the original full-data template schedule (5200 transitions, 350 saved ensembles) on 2026-10-15, with six figures and numerical checks passing; conservative diagnostics do not yet confirm convergence ([completed evidence](../../results/taiji-sgwb/template-formal/README.md)). RJ inference, EQ/2.9 experiments and independent-ensemble validation remain separate work.

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

A separate TaijiSGWB selected-data mini experiment has completed the real sampling, restart and analysis workflow ([report](taiji-sgwb/template-mini.md)). Its numerical checks pass while convergence is not confirmed. This mini experiment is separate from the subsequently completed full-data formal inference.

## Current TaijiSGWB execution boundary (2026-10-15)

No further EQ-template or RJMCMC long runs are planned on the local Mac. Completed work, convergence limits and the ordered cluster handoff are recorded in [current status and cluster work packages](taiji-sgwb/status-and-cluster-handoff.md). The current 2.8 template schedule is complete; the full paper and unknown-foreground research are not. Cluster hardware/access and runtime remain unconfirmed.
