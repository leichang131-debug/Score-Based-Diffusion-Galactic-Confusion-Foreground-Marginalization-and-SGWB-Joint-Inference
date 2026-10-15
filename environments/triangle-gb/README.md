# Triangle-GB isolated CPU environment

Dedicated macOS ARM64 environment at `environments/triangle-gb/.venv`, separate from existing TDC and Score-SDE environments. Python is **3.11.14**, managed by `uv` under `../.python-runtimes/`. The virtual environment and runtime are local, ignored artifacts; installation specifications and validation evidence are versioned.

## Dependencies and installation

The environment retains Triangle-Simulator's NumPy 1.26.4, SciPy 1.13.1, healpy 1.17.3 and PyCBC 2.7.2 pins. The pinned Triangle-BBH submodule and its bundled WF4Py are now installed editable to satisfy the network Fisher import and automatic package imports. Inference tools are Bilby 2.8.2, Nessai 0.15.2, nessai-bilby 0.3.2 and PyTorch 2.14.1. Setuptools 80.9.0 retains the `pkg_resources` API required by PyCBC waveform plugins. CPU NumPy/SciPy paths are used; CuPy is not installed. This PyTorch wheel requires macOS 14 or later. Linux cluster dependencies require a separate platform lock and validation.

`requirements.in` records direct requirements. `requirements-macos-arm64-py311.txt` freezes transitive dependencies with hashes for the tested platform. Rebuild from the repository root:

```bash
bash scripts/reproduction/setup-triangle-gb-macos.sh
environments/triangle-gb/.venv/bin/python scripts/reproduction/check-triangle-gb-environment.py
```

The script verifies source pins, synchronizes the isolated environment to the lock, installs Triangle-Simulator **before** Triangle_GB in editable mode without dependency re-resolution, runs `uv pip check`, registers an environment-local kernel and prepares ignored workspace paths. Existing environments are not synchronized or changed. Rebuilding may compile the legacy LIGO dependencies with Apple Command Line Tools.

The first Python 3.12.14 attempt failed to compile `ligo-segments==1.4.0`; it was replaced with Python 3.11.14. See [environment report](../../docs/reproduction/triangle-gb/environment-setup.md) for its environment-only checks; all five examples have since executed, with [current numerical limits](../../docs/reproduction/triangle-gb/README.md).

## Paths and notebook use

```bash
bash scripts/reproduction/launch-triangle-gb-jupyter.sh
```

Choose **Triangle-GB — Python 3.11.14 (CPU)**. Future fresh working copies belong in ignored `runs/triangle-gb/workspace/Triangle-GB/Examples/`. Path preparation creates only missing same-name working copies with source/Markdown unchanged and historical outputs cleared. The launcher does not execute notebooks. The sibling `Triangle-Simulator` symlink makes the original `../../Triangle-Simulator/OrbitData/...` path work; the local `LDCEqualArmOrbit` symlink preserves the Example 3 orbit path. Installed editable packages resolve from anywhere in this environment, without `sys.path` modifications.

`runs/triangle-gb/workspace/paths.local.json` records machine-specific absolute paths. Bulk input files belong in `data/raw/triangle-gb/`. Original author HDF5 strings remain unchanged. The dedicated launcher activates an external IPython startup hook mapping the three exact author paths to local verified files; mapping events are recorded locally. The h5py.File subclass preserves the structure-printer type checks. Preserve notebook filenames, code correspondence, Markdown and reference figures; clear copied outputs before local execution. Curated executed notebooks and evidence are now saved in `notebooks/reproduction/triangle-gb/` and `results/triangle-gb/` for all five examples.

Numerical thread defaults are one. This does not limit notebook `multiprocessing.cpu_count()` pools; choose and document an execution resource budget before parameter estimation on a 16 GB laptop.

## Scope

Environment checks are separate from complete scientific reproduction. Examples 1/2 public VGB files and Example 3 Sangria data plus the complete 26-million-row parameter cache are prepared locally. The network notebook additionally imports `Triangle_BBH.Fisher.MultiChannelFisher`; the pinned Triangle-BBH and WF4Py packages satisfy it. Its original Fisher/prior cells are checked separately from sampling. Sangria input and complete dgb cache preparation are documented in the [prerequisite report](../../docs/reproduction/triangle-gb/prerequisites-completion.md). Setup installs source dependencies but does not download large input files or run full examples.
