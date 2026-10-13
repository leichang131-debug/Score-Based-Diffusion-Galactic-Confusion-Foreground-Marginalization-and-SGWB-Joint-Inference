# TaijiSGWB selected-data template workflow

**COMPLETED workflow; convergence NOT confirmed.** Real local 8-week/512-bin subset, original 14-parameter priors/likelihood, 6 temperatures × 32 walkers, one compute process. Burn300 then production1000, thin_by=1; fresh-process restart at stored500. Sampling took about 4.61 minutes.

31/31 preparation checks and 11/11 stored-state/recovery/numerical checks pass. Only 2/14 parameter diagnostic flags pass. Quantiles/figures summarize the finite subset sample and are not paper/full-year inference results or established converged credible intervals. The original full-data chain stays paused at burn108.

[Report](../../../docs/reproduction/taiji-sgwb/template-mini.md). `selection.json` contains actual original indices; `analysis.json` contains the diagnostic verdict; per-phase folders contain original-named complete HDFs, paired state and actual execution/resource/source evidence. `audit.json`/`manifest.json` protect integrity. No raw inputs, transformed source algorithm or copied upstream output was substituted.
