# Tutorial 2: original-default reproduction

The second Triangle-Simulator tutorial completed locally on **2026-10-10** in a fresh macOS ARM64 CPU kernel. Its original filename, all code/Markdown cells and static illustration were preserved. All 14 nonempty code cells ran without an error. The upstream source remains unchanged at `ab796358e9a36c8987f6bb53a97230d603bfdfd5`.

[Executed notebook](../../../notebooks/reproduction/triangle-simulator/Tutorials/2_Demo_More_Advanced_Noise_and_TDI_Simulation.ipynb) · [Evidence](../../../results/tdc/tutorial-2/) · [Source/output audit](../../../results/tdc/tutorial-2/audit.json)

## Configuration and timing

All three simulation sections retain **100,000 seconds at 4 Hz (400,000 samples)**, six workers and interpolation order 31. The first two sections retain `clean_memory=False`, and the final simulation retains `clean_memory=True`. Orbit start is `10 * DAY`. Spectral boundaries discard 4,000 samples (1,000 s) per end. Modified-noise spectra use the original Kaiser beta=28, nbin=4; method-comparison spectra use nbin=1. No extra seed or scientific parameter changes were imposed. Python is 3.9.19 in the shared locked CPU environment.

Total wall time was **33.26 seconds**, including kernel startup, separate evidence probes and cleanup. The modified-noise simulation/TDI cell took 8.24 s, glitch simulation/TDI 6.61 s, final interferometer simulation/synchronization 5.21 s and four-method TDI calculation 7.84 s. All individual timings and kernel output timestamps are saved.

Sampled process-tree RSS sum peaked at **4,863,840 KiB (4.64 GiB)**. Samples are taken every two seconds for the runner and descendants. Shared pages may be counted repeatedly and transient peaks missed; this is not unique physical RAM. The measured runtime supersedes the earlier conservative 20–60 minute estimate for this tutorial only.

## Correspondence and observations

Indices below are zero-based upstream cell indices.

| Cells | Original workflow | Evidence |
| --- | --- | --- |
| 9, 11 | Generate noises, multiply each link's carrier readout noise by its original random 1.5–2.5 factor; build X2 and plot against nominal theory | `noise-diagnostics.json`, `noise-spectra-selected.npz`, `cell-11-output-1.png` |
| 13, 15 | Clear original acceleration noise; inject LPF legacy glitch in test mass 12 at 30,000 s; simulate X2 and plot | `glitch-diagnostics.json`, `glitch-window.npz`, `cell-15-output-1.png` |
| 17, 19, 20 | Define operator strings, cyclic Y/Z and A/E/T combinations | Original notebook outputs retained through local execution |
| 22, 24, 26 | Simulate noise with laser noise; compute X2 via name, fast Michelson, optical paths and operator strings; plot differences | `diagnostics.json`, `method-spectra-selected.npz`, `cell-26-output-1.png` |

The unchanged operations use `Triangle/Interferometer.py`, `Data.py`, `Noise.py`, `Glitch.py`, `FFTTools.py`, `Orbit.py` and `TDI.py`. No library method or notebook cell was patched. The external runner adds separate evidence-only probes after cells 11/15 and after the tutorial; these are absent from the saved notebook. They inspect existing arrays and recompute deterministic method spectra without generating additional random draws. Probe execution consumes counters, so execution numbers contain gaps. Kernelspec/timing metadata and outputs are the only intended changes.

### Modified noise

Six modified readout arrays and X2 are finite with 400,000 samples each; their hashes are saved. The modified ASD lies above the nominal secondary-noise curve where readout noise matters, consistent with the original demonstration. In 0.01–0.1 Hz, the median measured ASD/nominal ASD is **1.977**. This is a descriptive value for one stochastic realization, not an inferred scaling parameter or ensemble calibration. The individual random multipliers are not stored by the original code and were not reconstructed or invented.

### Glitch

The injection is at **30,000 s** and the largest absolute cropped X2 excursion occurs at **30,040.25 s**, with fractional-frequency amplitude **6.5651e-21**. Injection time is not necessarily the peak time of the delayed TDI response. The local plot shows the original bipolar transient. Acceleration, injected fractional-frequency noise and resulting X2 arrays are finite. The saved 8,001-sample window spans injection time plus/minus 1,000 s at the original cadence.

### Four TDI implementations

Method 1 (channel name) and method 3 (optical-path strings) are **bitwise identical across all 400,000 samples** in this run, matching the original comment that their zero difference is not visible on a log plot.

Methods 2 (fast Michelson) and 4 (operator strings) are not bitwise equal to method 1. Their difference ASDs are small over the useful lower-frequency band:

| Frequency band (Hz) | Median method-2 difference ASD / method-1 ASD | Median method-4 difference ASD / method-1 ASD |
| --- | --- | --- |
| 0.001–0.01 | 2.52e-6 | 2.72e-6 |
| 0.01–0.1 | 1.78e-7 | 2.31e-7 |
| 0.1–0.3 | 4.59e-8 | 5.86e-8 |

Near the upper end of the plotted band, differences rise sharply; the upstream reference plot shows the same behavior. This is consistent with differing numerical delay/interpolation implementations, but this run does not isolate every error contribution. **Full-band relative time-domain RMS differences are 0.904 and 1.000**, respectively. Therefore, this report does not claim all four implementations agree across the entire Nyquist band. It reproduces the original plot, verifies finite arrays and records the frequency-dependent limitations rather than hiding them with changed parameters.

**All 20 audit checks passed**, including exact cell sources, static-image identity, finite outputs, original scale, bitwise method-1/method-3 equality and exported images matching the executed notebook. All three local image byte streams differ from their upstream reference counterparts in this run; image differences alone are not proof of execution, which is also documented by kernel timestamps, logs and RSS samples.

All three locally generated figures were visually inspected against the original figures. Reference images under `reference/` were extracted only for comparison. They are not the executed notebook's outputs. Source/static images retain upstream GPL-3.0 attribution.

## Evidence and rerunning

```bash
environments/tdc/.venv/bin/python scripts/reproduction/run-tdc-tutorial-2.py
environments/tdc/.venv/bin/python scripts/reproduction/audit-tdc-tutorial-2.py
```

The runner intentionally overwrites its local result paths on another run. A new random realization changes outputs and hashes. Kernel working directory is upstream `Tutorials/`; original relative input paths remain intact. For manual rerunning of the saved copy, establish that working directory externally before running its original cells.

Saved evidence includes all three PNG figures, notebook outputs with kernel execution timestamps, console log, per-cell timing, sampled RSS, finite-value/shape checks, array hashes, selected spectral bins and a glitch time window. Spectral subsets use selected indices, not additional smoothing; notebook figures use original full spectra. Full time-series arrays are checked and hashed but not published as bulk data. The manifest includes upstream input/module hashes, execution scripts, report, notebook and result files.

Optional `phenomxpy`, `pyseobnr` and CuPy notices are preserved in outputs; no related optional path was used. No notebook execution error occurred. Completion means original-default single-realization tutorial reproduction, not ensemble calibration or an SGWB posterior-inference result.

Tutorials 1–2 are complete. Tutorials 3–4 remain pending. Tutorial 5 is excluded from the current scope following teacher guidance.
