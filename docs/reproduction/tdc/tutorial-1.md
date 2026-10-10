# Tutorial 1: original-default reproduction

The first Triangle-Simulator tutorial completed successfully on the local macOS ARM64 CPU environment on **2026-10-10**. All original nonempty code cells ran in a fresh kernel without errors. The original filename, cell sources, Markdown and static illustration were preserved. The upstream checkout at `ab796358e9a36c8987f6bb53a97230d603bfdfd5` remains unchanged.

[Executed notebook](../../../notebooks/reproduction/triangle-simulator/Tutorials/1_Demo_Laser_Interferometry_and_TDI.ipynb) · [Evidence](../../../results/tdc/tutorial-1/) · [Correspondence audit](../../../results/tdc/tutorial-1/audit.json)

## Configuration and execution

| Setting | Value |
| --- | --- |
| Python / environment | 3.9.19 ARM64; shared locked TDC CPU environment |
| Offset simulation | `YEAR`, 0.0001 Hz; 3,155 points |
| Offset interpolation order | 15 |
| Fluctuation simulation | 100,000 s, 4 Hz; 400,000 points |
| Interferometer / TDI interpolation order | 31 / 31 |
| Workers | Original `ncpu=6` |
| Spectral estimator | Original Kaiser window, beta=28, nbin=1 |
| Spectral edge removal | 4,000 samples at each end; 1,000 s each |
| Seed | Original behavior; no additional seed imposed |
| Total measured wall time | 28.30 s, including kernel startup, separate probes and shutdown |
| Sum of sampled process-tree RSS peak | 4,779,456 KiB, approximately 4.56 GiB |

RSS was sampled every two seconds for the runner and its descendants. Shared pages may be counted repeatedly, and short-lived peaks may be missed: this is not a measurement of unique physical RAM. These timings supersede the earlier conservative 10–30 minute planning budget for this tutorial; they do not establish runtimes for the larger remaining tutorials.

The main fluctuation simulation and synchronization cell took 13.54 s; Xi/Eta/X2 construction took 2.14 s; clock-noise correction took 5.09 s. All per-cell measurements are in `execution.json`.

## Source-to-result correspondence

Cell indices below are zero-based and refer to the unchanged upstream notebook.

| Cells | Upstream operations | Saved evidence |
| --- | --- | --- |
| 12, 14, 16 | Orbit and offset models; `SimulateInterferometers`, `OutputMeasurements`, `TPStoTCB` | `offset-diagnostics.json`; six finite LTT arrays |
| 18 | Plot six light-travel times | `cell-18-output-1.png` |
| 20 | Plot offset MHz carrier measurements | `cell-20-output-1.png` |
| 22, 23, 25 | Original ClockTime noise simulation and synchronization | Six finite 400,000-point carrier arrays; hashes in `diagnostics.json` |
| 27 | Plot six raw carrier ASDs | `cell-27-output-1.png` |
| 29 | `CalculateXi`, `CalculateEta`, `CalculateBasicTDI(channel="X2")` | Finite 400,000-point X2 array |
| 30 | `CalculateClockTDI(channel="X2")` | Finite X2_q correction and corrected X2 arrays |
| 32 | Plot raw, before/after clock correction and theory | `cell-32-output-2.png`; spectral diagnostics and selected bins |

The upstream implementations remain in `Triangle/Interferometer.py`, `Orbit.py`, `Data.py`, `Noise.py`, `FFTTools.py` and `TDI.py`. No methods or algorithms were replaced. The project-owned runner records timings and executes two separate diagnostic probes in the same kernel without adding them to the saved tutorial. The first probe consumes an execution counter, so saved execution numbers have a gap; code order and content are unchanged. The second probe recomputes deterministic spectra from already generated data, saves diagnostics, and closes the original pool after the tutorial finishes.

The executed notebook only changes outputs, execution counters, timing metadata and the kernelspec identifying the installed environment. Original outputs remain in the pinned reference notebook. Extracted upstream figures under `reference/` are explicitly references, not locally generated results. Their upstream GPL-3.0 attribution is retained.

## Numerical and visual checks

All **15 audit checks** passed: same filename, all 34 cell sources/types, Markdown attachments, static illustration bytes, original scale, clean upstream source, 16 executed nonempty code cells, no error outputs, four generated figures, finite measurements/TDI/spectra and matching saved hashes.

The four generated figures were inspected visually. They show the same labels, scales and physical behavior as the corresponding reference figures. Six light-travel times lie approximately between 9.889 and 10.040 seconds. Frequency offsets retain the original MHz plan and shaded excluded regions. Raw carriers show two nearly noise-free locked links. TDI suppresses the dominant raw noise; clock correction brings the spectrum toward the secondary-noise curve over the useful band. High-frequency interpolation error rises near Nyquist, as described in the original tutorial.

| Frequency band (Hz) | Median raw/corrected ASD | Median corrected/theoretical secondary ASD |
| --- | --- | --- |
| 0.001–0.01 | 3.35e7 | 0.901 |
| 0.01–0.1 | 5.68e6 | 0.822 |
| 0.1–0.3 | 1.40e6 | 0.846 |

These are descriptive ratios from one stochastic realization, excluding theoretical zeros. The unsmoothed periodogram fluctuates; its ASD need not equal the theoretical ensemble ASD pointwise. The ratios support the visual noise-suppression check and are not an ensemble calibration test or an estimate of detector sensitivity. Stochastic curves are not expected to be pixel-identical to the upstream realization.

`spectra-selected.npz` contains 1,326 selected frequency indices from a logarithmically spaced index grid from the full finite 196,000-bin spectra; it is not averaged/rebinned data. Notebook plots use the original full spectra. Full time-series arrays were checked and hashed in the kernel, but are not included in the curated package.

## Run and audit

From the research repository root:

```bash
environments/tdc/.venv/bin/python scripts/reproduction/run-tdc-tutorial-1.py
environments/tdc/.venv/bin/python scripts/reproduction/audit-tdc-tutorial-1.py
```

The runner overwrites its local executed notebook/evidence when intentionally repeated. A new stochastic realization will change result hashes and curves. Kernel working directory is the original `Tutorials/`; relative data paths are preserved without changing notebook cells. For manual execution of the saved copy, set the working directory externally to upstream `Tutorials/` before its original cells run.

Optional `phenomxpy`, `pyseobnr` and CuPy notices appeared, including worker imports; no execution error occurred and none of those optional paths was used. The numerical evidence, notebook and figure files are hashed in `manifest.json`; raw console output is normalized into `execution-log.txt` for publication.

## Remaining scope

Tutorial 1 original-default execution is complete. Tutorials 2–4 still need separate full execution and output checks. Tutorial 5 is excluded from the current reproduction scope following the teacher's guidance; its external data are not a blocker. No SGWB joint-inference or posterior-reconstruction result is claimed by this instrument/noise tutorial.
