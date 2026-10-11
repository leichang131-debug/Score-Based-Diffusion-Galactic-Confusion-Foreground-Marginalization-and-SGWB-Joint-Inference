# Example 2: full eight-parameter Galactic-binary posterior sampling

## Execution outcome and source correspondence

The unchanged `2_TDIFlyGB_Parameter_Estimation(CPU).ipynb` was executed in a fresh local Jupyter kernel on the ARM64 MacBook Air. All nonempty original code cells executed; prior source outputs were cleared before the run. All notebook images and sampler diagnostics were generated locally. Exact filename, code, Markdown and attachments are retained in `notebooks/reproduction/triangle-gb/Examples/`. Kernel metadata and execution outputs differ, as expected.

Pinned Triangle-GB: `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`; Triangle-Simulator: `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. Canonical sources are unchanged. Runtime versions: Python 3.11.14, NumPy 1.26.4, Bilby 2.8.2, NESSAI 0.15.2, nessai-bilby 0.3.2, Torch 2.14.1. The reference notebook used NESSAI 0.14.0.post0 and Python 3.9; our previously validated macOS environment uses the versions listed above, so this is original-source/method reproduction, not a bitwise historical environment reconstruction.

## Original settings and zero-based cell mapping

| Cells | Original operation |
| --- | --- |
| 1–2 | Single-thread numerical libraries, multiprocessing fork, original author HDF5 paths and relative orbit path. |
| 5–10 | Read complete verified VGB inputs, pad 200 zeros to t=0, XYZ-to-A/E, original Tukey FFT; plot full time series and spectrum. |
| 12–15 | Select source index 1 (different from rapid-search source index 4), f0=0.0048216991071498 Hz, full band width 5e-6 Hz, 157 bins; original constant median-power PSD estimate. |
| 17 | CPU TDIFlyGB model and original orbit, Nsparse=512. |
| 20 | Original Bilby likelihood wrapper calls TDIFlyGB.Likelihood for all eight source parameters. |
| 22 | Original priors: log-uniform A, uniform f0/fdot0, isotropic inclination/latitude, periodic longitude/phase0/psi. |
| 24 | Bilby/NESSAI nested sampling, nlive=500, stopping=0.01, npool=cpu_count(), plot=True, resume=False, original label and ./Samples output directory. |
| 25 | Original result.plot_corner(save=True). |

Data shape before FFT: `(2,3147175)`, dt=10 s; Tobs=31471750 s. The analyzed complex frequency data have shape `(2,157)` and PSD=3.217451233914247e-42. No time scale, priors, live-point count, tolerance or pool size was reduced. No seed was imposed. The original paths are mapped outside the source through the dedicated kernel hook to the verified ignored inputs. The run was fresh: a pre-existing Samples directory would have caused the runner to stop rather than silently reuse it.

The likelihood is the original `-2 * sum(abs(data-template)^2) / Tobs / PSDlevel`, equivalent to `-0.5 * (residual|residual)` in its frequency-domain convention. Unlike the preceding F-statistic search, this stage samples all eight physical parameters with their priors. NESSAI's normalizing-flow proposal is a sampling aid; it is not a score-based diffusion model.

## Posterior and evidence

Posterior sample count: **2458**. All eight parameter columns, posterior log likelihoods and log priors are finite and within prior bounds. The highest saved posterior log likelihood is -302.309994354425; reevaluation through the original wrapper gives -302.309994354425. At the injected parameters the likelihood is -308.305743201477.

Log evidence: **-345.511904 ± 0.281366**. Reference notebook: **-345.640 ± 0.282**, 2539 posterior samples, 1,026,087 evaluations. Both are unseeded single runs, with different NESSAI versions; exact equality is not expected. Estimated evidence error describes sampler uncertainty under the adopted likelihood/priors, not model accuracy. The wrapper has undefined noise evidence (`nan`) and hence undefined Bayes factor (`nan`), as in the original; neither is reported as a detection claim.

| Parameter | Injected | Posterior median | 16th–84th percentile |
| --- | ---: | ---: | --- |
| A | 9.402415442e-23 | 9.24741964e-23 | [9.117562749e-23, 9.377336236e-23] |
| f0 | 0.004821699107 | 0.004821696531 | [0.004821693496, 0.00482169943] |
| fdot0 | 2.53782495e-16 | 4.230903927e-16 | [2.450865238e-16, 6.103662913e-16] |
| inclination | 1.468694566 | 1.477524719 | [1.470186711, 1.484609817] |
| latitude | 1.154737624 | 1.154695606 | [1.151618495, 1.157680587] |
| longitude | 3.578406557 | 3.584008153 | [3.575490285, 3.594078475] |
| phase0 | 2.680478779 | 5.686657455 | [2.709300403, 5.951089546] |
| psi | 2.459968725 | 0.9277260097 | [0.899639005, 2.48063235] |

The unchanged default corner plot title formatter rounds very small A/f0/fdot0 values to 0.00; the axes, numerical table and posterior CSV preserve the actual scales. This existing presentation issue was not corrected in the original notebook.

These raw coordinate quantiles summarize this one run. Periodic and multimodal angles can make a single median/interval misleading; use the corner plot and equivalent-angle conventions for interpretation. They are not injection-study coverage results, and no parameter is declared calibrated merely because truth falls in a displayed interval.

## Sampler diagnostics and reliability

Final insertion-index KS statistic: **0.012135276**; p-value: **0.00083813116**. The final insertion-index uniformity check raises a warning (p < 0.05). The complete numerical workflow finished, but sampling reliability needs follow-up. This warning is not hidden and the run was not repeated to select a favorable result.

Number of recorded insertion indices: 24025; nested samples: 24525; likelihood evaluations: 903749. Nested-weight effective sample size: 3657.85, computed from normalized stored nested posterior weights; it is distinct from the final rejection-resampled posterior count and is not an MCMC ESS estimate. The complete insertion-index, state, trace, logX/logL and proposal diagnostic files are retained. Original reference final insertion-index p-value was 0.0003481 and also emitted a warning.

NESSAI reported its stopping condition in the actual local log. Reaching stopping=0.01 establishes algorithmic completion, not universal sampling correctness. Reliable scientific use should add independent seeded runs, mode/angle checks and injection-based coverage; if insertion diagnostics warn, investigate proposal/parameterization/sampler settings in separate documented experiments rather than changing this original reproduction silently.

## Actual timing, memory and artifacts

Total runner wall time: **411.536 s** (6.86 min), including fresh kernel initialization, original cells, the post-run diagnostics probe and output serialization. Original cell 24 sampling and its built-in plotting: **405.368 s**. NESSAI internal sampling time: **400.087 s**; training time 14.148 s; population time 58.536 s. These internal timers overlap and must not be added as independent totals.

Actual pool: 10 CPU workers, fork. Sampled peak runner/descendant RSS sum: **2.450 GiB** at 2-second intervals. Fork-shared pages may be counted repeatedly; sampled RSS sum is not an exact physical-memory peak. No memory error occurred.

`results/triangle-gb/example-2/` contains:

- Executed-notebook hash, UTC start, per-cell times, complete original kernel streams and sampled resources.
- Eight-parameter posterior CSV, analyzed frequency data NPZ, numerical diagnostics, input identity checks and source/figure audit.
- `Samples/`: copied actual Bilby/NESSAI scientific results, config, logs, corner and diagnostic plots, including the HDF5 nested/posterior samples and weights.
- `sampler-artifacts.json`: byte counts and SHA-256 of all local sampler products, with explicit exported/ignored classification. Binary resume checkpoints and flow weights remain in ignored runs; raw HDF5 inputs remain ignored.
- Manifest of tracked evidence, original source and environment locks. Scientific diagnostics are recorded separately from execution-integrity checks; posterior calibration remains unestablished.

## Preserved limitations and rerun

The original orbit coverage/extrapolation caveat remains: the VGB observation tail extends about 6.15 hours beyond the orbit text grid, with delayed-start extrapolation. Original fdot0 prior excludes negative values, and the narrow-band PSD is treated as a fixed estimated constant. This is one-source inference in a selected band, not the project's full foreground-marginalization/SGWB joint inference.

The original legacy Bilby parameter-state API emits deprecation warnings in the installed Bilby version but executes successfully; those warnings are preserved. Future Bilby major-version compatibility is not claimed. No upstream source or warning output was hidden.

From the research-repository root:

```bash
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-example-2.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/export-triangle-gb-example-2.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-example-2.py
```

Archive/move an existing ignored working Samples directory before an explicitly requested fresh rerun; the runner intentionally refuses to overwrite it. Local kernel startup needs loopback sockets and original CPU workers. Original resume=False is unchanged, and checkpoint existence does not imply that resume has been tested.
