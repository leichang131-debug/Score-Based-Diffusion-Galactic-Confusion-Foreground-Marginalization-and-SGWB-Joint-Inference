# Locally executed environment evidence

- `validation.json`: interpreter identity, package versions, check outcomes and timings, dependency-lock hash and outstanding example prerequisites.
- `validation.txt`: stdout/stderr from the actual environment check command.
- `installed-packages.json`: installed package inventory reported by `uv pip list`.
- `dependency-check.txt`: `uv pip check` output for the independent environment.
- `python312-build-failure.txt`: original failed Python 3.12 attempt, retained to substantiate the compatibility decision.
- `installation.txt`: successful final setup log after compatibility fixes.
- `kernel-smoke.ipynb`: new synthetic notebook executed by the dedicated local kernel, not a copied upstream example.
- `manifest.json`: hashes of configuration, setup/validation scripts and curated environment evidence.

These files demonstrate local environment/interface execution only. No original example notebook was executed here and no nested sampling run was performed. Historical upstream notebook outputs remain reference material. See the [setup report](../../../docs/reproduction/triangle-gb/environment-setup.md).
