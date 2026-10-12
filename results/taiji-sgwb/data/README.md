# TaijiSGWB official 2.8 input evidence

Stage 3: 24/24 actual data/orbit/interface checks passed. The official dataset and orbit filenames are preserved in ignored raw storage. The two original demo read/AET/trim interfaces ran locally.

- `zenodo-record.json`, `zenodo-latest.json`: official dataset-version and file metadata snapshots.
- `download.json`, `download-ranges.json`: official MD5, local SHA-256, orbit Git identity and verified download ranges.
- `hdf5-inventory.json`: all 40 data and 10 orbit datasets; shapes, dtypes and full numeric scans.
- `validation.json`, `validation-execution.txt`, `run.json`: actual checks, component identities, injection parameters, orbit coverage and command timings.
- `path-map.json`, `path-execution.txt`: original-demo filenames supplied by ignored relative symlinks.
- `input-preview.npz`: first 128 actual input samples/components, not generated simulation output.
- `analysis-grid.npz`: original analysis frequency/time geometry and interpolated light times, not full STFT/CSD output.
- `official-reference/`: pinned generation-source extracts, provenance and original license; no upstream output reuse.
- Earlier download and validation logs: retained local transfer/tooling history explained in the report.
- `audit.json`, `manifest.json`: input/evidence/source checks and portable file hashes.

[Stage 3 report](../../../docs/reproduction/taiji-sgwb/data-preparation.md). Full preprocessing, response grids and inference remain pending.
