# Final small-scale Score-SDE evidence package

See the [final report](../../../docs/reproduction/score-sde/final-report.md).

- `loss_curve.png`: full and late warmup panels; individual versions are `loss-full.png` and `loss-late.png`.
- `loss_history.npz`: the teacher's four field names and original loop labels.
- `loss_history.csv`: all 200 training / 14 validation observations, run provenance and completed update counts.
- `runtime-summary.csv` / `.json`: measured invocation scopes and key timing results.
- `issues.csv`: resolved diagnoses and remaining limitations, with evidence scope.
- `logs/`: nine normalized completed-stage text logs; these are not byte-identical original logs.
- `evidence/`: three byte-identical original TensorBoard files in portable stage directories.
- `evidence-index.json`: original/copy hashes and provenance.
- `summary.json`: loss extraction and NPZ validation outcome.

Raw checkpoints and datasets are outside this small published package. The four earlier sampling arrays/previews and checkpoint manifests remain in their existing directories. This package demonstrates functionality, not converged or teacher-level numerical reproduction.
