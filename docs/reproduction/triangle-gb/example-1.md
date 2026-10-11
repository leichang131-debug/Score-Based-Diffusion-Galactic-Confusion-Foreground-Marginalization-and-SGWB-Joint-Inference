# Example 1: rapid search of a verification Galactic binary

## Result and correspondence

`1_TDIFlyGB_Rapid_Search(CPU).ipynb` was executed completely in a fresh local Python 3.11.14 / NumPy 1.26.4 / SciPy 1.13.1 Jupyter kernel on the ARM64 MacBook Air. All 17 nonempty code cells executed, all four figures were generated locally, and the optimizer terminated successfully. The final empty cell is retained unexecuted.

Triangle-GB source commit: `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`. Triangle-Simulator commit: `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. The notebook filename, code, Markdown and attachments remain exactly as upstream; source outputs were cleared before execution. Only kernel metadata, execution records and outputs differ. Canonical sources stay unchanged. The executed copy is `notebooks/reproduction/triangle-gb/Examples/1_TDIFlyGB_Rapid_Search(CPU).ipynb`.

## Original processing and code interfaces

| Zero-based cells | Operation and original setting |
| --- | --- |
| 1–2 | Single-thread numerical-library settings; actual multiprocessing `fork`; original literal author paths retained. |
| 5–7 | Read verified full VGB HDF5 files, pad 200 zero samples to t=0, XYZ-to-A/E; two channels, 3,147,175 samples at 10 s cadence; plot time series. |
| 9–10 | Original Tukey FFT (`alpha=10000/Tobs`), plot full frequency data. |
| 12–15 | Select injected source index 4; f0=0.0032247077104776 Hz; 5e-6 Hz total band, 157 bins; estimate constant PSD from the channel median powers. |
| 17 | `Orbit` and CPU `TDIFlyGB`, original X2/Y2/Z2 combinations, Nsparse=512. |
| 20 | Bounds on f0, nonnegative fdot0, longitude and sin(latitude). |
| 22 | `cost_function` converts unit-cube coordinates using `IntParamArr2Dict`, minimizes negative `Fstatistics` using SciPy differential evolution. |
| 24–26 | `Fstatistics(return_a=True)` and `a_to_extrinsic` reconstruct amplitude parameters; `return_recovered_wave=True` gives an A/E template; plot data, template and residual. |

The original DE settings are unchanged: `strategy='best1exp'`, maxiter=1000, popsize=20 (80 population members for 4 dimensions), tol=1e-6, atol=1e-8, mutation=(0.4,0.95), recombination=0.7, polish=False, workers=-1, no supplied seed or initial point. SciPy's expected warning that parallel workers imply deferred updating appears in the local notebook, as in the original.

The dedicated kernel externally maps only the two author-specific HDF5 paths to ignored verified local data. The relative orbit path resolves through the prepared workspace. This does not alter data, priors, source cells or algorithm settings.

## Numerical outcome

- Optimization: success=True; 85 iterations; 6880 objective evaluations; population shape [80, 4].
- Local cost: **-3126.0340757022959**; upstream cost: **-3126.0335911147595**. Absolute difference 0.00048458754. Random initialization means exact parameter/iteration identity is not required.
- F-statistic at injected intrinsic parameters: 3125.960788612225; at searched parameters: 3126.034075702296. Small improvement over the injected point is consistent with fitting the particular noisy data; it is not proof of unbiased recovery.
- Band data, template and residual shape `(2,157)`; all finite. PSD level: 9.052560408655443e-43.
- Data weighted norm 6873.851479427470; residual weighted norm 621.783328022878. The identity `(data_norm-residual_norm)/2 = F_best` is independently verified from saved arrays. It checks the original linear-amplitude fit.
- Relative complex residual L2/data L2 by channel: [0.2732071358304736, 0.32722815185735626]. A nonzero residual is expected in noisy multi-source data; removing all residual would not be the goal.

| Parameter | Injected | Searched | Absolute difference |
| --- | ---: | ---: | ---: |
| f0 | 0.00322470771048 | 0.0032247085829 | 8.7242e-10 |
| fdot0 | 5.53676559023e-17 | 6.66266834504e-18 | 4.8705e-17 |
| longitude | 0.429491420034 | 0.431587281713 | 0.0020959 |
| latitude | -0.354892792765 | -0.3541936915 | 0.0006991 |
| A | 9.51718037304e-23 | 9.77489623502e-23 | 2.5772e-24 |
| inclination | 1.0471975512 | 1.06553609261 | 0.018339 |
| psi | 2.09936894107 | 2.11485214671 | 0.015483 |
| phase0 | 1.320818673 | 1.2455487003 | 0.07527 |

These are point estimates, not posterior uncertainties. In particular, fdot0 differs visibly from truth and phase/psi can have equivalent modes; this run does not demonstrate each parameter is measured accurately. No extra run was selected to obtain closer values.

## Actual timing and resources

Wall time **9.464 s**, covering fresh kernel startup, all original cells, external diagnostic probes, figure export and notebook writes. Cell 22 (entire parallel DE search): **4.440 s**. The input full-year signal is loaded from disk; it is not regenerated or searched sample-by-sample at every evaluation. TDIFly works with a sparse response and a 157-bin band, explaining why thousands of objective evaluations can be quick. This measurement should not be used as a nested-sampling runtime prediction.

Actual CPU count: 10; start method: fork; original workers=-1. Resource samples observed 13 processes (runner/process-monitor overhead, kernel and 10 workers). Sampled peak process-tree RSS sum **1.932 GiB**; sum of RSS can count fork-shared pages repeatedly and 2-second sampling can miss peaks. No memory error occurred. Per-cell times, UTC start and raw resource samples are preserved.

## Limitations preserved and explained

1. The notebook says four extrinsic parameters are "marginalized". In this implementation `Fstatistics` forms `0.5 * N^T M^(-1) N`, solving for the four linear amplitudes analytically and **maximizing** over them. It does not integrate a prior to produce Bayesian marginal likelihood or a posterior. The source explanation is retained unchanged, with this clarification outside the notebook.
2. This is an unseeded single stochastic search; successful DE termination and agreement with the reference neighborhood do not prove a global optimum or posterior coverage. The 1e-3 relative reference-neighborhood audit tolerance is a sanity check, not an uncertainty estimate. No fixed seed, shortened optimization or external resource monkeypatch was imposed.
3. Original fdot bounds exclude negative derivatives, despite the source comment noting mass-transfer systems. The estimated constant PSD and finite narrow band are original approximations, not a full foreground/noise uncertainty treatment.
4. Original VGB observation time extends beyond the orbit text grid by about 6.15 hours, with a delayed-start boundary also extrapolated. Finite execution and agreement with the upstream search do not certify boundary physics. See the existing VGB input-validation report; no replacement orbit or truncation was introduced.
5. The search plots retain original plotting code. Regenerated stochastic fit curves and plotting-library layout need not be pixel-identical to reference PNGs. Saved PNGs are checked against actual local notebook outputs.

## Evidence and rerun

`results/triangle-gb/example-1/` contains execution.json/txt, resource CSV, diagnostics.json, the complete selected band, recovered waveform, residual and final DE population in `search-band.npz`, four local PNGs, audit.json and a SHA-256 manifest. The audit rehashes both entire local HDF5 files against the recorded official size/MD5 and SHA-256. Bulk input files remain ignored.

From the research-repository root:

```bash
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-example-1.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-example-1.py
```

Local Jupyter startup needs loopback socket access, and this unchanged example forks local CPU workers. The working directory is the prepared ignored Examples workspace; the same-name tracked notebook is a portable record of this actual run. Other examples remain separate reproduction stages.
