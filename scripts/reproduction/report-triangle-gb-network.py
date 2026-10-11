"""Generate the English final report from measured local evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/network'
e=json.loads((OUT/'execution.json').read_text());d=json.loads((OUT/'diagnostics.json').read_text());s=json.loads((OUT/'sampling-diagnostics.json').read_text());v=json.loads((OUT/'physical-validation.json').read_text())
# The independent check handles the original nested cross-spectral dictionaries.
for k in ['confusion_psd_zero','confusion_csd_zero']:d[k]=v[k]
d['confusion_zero_check_provenance']='Independent unchanged preparation cells, recursive nested-dictionary check in validate-triangle-gb-network-physics.py.'
(OUT/'diagnostics.json').write_text(json.dumps(d,indent=2)+'\n')
warn='WARNING: final insertion-index p-value is below 0.05; investigate sampler reliability before using these samples for scientific claims.' if s['diagnostic_warning'] else 'Final insertion-index p-value is above 0.05. This single diagnostic does not establish posterior calibration.'
parameter_table='| Parameter | Injection | Median | 16th–84th percentile |\n|---|---:|---:|---|\n'+'\n'.join(f"| {k} | {d['true_parameters'][k]:.10g} | {q[2]:.10g} | [{q[1]:.10g}, {q[3]:.10g}] |" for k,q in d['quantiles_05_16_50_84_95'].items())
text=f'''# Original three-detector GB network parameter-estimation reproduction

Completed locally on Apple ARM64, in a fresh Python {d['python']} kernel. All upstream outputs were cleared before execution. The original filename, every code/Markdown cell and attachments are preserved. The source pin is `{e['source_commit']}`; the original notebook is in `external/triangle-gb/Examples/`. This is a full original-default tutorial execution, not a reduced demonstration and not a reproduction of every result in the associated paper.

## Original configuration and scope

- Notebook: `GB_network_PE_example_for_2609.16477.ipynb`.
- Detector/channel order: TianQin A/E, Taiji A/E, LISA A/E.
- Four-year observation, 10-second cadence, original analytic orbits and 1024 sparse response samples.
- Original injected GB: amplitude 1e-22, frequency 3 mHz, frequency derivative 2e-17 Hz/s; original seeded angles and noise seed 22222.
- Six-channel frequency-domain signal and analytic independent instrumental noise. Galactic confusion PSDs and cross-detector CSDs are **zero** in this notebook.
- Original eight-parameter Triangle-BBH MultiChannelFisher step tuning and priors. Amplitude, frequency and frequency derivative priors are centered on the injected truth using Fisher errors. This is local injection parameter estimation, not an unknown-source blind search.
- Original Bilby/NESSAI settings: 1000 live points, stopping=0.1, resume=False, plot=True, npool=multiprocessing.cpu_count()={d['cpu_count']}. The sampler itself has no imposed random seed.

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
| Nonempty original code cells | {len(e['cell_timings'])} |
| Total runner wall time including startup and exports | {e['wall_seconds']:.3f} s |
| Sampler reported time | {d['sampling_time']} |
| Peak sampled runner/descendant RSS sum | {e['peak_sampled_process_tree_rss_kib']/1024**2:.3f} GiB |
| Posterior samples | {d['posterior_samples']} |
| Likelihood evaluations | {s['total_likelihood_evaluations']} |
| Injected network SNR | {d['snr_injected']:.9f} |
| Truth log likelihood | {d['truth_log_likelihood']:.9f} |
| Log evidence | {d['log_evidence']:.6f} ± {d['log_evidence_err']:.6f} |
| Nested-weight effective sample size | {s['nested_weight_effective_sample_size']:.3f} |
| Final insertion-index p-value | {s['final_p_value']:.9g} |

RSS is a two-second sampled sum, not unified-memory usage: forked shared pages can be counted repeatedly and brief peaks can be missed. Cell-by-cell timings, actual host identity, process samples and local kernel stream are retained. No time estimates are substituted for measurements.

{parameter_table}

These are raw-coordinate quantiles, not mode-specific summaries. The original corner title formatting rounds very small dimensional parameters to 0.00; the CSV and table retain their scales.

## Numerical and source checks

`audit.json` records the final checks. The saved band arrays independently verify data=signal+noise, exact noise regeneration from the original seed, six-channel shapes, finite values, Hermitian positive inverse covariance, diagonal instrument-only covariance, and independent SNR/truth-likelihood contractions. The best posterior likelihood is recomputed through the original likelihood. CSV posterior values must be finite and inside the original priors. Sampler HDF5 and Bilby summaries are cross-checked.

`physical-validation.json`, `fisher.npz` and `likelihood-scans.npz` additionally come from a separate fresh execution of the original preparation cells and all six 501-point conditional scans; the sampler is not rerun. The raw Fisher condition number is {v['fisher_raw_condition_number']:.3e}; after scaling each parameter by its diagonal Fisher scale it is {v['fisher_scaled_condition_number']:.3e}. The raw warning is preserved, and scaling alone does not prove Fisher error accuracy.

The deterministic reference values are SNR=319.8 and truth log likelihood=-19073.45, consistent with local printed values. Upstream reports log evidence=-19105.434 ± 0.176, 4650 posterior samples, 602977 likelihood calls and an insertion p-value of 0.000249. Posterior/evidence values and sample counts need not match exactly: the sampler is unseeded, worker counts and NESSAI versions differ (upstream 0.14.0.post0; local {d['nessai']}). Differences are retained rather than replaced with upstream outputs.

## Issues and interpretation

{warn}

The original scan computes six parameters but hides the last psi panel with `axes[-1].set_visible(False)`. This is retained exactly; the additional NPZ contains all six scans. Noisy-data conditional likelihood maxima need not equal the injection exactly, and coarse full-sky 501-point grids need not resolve the narrow maximum. They are not joint posterior marginals. The original 3 mHz injection also differs from a nearby comment mentioning instrument domination above 4 mHz; the actual setting is retained.

Finite samples and successful termination establish execution integrity, not calibrated parameter coverage, complete mode discovery or paper-level scientific validation. Phase/polarization periodic degeneracies require joint interpretation of the corner plot. Evidence uses the original likelihood without its constant Gaussian normalization; do not compare evidence across different noise models as if normalization had been included. The original likelihood does not provide a finite noise-evidence/Bayes-factor calculation.

## Evidence and rerun

- Executed same-name notebook: `notebooks/reproduction/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb`.
- `results/triangle-gb/network/`: execution log/JSON, kernel stream, resources CSV, locally rendered figures, posterior CSV, band/Fisher/scan arrays, numerical checks, sampler diagnostics and hash manifest.
- `Samples/`: exported final Bilby JSON, NESSAI HDF5, original logs and diagnostic figures. Local binary flow weights/checkpoints remain under ignored `runs/`; every sampler artifact has size/SHA-256 in `sampler-artifacts.json`.

Run `environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-network.py` in the main repository, then the network exporter, independent physics validator, report generator and audit scripts. An existing dedicated `runs/triangle-gb/network/Examples/Samples` causes the fresh-run runner to stop; archive that directory deliberately before rerunning. Do not mix a prior run with resume=False outputs. Runtime environment, TeX rendering and original package sources remain those documented in the common environment report.
'''
(ROOT/'docs/reproduction/triangle-gb/network.md').write_text(text)
