# Joint Inference of Galactic Confusion Foreground Marginalization and Stochastic Gravitational-Wave Background Based on Score-Based Diffusion Models

Research workspace for probabilistic marginalization of the Galactic confusion foreground and joint inference of a target stochastic gravitational-wave background (SGWB) using score-based diffusion models.

**Status:** research architecture and plan, plus a validated macOS ARM64 CPU environment for Score-SDE. The pinned Score-SDE source is available as a recursive Git submodule. Synthetic gradient-update, checkpoint-roundtrip, and sampling checks passed. Full CIFAR-10 preparation and original input-pipeline validation also passed; An original-network, batch-one CIFAR-10 smoke run completed 20 updates and four finite validation losses, with saved-state inspection passing. A separate fresh-process [resume check](docs/reproduction/score-sde/resume-check.md) restored the complete typed state, continued from update 20 to 22, and passed a second restart. Continuation to 200 total updates and a synchronized CPU [speed benchmark](docs/reproduction/score-sde/original-200-updates.md) passed, including final checkpoint readback. Converged training and faithful numerical reproduction have not yet been completed. See [the 20-update report](docs/reproduction/score-sde/original-20-updates.md). No performance improvement is claimed.

## Scientific objective

The observed data contain a Galactic foreground, a target SGWB, and instrument noise. The goal is to propagate uncertainty in the foreground and noise into calibrated SGWB parameter constraints, and to determine whether the learned distribution uses information beyond a strong second-order statistical baseline.

Foreground marginalization accounts for possible foreground realizations; it does not assume that the true foreground can be subtracted from observed data. The primary outputs are parameter posteriors and component spectra with uncertainty, rather than a uniquely recovered random waveform.

## Initial inference model

The first controlled experiment fixes the SGWB spectral index and jointly estimates four power scales:

- Target SGWB amplitude.
- Galactic foreground amplitude.
- Acceleration-noise amplitude.
- Optical-metrology-noise amplitude.

Known orbit and processing states are conditioning variables. Unknown physical quantities belong in the inference model. Later experiments can release spectral and population parameters and incorporate source-subtraction errors.

## Method and validation

1. Define the physical model, observational representation, and independent simulation splits.
2. Establish solvable controls and strong Gaussian and flexible-foreground baselines.
3. Generate conditional samples with independently drawn foreground, background, and noise realizations.
4. Train a conditional score model; compare direct and residual-score implementations.
5. Use a probability-flow ODE to evaluate a normalized flow-model density. A score vector alone is not a parameter likelihood.
6. Obtain the joint posterior and marginalize nuisance parameters.
7. Assess numerical closure, posterior calibration, parameter bias, false alarms, detection power, and computational cost.
8. Use covariance-matched Gaussian controls and realistic mismatch experiments to identify the source and limits of any improvement.

Time modulation and nonstationarity do not automatically imply non-Gaussianity. Any scientific benefit must be demonstrated against fair baselines on independent data.

## Repository layout

```text
.
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── external/                     # Upstream source slots and provenance
│   ├── score-sde-reproduction/
│   ├── triangle-simulator/
│   ├── triangle-gb/
│   └── taiji-sgwb/
├── environments/                 # Separate component/platform environments
│   ├── score-sde/
│   ├── tdc/
│   └── taiji-sgwb/
├── configs/                      # Local, cluster, and inference configurations
│   ├── local/
│   ├── cluster/
│   └── inference/
├── scripts/                      # Reproduction and cluster execution entry points
│   ├── reproduction/
│   └── cluster/
├── src/                          # Future project-owned research implementation
│   └── sgwb_diffusion/
│       ├── data/
│       ├── models/
│       ├── likelihoods/
│       ├── inference/
│       └── validation/
├── notebooks/                    # Explanatory and exploratory notebooks
├── tests/                        # Future scientific and numerical checks
├── docs/                         # Plan, methodology, notes, and meetings
│   ├── research-plan/
│   ├── reproduction/
│   └── meetings/
├── data/                         # Data documentation; bulk data kept outside Git
├── results/                      # Curated results and artifact inventories
│   ├── figures/
│   ├── tables/
│   └── manifests/
└── runs/                         # Local generated outputs; ignored by Git
```

Score-SDE is now integrated as an unmodified, pinned Git submodule, with environment and launch scripts. Other upstream component directories remain source slots. See [the reproduction roadmap](docs/reproduction/README.md).

## Research plan

- [Research framework and implementation plan (PDF)](docs/research-plan/research-framework-and-implementation-plan.pdf).
- [Standalone LaTeX source](docs/research-plan/research-framework-and-implementation-plan.tex).
- [Scientific workflow](docs/methodology.md).
- [Research milestones](docs/roadmap.md).

The archived PDF and LaTeX source are the existing Chinese-language planning document, preserved without translation. New repository documentation and path names are in English. The plan is a design document, not a report of completed experiments.

## Referenced upstream projects

| Component | Source | Planned role |
| --- | --- | --- |
| Score-SDE reproduction | [iphysresearch/score-sde-reproduction](https://github.com/iphysresearch/score-sde-reproduction) | Compatibility layer and reference image-generation workflow |
| Original Score-SDE | [yang-song/score_sde at 0acb9e0](https://github.com/yang-song/score_sde/tree/0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c) | Reference SDE, score training, sampling, and likelihood implementation |
| Triangle-Simulator | [TriangleDataCenter/Triangle-Simulator](https://github.com/TriangleDataCenter/Triangle-Simulator) | Space-based detector simulations |
| Triangle-GB | [TriangleDataCenter/Triangle-GB](https://github.com/TriangleDataCenter/Triangle-GB) | Galactic-binary response calculations |
| TaijiSGWB | [DrizzleatDusk/TaijiSGWB](https://github.com/DrizzleatDusk/TaijiSGWB) | SGWB inference reference workflow |

Related reference: [Isotropic stochastic gravitational wave background reconstruction for Taiji constellation](https://arxiv.org/abs/2601.00169).

Use pinned upstream commits and preserve upstream licenses when integrating code. Keep project adapters and patches separate from reference sources.

## Environment and execution policy

Use independent environments for Score-SDE, TDC, and TaijiSGWB. Validate and lock the dependency versions for each platform before publishing installation commands.

Local macOS CPU runs will establish minimal functionality and support learning. Linux cluster resources will support full training, large simulations, posterior sampling, and repeated injection studies. Apple GPU compatibility has not been validated. Score-SDE environment setup, command-line configuration parsing, and synthetic CPU execution have been validated on macOS. See [Score-SDE setup](environments/score-sde/README.md). Other component installation commands are not yet validated.

## Reproducibility and results

For each experiment, record the source commit, environment lock, configuration, seed, dataset provenance and split, hardware, runtime, diagnostics, and artifact hashes. Distinguish installation, smoke-test completion, converged inference, and faithful numerical reproduction.

Commit small curated figures, tables, and summaries under `results/`. Keep raw datasets, checkpoints, and large chains outside normal Git history; register them with checksums and retrieval locations in `results/manifests/`, and use an appropriate release, Git LFS, or laboratory storage when needed. No repository-wide rule excludes all research results.

## License and attribution

Project-owned material is distributed under the [MIT License](LICENSE). Referenced or later incorporated third-party code retains its original license and attribution; the root MIT license does not relicense it.

Maintained by [leichang131-debug](https://github.com/leichang131-debug). See [CONTRIBUTING.md](CONTRIBUTING.md) for collaboration and reporting conventions.
