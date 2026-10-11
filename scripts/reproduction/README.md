# Reproduction scripts

Score-SDE has completed environment/data checks, original-network training to 200 updates, typed checkpoint continuation, and four original EMA sampling calls. These establish functionality; converged image generation and standard generative metrics remain unvalidated.

All teacher source lives unchanged in `external/score-sde-reproduction/`, including its original `score_sde` submodule. Project scripts provide macOS setup, execution settings and diagnostics. See [the source-to-workflow map](../../docs/reproduction/score-sde/source-alignment.md).

| Script | Purpose |
| --- | --- |
| `setup-score-sde.sh` | Install/sync the locked macOS CPU environment |
| `score_sde_bootstrap.py` | Skip unused TF-GAN legacy Estimator imports |
| `run-score-sde.sh` | General launcher for the teacher training/evaluation entry |
| `check-score-sde.py` | Historical reduced-network synthetic environment check |
| `download-cifar10-archive.py` | Download and checksum the official CIFAR-10 archive |
| `prepare-cifar10.py` | Prepare TFDS and validate all examples and original input pipeline |
| `check-original-20-updates.py` | Original training, 20 fresh updates |
| `verify-original-20-checkpoint.py` | Read and inspect the 20-update saved state |
| `check-score-sde-resume.py` | Typed restoration at update 20, two updates, separate restart verification |
| `benchmark-score-sde-200.py` | Original continuation from 22 to 200 with synchronized timing |
| `analyze-score-sde-200.py` | Fresh checkpoint readback and timing records/figure |
| `check-score-sde-sampling.py` | Four original EMA samples, finite-value checks and warm-call timing |
| `audit-score-sde-source.py` | Every tracked upstream file and recursive Git link; online HEAD check |
| `export-score-sde-results.py` | Publish portable logs/events and regenerate merged loss exports/figures without model execution |
| `audit-score-sde-evidence.py` | Original TensorBoard reader, configuration parity and artifact checksums |

Run audits from the repository root using `environments/score-sde/.venv/bin/python`. Source audit is online by default; `--offline` explicitly skips current remote HEAD verification. Evidence audit requires the preserved local run directories and checkpoints. Neither audit executes training or sampling.

Shared hashing, model-state initialization and log parsing could later be extracted into a common utility. Stage scripts currently preserve the exact operations used for each completed check; their different update counts and assertions are intentional.

## Triangle-Simulator

- `setup-tdc-macos.sh`: install locked Python 3.9.19 CPU environment and project-local kernel.
- `launch-tdc-jupyter.sh`: launch Jupyter in upstream Tutorials with project-local runtime/cache directories.
- `check-tdc-environment.py`: dependency/source/backend/data/kernel smoke checks, emitting curated evidence.

See [environment instructions](../../environments/tdc/README.md). Full notebooks are not executed by these scripts.

- `run-tdc-tutorial-1.py`: execute unchanged Tutorial 1 and record outputs, timings, sampled process RSS and numerical diagnostics.
- `audit-tdc-tutorial-1.py`: audit code/Markdown/static-image correspondence and saved evidence, without rerunning simulation.

- `run-tdc-tutorial-2.py`: execute all unchanged Tutorial 2 cells and record noise/glitch/method-comparison evidence.
- `audit-tdc-tutorial-2.py`: audit cell/static-image correspondence, finite results and exported figures without rerunning.

- `run-tdc-tutorial-3.py`: execute all unchanged GW injection cells at original scale, recording GB/MBHB/EMRI/SGWB stage evidence and resource use.
- `audit-tdc-tutorial-3.py`: audit source, configurations, finite outputs and all seven exported figures without simulation.

- `run-tdc-tutorial-4.py`: execute unchanged joint simulation, 100-GB fast responses, MBHB/EMRI and sensitivity examples with provenance.
- `audit-tdc-tutorial-4.py`: verify source correspondence, original scales, finite outputs and six figure exports.

- `audit-triangle-gb-source.py`: check full pinned source preservation and inventory without importing or executing Triangle-GB.

## Triangle-GB independent environment

- `setup-triangle-gb-macos.sh`: install the hashed Python 3.11.14 ARM64 dependency set and both pinned editable packages.
- `prepare-triangle-gb-paths.py`: build ignored working paths and original orbit-path links.
- `check-triangle-gb-environment.py`: run local CPU interface, flow-gradient, plugin and Jupyter-kernel checks.
- `launch-triangle-gb-jupyter.sh`: open the prepared working directory with the dedicated environment.

See [environment instructions](../../environments/triangle-gb/README.md). These scripts do not execute full upstream examples.

## Triangle-GB public VGB inputs

- `download-triangle-gb-vgb.py`: download the original Example 1/2 filenames, verify official byte counts/MD5 and record local SHA-256; raw files stay ignored.
- `check-triangle-gb-vgb-data.py`: scan complete HDF5 arrays, execute unchanged input-preparation cells and check source selection, FFT bands and orbit coverage. Exit 2 records the currently diagnosed strict orbit-coverage gap; it is not a full tutorial runner.

See [data preparation and orbit issue](../../docs/reproduction/triangle-gb/data-preparation.md).

## Sangria and network Fisher prerequisites

- `download-triangle-gb-sangria.py`: resumable official Sangria input download, complete-file MD5/SHA-256 verification.
- `prepare-triangle-gb-sangria.py`: bounded full HDF5 scan, complete original dgb text-cache preparation and unchanged non-plot tutorial input/template checks.
- `audit-triangle-bbh-source.py`: compare all pinned Triangle-BBH/WF4Py files to Git blobs.
- `check-triangle-gb-fisher.py`: original imports, independent analytic Fisher/error test, actual LaTeX rendering and original network Fisher/prior cells.
- `triangle_gb_path_adapter.py`: dedicated-kernel external hook for exact original HDF5 paths; source cells stay unchanged.

See [prerequisite completion](../../docs/reproduction/triangle-gb/prerequisites-completion.md). None of these scripts claims complete posterior-sampling reproduction.

- `check-triangle-gb-prerequisites.py`: consolidate actual validated data/import readiness and verify all five same-name working notebook source/Markdown cells, with full reproduction explicitly pending.
