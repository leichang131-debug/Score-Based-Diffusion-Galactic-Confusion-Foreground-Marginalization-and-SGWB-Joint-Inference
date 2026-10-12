# TaijiSGWB Stage 5: complete original preprocessing

Completed locally for both original programs: **20/20 numerical/interface checks passed per entry**, at full original one-year input scale. The independent runs produce byte-identical final frequency, complex FFT and CSD arrays. Full response construction and inference remain pending.

## Exact correspondence to original programs

- `external/taiji-sgwb/demos/template_nofg_28t.py`
- `external/taiji-sgwb/demos/rj_nofg_28t.py`

Both are pinned at `4afaad4044b08721e7f1ce29cba3b0d912636dce`. Same-name byte-identical working copies are retained under ignored `runs/taiji-sgwb/preprocessing/<entry-stem>/demos/`. The adapter executes every original top-level AST node from the beginning through the final notch selection, stopping before `orbit = InterpolationOrbit(...)`. It executes the original expressions and function bodies without modifying their AST.

The original PROJ_DIR assignment is followed by an explicitly recorded runtime override pointing to `runs/taiji-sgwb/workspace/`; __file__ points to the identical local working copy, so original PARENT_DIR output routing stays inside the ignored run. No scientific settings or source files are edited. In particular, npool=62 remains in the namespace but is unused because the response/sampling section is not reached. All execution nodes, source text, line numbers, hashes and per-node timings are preserved in each `source-execution.json`.

## Fully executed workflow

1. Read all original time/XYZ/foreground arrays; subtract provided foreground truth.
2. Transform to A/E/T and crop 400 samples (2000 seconds) at each end.
3. Use 52 full consecutive seven-day segments, each 120960 samples at dt=5 seconds. The remaining 20909 tail samples do not enter the original STFT.
4. Apply the original Kaiser window, beta=14, with constant detrending.
5. Run `ShortTimeFFT` with hop=120960, onesided mode, scale_to=psd, p0=0, p1=52 and k_offset=60480.
6. Form every complex auto/cross product using the original conjugate-first convention.
7. Average six adjacent raw bins and multiply the CSD by two.
8. Select merged-bin centers in [1e-4, 0.05) Hz.
9. Generate the original `asd_AET_nofg.png` plot before notch removal, including the original shaded intervals.
10. Remove original notch intervals [0.0235, 0.0265) and [0.047, 0.052) Hz.

These operations use the complete downloaded input; no time shortening, frequency narrowing or approximate FFT is introduced.

## Shapes and frequency bookkeeping

| Stage | Shape or count |
| --- | --- |
| Cropped AET time series | 3 channels × 6310829 samples |
| Full complex STFT | `(3, 52, 60481)` |
| Original unmerged cross products | `(3, 3, 52, 60481)` |
| Raw bins used for complete six-bin groups | 60480 |
| Raw remainder discarded | 1 (Nyquist) |
| Merged CSD | `(3, 3, 52, 10080)` |
| Selected band before notches | 5030 bins |
| Bins removed by notches | 604 |
| Final CSD | `(3, 3, 52, 4426)` |

Actual merged spacing is 9.92063492063492e-6 Hz. Final frequencies match Stage 3 geometry exactly. The original plot is based on the in-band arrays before notch removal, while the inference cache's final arrays exclude the notch bins.

## Independent numerical verification

A separate direct NumPy rFFT implementation processes every channel of every week from contiguous, mean-subtracted data. It explicitly applies the same PSD window normalization and a half-window circular roll that accounts for SciPy's default centered phase convention. The roll matters for complex FFT equality; a common phase cancels in cross products. The reference constructs cross products and merged/masked spectra separately from the original ShortTimeFFT implementation.

| Check | Measured result |
| --- | --- |
| Maximum week/channel FFT relative L2 difference | 7.360703e-16 |
| Full final CSD relative L2 difference | 1.247945e-15 |
| Maximum windowed Parseval relative error | 1.776357e-15 |
| CSD Hermitian relative discrepancy | 4.043635e-17 |
| Largest diagonal imaginary/real ratio | 4.287454e-17 |
| Matrices checked | 230152 |
| Minimum eigenvalue after diagonal normalization | 7.298798e-06 |
| Largest squared coherence, including autos | 1.0 |

FFT, Parseval and independent CSD tolerances are 1e-12 relative; Hermitian tolerance is 1e-14 relative. Diagonal imaginary terms are bounded by 8×float64 machine epsilon (approximately 1.776e-15 relative). No original matrix is symmetrized, projected to real or otherwise changed. All diagonal real powers are positive; normalized matrices pass the declared eigenvalue tolerance. These are numerical consistency checks, not proof of Gaussianity, independent frequency bins or posterior calibration.

