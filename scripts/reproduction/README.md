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

- `check-triangle-gb-prerequisites.py`: consolidate actual validated data/import readiness and verify all five same-name working notebook source/Markdown cells, without executing the examples in that preparation check. All five examples have since executed; current reports remain authoritative.

## Triangle-GB Example 0

`run-triangle-gb-example-0.py` executes all unchanged original cells at full default scale, clears source outputs, saves the same-name notebook and local figures, times and numerical evidence. `audit-triangle-gb-example-0.py` verifies source correspondence, execution, finite arrays and upstream mismatch precision, and writes the evidence manifest. See the [report](../../docs/reproduction/triangle-gb/example-0.md).

## Triangle-GB Example 1

`run-triangle-gb-example-1.py` executes the unchanged original VGB rapid-search notebook with fresh local outputs and original multiprocessing defaults. `audit-triangle-gb-example-1.py` verifies input hashes, source correspondence, optimization, the F-statistic/residual identity and saved local outputs. See [report](../../docs/reproduction/triangle-gb/example-1.md).

## Triangle-GB Example 2

`run-triangle-gb-example-2.py` executes the unchanged eight-parameter Bilby/NESSAI notebook with original nlive=500, stopping=0.01 and CPU pool settings. `export-triangle-gb-example-2.py` exports final scientific sampler artifacts and insertion diagnostics while retaining checkpoints/flow weights in ignored runs. `audit-triangle-gb-example-2.py` verifies inputs, original source, settings, posterior bounds/finiteness and likelihood/evidence consistency, separately from scientific calibration. See [report](../../docs/reproduction/triangle-gb/example-2.md).

## Triangle-GB Example 3

`run-triangle-gb-example-3.py` executes the full unchanged Sangria notebook using the complete original-supported catalog cache and original LDC orbit/band/response settings. `audit-triangle-gb-example-3.py` rehashes the raw file and complete cache, checks selected catalog conventions, original source, finite reconstruction and local outputs, and writes the evidence manifest. See [report](../../docs/reproduction/triangle-gb/example-3.md).

## TaijiSGWB source preservation

`audit-taiji-sgwb-source.py` checks the complete pinned upstream tree, exact names and byte contents, Git file modes, directly tracked snapshot files, reconstructed original Git tree, Python syntax and original GPL license. The shared `taiji_sgwb_source.py` reads `configs/upstream/taiji-sgwb.json`; no nested Git repository or submodule initialization is required for TaijiSGWB. It writes a file list, SHA-256 manifest and audit report under `results/taiji-sgwb/source/`. The default audit checks current upstream HEAD online; `--offline` skips only that network check. It uses the standard library and never imports or executes upstream programs.

See [Stage 1 source integration](../../docs/reproduction/taiji-sgwb/source-integration.md).

## TaijiSGWB independent environment

- `setup-taiji-sgwb-macos.sh`: sync the hashed Python 3.11.14 ARM64 environment and install unchanged original source editable.
- `run-taiji-sgwb-python.sh`: dedicated Python invocation with local plotting cache and CPU thread settings.
- `check-taiji-sgwb-environment.py`: execute both demos' exact import statements and small synthetic response/Eryn/HDF5 checks.
- `run-taiji-sgwb-environment-check.py`: preserve command logs, timings and dependency-lock parity; `--setup` also syncs installation.
- `audit-taiji-sgwb-environment.py`: source/evidence audit and manifest export without re-running sampling.

All 25 Stage 2 checks passed locally. These scripts do not run either complete original demo or establish physical posterior accuracy. See [Stage 2 report](../../docs/reproduction/taiji-sgwb/environment-setup.md).

## TaijiSGWB official 2.8 inputs

- `download-taiji-sgwb-data.py`: preserve official filenames, download/check Zenodo 2.8 data and pinned official orbit, verify MD5/Git blob and local SHA-256; four bounded verified ranges for resumable downloads.
- `prepare-taiji-sgwb-paths.py`: ignored symlinks for original demo-relative filenames; upstream PROJ_DIR remains unchanged.
- `check-taiji-sgwb-data.py`: complete HDF5 finite-value scan, components/injections, exact original read/AET/trim code and all-week orbit coverage.
- `run-taiji-sgwb-data-check.py`: record actual commands, logs and timings; `--download` optionally retrieves/rechecks inputs.
- `audit-taiji-sgwb-data.py`: rehash raw inputs, verify aliases and original source, export evidence manifest.

[Stage 3 report](../../docs/reproduction/taiji-sgwb/data-preparation.md). These commands do not execute a full SGWB inference demo.

## TaijiSGWB Stage 5 full original preprocessing

- `taiji_sgwb_preprocessing.py`: execute unchanged original preprocessing AST nodes with explicit local path routing; provide `load_preprocessing_cache()` for subsequent code.
- `check-taiji-sgwb-preprocessing.py`: full original prefix per same-name entry, complete direct FFT/CSD/Parseval reference and spectrum-matrix checks, cache export.
- `run-taiji-sgwb-preprocessing.py`: independent runs for both original entries, execution/timing/resource logs and byte-level scientific array parity.
- `audit-taiji-sgwb-preprocessing.py`: rehash source/caches/summaries and compare original executed nodes without FFT reruns.

Both original full-year prefixes passed 20/20 checks. See [Stage 5 report](../../docs/reproduction/taiji-sgwb/preprocessing.md). Original names/source are retained; response and inference are subsequent stages.

## TaijiSGWB Stage 6 original response and cache

- `taiji_sgwb_response.py`: original noise/ORF node extraction, bounded execution, exact-input channel-response memoization and original-name cache readback.
- `check-taiji-sgwb-response.py`: full original-grid noise/ORF cache with unblocked controls and all matrix checks.
- `run-taiji-sgwb-response.py`: actual execution, return code, per-block progress and sampled RSS.
- `report-taiji-sgwb-response.py`: render the saved ORF diagnostic without recomputation.
- `audit-taiji-sgwb-response.py`: verify original node/source correspondence, full-cache/array hashes and exact block coverage.

All 32 response checks passed. Both original examples share a verified full response cache; [Stage 6 report](../../docs/reproduction/taiji-sgwb/response.md). No parameter likelihood or posterior sampling is executed here.

## Repository-wide documentation and evidence audit

`audit-repository-documentation.py` checks tracked JSON syntax, Python syntax, local Markdown link targets and SHA-256 records in supported artifact manifests. It does not rerun simulations, MCMC, training, scientific acceptance tests or remote-link checks. Historical preparation/pause/failure reports retain their original dates and scope; current summaries link to them.

The mini analyzer now checks before/after formal-artifact hashes rather than requiring a live paused status. Historical analysis and its original analyzer remain preserved; the updated analysis-only verification reproduced all four mini figures and numerical summaries. See `results/repository-maintenance-20261015/`.
