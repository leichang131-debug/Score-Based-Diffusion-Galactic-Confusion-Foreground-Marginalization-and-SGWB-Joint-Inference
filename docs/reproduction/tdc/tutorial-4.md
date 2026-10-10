# Tutorial 4: original-default scientific-data simulation reproduction

Completed locally on 2026-10-10 with a fresh **Python 3.9.19 ARM64 CPU kernel on Apple M5 / 16 GiB**. All **31 nonempty code cells** in the original 58-cell notebook executed successfully. Its exact filename, all code, Markdown and attachments remain unchanged. The pinned Triangle-Simulator source commit is `ab796358e9a36c8987f6bb53a97230d603bfdfd5` and its checkout is clean. Tutorial 5 was not executed.

[Executed notebook](../../../notebooks/reproduction/triangle-simulator/Tutorials/4_Demo_Simulation_for_Scientific_Data_Analysis.ipynb) · [Evidence](../../../results/tdc/tutorial-4/) · [Audit](../../../results/tdc/tutorial-4/audit.json) · [Live local processes](../../../results/tdc/tutorial-4/local-processes.json)

## Scope and code-to-result correspondence

| Original cell indices (zero-based) | Original computation | Saved evidence |
| --- | --- | --- |
| 5–23 | 10-day, 0.1 Hz joint interferometer simulation; GB + MBHB + supplied EMRI + 300 SGWB directions; synchronization and fast Michelson A/E/T | `combined-diagnostics.json` |
| 25, 27 | A₂/E₂/T₂ time series and Hann-window ASD, cropped by 100 samples at both ends and divided by `F_LASER` | Two generated PNGs |
| 29–36 | 100-day, 10 s spacing, CPU fast X₂ response for 100 randomized GBs; plot first 10 | `fast-gb-diagnostics.json`, GB figure |
| 38–42 | Fast MBHB X₂ response, `IMRPhenomT`, chirp mass 400,000, coalescence at day 50 | `fast-mbhb-diagnostics.json`, merger figure |
| 44–48 | Fast EMRI X₂ response using supplied waveform and original random extrinsic orientation | `fast-emri-diagnostics.json`, EMRI figure |
| 52–56 | X₂/A₂ sensitivity at a random orbit snapshot; 512 frequencies from 10⁻⁴ to 1 Hz | `sensitivity-diagnostics.json`, `sensitivity.npz`, sensitivity figure |

The joint simulation has **86,400 samples**, interpolation order **31**, six workers, acceleration/readout noise enabled and the original remaining noise flags. Its **303 GW objects** are one GB, one MBHB, one EMRI and 300 SGWB directions. `default_noise=True` selects the default-noise branch; the alternative rescaled-noise/glitch branch is preserved but **not executed**. The first MBHB initialization uses `SEOBNRv4_opt` with coalescence at day 5; the later fast-response example uses `IMRPhenomT` at day 50. These are two distinct examples.

Fast-response examples retain **864,000 samples each**, `drop_points=100`, `use_gpu=False`, linear interpolation for GB and `linear_interp=False` for MBHB/EMRI. The GB pool uses unchanged `cpu_count()`, which was **10** locally. The original explicit `multiprocessing.set_start_method("fork")` ran successfully. The earlier six-worker pool and the additional original pool creation were retained. No source patch or scale reduction was required.

All six synchronized links and the three joint TDI arrays are finite with the expected size. All 100 GB response arrays and both MBHB/EMRI response arrays are finite with 864,000 samples. Full arrays are checked and hashed; they are not uploaded as bulk time-series files. GB injection parameters and MBHB fast-response parameters are recorded in diagnostics. EMRI random orientation is not separately exported in this run; no exact random-seed replay is claimed.

## Actual local timing and resources

Measured total elapsed time: **41.64 seconds**, including kernel startup, original cells, separate probes and cleanup. This is a direct measurement, not a planning estimate.

| Operation | Cell | Measured seconds |
| --- | --- | --- |
| Generate 300 SGWB directional waveforms | 16 | 5.40 |
| Joint interferometry and synchronization | 21 | 10.91 |
| Joint Xi/Eta and fast Michelson | 23 | 0.54 |
| Prepare GB fast-response generator | 31 | 2.11 |
| Parallel responses for all 100 GBs | 35 | 10.10 |
| MBHB fast response | 41 | 1.21 |
| EMRI fast response | 47 | 1.71 |
| Both sensitivity curves | 56 | 0.40 |

Sampled process-tree RSS sum peaked at **13.42 GiB**. The monitor samples every two seconds and sums runner/kernel/descendant RSS; fork-shared pages may be counted repeatedly and brief peaks may be missed. This is not unique physical memory usage. No memory error or kernel failure occurred. `local-processes.json` captures the actual M5 hardware, 17,179,869,184 bytes of RAM, live runner/kernel/six worker PIDs, elapsed times and CPU/RSS during the joint simulation. The original parallelism is unchanged.

## Output interpretation and limits

All six generated plots were visually inspected. The joint time plot includes the day-5 MBHB feature; the ASD plot spans the original sampled band ending at 0.05 Hz. The GB plot displays the first 10 individual responses, **not their sum** and not a full Galactic confusion population. The MBHB plot resolves the day-50 merger. The EMRI plot retains the original day-80 to day-80.5 interval and `hc=-h2` convention.

The sensitivity curves are positive and finite. Their 512-frequency grid extends to 1 Hz: this is a separate theoretical sensitivity calculation, not data measured above the joint simulation's Nyquist frequency. `TDISensitivity.TDI_sensitivity` retains its original **1,024-direction Monte Carlo default per curve**. X₂ and A₂ use separate finite direction averages at the same random orbit snapshot, so small Monte Carlo differences are expected. The saved NPZ contains the underlying sensitivity values, before the square root plotted by the original code.

The notebook demonstrates joint data generation and response/sensitivity methods. It does **not** perform SGWB parameter inference, diffusion training, foreground marginalization, realistic population synthesis or posterior calibration. Random instrument noise, SGWB realizations, GB parameters, EMRI orientations and sensitivity averaging need not match the original images pixel-for-pixel. Reference image comparison is observational, not a numerical validation criterion.

## Provenance and rerunning

```bash
environments/tdc/.venv/bin/python scripts/reproduction/run-tdc-tutorial-4.py
environments/tdc/.venv/bin/python scripts/reproduction/audit-tdc-tutorial-4.py
```

The runner clears all original outputs/counters in a copy, then executes the unchanged cells in sequence in upstream `Tutorials/` so the original relative input paths resolve. Separate numerical probes and pool-reference/cleanup probes are executed outside the saved tutorial cell list; they consume counters, explaining gaps. They introduce no random draws or replacement tutorial algorithms. Only outputs, timing metadata, counters and kernelspec change. The source notebook and source modules remain untouched.

Evidence includes regenerated notebook/PNGs, per-cell timings, sampled resources, console log, live process snapshot, numerical shape/finite/hash diagnostics, sensitivity arrays and file manifest. `reference/` explicitly contains copied original output images for comparison; it is never used as local execution output. Original static Markdown content is unchanged; this tutorial has no linked static figure to copy. Upstream materials retain GPL-3.0 attribution. Optional-backend notices and original warnings remain visible in notebook outputs; no required computation failed.

Tutorials **1–4 are now complete at original defaults**. Tutorial 5 remains excluded following teacher guidance.
