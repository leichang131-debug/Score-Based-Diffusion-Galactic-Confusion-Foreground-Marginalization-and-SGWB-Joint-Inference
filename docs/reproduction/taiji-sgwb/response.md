# TaijiSGWB Stage 6: original response, bounded controls and cache

Completed locally on the complete Stage 5 grid: **32/32 checks passed**. Original ACC/OMS transfer arrays and SGWB ORF are cached for all 52 weekly midpoints and 4426 retained frequencies. The two original examples share the cache after their preprocessing settings, response-node text and actual control results are verified identical. No physical likelihood or posterior sampling has run in this stage.

## Original source and entry correspondence

Original source is unchanged at `4afaad4044b08721e7f1ce29cba3b0d912636dce`. Both `demos/template_nofg_28t.py` and `demos/rj_nofg_28t.py` keep their original names, comments and byte contents. Same-name full working copies are preserved under ignored `runs/taiji-sgwb/response/<entry-stem>/demos/`.

The adapter extracts and executes the original response nodes: orbit construction, interferometer construction, original weekly-midpoint formula, noise-array allocation/loops, unit-amplitude noise spectra, ORF allocation and the six-pair ORF loop. Original code text, line numbers and source hashes are retained in each entry's `source-execution.json`. Local PROJ_DIR and the already verified preprocessing variables are supplied by the caller.

The full noise nodes execute on the entire grid using the template program. Both original noise sections additionally execute on the same three actual control times and 32 actual frequencies; the control subset uses an explicitly recorded t_seg override after the original formula assignment. Both original ORF loops execute without blocking/reuse on that same control grid. Their response node text and input settings match; consequently, the common full response is computed once rather than duplicating identical arrays for two entries. This is one full shared cache with two verified original interfaces, not two independent full ORF runs.

## Methods and unchanged physics

The underlying original functions remain:

- `InterpolationOrbit` on the official downloaded `MicroSateOrbit.hdf5`.
- `Interferometer.calc_noise_acc_corr_factor` and `calc_noise_ro_corr_factor`.
- `TaijiNoisePSD.calc_psd_acc(f, 1.)` and `calc_psd_ro(f, 1.)`.
- `Interferometer.calc_orf`, internally calling original `calc_gw_response` and `calc_oneway_response`.

TDI uses the original `tdi_aet_from_tdi_x(tdi_X2)` A/E/T combinations. The ORF uses the unchanged hardcoded nside=14, all 2352 original sky pixels, both polarizations, the original factor one-half and original mean over sky pixels. No equal-arm substitution, reduced sky grid, frequency interpolation or weekly averaging is introduced into the full cache.

## Why and how blocking works

A single unblocked complex sky array would hold 52×4426×2352 values: 8661080064 bytes (about 8.07 GiB). The original functions need multiple arrays of this scale, so a full monolithic ORF call was not attempted on the 16 GB laptop.

The full ORF loop is executed on blocks of four weeks × 96 frequency points, including all remaining edge points. One maximum-size complex sky array is 14450688 bytes (about 13.78 MiB). There are 611 blocks; the evidence audit independently checks every time-frequency point is covered exactly once. Blocking slices input axes only; each retained point still uses the original entire sky quadrature.

Within each block, a context manager temporarily memoizes `calc_gw_response` output for a channel, after checking exact longitude/latitude/frequency/time input equality. `calc_orf` itself is unchanged. Its six channel pairs normally request nine channel responses; three original channel calls and six identical-input reuses suffice. The cache is cleared and the instance restored at every block boundary, including exception exit. No spherical response formula or reduction is reimplemented by this optimization.

## Unblocked and cross-entry controls

The actual control mesh includes weekly indices 0,26,51 and 32 frequencies spanning the retained band; exact indices and arrays are archived. Reference calls execute the original ORF allocation/loop unblocked with no response reuse. A second calculation splits this mesh into two-time/seven-frequency blocks, different from the full-grid block size.

| Control | Measured relative L2 difference |
| --- | ---: |
| Reused channel responses vs direct original ORF | 0.000000e+00 |
| Alternate blocked mesh vs unblocked original ORF | 4.382697e-19 |
| Full ORF cache at original control points vs unblocked original | 0.000000e+00 |
| Original ACC control nodes/direct calls vs full-grid subset | 1.886508e-17 |
| Original OMS/RO control nodes/direct calls vs full-grid subset | 0.000000e+00 |
| Two original ORF sections on the same mesh | 0.000000e+00 |

Declared control tolerance: 1e-11 relative. Direct reference arrays, blocked/reused arrays and noise controls are retained in `unblocked-controls.npz`. The control benchmark showed approximately 0.275 seconds for direct calls and 0.094 seconds with reuse; this is a small-grid observed speed difference, not a guaranteed speedup for all hardware.

## Complete response arrays and numerical properties

