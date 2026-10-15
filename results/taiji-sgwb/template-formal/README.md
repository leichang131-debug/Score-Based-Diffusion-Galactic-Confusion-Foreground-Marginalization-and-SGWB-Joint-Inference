# TaijiSGWB full-data template sampling: completion and evidence

Completed locally at **2026-10-15 06:13:36 Asia/Shanghai**: 1000 burn transitions plus 350 saved production ensembles at thin_by=12, exactly 5200 transitions. The original full 2.8 grid, six temperatures, 62 walkers and four CPU workers were retained. All 19 pinned upstream files and frozen scientific adapters remain unchanged.

**Status: SAMPLING_COMPLETE_CONVERGENCE_NOT_CONFIRMED.** All 7 numerical/source/schedule checks passed. This is a completed original-template run, not the full paper's EQ/2.9/RJMCMC suite, unknown-foreground marginalization, or a guarantee of posterior convergence.

## Results and diagnostics

The sampled 16–84% interval for Omega0 is [8.7695e-13, 1.03885e-12], median 9.5567e-13 (injection 1e-12). For alpha the interval is [0.63466, 0.72659], median 0.68020 (injection 2/3). Both injection values lie in these sampled intervals. This agreement alone does not establish convergence or repeated-injection coverage.

Cold production acceptance is 0.2942. Only 2 of 14 parameters pass the predeclared conservative single-ensemble diagnostics. Omega0/alpha ensemble-mean autocorrelation estimates are about 28.2/31.5 saved steps; 350 time steps do not meet the 50*tau length heuristic. Their heuristic mean ESS values are about 337/324. These are interacting walkers, not 62 independent chains; no independent-ensemble R-hat or coverage result is claimed. Do not automatically extend the run based on this report.

## Saved artifacts

| Artifact | Content |
| --- | --- |
| template_AET_nofg.h5 | Actual complete original-named HDF chain; all six temperatures, walkers, likelihood/prior records |
| final-state.json / final-state.npz | Final paired sampler state: coordinates, masks, likelihood/prior, betas, both RNG states and adaptive/move counters |
| burn-exit-state.json | Preserved counters at the end of burn; enables all-production acceptance calculation |
| posterior-cold-chain.npz | 350 x 62 x 14 actual cold samples, truth, labels, log likelihood and betas; 21700 correlated draws |
| posterior-parameters.csv | 14 parameter sampled quantiles, truth locations and 95% interval checks |
| sampling-diagnostics.csv / analysis.json | Autocorrelation, heuristic ESS/MCSE, drift, acceptance, swap counts and saved-state likelihood rechecks |
| posterior-spectrum.npz | All-draw pointwise 2.5/16/50/84/97.5% spectral quantiles over 0.1–50 mHz |
| execution.txt / resources.csv / run.json | Actual local logs, resources and runtime; final uninterrupted continuation about 16.52 hours, not all earlier attempts |
| source-execution.json / configs/.../template-formal.json | Original executed AST/function correspondence and fixed configuration |
| sessions/ / pause-checkpoint/ / overnight-pause-checkpoint/ | Timestamped start/recovery evidence and earlier pause backups |
| completion-summary.json / figure-provenance.json / audit.json / manifest.json | Completion dimensions, plotting provenance, integrity checks and SHA-256 artifact inventory |

## Figures

- [SGWB posterior](posterior-sgwb.png): paper Figure 3's 2.8 component, pink 68%/95% contours and red injection.
- [Noise posteriors](posterior-noise-spacecraft.png): paper Figure 8's available 2.8 template component, draw-by-draw spacecraft averages in physical fm/pm units. Cyan 16/50/84% dashed markers are added using Figure 4's marker convention; this is not the EQ experiment.
- [SGWB spectrum](posterior-spectrum.png): paper Figure 6's template component, 95% pointwise band and fractional error panel. Display is 1–40 mHz; full numerical range is retained in NPZ.
- [SGWB production traces](production-traces.png).
- [All 14 production traces](production-traces-all.png).
- [Parameter correlation matrix](parameter-correlation.png).

All six figures were generated from this run and visually inspected. No upstream plot or mini-run sample is substituted. Diagnostic figures supplement the publication-style result figures. The original upstream demo itself does not contain all publication postprocessing scripts.

## Postprocessing repair

The automatic analysis initially stopped at an external analyzer path typo, ROOT[...] instead of ROOT / ..., before plotting. Original failure log, pre-fix analyzer and status are retained under attempts/automatic-postprocessing-path-error/. Corrected postprocessing was rerun against the unchanged completed chain. SHA-256 comparisons confirm both live/exported HDF and final NPZ/JSON were not altered. This was not a sampling failure or MCMC rerun. The completed-state audit now requires analysis, status consistency, all six figures and published final-state hashes; an integrity-only audit cannot stand in for postprocessing completion.

[Detailed method and history](../../../docs/reproduction/taiji-sgwb/template-formal.md).

## Reference-figure detail review

See [figure-by-figure correspondence](paper-figure-correspondence.md). Paper Figure 3 also contains 2.8_EQ posteriors; Figure 4 is specifically 2.8_EQ; Figure 6 also contains a separate RJMCMC interpolation result. Those experiments have not been executed. Available-data quantile markers were added without changing sample values. Full-paper figure reproduction remains incomplete.
