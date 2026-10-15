# Research results

Track curated figures, tables, summaries, and artifact manifests here. Each result must point to its configuration, source version, environment, seed, data provenance, and validation status. Results are now available for Score-SDE, TDC, Triangle-GB and TaijiSGWB; see the status table below.

Large checkpoints, data, and posterior chains should have durable storage locations and checksums in manifests. Use laboratory storage, Git LFS, or releases as appropriate; do not silently omit the record of a result.

## Current evidence (2026-10-15)

| Component | Entry point | Interpretation |
| --- | --- | --- |
| Score-SDE | [Final summary](score-sde/final-summary/README.md) | Small-scale workflow, not 214k quality reproduction |
| Triangle-Simulator | [Four tutorial reports](../notebooks/reproduction/triangle-simulator/README.md) | Original-default local execution; Tutorial 5 excluded |
| Triangle-GB | [Example and core evidence](triangle-gb/README.md) | Five examples executed; six core-check failures retained |
| TaijiSGWB | [Formal template results](taiji-sgwb/template-formal/README.md), [figure/source review](taiji-sgwb/review-20261015/README.md) | 2.8 template schedule complete; convergence unconfirmed, EQ/RJ not sampled |

Timestamped attempts, preparation-only reports and paused checkpoints describe their own historical stages. Use current component status for present progress; do not overwrite original failure or pause evidence to make it look current.
