# TaijiSGWB Stage 6 response evidence

Full original-grid response calculation completed locally: 32/32 checks passed. Both original programs' response nodes/settings and unblocked control results agree; one shared full cache is available to both. Original source is unchanged.

- `validation.json`: full shapes, original sky settings, controls, matrix checks, cache/array hashes and timings.
- `run.json`, `execution.txt`, `resources.csv`: actual command, PID, return code, local timings and memory samples.
- `block-timings.json`: all 611 actual blocks and original-call/reuse counts.
- `unblocked-controls.npz`: original, reused and alternate-block ORF reference arrays, and actual noise controls.
- `response-summary.npz`, `orf-auto.png`: portable summaries of full cached responses, not replacement weekly inference arrays.
- `report-execution.txt`: diagnostic regenerated from the saved cache without recomputation.
- `template_nofg_28t/`, `rj_nofg_28t/`: exact original response-node correspondence and shared-cache reference.
- `initial-benchmark.json`, `attempts/`, `attempts.json`: initial timing and retained parser-boundary issue.
- `audit.json`, `manifest.json`: evidence/source/cache checks and portable artifact hashes.

Full `response.h5` remains in ignored `data/processed/taiji-sgwb/response/`. [Stage 6 report](../../../docs/reproduction/taiji-sgwb/response.md). Physical likelihood and posterior sampling remain pending.
