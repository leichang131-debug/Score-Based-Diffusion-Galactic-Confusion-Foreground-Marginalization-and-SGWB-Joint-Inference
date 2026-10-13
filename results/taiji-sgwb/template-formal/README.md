# TaijiSGWB formal template inference

**Initial launch state: RUNNING. Read `status.json` for the current published outcome; posterior results are unavailable until sampling and analysis finish.**

Configuration: 1000 unrecorded burn transitions + 350 saved ensembles at thin_by=12, six temperatures, 62 walkers, four CPU workers, full verified grid. The first ten real burn updates and numerical checks are archived in `initial-burn-check/`. `checkpoint-interface-check.json` is a separate synthetic recovery test.

`launch.json` identifies the active supervisor/worker. `progress-snapshot.json` is timestamped portable progress, while current local progress lives under ignored `runs/`. Check `status.json` and later `analysis.json` for completion and diagnostic limits. Live outputs are not committed continuously; the persistent supervisor syncs owned evidence hourly and at completion.

[Stage 9 method and status](../../../docs/reproduction/taiji-sgwb/template-formal.md). Do not interpret startup traces as a posterior or original schedule length as proof of convergence.
