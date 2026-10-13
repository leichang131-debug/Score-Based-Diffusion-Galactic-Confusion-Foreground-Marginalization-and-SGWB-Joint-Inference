# TaijiSGWB Stage 7 evidence

Both original full-grid spectral likelihoods have passed 206/206 checks on the local CPU. No MCMC updates or posterior calibration were performed. Original source is unchanged.

- `validation.json`, `likelihood-comparisons.csv`: original vs independent results, priors, covariance conditioning, interfaces and input hashes.
- `determinant-warning-controls.json`: independent real/complex identity controls for NumPy warnings.
- `spectral-summary.npz`, `spectral-likelihood-check.png`: portable diagnostics; amplitude scan is conditional, not posterior.
- Per-entry `source-execution.json`: exact original nodes and identical same-name working copies.
- `execution.txt`, `run.json`, `resources.csv`: real local command, PID, outcome, time and memory.
- `attempts/`: retained checks and external harness issues, not source patches.
- `audit.json`, `manifest.json`: integrity and artifact hashes.

[Full Stage 7 report](../../../docs/reproduction/taiji-sgwb/likelihood.md).
