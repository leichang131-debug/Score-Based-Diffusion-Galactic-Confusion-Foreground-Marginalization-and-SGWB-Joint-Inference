# Triangle-Simulator shared environment setup

Current scope update: Tutorial 1 completed at original scale; see [report](tutorial-1.md). Tutorials 2–4 remain pending. Tutorial 5 is excluded following teacher guidance. The setup notes below retain the earlier environment-only validation scope.

## Outcome and scope

The shared macOS ARM64 CPU environment is installed for all five tutorial notebooks at upstream commit `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. The source is unchanged, including its five notebooks, example waveforms, orbit data and GPL-3.0 license. Setup and smoke checks passed on 2026-10-10. **Full tutorial execution and scientific output reproduction have not yet been performed.**

Tutorial 5 additionally requires external TDC II challenge data. Teacher confirmation of that file is pending; environment readiness does not imply dataset readiness.

## Environment

| Component | Installed version |
| --- | --- |
| CPython | 3.9.19, native ARM64 |
| uv | 0.12.19 |
| NumPy / SciPy | 1.26.4 / 1.13.1 |
| Matplotlib / healpy | 3.9.4 / 1.17.3 |
| PyCBC / LALSuite | 2.7.2 / 7.25.1 |
| Astropy / h5py | 6.0.1 / 3.13.0 |
| JupyterLab / ipykernel | 4.4.1 / 6.29.5 |
| Triangle | 0.1.0, editable pinned source |

All 136 installed distributions passed `uv pip check`. Scientific and transitive versions derive from upstream `uv.lock`, exported with `--locked --no-dev --no-emit-project`, then installed without modifying upstream. Requirements include artifact hashes and conditional markers. Package downloads used the installer's default PyPI endpoint; the versions/hashes remain upstream-locked. Some transitive packages built from source successfully. The editable project build was isolated; Triangle runtime dependencies were not re-resolved. The installed manifest records the applicable Python 3.9/macOS selection rather than every alternative in the universal lock.

Environment disk use measured approximately 676 MB; standalone Python approximately 52 MB; installation cache approximately 693 MB. Measurements can grow with subsequent work and are not peak RAM measurements. No GPU backend is installed. Existing Score-SDE Python 3.12 environment and results were left intact.

## Validation evidence

See [machine-readable validation](../../../results/tdc/environment/validation.json), [console log](../../../results/tdc/environment/validation.log), [installation log](../../../results/tdc/environment/install.log), [dependency compatibility log](../../../results/tdc/environment/pip-check.log), and [installed versions](../../../environments/tdc/installed-macos-arm64.json).

Checks cover:

1. Exact Python architecture/version and source commit; clean source checkout; five notebook hashes and upstream lock/requirements hashes.
2. All Triangle modules and required scientific, Jupyter and waveform-library imports, with Triangle loaded from the pinned editable checkout.
3. FFT roundtrip, interpolation and non-interactive plot output using a synthetic sinusoid.
4. Actual PyCBC/LAL time-domain generation with **IMRPhenomT** and **SEOBNRv4_opt**, both finite and nonempty. Small stellar masses were used to test backend availability quickly; this is not a test of tutorial MBHB response accuracy.
5. Every bundled numeric orbit `.dat` and GW `.npy/.npz` file read with finite values; file shapes/sizes/SHA-256 recorded.
6. Real Triangle orbit construction and six positive, finite light-travel-time functions evaluated within the supplied time range.
7. A synthetic six-link `eta` HDF5 roundtrip through the actual Triangle reader. This does not validate the missing challenge dataset or full preprocessing.
8. A two-worker macOS `spawn` process pool. This is a generic multiprocessing check, not validation of every Triangle pool operation.
9. A fresh registered Jupyter kernel executing NumPy/Triangle imports in the upstream Tutorials directory.

The final check suite passed all **10 checks** in approximately **3.0 seconds** with the font cache already present. JupyterLab configuration was also initialized successfully: the repository is the browser root, Tutorials is the opening page, and its data/config/runtime paths stay inside the project. Initialization needs localhost sockets, so it was checked outside the tool sandbox. No persistent server was left running.

The first validation took approximately **91.4 seconds**, including initial matplotlib font-cache creation. Final validation runtime and per-check timings are in `validation.json`. Dependencies prepared in 16.08 seconds and installed in 0.325 seconds after resolution (installer's timings, excluding Python/source download and later validation).

## Notices and resolved setup issue

- The first full-history Git clone failed with an interrupted transfer (`curl 18`, early EOF). A shallow clone succeeded. It preserves the entire pinned source tree, not historical commits; use an explicit fetch/unshallow later if history is needed.
- `PyCBC.libutils: pkg-config call failed, setting NO_PKGCONFIG=1` is a runtime library-discovery fallback on this machine. Both required waveform backends subsequently passed; no source patch was made.
- `No phenomxpy.`, `No pyseobnr.` and `no cupy` are upstream notices for optional packages. These are not required for the checked CPU tutorial paths. Other waveform families or GPU paths remain unvalidated.
- Legacy transitive dependency metadata produced uv version-specifier normalization warnings. Installation and compatibility checks succeeded; these warnings are retained in the install log.
- Upstream notebook multiprocessing and full dataset memory loads are not exercised by installation. Keep default science configurations unchanged in the reference source. If local reductions are needed, use separately recorded working copies and distinguish smoke runs from original-scale reproduction.

## Start working

From the research repository root:

```bash
bash scripts/reproduction/launch-tdc-jupyter.sh
```

Choose **Triangle TDC — Python 3.9.19**, then start Tutorial 1 in a working copy. A working-copy notebook normally starts its kernel in its own directory. Set its working directory to upstream `Tutorials/` with an absolute `%cd` in the copy, so relative input paths resolve. Preserve clean reference notebooks by saving executed copies under ignored `runs/tdc-tutorials/` and publishing curated evidence separately. See [environment README](../../../environments/tdc/README.md) for installation and validation commands.

## Tutorial-specific readiness

| Notebook | Environment/data status | Still to validate |
| --- | --- | --- |
| 1: Laser interferometry and TDI | Imports and supplied orbit ready | Full noise/interferometry/TDI execution and suppression diagnostics |
| 2: Advanced noise and TDI | Imports and supplied orbit ready | Glitch and alternative TDI runs, comparison and memory use |
| 3: GW injection | GB/MBHB/EMRI/SGWB dependencies and example data ready | Original response runs, all signal types, full-size memory/runtime |
| 4: Scientific data analysis | Required CPU waveform backends ready | Combined simulation, TDI/response and sensitivity outputs |
| 5: TDC preprocessing | HDF5 reader and processing modules available | External file/path/units/channel schema; real preprocessing after teacher confirmation |

The Tutorial 5 hard-coded external `MBHB_EHM.h5` path is not portable and the file is not supplied by this upstream checkout. Confirm file retrieval, six-link `eta` units, time sampling, matching orbit, duration and expected outputs before execution. Do not substitute synthetic data and label it challenge reproduction.
