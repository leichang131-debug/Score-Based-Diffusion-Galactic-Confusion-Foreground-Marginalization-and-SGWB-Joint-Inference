# Triangle-GB isolated CPU environment

Dedicated macOS ARM64 environment at `environments/triangle-gb/.venv`, separate from existing TDC and Score-SDE environments. Python is **3.11.14**, managed by `uv` under `../.python-runtimes/`. The virtual environment and runtime are local, ignored artifacts; installation specifications and validation evidence are versioned.

## Dependencies and installation

The environment retains Triangle-Simulator's NumPy 1.26.4, SciPy 1.13.1, healpy 1.17.3 and PyCBC 2.7.2 pins. Inference tools are Bilby 2.8.2, Nessai 0.15.2, nessai-bilby 0.3.2 and PyTorch 2.14.1. Setuptools 80.9.0 retains the `pkg_resources` API required by PyCBC waveform plugins. CPU NumPy/SciPy paths are used; CuPy is not installed. This PyTorch wheel requires macOS 14 or later. Linux cluster dependencies require a separate platform lock and validation.

`requirements.in` records direct requirements. `requirements-macos-arm64-py311.txt` freezes transitive dependencies with hashes for the tested platform. Rebuild from the repository root:

```bash
bash scripts/reproduction/setup-triangle-gb-macos.sh
environments/triangle-gb/.venv/bin/python scripts/reproduction/check-triangle-gb-environment.py
```

The script verifies source pins, synchronizes the isolated environment to the lock, installs Triangle-Simulator **before** Triangle_GB in editable mode without dependency re-resolution, runs `uv pip check`, registers an environment-local kernel and prepares ignored workspace paths. Existing environments are not synchronized or changed. Rebuilding may compile the legacy LIGO dependencies with Apple Command Line Tools.

The first Python 3.12.14 attempt failed to compile `ligo-segments==1.4.0`; it was replaced with Python 3.11.14. See [environment report](../../docs/reproduction/triangle-gb/environment-setup.md) for actual validation status and remaining example prerequisites.

## Paths and notebook use

```bash
bash scripts/reproduction/launch-triangle-gb-jupyter.sh
```

Choose **Triangle-GB — Python 3.11.14 (CPU)**. Future fresh working copies belong in ignored `runs/triangle-gb/workspace/Triangle-GB/Examples/`. The launcher does not copy or execute upstream notebooks. The sibling `Triangle-Simulator` symlink makes the original `../../Triangle-Simulator/OrbitData/...` path work; the local `LDCEqualArmOrbit` symlink preserves the Example 3 orbit path. Installed editable packages resolve from anywhere in this environment, without `sys.path` modifications.

`runs/triangle-gb/workspace/paths.local.json` records machine-specific absolute paths. Bulk input files belong in `data/raw/triangle-gb/`. Original hard-coded author HDF5 paths are not rewritten by setup; future execution adapters must map those values explicitly and record the differences. Preserve notebook filenames, code correspondence, Markdown and reference figures; clear copied outputs before local execution. Curated executed notebooks and evidence will be placed in `notebooks/reproduction/triangle-gb/` and `results/triangle-gb/` after execution.

Numerical thread defaults are one. This does not limit notebook `multiprocessing.cpu_count()` pools; choose and document an execution resource budget before parameter estimation on a 16 GB laptop.

## Scope

Environment checks are separate from complete scientific reproduction. Examples 1/2 still require public VGB files; Example 3 requires the LDC Sangria dataset. The network notebook additionally imports `Triangle_BBH.Fisher.MultiChannelFisher`, absent from the two pinned repositories, so its complete Fisher/prior/inference chain is not ready yet. The core `TDIFlyGBNetwork` class can still be checked independently. No example datasets or optional external Fisher package are downloaded by setup.
