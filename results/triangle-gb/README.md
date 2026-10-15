# Triangle-GB reproduction evidence

Updated: 2026-10-15. All five upstream example notebooks have completed fresh local execution with original source, Markdown, filenames and defaults.

- `source/`, `environment/`, `data/`, `sangria/`, `fisher/`, `prerequisites/`: source pins, installed dependencies, official checksums, input validation and Fisher interfaces. These folders record preparation stages.
- `example-0/`, `example-1/`, `example-2/`, `example-3/`, `network/`: actual local execution, original-named notebooks, figures, diagnostics, commands, logs, timings and artifact manifests.
- `core-validation/`: 22/28 checks passed; six original interface/precision failures retained. Successful notebook execution does not establish package-wide acceptance or posterior calibration.

The original VGB strict orbit-coverage gap and sampler/angle-degeneracy limitations remain documented. Original reference images are separate from local outputs. Bulk inputs/caches remain ignored. See [current reports](../../docs/reproduction/triangle-gb/README.md).
