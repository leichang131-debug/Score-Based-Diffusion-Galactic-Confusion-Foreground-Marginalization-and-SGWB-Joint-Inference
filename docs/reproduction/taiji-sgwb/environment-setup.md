# TaijiSGWB Stage 2: independent environment and original import checks

Completed locally on macOS ARM64 with a dedicated Python 3.11.14 virtual environment. The original source remains pinned and unchanged. Environment checks: **25/25 passed**. Source preservation recheck: **13/13 passed** (offline, against the previously verified pin). Dependency consistency and all 51 locked package versions passed.

## Exact original import correspondence

The checker parses each original demo as data, extracts every top-level `import` and `from ... import ...` statement, and executes those exact AST nodes. It does not execute the demo body. The report preserves the original import text and file hashes.

| Original entry | Import statements executed | Result |
| --- | ---: | --- |
| `demos/template_nofg_28t.py` | 16 | All passed |
| `demos/rj_nofg_28t.py` | 19 | All passed |

All 13 package module/import paths also passed, including `analyorf`, `plotlib` and all detector modules. Editable-install metadata and the actual import path resolve to the pinned `external/taiji-sgwb/src/taijisgwb/` directory.

## Additional meaningful interface checks

- Original AET transform: synthetic shape and norm preservation.
- Original SciPy `ShortTimeFFT`, Kaiser-window and detrending API: finite `(65, 4)` output.
- Original power-law/double-broken-power-law functions, noise PSDs and Omega/PSD round trip.
- Synthetic HDF5 orbit written with the original `tcb` fields, then read through `InterpolationOrbit`; interpolation agrees at input samples. This is not validation of official orbit coverage.
- Original ACC/OMS transfer factors and numerical ORF using two times and three frequencies at the unchanged nside=14: finite shapes, positive auto-response and conjugate cross-response identity. This is a small-grid compatibility check, not full response convergence.
- Actual macOS fork pool with two workers.
- Fixed-dimensional Eryn API with the original `[6, 6, 2]` branch dimensions: two temperatures, 32 walkers, three stored steps on a synthetic Gaussian likelihood; HDF backend re-opened and last state read in a separate Python process. No continuation steps were tested in this stage.
- Original RJ move classes (`StretchMove`, `GaussianMove`, `CombineMove`), `State`, `compute_log_prior`, `compute_log_like` and `rj_moves=True`: eight steps on a synthetic likelihood, one to three active internal leaves observed. Priors, likelihood, leaf maximum and run lengths are explicitly reduced for this environment check; they are not the physical example settings.
- Headless Matplotlib file generation and the original plotting-module import. The original corner wrapper is imported, not numerically audited.
- Original source commit and clean checkout after all checks.

## Dependencies and installation issues

NumPy 1.26.4 and SciPy 1.13.1 preserve upstream pins. Eryn 1.2.6 is explicitly fixed and locally verified. h5py is added because original code imports it but the upstream dependency table does not declare it. Hatchling's editable build, with build isolation disabled, additionally required editables; it is included in the final hashed lock. No upstream source was patched.

The first setup attempt encountered a local launcher parsing error while the launcher was being updated; the initial log is retained. The following attempt diagnosed the missing editable-build helper. The finalized setup succeeded and was re-run successfully from the locked dependencies. The first checker passed 24/25: its path assertion did not decode percent-escaped spaces in the editable installation URL. The actual import was from the correct checkout. The checker was corrected using URL parsing/unquoting, and the final run passed 25/25. Original first-attempt reports and logs are retained to document these local tooling issues.

## Timing and execution evidence

`run.json` records the final setup/check command arguments, return codes and external wall time. The final warm-cache check process took approximately 1.79 seconds; its internal measured work took 1.69 seconds. The complete final setup/check wrapper took approximately 2.42 seconds. These are small interface checks after installation/font caching, not initial download time, full-demo execution time or an SGWB performance benchmark.

Full local toy backends and synthetic orbit/plot files are in ignored `runs/taiji-sgwb/environment-check/`. Portable logs, settings, chain shapes, cross-process readback evidence and installed versions are tracked under [results/taiji-sgwb/environment](../../../results/taiji-sgwb/environment/README.md). Files are covered by the evidence manifest.

## Reusable project interfaces

| Script | Interface |
| --- | --- |
| `setup-taiji-sgwb-macos.sh` | Install/sync hashed dependencies and pinned editable source |
| `run-taiji-sgwb-python.sh` | Launch Python in the independent environment with local cache/thread settings |
| `check-taiji-sgwb-environment.py` | Original imports and small synthetic API checks |
| `run-taiji-sgwb-environment-check.py` | Run checks, retain logs/timings and verify installed versions; optional `--setup` |
| `audit-taiji-sgwb-environment.py` | Audit evidence and original source, refresh hashes without sampling |

See [environment commands](../../../environments/taiji-sgwb/README.md).

## Remaining work

Stage 3 must obtain and validate the actual TDC II 2.8 dataset and associated orbit. Source-specific absolute paths, worker counts and full-grid response memory need a separately documented execution adapter. Existing synthetic checks do not prove full-year feasibility, converged posteriors, recovery/calibration, or complete paper reproduction.
