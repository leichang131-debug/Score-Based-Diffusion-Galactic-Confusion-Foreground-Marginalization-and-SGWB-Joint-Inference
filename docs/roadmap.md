# Research roadmap

| Stage | Planned deliverable | Completion criterion |
| --- | --- | --- |
| Repository foundation | English architecture and archived research plan | Files and version history accessible |
| Reference reproduction | Score-SDE, TDC, and TaijiSGWB reports | Minimal workflows and exact environment records |
| Numerical controls | Solvable likelihood and posterior experiments | Agreement with independently known results |
| Physical baselines | Consistent data adapter and fair baselines | Correct units, response, covariance, and validation |
| Conditional score model | Training and normalized density evaluation | Numerical closure and held-out diagnostics |
| Joint inference | Four-scale posterior and SGWB marginal | Stable inference with calibration checks |
| Attribution and realism | Covariance-matched controls and mismatch studies | Documented mechanism and applicability limits |

The repository foundation and several reference workflows are now complete locally: Score-SDE small-scale training/recovery/sampling, four Triangle-Simulator tutorials, five Triangle-GB examples and the full TaijiSGWB 2.8 template schedule. Score-SDE quality reproduction, six Triangle-GB core-check failures, TaijiSGWB convergence and EQ/RJ comparisons remain unresolved. See [current reproduction status](reproduction/README.md). The conditional score model, unknown-foreground joint inference, calibration and attribution experiments remain future research. A publication venue is a research ambition, not a guaranteed outcome.
