# TaijiSGWB independent macOS CPU environment

Status: Stage 2 installed and checked locally on macOS ARM64. All 25 environment/interface checks passed. Full TDC data preparation and both upstream inference demos remain pending.

## Runtime and dependencies

- Python 3.11.14 in `environments/taiji-sgwb/.venv/`; `include-system-site-packages = false`.
- Original `taijisgwb==0.1.0`, editable from `external/taiji-sgwb/` at `4afaad4044b08721e7f1ce29cba3b0d912636dce`.
- Original scientific pins: NumPy 1.26.4 and SciPy 1.13.1.
- healpy 1.17.3, Eryn 1.2.6, h5py 3.16.0, Matplotlib 3.11.2 and corner 2.3.0.
- Hatchling and editables support the original editable build without altering upstream configuration.

`requirements.in` declares project-owned environment inputs. `requirements-macos-arm64-py311.txt` locks 51 third-party distributions with package hashes. The original editable package is installed separately using `--no-deps --no-build-isolation`. The full 52-distribution installed inventory is recorded in the evidence report. The `[sampler]` optional dependency is satisfied by the explicitly locked Eryn installation.

The upstream dependency table omits h5py although its modules and demos import it, so the independent environment explicitly includes h5py. Upstream does not pin Eryn; 1.2.6 is the locally checked version, not a claim about the author's historical environment. No JAX, TensorFlow or Triangle package is required by these original imports. This environment does not install Jupyter; the upstream entry points are Python scripts.

## Install or check

From the research repository root, with uv available:

```bash
bash scripts/reproduction/setup-taiji-sgwb-macos.sh
python3 scripts/reproduction/run-taiji-sgwb-environment-check.py
python3 scripts/reproduction/audit-taiji-sgwb-environment.py
```

Or sync dependencies and check in one call:

```bash
python3 scripts/reproduction/run-taiji-sgwb-environment-check.py --setup
python3 scripts/reproduction/audit-taiji-sgwb-environment.py
```

The setup script reuses the project-local Python runtime, creating it if absent, and does not replace the user's global Python executable. Environments and downloaded installation caches stay ignored.

## Python invocation interface

```bash
bash scripts/reproduction/run-taiji-sgwb-python.sh -c 'from taijisgwb import Interferometer; import eryn.ensemble; print("Imports OK")'
```

The launcher uses this environment, project-local Matplotlib cache, a headless plotting backend, disabled bytecode writes and one numerical thread per process by default. Arguments are forwarded to Python. It does not adapt the demo's absolute input paths, 62-worker defaults or full-grid response memory usage; those require the subsequent data and execution stages.

## Evidence and scope

See [Stage 2 report](../../docs/reproduction/taiji-sgwb/environment-setup.md) and [local evidence](../../results/taiji-sgwb/environment/README.md). Synthetic sampler checks establish compatibility with the original branch/move/backend APIs. They do not establish a physical posterior, full checkpoint continuation, sampler calibration, or feasibility of the original full-year computation on 16 GB RAM. Linux/cluster deployment is not yet checked.