| Original variable/cache field | Shape |
| --- | --- |
| `f_est` | `(4426,)` |
| `t_seg` | `(52,)` |
| `acc_corr_factor` | `(3, 3, 6, 52, 4426)` |
| `ro_corr_factor` | `(3, 3, 6, 52, 4426)` |
| `spectrum_acc`, `spectrum_ro` | `(4426,)` each |
| `orf` | `(3, 3, 52, 4426)` |

All arrays are finite. Original lower cross terms are filled by conjugation. Diagonal response powers are nonnegative. Hermitian relative tolerance is 1e-14; diagonal-normalized matrices pass the semidefinite tolerance of 128×float64 epsilon, approximately 2.842e-14. The minimum normalized eigenvalues are approximately -1.904e-15 for ACC, -1.885e-15 for OMS/RO and +2.971e-13 for ORF. Per-link noise matrices are rank-one Gram contributions, so roundoff-scale negative eigenvalues are retained rather than projecting or modifying original results.

The small positive ORF eigenvalue indicates some standalone signal-response matrices are nearly singular. Stage 7 must inspect conditioning of the combined noise-plus-signal covariance and validate its inversion/log determinant. Passing response checks does not validate that subsequent inference or posterior uncertainties are calibrated.

## Array index convention and parameter ordering

Channel order: A,E,T. Original link order: **12,13,23,21,31,32**. This is not alphabetical order. The HDF5 metadata explicitly records it; subsequent code must map injected parameters or fitted amplitudes to this order.

Noise arrays have axes `[channel_i, channel_j, link, week, frequency]`; ORF has `[channel_i, channel_j, week, frequency]`. Response cross terms follow `response_i * conjugate(response_j)`, as in the original functions. Stage 5 measured CSD used `conjugate(data_i) * data_j`; these conventions must be retained in the original likelihood contraction rather than silently transposing either cache.

`spectrum_acc` and `spectrum_ro` use unit amplitude. Stage 7 multiplies them by each original link amplitude squared and sums corresponding transfer contributions. They do not contain a fitted or fixed six-link noise realization. Weekly response matrices are retained individually; the figure and portable time means are only summaries.

## Cache and callable interfaces

Full cache: `data/processed/taiji-sgwb/response/response.h5`, 430959976 bytes (about 431 MB). SHA-256: `4e8f12c8371a6afa84fdb7f7b3401968d3d23c9433d201cbd14d5a8e0cd2ca13`. Large caches stay ignored by Git.

`load_response_cache(filename)` in `scripts/reproduction/taiji_sgwb_response.py` returns all seven original named arrays and provenance metadata. A complete readback check passed exact array equality. Original orbit, frequency/time hashes, sky settings, block dimensions, axis conventions and compatible entries are embedded in HDF5. Both entry-specific `cache-reference.json` files identify the shared cache.

Project interfaces:

- `original_response_nodes`: identify the exact original noise and ORF nodes.
- `initialize_original_response`: call original noise nodes with supplied verified inputs.
- `original_orf_block`: call the exact original allocation/ORF loop for a supplied block, with optional identical-input reuse.
- `load_response_cache`: subsequent model/likelihood readback without recomputation.

From the repository root:

```bash
python3 scripts/reproduction/run-taiji-sgwb-response.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/report-taiji-sgwb-response.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-response.py
```

The first command runs the full calculation and collects logs/resources. The second generates a readable diagnostic from the saved cache, with excluded bands shaded and gaps not connected. The third verifies original source nodes, array hashes, cache/summary integrity and exact block coverage without repeating ORF calculation. Configuration is recorded in `configs/reproduction/taiji-sgwb/response-macos.json`.

## Local execution and resources

- Original full-grid noise section: 1.979 seconds.
- Complete blocked ORF: 226.186 seconds.
- Parent-observed complete worker, including controls/validation/cache/export: 231.255 seconds (about 3 minutes 51 seconds).
- Sampled maximum worker RSS: 1.645 GiB.

The single CPU worker uses numerical-thread limits of one. RSS is sampled every approximately 0.5 seconds and may miss short peaks. It is not total system memory and does not predict MCMC memory or runtime. Per-block actual timings and call/reuse counts are preserved for all 611 blocks.

## Retained initial issue and scope

The initial adapter boundary check included RJ's `log_f_est` statement following the ORF loop, which belongs to spectrum/likelihood setup. The parser now explicitly ends at the original ORF allocation and loop. The failed initial log, return code, timings and resource samples are retained under `attempts/initial-boundary-check/`. No original source or physics was patched.

This stage verifies reproduction of the original numerical response at its original sky resolution. Higher-resolution sky quadrature convergence and segment-midpoint approximation errors are not assessed. Stage 7 likelihood checks, Stage 8 template recovery and the Stage 9 original full-data template schedule have since completed. Posterior convergence/calibration and EQ/RJ sampling remain incomplete; see [current status](status-and-cluster-handoff.md).
