# Tutorial 3: original-default GW injection reproduction

The third Triangle-Simulator tutorial completed locally on **2026-10-10**, using a fresh Python 3.9.19 ARM64 CPU Jupyter kernel on the user's **Apple M5 with 16 GiB RAM**. All 26 nonempty code cells ran without an execution error. The original filename, all 57 cells' source/Markdown and the static GW injection illustration were preserved. The pinned upstream checkout at `ab796358e9a36c8987f6bb53a97230d603bfdfd5` remains unchanged.

[Executed notebook](../../../notebooks/reproduction/triangle-simulator/Tutorials/3_Demo_GW_Injection.ipynb) · [Evidence](../../../results/tdc/tutorial-3/) · [Audit](../../../results/tdc/tutorial-3/audit.json) · [Live local processes](../../../results/tdc/tutorial-3/local-processes.json)

All **28 audit checks passed**. The regenerated GB time/FFT and MBHB figures are byte-identical to their deterministic upstream counterparts; the four random-orientation/SGWB/Monte Carlo figures differ. This is an observed comparison, not an execution test: local kernel timestamps, per-cell logs and live processes independently document actual computation.

## Original configuration and measured execution

| Stage | Duration / rate | Samples | Interpolation order |
| --- | --- | --- | --- |
| GB | Source `YEAR` / 0.1 Hz | 3,155,814 | 15 |
| MBHB | 10 days / 1 Hz | 864,000 | 15 |
| EMRI | 10 days / 0.1 Hz | 86,400 | 15 |
| SGWB | 15 days / 0.1 Hz | 129,600 | 11 |

Source `Triangle/Constants.py` defines `YEAR = 31558149.763545603` seconds. The run retained that exact constant, not an assumed Julian-year or 365-day replacement. All stages retain the original six workers, `clean_memory=True`, source parameters, waveform choices, interpolation settings and noise switches. No duration, sky resolution or waveform parameters were reduced. No additional random seed was imposed.

Total wall time was **127.95 seconds (about 2 minutes 8 seconds)**, including kernel setup, execution, separate diagnostic probes and cleanup. Selected original cell measurements:

| Operation | Cell index (zero-based) | Seconds |
| --- | --- | --- |
| One-year GB interferometry and synchronization | 12 | 67.76 |
| GB Xi/Eta and A/E/T combination | 14 | 14.63 |
| Actual MBHB waveform initialization, IMRPhenomT | 22 | 0.17 |
| MBHB interferometry and synchronization | 25 | 6.49 |
| MBHB TDI | 27 | 2.38 |
| EMRI interferometry, synchronization and TDI | 36 | 0.84 |
| Generate 300 SGWB directional waveform pairs | 43 | 8.24 |
| SGWB interferometry and synchronization | 45 | 17.22 |
| SGWB XYZ TDI | 47 | 0.30 |
| 1,024-direction response average | 50 | 0.92 |

The first-run timing is a measurement, not an assumed performance estimate. The previous 45–150 minute planning range was overly conservative and is superseded for this completed local run. It does not establish the fourth tutorial's runtime.

Sampled process-tree RSS sum peaked at approximately **7.01 GiB**. Sampling interval was two seconds, covering the runner and descendants. Shared pages may be counted repeatedly and transient peaks may be missed; this is not unique physical RAM. No memory or kernel execution error occurred. `local-processes.json` records the real M5 identity, physical memory, local runner/kernel/worker PIDs and a live CPU/RSS snapshot during execution.

## Code-to-output correspondence

| Original cells | Workflow | Local figures / diagnostics |
| --- | --- | --- |
| 7, 9, 12, 14, 16, 17 | GB waveform, six-link response, interferometry, synchronization, A/E/T and time/FFT plots | `gb-diagnostics.json`; `cell-16-output-1.png`, `cell-17-output-1.png` |
| 20, 22, 25, 27, 29 | Original massive-binary IMRPhenomT waveform and A/E/T response | `mbhb-diagnostics.json`; `cell-29-output-1.png` |
| 32, 34, 36, 37 | Supplied EMRI waveform with original random extrinsic orientation | `emri-diagnostics.json`; `cell-37-output-1.png` |
| 41, 43, 45, 47, 48 | SGWB directional waveforms, summed link responses, XYZ TDI and spectra | `sgwb-diagnostics.json`; `cell-48-output-1.png` |
| 50, 51 | Response average over 1,024 random directions versus low-frequency equal-arm approximation | `cell-51-output-1.png`; saved response arrays |
| 53 | Convert XYZ to A₂; compare measured PSD with both theory curves | `cell-53-output-1.png`; `sgwb-spectra-selected.npz` |

Underlying implementations remain in the unchanged upstream `Triangle/GW.py`, `Interferometer.py`, `Data.py`, `FFTTools.py`, `Orbit.py`, `TDI.py`, `Noise.py` and `Cosmology.py`. Project-owned runner/audit scripts do not replace any of these methods.

