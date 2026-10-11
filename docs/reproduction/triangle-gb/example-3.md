# Example 3: Sangria Galactic-binary frequency-band reconstruction

## Result and source correspondence

The complete unchanged `3_LDC2a_GB_Reconstruction.ipynb` was executed in a fresh local kernel on the ARM64 MacBook Air (Python 3.11.14, NumPy 1.26.4). All **16 nonempty code cells** executed and **four figures** were regenerated locally. The final empty cell remains empty. Upstream computation outputs were cleared before execution; neither old notebook outputs nor the earlier input-preparation results were reused as execution outputs.

Triangle-GB source pin: `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`; Triangle-Simulator: `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. The same-name executed notebook is under `notebooks/reproduction/triangle-gb/Examples/`, retaining all code, Markdown and attachments. Only runtime metadata/counts/timestamps and outputs differ. Canonical sources remain unchanged. The dedicated kernel maps the exact author HDF5 path to verified local data, and the ignored working directory supplies the original relative cache and LDC orbit paths. No original science parameters were changed.

## Original workflow by zero-based cell index

| Cells | Operation and retained settings |
| --- | --- |
| 0, 3–4 | Import original modules, retain the original structure-printer function and open full Sangria HDF5; print real local fields. |
| 6–7 | GB_TYPE='dgb'; XYZ-to-A/E/T, 6,307,200 samples at 5 s cadence; plot the full one-year data. |
| 9–10 | Original Tukey-window FFT (`alpha=10000/(data_time[-1]-data_time[0])`), drop T channel from frequency analysis; plot full A/E spectrum. |
| 12–13 | Original catalog dtype and supported np.loadtxt cache branch; load every row of the 26,000,000 × 8 parameter cache. |
| 15 | Apply original LDC-to-TDC convention: psi += pi/2 and phase0 *= -1, exactly once in this fresh kernel. |
| 17–19 | Select original source closest to 4 mHz, center ±5e-6 Hz, retain 39 sources and 315 frequency bins; plot analyzed band. |
| 22 | Original X/Y/Z TDI strings, bundled LDCEqualArmOrbit, dt=DAY, pn_order=0, default Nsparse=512, CPU. |
| 24–25 | Generate all 39 frequency templates, XYZ-to-A/E, original FFT-bin placement and sum over sources; compare data/template/complex-difference magnitude. |

This is catalog-truth waveform reconstruction in one frequency band. It does **not** search unknown parameters, run a posterior sampler, or reconstruct the full 26-million-source Galaxy. The preceding Example 2 sampling diagnostic warning is independent of this reconstruction stage.

## Inputs and numerical checks

The unchanged original supported cache contains **all 26 million sources**, not a reduced catalog. It retains original pre-conversion fields, in the exact order A, f0, fdot0, phase0, inclination, longitude, latitude, psi. Its entire-catalog round trip was verified during input preparation; this run additionally checks all eight selected fields against HDF5 after the original conversion. No cache values are rewritten by the notebook's in-memory convention change.

Sangria file: `LDC2_sangria_training_v2.h5`, 3,082,321,484 bytes, official/local MD5 `b8369cb5c06bcf984ef8057198683250`, SHA-256 `f54ca61355d0c6208fbea5fc1b2dcce7332025de264fef33ebe87dea657c7ee6`. Complete cache: 5,218,391,053 bytes, SHA-256 `38177fda2a108b1076055237e737a4d2a3ef03ce5aeba7994e87014f138aa3c3`. Both are rehashed after execution; both remain ignored locally.

- Band center: **0.0040001634350846993 Hz** (4.000163435084699 mHz), agreeing with the reference displayed center.
- Selected sources: **39**; frequency bins: **315**; data/template shape: **(2,315)**, matching the original outputs.
- Full time data `(3,6307200)` and full A/E FFT `(2,3153600)`; all checked arrays and selected parameters finite.
- Complex relative L2 differences, A/E: **0.034578646 / 0.026119006** (about 3.46% / 2.61%).
- Combined unweighted mismatch: **0.000467631637459**, independently recomputed from saved complex arrays. This extra diagnostic is outside notebook source; it is not PSD-weighted or a posterior-accuracy metric.
- Saved residual equals data minus template exactly. Final plots were visually compared with the original: peak structure, reconstructed response and residual structure agree; pixel equality is not required across rendering versions.

Nonzero residual is compatible with this selected-band reconstruction: data contain contributions from the full population whereas only sources with catalog frequencies inside the band are regenerated; finite-window spectral tails and response/window approximations can also contribute. Their separate numerical contributions were not measured in this run, so no particular cause or arbitrary residual acceptance threshold is claimed.

## Measured runtime and resources

Runner wall time: **30.475 s**, including fresh kernel startup, all original cells, external numerical diagnostics, figure extraction and final serialization. Complete text-cache loading (cell 13): **24.910 s**. Original template generation and band summation (cell 24): **0.022049 s**; that includes the complete cell, not an isolated generator benchmark.

Sampled peak runner/descendant RSS sum: **3.499 GiB**, measured every 2 seconds; shared pages can be counted repeatedly and instantaneous peaks can be missed. No memory error occurred. File rehashing and evidence audit happen after the timed notebook runner and are not included in that 30.48-second total. The already-prepared cache was read, not regenerated; the earlier approximately 96-second data-preparation process is a separate milestone.

## Preserved presentation and physical caveats

- The original Markdown says psi -> psi - pi/2 while cell 15 adds pi/2. These differ by pi, the polarization-angle period in this model; the executable conversion is preserved. Initial phase is negated according to the original convention, not inferred from the data.
- The final plot multiplies frequency by 1e3 but retains the original `Frequency (Hz)` label; plotted numerical values are mHz. The source is not silently corrected.
- Bundled LDC orbit grid covers the observed year and nominal sparse endpoint. The original delayed-start response query reaches about -25.017 s and extrapolates at the initial boundary; matching the reference reconstruction does not independently validate that extrapolation's accuracy.
- Only original CPU/default response paths and this band are demonstrated. No claim is made about complete full-Galaxy reconstruction, inference calibration, SGWB separation or other detector configurations.

## Evidence and rerun

`results/triangle-gb/example-3/` contains original-cell execution logs, UTC start/per-cell times, resource CSV, four local PNGs, numerical diagnostics/hashes, full selected-band data/template/residual plus 39-source parameters in NPZ, audit and SHA-256 manifest. The evidence links the exact original source and both package pins, environment locks, data provenance and local executed notebook. Bulk HDF5 and full parameter cache remain in ignored directories.

```bash
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-example-3.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-example-3.py
```

Run from the research-repository root with prepared Sangria/cache/orbit paths and loopback socket permission for Jupyter. Use a fresh kernel so the original in-place phase/polarization conversion is applied only once. The final empty cell and all original explanations stay unchanged.
