# TaijiSGWB selected-data template workflow

**COMPLETED workflow; convergence NOT confirmed.** Real local 8-week/512-bin subset, original 14-parameter priors/likelihood, 6 temperatures × 32 walkers, one compute process. Burn300 then production1000, thin_by=1; fresh-process restart at stored500. Sampling took about 4.61 minutes.

31/31 preparation checks and 11/11 stored-state/recovery/numerical checks pass. Only 2/14 parameter diagnostic flags pass. Quantiles/figures summarize the finite subset sample and are not paper/full-year inference results or established converged credible intervals. The full-data chain was paused at burn108 during this historical mini experiment; it subsequently completed all 5200 transitions on 2026-10-15, with convergence unconfirmed.

[Report](../../../docs/reproduction/taiji-sgwb/template-mini.md). `selection.json` contains actual original indices; `analysis.json` contains the diagnostic verdict; per-phase folders contain original-named complete HDFs, paired state and actual execution/resource/source evidence. `audit.json`/`manifest.json` protect integrity. No raw inputs, transformed source algorithm or copied upstream output was substituted.

## Analysis-only maintenance (2026-10-15)

The historical mini analysis recorded that the separate formal run was paused at that time. The formal run later completed. The current analyzer now checks before/after identity of the existing formal status, final artifacts and saved pause checkpoint instead of requiring a permanently paused live status. Its pre-update source is archived under `results/taiji-sgwb/template-mini/attempts/before-lifecycle-guard-update/analyzer.py`. Canonical mini samples, analysis JSON, figures and execution logs remain historical and unchanged. A redirected analysis-only check passes all 11 numerical checks and reproduces all four PNGs and posterior/diagnostic values exactly; the new evidence is in `results/repository-maintenance-20261015/`. No MCMC was launched.
