# Sangria and network Fisher prerequisite completion

## Scope

This milestone prepares original-scale inputs and required interfaces for all five upstream Triangle-GB example notebooks. It does not claim full notebook execution, optimizer recovery, likelihood-scan reproduction, sampling convergence or posterior agreement.

Canonical upstream folders, source, filenames and explanatory cells remain unmodified. Triangle-GB is pinned at `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`. Triangle-Simulator remains pinned at `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. Triangle-BBH is fully preserved as a shallow, detached submodule at `f99b0a34ea8d085aff67220bdc165a746ba5ceda`; all 80 tracked files, including the bundled modified WF4Py, are checked against Git blobs. Upstream licenses are retained. Triangle-BBH's GPL-3.0 LICENSE is not replaced by the main repository's MIT license or by its setup.py classifier.

## Sangria

Official source: https://zenodo.org/records/7132178 . Requested file: `LDC2_sangria_training_v2.h5`, 3,082,321,484 bytes, official MD5 `b8369cb5c06bcf984ef8057198683250`. The local input stays under ignored `data/raw/triangle-gb/` with its original filename. Download provenance includes local SHA-256 and actual timestamps. Six disjoint HTTP ranges support resumable segments; assembly is renamed only after full size and MD5 checks.

The preparation script scans every dataset in bounded blocks, records compound-field shapes/dtypes and full numeric NaN/Inf counts, and specifically checks the original default `/sky/dgb/cat` and `/sky/dgb/tdi` inputs. Optional fields outside the required default data are reported separately if they contain nonfinite values.

The original notebook defaults to `GB_TYPE="dgb"`, whose catalog contains 26 million sources. Its supported `../Test/dgb_parameters.txt` cache is prepared for **all catalog rows**, with exactly the eight original columns: `A, f0, fdot0, phase0, inclination, longitude, latitude, psi`. This is not a selected-frequency subset or reduced-source approximation. Streaming preparation avoids hundreds of millions of scalar HDF5 reads and the fallback's large Python lists. The unchanged notebook loads its normal text-cache branch; every loaded field is compared with the complete catalog in blocks. The original cell 15 polarization and phase convention changes occur after cache loading; cached values stay in original catalog convention. Cache and raw data are both local/ignored.

The checker executes only unchanged non-plot preparation/interface cells, including original channel conversion, FFT, source selection, response initialization and selected-bin template generation. Executed cell hashes, time grid, original source count/bin selection, template shape and orbit coverage are recorded. Default LDC orbit files contain 1,827 daily rows and span approximately five years; the observed one-year grid (5 s cadence) and sparse endpoint are checked against the actual range. Negative delayed start-boundary queries are disclosed, not declared physically exact simply because extrapolation is finite.

Commands from repository root:

```bash
python3 scripts/reproduction/download-triangle-gb-sangria.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/prepare-triangle-gb-sangria.py
```

The full parameter cache is several GB and full-size load/FFT preparation uses significant RAM. Preparation timings are recorded independently of a full notebook run. See `results/triangle-gb/sangria/` for actual completion status.

## Triangle-BBH and Fisher

`Triangle_BBH.__init__` automatically imports every package module. `Waveform.py` unconditionally imports WF4Py, so the pinned repository's bundled `WF4Py/` is installed **before** Triangle-BBH. Both editable packages are installed with `--no-deps --no-build-isolation` after the locked scientific environment. They add no unpinned external Python dependencies. CuPy and BBHx are optional guarded imports on this CPU path; no CUDA backend is needed for the GB Fisher interface. All autoloaded modules and `from Triangle_BBH.Fisher import MultiChannelFisher` are checked directly.

Validation includes a correlated two-channel problem with analytic derivatives, independent expected Fisher matrix and inverse covariance, finite positive marginal errors, and automatic finite-difference step tuning. It also executes the original network notebook's preparation/Fisher/prior cells (0, 2, 4, 5, 7, 9, 11, 13, 15, 17) at its original four-year grid. Likelihood scans (cell 18), nested sampling (cell 20) and posterior plotting (cell 21) were not executed during this prerequisite check; the later [network reproduction](network.md) executed the complete notebook. Raw-unit Fisher condition warnings remain in logs; finite errors do not alone establish numerical conditioning or posterior coverage. Priors are sampled to check their finite outputs.

The original network notebook enables `text.usetex=True`. Actual LaTeX PNG rendering is validated using the existing local TinyTeX `latex` and `dvipng`, not by disabling the original setting. Local executable paths are recorded. Rebuilding elsewhere requires a suitable TeX installation on PATH.

```bash
python3 scripts/reproduction/audit-triangle-bbh-source.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/check-triangle-gb-fisher.py
```

## Unchanged notebooks and local path handling

The canonical `external/triangle-gb/` still contains both `Examples/` and `Triangle_GB/`. Ignored working copies use the same layout under `runs/triangle-gb/workspace/Triangle-GB/`; all five filenames and all source/Markdown cells are checked equal to upstream. Only copied historical outputs/execution counts are cleared and the kernel metadata points to the dedicated environment. Working copies are never overwritten if they already exist; changed source/Markdown triggers an explicit check failure.

The working tree has the original `Examples/LDCEqualArmOrbit` path and sibling `Triangle-Simulator` orbit path via links, plus the original `../Test/` cache directory. A dedicated IPython startup hook maps only the three exact author-specific HDF5 paths to verified local inputs. It uses an `h5py.File` subclass so the notebook's `isinstance(obj, h5py.File)` structure printer still works. The mapping is external to all notebook cells, applies only to the dedicated launcher/kernel, and records local mapping events in ignored output. No directories are created in the original author's home.

```bash
bash scripts/reproduction/launch-triangle-gb-jupyter.sh
```

Select the same-name working notebook and the **Triangle-GB — Python 3.11.14 (CPU)** kernel. The launcher sets the dedicated IPython directory so the path hook is active. Opening notebooks through a different Jupyter installation without this hook will not automatically resolve the author's absolute paths. Checksum/schema evidence and source audits remain separate from future fresh execution evidence.

## What remains for full reproduction

Examples 1/2 retain the original default orbit boundary extrapolation documented in `data-preparation.md`. The frequency-domain method discards its final sparse endpoint, but start-boundary extrapolation and scientific accuracy remain distinct checks. The input-coverage gap is not silently changed to a pass by this milestone.

Search runtime, multiprocessing pools, original-scale nested sampling and posterior convergence still need per-notebook execution and review. On a 16 GB laptop, original `npool=cpu_count()` can multiply process memory; choose and document a resource budget before long sampling rather than promise all defaults fit. These are execution concerns, not missing datasets or missing Fisher imports. No sources, time grids, network configurations or sampler settings are reduced in the prerequisite evidence.

## Actual final evidence

Sangria size and MD5 match the official metadata. Local SHA-256: `f54ca61355d0c6208fbea5fc1b2dcce7332025de264fef33ebe87dea657c7ee6`. First download/assembly/checksum time was 739.082 s. Complete scan/cache/original input-interface preparation took 95.773 s. These timings do not measure full notebook reproduction. All numeric fields in the scanned file were finite; optional nonfinite-field list is empty.

Measured Sangria grid: **5 s cadence**, **6,307,200** samples, **0 to 31,535,995 s**, approximately one year. The default nominal sparse endpoint is **31,536,000 s**, within the LDC orbit end **157,766,400 s**. Starting delayed queries reach **-25.017307 s** and require approximately 25 s of boundary extrapolation. Coverage statements use measured timestamps, not an assumption that the sampling interval matches the VGB files.

Complete original cache: **26,000,000 x 8** values, **5,218,391,053 bytes**, SHA-256 `38177fda2a108b1076055237e737a4d2a3ef03ce5aeba7994e87014f138aa3c3`. Every loaded column matches the full source catalog exactly before the original convention transforms. The original selected band contains **39** sources, and the finite template/data band shapes match at `[2, 315]`.

Fisher checks: **4/4 passed**, including unchanged original network Fisher/prior cells; all eight reported errors are finite and positive. The raw-unit original network Fisher condition number is **1.338e+49**. Its original warning is preserved; this check does not certify covariance conditioning or posterior agreement. At this preparation milestone, full scans and sampling had not run. All five examples have since executed; see [current reports](README.md) for their results and numerical limitations.

Latest consolidated status is in `results/triangle-gb/prerequisites/readiness.json`. Five same-name source/Markdown-preserving working notebooks and the kernel's actual three author-path opens are checked. Large inputs/cache remain local and ignored.