The original two-factor applies to every merged raw CSD bin. DC and Nyquist need different factors when checking a full one-sided Parseval sum, so the independent energy check uses one at the endpoints and two in the interior. DC does not survive the analysis band mask and Nyquist is outside the selected band (and discarded before merging). The retained inference grid therefore contains interior positive frequencies with the original factor two.

The original normalized equivalent noise bandwidth is 2.16114357268853 raw bins. Neighboring windowed frequencies may be correlated; preserving the original ENBW weighting does not independently validate the approximate likelihood or its uncertainty calibration. That is a later stage.

## Reusable cache and index convention

Each entry has an ignored `data/processed/taiji-sgwb/preprocessing/<entry-stem>/preprocessing.h5` cache of 222819488 bytes. Each contains:

- `strain_segs`: full complex unmerged FFT, axes `[channel, week, raw_frequency]`.
- `csd_est`: full final CSD, axes `[channel_i, channel_j, week, merged_frequency]`.
- `frequency`, `segment_center`, `window`.
- `frequency_before_notch`, `csd_before_notch` for original plot correspondence.
- Original source/input hashes, configuration, window normalization and index metadata.

The final matrix is `CSD[i,j] = 2 * mean(conj(STFT[i]) * STFT[j])` over each six-bin group. Some covariance conventions instead use `STFT[i] * conj(STFT[j])`; they are conjugate transposes. Future likelihood/model code must preserve the original contraction convention, especially for nonzero imaginary cross spectra. No silent transpose is performed. Weekly matrices are kept individually: the full-year mean in portable plot summaries is not the inference input.

`load_preprocessing_cache(filename)` in `scripts/reproduction/taiji_sgwb_preprocessing.py` returns final frequency/CSD arrays, weekly midpoints, nperbin, win_bw and metadata without rerunning preprocessing. Readback matched original arrays exactly. Raw FFT data remain available in HDF5 without being loaded by that helper.

Portable files in each results folder include the original-named plot, full-frequency mean CSD summaries, selected actual matrices, configuration/results, source correspondence, execution log and sampled resources. Cache file hashes and scientific array hashes are recorded; cache bytes differ between entries because provenance attributes identify different programs, while all scientific array hashes match. Large caches and raw inputs are ignored by Git.

## Actual runtime and memory

| Entry | Original prefix (s) | Full worker, validation/export included (s) | Sampled peak worker RSS (GiB) |
| --- | ---: | ---: | ---: |
| `template_nofg_28t` | 1.357 | 2.472 | 1.570 |
| `rj_nofg_28t` | 1.289 | 2.361 | 1.638 |

Total final two-run wrapper: 4.835 seconds. Data are already local and cached; this is a single full-year preprocessing pass plus a direct FFT reference. It is not the runtime of SGWB response integration or MCMC. The original-prefix timing includes imports, reads, all preprocessing and plotting. Parent wall timing additionally includes interpreter startup, validation, exports, hashing and process-monitoring overhead. RSS was sampled every approximately 0.1 seconds and can miss shorter peaks; it is neither total system memory nor future response memory demand.

## Retained issues and first attempts

An initial sandbox invocation denied `ps` resource monitoring; the finalized wrapper was run with process monitoring available. The wrapper now records monitoring failures rather than aborting scientific execution.

The first template check passed 19/20; its exact imaginary==0 assertion rejected tiny complex multiplication roundoff. Inspection found a maximum relative imaginary term of 4.287454433616065e-17, below float64 epsilon. The corrected explicit roundoff criterion passes without changing original arrays. The first failed report/log/resources are retained under `attempts/template_nofg_28t/`; the audit verifies its scientific array hashes equal the final successful run. This local validation-criterion correction is distinct from a source defect.

The first saved-summary audit also used exact equality for a derived time mean. Recomputing the mean after contiguous HDF5 readback changes the floating-point reduction order relative to the original masked-array layout: relative L2 difference is approximately 2.287032e-16. Full FFT/CSD/frequency hashes matched exactly. The audit now bounds the derived mean discrepancy by 32×float64 epsilon, while retaining the original summaries and recording the initial failed audit under attempts/first-audit.json. No scientific input array was changed.

## Run and audit

From the repository root:

```bash
python3 scripts/reproduction/run-taiji-sgwb-preprocessing.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-preprocessing.py
```

The first command performs both full prefixes in separate processes and collects logs/resources. The second reads existing caches/evidence, rehashes arrays and source, checks original node correspondence and exports a manifest without repeating FFT calculations. Full source/work copies preserve both original Python filenames and comments.

## Next stage

Stage 6 will compute/cross-check and cache original instrument-noise transfer factors and the SGWB ORF on the verified grid, with bounded memory where needed. Stage 7 will independently verify the spectral model, CSD contraction and likelihood normalization. No physical posterior or scientific parameter-recovery claim is made by Stage 5.
