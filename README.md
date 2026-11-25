# Galactic Foreground and SGWB Joint Inference

Research on joint inference of the Galactic foreground, stochastic gravitational-wave background (SGWB), and instrument noise. The current baseline is the full-covariance Taiji framework of Liang et al. Score-based likelihood correction remains a future research direction.

## Current baseline

The immediate task is to reproduce Figure 8 of [Full-Covariance Bayesian Inference of Stochastic Gravitational-Wave Backgrounds with Time-Domain Simulations for Taiji-like Missions](https://arxiv.org/abs/2608.11276v2) using the [authors' code](https://github.com/Eric-Friedman-666/taiji-sgwb-time-domain/tree/e5ebd75639c3433717ff2cafe52e7f2f5a3f34bb). The paper and source have been reviewed. The complete upstream source is tracked in [`external/taiji-sgwb-time-domain/`](external/taiji-sgwb-time-domain/README.md). See the [local environment setup and checks](environments/taiji-sgwb-time-domain/README.md). The [archived Figure 8 replay](results/taiji-sgwb-time-domain/reference-replay/README.md) is complete. All three [formal ten-parameter fits and timing records](results/taiji-sgwb-time-domain/formal-sampling/README.md) are archived. Matched null runs remain pending.

The model combines two instrument-noise amplitudes, four effective Galactic double white dwarf foreground parameters, two astrophysical SGWB parameters, and two phase-transition sound-wave parameters. It uses complex XYZ spectral covariance and Bilby/Dynesty nested sampling.

| Configuration | Ten-parameter posterior | Eight-parameter no-sound-wave fit |
| --- | --- | --- |
| Static equal-arm frequency domain | `fit_079` | `fit_078` |
| Equal-arm time domain | `fit_081` | `fit_080` |
| Unequal-arm time domain | `fit_083` | `fit_082` |

The three full fits supply the joint posteriors. Each matched null fit supplies the reference evidence for the corresponding Bayes factor. The [baseline plan](docs/research-plan/full-covariance-baseline.md) defines the acceptance criteria. The [reproduction index](docs/reproduction/taiji-sgwb-time-domain/README.md) tracks progress.

## Repository layout

| Location | Purpose |
| --- | --- |
| [`external/`](external/README.md) | Pinned upstream source and attribution |
| [`environments/`](environments/README.md) | Independent component environments |
| [`configs/`](configs/README.md) | Experiment definitions and execution settings |
| [`scripts/`](scripts/README.md) | Project-owned reproduction and cluster tools |
| [`src/`](src/README.md) | Project-owned research implementation |
| [`docs/`](docs/research-plan/README.md) | Research plans, methods, references, and reproduction reports |
| [`data/`](data/README.md) | Dataset and cache documentation |
| [`results/`](results/README.md) | Curated figures, summaries, and artifact records |
| [`notebooks/`](notebooks/README.md), [`tests/`](tests/README.md), [`runs/`](runs/README.md) | Notebooks, validation, and local run storage |

Baseline-specific directories use `taiji-sgwb-time-domain`. The earlier Jiang TaijiSGWB study uses `taiji-sgwb`. See the [methodology](docs/methodology.md) and [roadmap](docs/roadmap.md) for the sequence from the current baseline to follow-up experiments.

## Prior reproduction work

| Component | Completed locally | Remaining limits and evidence |
| --- | --- | --- |
| Score-SDE | Original network: 200 updates, typed optimizer/EMA recovery and four finite EMA sampling calls | Previews remain saturated noise; 214k quality and standard image metrics are not reproduced. [Final report](docs/reproduction/score-sde/final-report.md) |
| Triangle-Simulator | All four in-scope tutorials executed at original default scales, with unchanged source/Markdown and local outputs | Tutorial 5 excluded by teacher guidance. [Tutorial index](notebooks/reproduction/triangle-simulator/README.md) |
| Triangle-GB | All five example notebooks executed with original defaults; Sangria and Fisher prerequisites prepared | Core verification: 22/28 pass, six retained failures; orbit-coverage and posterior-calibration limits remain. [Reports](docs/reproduction/triangle-gb/README.md) |
| TaijiSGWB | Original 2.8 data/orbit, both preprocessing entries, response cache, both likelihood interfaces, template recovery and full 5200-transition template schedule | Six formal plots re-render exactly; convergence unconfirmed (2/14 diagnostic flags pass). EQ/RJ sampling and full-paper reproduction remain incomplete. [Current status](docs/reproduction/taiji-sgwb/status-and-cluster-handoff.md) |

Score-SDE (including its nested original source), Triangle-Simulator, Triangle-GB and Triangle-BBH retain pinned submodules. TaijiSGWB is an unmodified 19-file fixed source snapshot at `4afaad4044b08721e7f1ce29cba3b0d912636dce`, included directly in ordinary clones; [its source lock](configs/upstream/taiji-sgwb.json) records the upstream tree and file hashes. See [source integration](external/README.md) and [the reproduction roadmap](docs/reproduction/README.md).

Jiang and Huang's [TaijiSGWB study](https://arxiv.org/abs/2601.00169) remains a reference for spectral reconstruction. Earlier [Route B and research plans](docs/research-plan/README.md) record the motivation for learned likelihood correction. Local A800 preparation for the earlier workflow included environment and restart checks. The Liang baseline requires its own deployment and timing measurements.

## Reproducibility

Track source revisions, inputs, effective settings, sampling seeds, run diagnostics, and artifact hashes. Put large data, response caches, sampler states, and posterior archives on research storage. Keep figures, compact summaries, and artifact inventories under `results/`.

## License and attribution

Project-owned material is distributed under the [MIT License](LICENSE). Referenced or later incorporated third-party code retains its original license and attribution; the root MIT license does not relicense it.

Maintained by [leichang131-debug](https://github.com/leichang131-debug). See [CONTRIBUTING.md](CONTRIBUTING.md) for collaboration and reporting conventions.
