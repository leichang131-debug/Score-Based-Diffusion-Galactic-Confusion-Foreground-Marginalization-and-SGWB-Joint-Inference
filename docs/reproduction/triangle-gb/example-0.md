# Example 0: time-domain / frequency-domain waveform comparison

## Result and scope

The complete unchanged `0_TDIFlyGB_Compare_TD_FD_Waveforms(CPU).ipynb` was executed in a fresh local Jupyter kernel on the MacBook Air (ARM64, Python 3.11.14, NumPy 1.26.4). All 10 nonempty code cells executed and two figures were regenerated; no upstream computation outputs were reused. The final empty cell stays empty. Source: Triangle-GB commit `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`; Triangle-Simulator `ab796358e9a36c8987f6bb53a97230d603bfdfd5`.

The executed copy retains the original filename, all code, Markdown and attachments, in `notebooks/reproduction/triangle-gb/Examples/`. Only kernel metadata, execution timestamps/counts and generated outputs differ. The canonical submodule is unchanged. Relative orbit paths resolve through the prepared ignored workspace. The HDF5 path hook is present in the dedicated kernel but this example does not open any HDF5 data.

## Original calculation, by zero-based cell index

| Cells | Operation and retained setting |
| --- | --- |
| 0 | Import Triangle simulator and Triangle_GB.TDIFly from pinned editable sources. |
| 2 | One original `YEAR`: 31558140 seconds, `dt=10`, 3,155,814 time samples. MicroSateOrbitEclipticTCB, CPU, Spline5, `drop_points=100` (boundary zeros, not shortened arrays). |
| 4 | Construct X2/Y2/Z2 TDIFly combinations, `Nsparse=1024`, CPU. |
| 6 | Retain all eight original source parameters without modification. |
| 8–10 | Generate full A2/E2/T2 response, plot time series, apply original Tukey-window FFT (`alpha=10000/Tobs`), select `abs(f-f0)<1e-5 Hz`. |
| 12 | Generate frequency-domain template, XYZ-to-AET and original FFT-bin placement. |
| 14–15 | Plot absolute TD FFT, FD template and complex difference magnitude; calculate the original mismatch. |

Both band arrays have shape `(3,631)` and all time/frequency arrays are finite. Local mismatch: **0.00036493088281219777**; upstream displayed result: **0.00036493**, agreeing to its displayed precision. An independent NumPy calculation checks the same formula. Per-channel relative complex L2 differences (A/E/T): 0.03439918, 0.01801189, 0.02430447. These describe a single source/band, not general parameter-estimation accuracy.

## Timing, resources and evidence

Full runner wall time: **13.757 s**, including kernel startup, all original cells, separate diagnostics, plot extraction and notebook serialization. Cell 8 time-domain generation: **8.826 s**. Cell 12 includes the FD call and FFT-series fill: **0.006324 s**; it is not an isolated benchmark of the FD generator. Sampled peak process-tree RSS sum: **4.275 GiB** (2-second samples, shared pages can be counted repeatedly; this is not a guaranteed true peak). No memory error occurred. This CPU vectorized waveform example is much lighter than a posterior sampling run; its duration should not be used to estimate Examples 1/2.

`results/triangle-gb/example-0/` contains the original-cell execution transcript, UTC start and per-cell times, sampled resource CSV, numerical diagnostics and waveform hashes, the full selected frequency band in NPZ, two locally generated PNGs, audit and SHA-256 manifest. Original source plots were inspected separately only as references; they are not saved as local evidence. Local PNGs were checked against the executed notebook outputs. The time plot canvas is 1013×386 pixels locally versus 1012×386 upstream; the comparison plot is 1214×392 locally versus 1214×393 upstream. These one-pixel layout differences do not change the retained plotting code or the numerical mismatch agreement.

## Caveats inherited from upstream

- `TDIFlyGB.mismatch` is `1 - Re(sum(conj(h1)*h2))/sqrt(sum(abs(h1)^2)*sum(abs(h2)^2))` across all A/E/T bins. It has no PSD weighting or phase/time maximization. A small value is agreement for this test, not proof of unbiased or calibrated posteriors.
- The original orbit text grid ends at 31,449,600 s, whereas this example's last data time is 31,558,130 s. Orbit interpolation therefore extrapolates near the observation boundary (and delayed initial samples). The source/defaults are preserved; matching the reference result does not validate extrapolation physics. This example's longer `YEAR` is different from the VGB HDF5 example's time range; the earlier 6.15-hour VGB tail estimate must not be applied here.
- Cell 14 multiplies frequency by 1e3 but labels the axis `Frequency (Hz)`. The displayed numbers are mHz. This existing label is retained to comply with exact source correspondence, and documented rather than silently corrected.
- An initial sandbox-only launch was blocked before any source cell executed because Jupyter requires a loopback socket. `sandbox-startup.txt` retains that failure. The successful authorized local run is `execution.txt`; no notebook scientific code was changed to resolve it.

## Re-execution

From the research-repository root, with the existing environment and prepared workspace:

```bash
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-example-0.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-example-0.py
```

Local Jupyter kernel startup requires loopback socket permission. The runner clears original code outputs before execution and records diagnostics outside the retained notebook cells. Later examples remain separate pending reproduction stages.
