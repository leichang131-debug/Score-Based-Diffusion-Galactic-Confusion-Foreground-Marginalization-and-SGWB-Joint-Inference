# Public VGB download and local input-check evidence

- `download-provenance.json`: original filenames, official record/metadata/download URLs, sizes, MD5, local SHA-256, verification timestamps and timings.
- `download.txt`: actual download/check stdout.
- `hdf5-schema.json`: all groups/datasets, shapes, types, storage information and full-array NaN/Inf/finite counts.
- `validation.json`: unchanged tutorial-cell hashes, original source selection, preprocessing results, actual orbit coverage and boundary-query diagnostics.
- `validation.txt`: actual local input-check stdout/stderr.
- `initial-coverage-failure.txt`: initial strict assertion failure retained as evidence of the uncovered orbit range; later diagnostics quantify it without masking it.
- `manifest.json`: hashes of scripts, documentation and evidence, plus separate local input-file hashes.

Seven input-preparation checks pass. The eighth check, strict orbit coverage, fails. The final checker exits **2** intentionally when the structured report records this gap; it is not a download failure, numerical NaN failure or a full notebook execution. Do not change this result to a success merely because default orbit extrapolation returns finite values.

Original input files stay in ignored `data/raw/triangle-gb/`; no search, waveform fitting, posterior sampling, plotting or full example reproduction took place. See the [report](../../../docs/reproduction/triangle-gb/data-preparation.md).
