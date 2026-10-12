# Triangle-GB core CPU interface verification

## Outcome

The verification work completed locally. **22 of 28 checks passed; 6 failed. Package-wide acceptance did not pass.** Do not interpret script exit code zero, an evidence-integrity audit, or completion of five example notebooks as proof that every original interface is correct.

The checks use the pinned unmodified source, public imports, original three-detector analytic orbit configuration, three deterministic synthetic GB sources, 65,536 time samples at 10 seconds, and independently computed numerical references. This is a targeted small CPU test suite, not another full-scale tutorial or posterior rerun. Raw and real-waveform boundary probes make truncation defects observable.

Whole-process time including imports: 3.611 s for the two sequential commands. Core computational section: 0.446 s; actual command timings are in `run.json`. These timers have different scopes. No GPU, arbitrary-orbit accuracy, complete auxiliary-method coverage or posterior calibration is claimed.

## Passed paths

Original package imports and module origin; batched vs single-source frequency responses; full spectral scatter and vectorized wide-band filling; full/intrinsic parameter coordinate round-trips; explicit XYZ-to-A/E/T transform; likelihood from the explicit residual formula; SNR and mismatch normalization; F-statistic vs an independent real four-amplitude least-squares solution; non-default time response batch consistency; six-channel network vs three separately instantiated single-detector responses; network source batching; declared rejection of network time mode; positive-frequency auxiliary PSD smoke checks; source pins and clean checkouts.

Likelihood agreement relative error is 7.119e-17; independent F-statistic relative error is 4.862e-16. Network/single-detector and batch/single-source responses match exactly in the selected configurations.

## Unresolved original issues

### 1. Default time-domain output is all zero

`TDIFlyGB.__call__(domain="time")` assigns `res[:, -self.drop_points:] = 0`. For the default `drop_points=0`, `-0` is zero and this clears the entire array. A nonzero injection therefore returns zero. With explicit `drop_points=1`, the original branch produces finite nonzero outputs and batch/single results agree. This is a diagnostic contrast, not a source repair and not approval to silently replace the default.

The first official example's independent time reference does not directly validate this package time branch. Frequency-domain tutorial calls do not execute this zeroing statement.

### 2. Vectorized partial-band fill overwrites boundary bins

`fill_fftseries` clips all indices to StartBound/EndBound before assignment, rather than discarding out-of-band samples. Repeated clipped indices overwrite the edge bins with out-of-band data. The synthetic partial-band probe and a real generated response both disagree with independent cropping; interior bins agree in the assessed original Example 2. Wide bands containing the complete support pass.

### 3. Loop fill fails on the tested wide band

When a source starts after StartBound, `fill_fftseries_loop` sets `temp_start_idx=StartBound-start_idx_event`, a negative offset. In the tested wide-band case this leads to an empty destination slice and a broadcast ValueError. The tested narrow overlapping case passes. It is not safe to recommend this helper as a universal replacement for vectorized filling.

### 4. Selected time/frequency accuracy criterion not met

Using explicit `drop_points=1`, the rectangular 7.59-day comparison does not achieve the predeclared 1% relative-norm smoke tolerance at either 128 or 4096 sparse points. Increasing resolution decreases the error:

| Nsparse | Relative norm difference |
|---:|---:|
| 128 | 8.0071% |
| 512 | 3.9126% |
| 1024 | 2.7436% |
| 2048 | 1.9230% |
| 4096 | 1.3668% |

These are **two failed precision checks**, not evidence of an additional proven algebraic bug. Sparse approximation, finite support, envelope endpoint discontinuity/aliasing, and endpoint dropping require a controlled window/observation/resolution study. The failure is not relabeled as success or erased by increasing the tolerance. This short test is not numerically comparable to the first tutorial's year-scale, differently constructed time-domain reference and mismatch metric.

## Impact on existing tutorials

Original Example 2, at its recorded injection and exact time-axis SHA-256: Nsparse=512, analyzed bins [151669, 151825], sparse start [151491]. The original vectorized template differs from independent proper cropping by **0.4512%** in relative norm. Interior bins are exactly equal. Original truth log likelihood is -308.305743201; mathematical-crop reference is -308.241104415; difference is **0.064638786**.

This confirms a real, small but nonzero boundary effect in that assessed template. It does not bound the effect at every posterior sample or prove posterior bias is negligible. Neither the original posterior nor its existing evidence is replaced. Examples 0, 1 and 3 also use vectorized filling; their actual boundary impacts have not been quantified in this milestone and should not be assumed zero.

For the network tutorial's original injection, its 1024-bin sparse support lies completely inside the analyzed band; the saved six-channel injected signal reproduces. That injection does not trigger the clipping defect. This is not a proof for every network posterior sample, and does not resolve posterior angle mode weights or calibration.

## Complete check ledger

| Check | Result | Relative error or exception |
|---|---|---|
| actual_public_imports_and_origins | PASS | — |
| frequency_batch_vs_single | PASS | 0.0 |
| frequency_shape_finite_nonzero | PASS | — |
| full_fft_fill_independent_scatter | PASS | — |
| fill_vectorized_wide_band | PASS | 0.0 |
| fill_loop_wide_band | FAIL | ValueError('could not broadcast input array from shape (3,128) into shape (3,0)') |
| fill_vectorized_clipped_band | FAIL | 0.006365249874555233 |
| fill_loop_clipped_band | PASS | 0.0 |
| fill_vectorized_clipped_physical_signal | FAIL | 0.011449956712360059 |
| full_parameter_roundtrip | PASS | 0.0 |
| intrinsic_parameter_roundtrip | PASS | 0.0 |
| XYZ_to_AET_independent | PASS | 0.0 |
| XYZ_to_AE_matches_AET | PASS | 0.0 |
| likelihood_explicit_residual | PASS | 7.119136404233238e-17 |
| SNR_explicit_integral | PASS | 0.0 |
| mismatch_explicit_overlap | PASS | 0.0 |
| Fstatistics_independent_lstsq | PASS | 4.86244039842218e-16 |
| time_default_nonzero | FAIL | — |
| time_batch_vs_single_drop_one | PASS | 0.0 |
| time_drop_one_finite_nonzero | PASS | — |
| time_FFT_vs_sparse_frequency_drop_one | FAIL | 0.08007121628697524 |
| time_FFT_sparse_convergence_4096 | FAIL | — |
| network_vs_single_detectors_order | PASS | 0.0 |
| network_batch_vs_single_sources | PASS | 0.0 |
| network_time_explicitly_unsupported | PASS | — |
| auxiliary_PSDs_positive_finite | PASS | — |
| triangle-gb_pin_clean | PASS | — |
| triangle-simulator_pin_clean | PASS | — |

## Reproducibility and evidence

Run from the main repository:

```sh
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-core-validation.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/report-triangle-gb-core.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-core.py
```

`results/triangle-gb/core-validation/` retains all check statuses, exact test parameters/seeds, host/runtime/command records, stdout/stderr, band arrays, comparison figures, real tutorial boundary references and SHA-256 manifest. Package-level failures are separate from evidence-integrity audit status.

Upstream source remains pinned and clean. Fixes should be developed later as explicit reviewed patches or an upstream update, with before/after verification. These findings are not a claim that the five tutorial reproductions were fabricated or failed to run; they limit the numerical guarantees that can be inferred from those reproductions.
