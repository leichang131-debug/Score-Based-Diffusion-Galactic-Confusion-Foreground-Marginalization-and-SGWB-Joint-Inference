# TaijiSGWB source-only evidence

Pinned upstream commit: `4afaad4044b08721e7f1ce29cba3b0d912636dce`.

- `file-list.txt`: exact original paths for all 19 files.
- `manifest.json`: byte count, SHA-256, pinned Git blob ID and file mode for each file.
- `audit.json`: source identity, completeness, clean checkout, license, syntax and current upstream reference checks.

Produced by `scripts/reproduction/audit-taiji-sgwb-source.py`. This evidence establishes Stage 1 source preservation only. No upstream package imports, environment deployment, data download or inference execution have occurred in this stage.
