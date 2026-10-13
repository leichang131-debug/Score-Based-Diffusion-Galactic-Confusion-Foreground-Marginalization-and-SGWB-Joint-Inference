# TaijiSGWB Stage 8 short-chain evidence

Original template, 6 temperatures × 62 walkers, full weekly/frequency likelihood. Real local 4-step save/exit plus fresh-process 4-step continuation; same-seed uninterrupted 8-step control. 88/88 checks pass; all 11 arrays match bit for bit. This is not a converged posterior.

`initial/`, `resume/`, `continuous/` contain original-named `template_AET_nofg.h5`, paired `restart-state.json`, numeric arrays, exact source correspondence and real command/PID/time/RSS logs. `validation.json` includes saved-state recalculation and continuity checks. `attempts/` retains an actual Eryn HDF restart type-comparison failure and resource-audit issues.

An external HDF key-order readback adapter and JSON sidecar preserve restart state; neither original source nor installed Eryn files are patched. Source/library/cache/backend integrity is independently audited.

[Detailed report](../../../docs/reproduction/taiji-sgwb/template-short-chain.md). Figure is a short-chain trace diagnostic, not posterior parameter recovery.
