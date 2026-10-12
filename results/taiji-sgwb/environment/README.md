# TaijiSGWB Stage 2 environment evidence

Final local result: 25/25 environment and small synthetic interface checks passed. The complete source recheck passed 13/13; all 51 locked third-party versions match the installed environment, with the pinned editable original package installed separately.

- `check.json`, `execution.txt`: actual original imports, module paths, versions, synthetic response/sampler/backend results.
- `run.json`: command arguments, return codes, externally timed wall durations and lock parity.
- `setup-execution.txt`, `dependency-check.txt`: final successful installation and dependency checks.
- `source-audit/`, `source-check.txt`: original source identity and byte/mode preservation after execution.
- `first-check.json`, `first-check-execution.txt`: first path-validation failure retained; explained in the Stage 2 report.
- `install.txt`, `install-retry.txt`, `install-final.txt`: setup history including diagnosed launcher/build-helper issues and successful installation.
- `audit.json`, `manifest.json`: evidence integrity checks and SHA-256 for evidence, scripts, environment specifications and report.

The toy likelihoods and small arrays only establish environment/API compatibility. No official TDC data or full upstream demo was run in this stage. Full local synthetic artifacts remain in ignored `runs/taiji-sgwb/environment-check/`.

[Stage 2 report](../../../docs/reproduction/taiji-sgwb/environment-setup.md)
