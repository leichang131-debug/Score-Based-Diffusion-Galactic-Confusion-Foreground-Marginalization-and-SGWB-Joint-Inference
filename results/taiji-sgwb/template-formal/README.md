# TaijiSGWB formal template inference

**PAUSED BY USER at burn-in 108/1000, production 0/350. Compute processes exited; no completed formal posterior.**

The complete paired state and 19/19 static restore evidence are in `pause-checkpoint/`. The cluster migration plan is in [deployment planning](../../../docs/deployment/taiji-cluster-migration-plan.md). Existing code, environments and data are preserved.

Configuration: 1000 unrecorded burn transitions + 350 saved ensembles at thin_by=12, six temperatures, 62 walkers, four CPU workers, full verified grid. The first ten real burn updates and numerical checks are archived in `initial-burn-check/`. `checkpoint-interface-check.json` is a separate synthetic recovery test.

`launch.json` identifies the active supervisor/worker. `progress-snapshot.json` is timestamped portable progress, while current local progress lives under ignored `runs/`. Check `status.json` and later `analysis.json` for completion and diagnostic limits. Live outputs are not committed continuously; the persistent supervisor syncs owned evidence hourly and at completion.

[Stage 9 method and status](../../../docs/reproduction/taiji-sgwb/template-formal.md). Do not interpret startup traces as a posterior or original schedule length as proof of convergence.
