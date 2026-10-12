# TaijiSGWB Stage 5 preprocessing evidence

Both original demo prefixes were executed locally at full one-year scale. Each passed 20/20 checks. Their frequency, complex FFT and final CSD arrays are byte-identical.

- `template_nofg_28t/`, `rj_nofg_28t/`: exact source execution nodes/timings, original-named local ASD plot, complete checks, portable spectral/matrix summaries and worker resources.
- `run.json`: separate commands/PIDs, return codes, timings, memory samples and cross-entry scientific array hash parity.
- `attempts.json`, `attempts/template_nofg_28t/`: retained first attempts and the original overly strict exact-zero imaginary assertion.
- `audit.json`, `manifest.json`: source/array/cache correspondence and portable artifact hashes.

Full raw FFT/final weekly CSD caches remain in ignored `data/processed/taiji-sgwb/preprocessing/`. The exported full-year means are for plots and evidence; they do not replace weekly inference inputs.

[Stage 5 report](../../../docs/reproduction/taiji-sgwb/preprocessing.md). No ORF response grid or physical posterior sampling was run here.
