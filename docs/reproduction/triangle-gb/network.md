# Original three-detector GB network parameter-estimation reproduction

Completed locally on Apple ARM64, in a fresh Python 3.11.14 kernel. All upstream outputs were cleared before execution. The original filename, every code/Markdown cell and attachments are preserved. The source pin is `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`; the original notebook is in `external/triangle-gb/Examples/`. This is a full original-default tutorial execution, not a reduced demonstration and not a reproduction of every result in the associated paper.

## Original configuration and scope

- Notebook: `GB_network_PE_example_for_2609.16477.ipynb`.
- Detector/channel order: TianQin A/E, Taiji A/E, LISA A/E.
- Four-year observation, 10-second cadence, original analytic orbits and 1024 sparse response samples.
- Original injected GB: amplitude 1e-22, frequency 3 mHz, frequency derivative 2e-17 Hz/s; original seeded angles and noise seed 22222.
- Six-channel frequency-domain signal and analytic independent instrumental noise. Galactic confusion PSDs and cross-detector CSDs are **zero** in this notebook.
- Original eight-parameter Triangle-BBH MultiChannelFisher step tuning and priors. Amplitude, frequency and frequency derivative priors are centered on the injected truth using Fisher errors. This is local injection parameter estimation, not an unknown-source blind search.
- Original Bilby/NESSAI settings: 1000 live points, stopping=0.1, resume=False, plot=True, npool=multiprocessing.cpu_count()=10. The sampler itself has no imposed random seed.

## Original code-to-result mapping (zero-based cell indices)

| Cells | Original code and result |
|---|---|
| 0, 2, 4 | Imports, three analytic mission orbits, PSD/CSD/covariance and noise helper functions. |
| 5, 7 | Four-year time/frequency grid and `TDIFlyGBNetwork` construction. |
| 9, 11 | Seeded eight-parameter injection, `response_on_band`, six-channel signal spectrum. |
| 13, 15 | Instrumental band PSDs, inverse covariance, seeded noise; `GBNetworkLikelihood` and injected SNR/likelihood. |
| 17 | `Triangle_BBH.Fisher.MultiChannelFisher`: tuned differences, Fisher inversion and eight priors. |
| 18 | Six conditional 501-point likelihood scans; five visible panels. |
| 20, 21 | Original Bilby/NESSAI full nested sampling and saved eight-parameter corner plot. |

The copied notebook executes package implementations directly from the pinned `Triangle_GB/`, `Triangle/` and `Triangle_BBH/` sources. The runner and audit scripts live outside these sources; no notebook model or algorithm is replaced by a project wrapper.

## Measured results

| Item | Local measurement |
|---|---:|
| Nonempty original code cells | 13 |
| Total runner wall time including startup and exports | 1563.635 s |
| Sampler reported time | 1522.544631 |
| Peak sampled runner/descendant RSS sum | 1.663 GiB |
| Posterior samples | 4812 |
| Likelihood evaluations | 674320 |
| Injected network SNR | 319.750763773 |
| Truth log likelihood | -19073.446987945 |
| Log evidence | -19105.142740 ± 0.174445 |
| Nested-weight effective sample size | 6906.876 |
| Final insertion-index p-value | 0.236936043 |

RSS is a two-second sampled sum, not unified-memory usage: forked shared pages can be counted repeatedly and brief peaks can be missed. Cell-by-cell timings, actual host identity, process samples and local kernel stream are retained. No time estimates are substituted for measurements.

| Parameter | Injection | Median | 16th–84th percentile |
|---|---:|---:|---|
| A | 1e-22 | 1.015736363e-22 | [9.598727536e-23, 1.071814561e-22] |
| f0 | 0.003 | 0.002999999981 | [0.002999999929, 0.003000000035] |
| latitude | 0.03015965388 | 0.03245709449 | [0.02925118224, 0.03574860635] |
| longitude | 1.36078839 | 1.360857724 | [1.36029731, 1.361439238] |
| fdot0 | 2e-17 | 2.042513009e-17 | [1.961330852e-17, 2.124326573e-17] |
| inclination | 0.391128855 | 0.4300223309 | [0.27000401, 0.5387595683] |
| phase0 | 3.930817116 | 3.129005824 | [1.4650507, 5.861461396] |
| psi | 0.2173165029 | 1.41341207 | [0.6097749189, 2.411763445] |

These are raw-coordinate quantiles, not mode-specific summaries. The original corner title formatting rounds very small dimensional parameters to 0.00; the CSV and table retain their scales.

## Numerical and source checks

`audit.json` records the final checks. The saved band arrays independently verify data=signal+noise, exact noise regeneration from the original seed, six-channel shapes, finite values, Hermitian positive inverse covariance, diagonal instrument-only covariance, and independent SNR/truth-likelihood contractions. The best posterior likelihood is recomputed through the original likelihood. CSV posterior values must be finite and inside the original priors. Sampler HDF5 and Bilby summaries are cross-checked.

`physical-validation.json`, `fisher.npz` and `likelihood-scans.npz` additionally come from a separate fresh execution of the original preparation cells and all six 501-point conditional scans; the sampler is not rerun. The raw Fisher condition number is 1.338e+49; after scaling each parameter by its diagonal Fisher scale it is 7.721e+05. The raw warning is preserved, and scaling alone does not prove Fisher error accuracy.

The deterministic reference values are SNR=319.8 and truth log likelihood=-19073.45, consistent with local printed values. Upstream reports log evidence=-19105.434 ± 0.176, 4650 posterior samples, 602977 likelihood calls and an insertion p-value of 0.000249. Posterior/evidence values and sample counts need not match exactly: the sampler is unseeded, worker counts and NESSAI versions differ (upstream 0.14.0.post0; local 0.15.2). Differences are retained rather than replaced with upstream outputs.

## Issues and interpretation

Final insertion-index p-value is above 0.05. This single diagnostic does not establish posterior calibration.

The original scan computes six parameters but hides the last psi panel with `axes[-1].set_visible(False)`. This is retained exactly; the additional NPZ contains all six scans. Noisy-data conditional likelihood maxima need not equal the injection exactly, and coarse full-sky 501-point grids need not resolve the narrow maximum. They are not joint posterior marginals. The original 3 mHz injection also differs from a nearby comment mentioning instrument domination above 4 mHz; the actual setting is retained.

Finite samples and successful termination establish execution integrity, not calibrated parameter coverage, complete mode discovery or paper-level scientific validation. Phase/polarization periodic degeneracies require joint interpretation of the corner plot. Evidence uses the original likelihood without its constant Gaussian normalization; do not compare evidence across different noise models as if normalization had been included. The original likelihood does not provide a finite noise-evidence/Bayes-factor calculation.

## Evidence and rerun

- Executed same-name notebook: `notebooks/reproduction/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb`.
- `results/triangle-gb/network/`: execution log/JSON, kernel stream, resources CSV, locally rendered figures, posterior CSV, band/Fisher/scan arrays, numerical checks, sampler diagnostics and hash manifest.
- `Samples/`: exported final Bilby JSON, NESSAI HDF5, original logs and diagnostic figures. Local binary flow weights/checkpoints remain under ignored `runs/`; every sampler artifact has size/SHA-256 in `sampler-artifacts.json`.

Run `environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-network.py` in the main repository, then the network exporter, independent physics validator, report generator and audit scripts. An existing dedicated `runs/triangle-gb/network/Examples/Samples` causes the fresh-run runner to stop; archive that directory deliberately before rerunning. Do not mix a prior run with resume=False outputs. Runtime environment, TeX rendering and original package sources remain those documented in the common environment report.
