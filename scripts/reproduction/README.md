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
