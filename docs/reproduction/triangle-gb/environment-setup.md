# Triangle-GB environment and path setup

## Scope and version choice

This milestone installs an independent macOS ARM64 CPU environment and checks local package interfaces, path resolution, the inference plugin and Jupyter execution. It does not execute the original example notebooks, download their HDF5 datasets or claim parameter-estimation convergence.

Pinned source remains Triangle-GB `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c` and Triangle-Simulator `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. Both are installed editable and kept unmodified.

Python 3.11.14 supports the modern Bilby/Nessai/PyTorch set while retaining the simulator's scientific pins. Python 3.12.14 was initially attempted using the existing runtime; `ligo-segments==1.4.0` failed to build with an incompatible pointer-to-integer error in `src/infinity.c`. The newly created incomplete environment was rebuilt with Python 3.11.14; no existing TDC/Score-SDE environment was changed. An explicit `aarch64-apple-darwin` compile target initially defaulted to macOS 13 and rejected the PyTorch wheel (minimum macOS 14), so resolution uses the actual macOS 27 ARM64 host. This is a host-specific lock, not a tested Linux or older macOS specification.

The first import validation also found that PyCBC 2.7.2 waveform-plugin discovery requires `pkg_resources`, removed by newer setuptools. Pinning setuptools 80.9.0 restores this API while satisfying PyTorch's setuptools requirement. No upstream code was patched.

## Rebuild and validation

See [environment instructions](../../../environments/triangle-gb/README.md). Project-owned scripts:

- `setup-triangle-gb-macos.sh`: hashed dependency synchronization, ordered editable installs, environment-local kernel registration.
- `prepare-triangle-gb-paths.py`: ignored workspace, orbit symlinks and local path inventory, without upstream edits.
- `check-triangle-gb-environment.py`: actual local import and interface checks with structured evidence.
- `launch-triangle-gb-jupyter.sh`: launch the dedicated environment in the prepared workspace.

Structured results are under `results/triangle-gb/environment/`. The kernel smoke notebook is a newly created synthetic check; it is not an upstream notebook or reference output. The waveform check uses 2,048 time samples and 128 sparse samples for a single synthetic source; finite, nonzero time/frequency outputs check compatibility only. The network smoke check uses two identical orbit objects and is not a physical detector-network cross-validation. The glasflow check evaluates a tiny CPU normalizing flow and finite backward gradients. Bilby checks Nessai plugin discovery without starting nested sampling.

## Actual local validation result

All **31/31** environment checks passed on macOS ARM64 Python 3.11.14. Dependency consistency passed for **152** installed packages. The final validation took **3.627 seconds** after imports and font caches had been warmed by earlier attempts; this is not the cold installation time or an example-reproduction runtime.

Single-detector response shapes were `(3, 1, 2048)` in time and `(3, 1, 128)` in frequency. Two-detector sparse responses are a list of two `(3, 1, 128)` arrays, as specified by the upstream API; the joint A/E band shape was `(4, 1, 41)`. All checked arrays were finite and the single-detector time/frequency responses were nonzero. The initial project-owned check incorrectly assumed the network list was one array; it was corrected to match the upstream interface, without changing source.

The final log retains harmless diagnostic messages: CuPy/optional waveform packages are absent, PyCBC falls back when `pkg-config` is unavailable, NumPy warns about header-row counting in the reduced orbit read, and Jupyter prints its local TCP transport notice. No check failed. CPU backend selection is explicit; CUDA/MPS capability is not a reproduction claim.

The dedicated kernel executed a freshly created synthetic notebook locally and was shut down after the check. Source preservation was rechecked after editable installs. Full examples, datasets and posterior convergence are not validated by these checks.

## Remaining interfaces

| Example | Remaining prerequisites |
| --- | --- |
| 0: TD/FD comparison | Fresh copy with cleared outputs, original-scale execution and scientific audit |
| 1: rapid search | VGB data and parameter HDF5 download/checksum/schema checks; explicit author data-path mapping |
| 2: parameter estimation | Same VGB inputs; sampling and multiprocessing resource budget |
| 3: LDC reconstruction | External Sangria HDF5 file; explicit author data-path mapping |
| Network | `Triangle_BBH.Fisher.MultiChannelFisher` source/version and separate installation/validation, then full inference run |

No author-specific absolute directories are created. Notebook source strings are unchanged. The working-directory orbit links satisfy original relative paths; the future execution runner must explicitly substitute unavailable absolute HDF5 paths. Future curated notebooks retain their upstream names and explanatory content, with all adapters documented separately.
