# Triangle-Simulator shared tutorial environment

Dedicated macOS ARM64 CPU environment for all five upstream notebooks, independent of Score-SDE. Source is an unmodified Git submodule at `external/triangle-simulator`, pinned to `ab796358e9a36c8987f6bb53a97230d603bfdfd5`; third-party code retains GPL-3.0.

## Installation

Python **3.9.19** matches the upstream README's tested recipe. `uv` installs a standalone runtime under `../.python-runtimes/` (relative to the research repository) and creates `environments/tdc/.venv`. No Conda distribution is needed for this equivalent isolated installation.

From the research repository root:

```bash
bash scripts/reproduction/setup-tdc-macos.sh
```

The script exports pinned upstream `uv.lock` without dev dependencies, installs the hashed requirements, then explicitly installs Triangle in editable mode without resolving its dependencies again. `requirements-upstream.txt` records upstream resolution with Python/platform markers; only applicable packages are installed. This environment targets macOS ARM64 Python 3.9; Linux cluster compatibility needs separate validation.

Scientific pins: NumPy 1.26.4, SciPy 1.13.1, healpy 1.17.3 and PyCBC 2.7.2. Jupyter and transitive packages follow the lock. CPU uses NumPy/SciPy; CUDA/CuPy, JAX, TensorFlow and PyTorch are not required by these tutorial paths. Optional waveform packages for other models are not installed.

## Launch and validate

```bash
bash scripts/reproduction/launch-tdc-jupyter.sh
environments/tdc/.venv/bin/python scripts/reproduction/check-tdc-environment.py
```

Select **Triangle TDC — Python 3.9.19**. The kernel is registered inside the virtual environment, not globally. The launcher opens upstream `Tutorials/` and exposes the research repository as the file-browser root, so working copies can be saved under `runs/`. Numerical library threads default to one; notebook multiprocessing pools are not overridden.

To preserve original notebooks, use **Save As** to an ignored path under `runs/tdc-tutorials/`. A notebook normally starts its kernel in its own directory. In a working copy, set the kernel working directory to `external/triangle-simulator/Tutorials/` using `%cd` with its absolute local path (check `Path.cwd()`), or use absolute data paths in the working copy. Setup synchronizes installed packages to the lock: use the launcher for ordinary notebook work.

Source, scripts, requirements and curated evidence are versioned. The interpreter, virtual environment, caches, Jupyter configuration and bulk outputs stay local. Never commit Jupyter server tokens or connection URLs.

## Scope and remaining work

Environment checks establish imports, waveform backends, bundled-data readability and Jupyter execution. They do not reproduce five full tutorial outputs. See [validation report](../../docs/reproduction/tdc/environment-setup.md).

Tutorials 1–4 use supplied orbit/waveform examples. Tutorial 5 is excluded from the current reproduction scope following teacher guidance; its external HDF5 dataset is not a blocker. Synthetic HDF5 tests check interfaces and do not replace the actual dataset.