Before execution, the runner removes original computation outputs and execution counters from an in-memory copy. It executes original cells in order through the installed local kernel, with working directory at upstream `Tutorials/` so all original input paths resolve. Separate probes after GB/MBHB/EMRI plots and after the SGWB section capture numerical evidence; they are not saved as tutorial cells and do not draw new random values. They consume execution counters, so gaps in the notebook's counters are expected. Output, execution/timing metadata and kernelspec change; all original cell sources remain identical.

## Observations and scientific limits

**GB:** All six link responses and A₂/E₂/T₂ arrays are finite with 3,155,814 samples. The first plot shows annual amplitude modulation; the original narrow FFT window displays a modulated line near the source's 0.00984299 Hz. Within that original plotting window, strongest A₂/E₂ bins are approximately 0.0098426804/0.0098427121 Hz. A source frequency is not necessarily the strongest individual modulated detector-frequency bin. T₂ is much weaker in this example. This is one binary, not a simulated Galactic confusion population.

**MBHB:** The actual tutorial chirp mass, mass ratio, spins, distance, orientation and `IMRPhenomT` backend were used; this is not the earlier small stellar-mass environment smoke check. Coalescence time remains 432,000 s. The largest cropped A₂ excursion occurs at 432,069 s, in the original plotted merger interval. All channels are finite with 864,000 samples. Detector-response extrema need not equal the prescribed waveform coalescence time.

**EMRI:** The supplied `Demo_EMRI_waveform_data.npz` is read with the original `hc=-h2` convention. Its file hash is recorded. The run computes the detector response, not a new intrinsic EMRI waveform. The original randomized longitude/latitude/psi are recorded in `emri-diagnostics.json`; these random orientations explain differences from the reference time plot. All channels and link arrays are finite with 86,400 samples.

**SGWB:** The run retains `NSIDE=5`, 300 sky directions and two independently generated polarizations per direction, with the original `1/sqrt(NPIX)` normalization and spectral function. The unmodified simulation builds six-link responses and XYZ TDI, then A₂ for PSD comparison. All XYZ/A₂ arrays, measured PSD and response functions are finite. The Monte Carlo response uses the original 1,024 random directions and 10,000-frequency grid at the 7.5-day orbit snapshot.

| Frequency band (Hz) | Bins | Median measured A₂ PSD / interpolated “precise” theory |
| --- | --- | --- |
| 0.0003–0.001 | 91 | 1.013 |
| 0.001–0.003 | 259 | 0.991 |
| 0.003–0.01 | 906 | 1.004 |
| 0.01–0.03 | 2,589 | 1.004 |

The theory uses the original `2 * Response_precise * S_SGWB` normalization. Diagnostic ratios interpolate the theory onto measured positive-frequency bins; no notebook plot or estimator is changed. The ratios support single-realization consistency over these bands, not exact equality at every frequency or ensemble calibration. “Precise” is the upstream curve name: it still uses a finite directional average and fixed orbit snapshot, not an exact time-dependent response. The low-frequency equal-arm approximation departs at higher frequency, as in the original plots. Theory drawn beyond the 0.05 Hz Nyquist limit is not measured simulation data.

All instrument-noise switches are off in these original GW-only simulations. The instrumental-noise curve in the SGWB figure is a theoretical overlay, not noise included in the generated data. This tutorial does not yet simulate a full Galactic foreground plus SGWB plus instrument-noise mixture, nor perform parameter inference.

All seven figures were inspected. Their ordering, labels, plotting scales and qualitative behavior match the original tutorial. Random SGWB, EMRI orientation and response Monte Carlo outputs are not expected to be pixel-identical to reference images; deterministic figures may agree exactly. `reference/` images are copied upstream comparisons, explicitly separate from the locally executed notebook's outputs.

## Evidence and repeatability

```bash
environments/tdc/.venv/bin/python scripts/reproduction/run-tdc-tutorial-3.py
environments/tdc/.venv/bin/python scripts/reproduction/audit-tdc-tutorial-3.py
```

Rerunning intentionally overwrites this tutorial's local result paths and creates new random realizations. The runtime kernel uses upstream `Tutorials/` as its working directory; for manual execution of the saved copy, establish this externally before its original cells.

Curated evidence contains the same-name executed notebook with real kernel timestamps, seven generated PNGs, original comparison PNGs, console logs, per-cell timing, sampled RSS, live local process/hardware snapshot, stage-specific array hashes/finite-value checks and a spectral subset plus full 10,000-point response curves. Full time series are checked and hashed but not uploaded as bulk arrays. The manifest hashes source modules, orbit inputs, EMRI input, scripts, report and saved artifacts. Static illustrations and copied upstream materials retain GPL-3.0 attribution.

The original optional-backend notices (`phenomxpy`, `pyseobnr`, CuPy) and any original warnings remain in notebook outputs. No required backend or execution step failed. Completion means original-default GW injection/response tutorial reproduction on one realization, not inference convergence or statistical calibration.

Tutorials 1–3 are complete. Tutorial 4 remains pending; Tutorial 5 is excluded following teacher guidance.
