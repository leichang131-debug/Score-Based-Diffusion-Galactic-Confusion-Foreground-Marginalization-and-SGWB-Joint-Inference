# Research roadmap

The current milestone is the ten-parameter full-covariance Taiji baseline. See the [Figure 8 reproduction plan](research-plan/full-covariance-baseline.md).

| Stage | Deliverable | Completion criterion |
| --- | --- | --- |
| Repository preparation | Baseline documentation and directory layout | Study, scope, and artifact locations are discoverable |
| Source and environment | Fixed upstream snapshot, separate environment, and six-fit campaign | Source identity and dependency checks pass |
| Reference replay and regenerated inputs | Archived Figure 8 reference and three fresh input bundles | Shapes, conventions, and original truth likelihoods agree |
| Production inference | Three full fits and three paired null fits | Sampler completion, restart and provenance records, posterior and evidence summaries |
| Benchmark and figure | Fresh Figure 8 and per-configuration runtime report | Recorded sample sources, evidence errors, and comparable timing |
| Foreground realism | Controlled anisotropy and data-model mismatch studies | Bias, coverage, and cost evaluated against the baseline |
| Score-based extensions | Conditional likelihood correction experiments | Independent validation against calibrated physical baselines |

Earlier reproduction milestones remain documented in the [reproduction index](reproduction/README.md). The [Route B plan](research-plan/README.md) records the earlier sequence for learned corrections.
