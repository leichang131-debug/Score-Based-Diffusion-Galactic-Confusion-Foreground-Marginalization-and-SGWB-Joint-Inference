# TaijiSGWB selected-data template workflow reproduction

**Workflow completed; posterior convergence is not confirmed.** This real local experiment executes selected-data preparation, exact original likelihood validation, MCMC, state save/exit/restart, sampling diagnostics and finite-sample posterior summaries. It is not the original full-year inference or the paper's numerical result.

Status is `SUBSET_WORKFLOW_COMPLETE_CONVERGENCE_NOT_CONFIRMED`. Preparation passed **31/31** checks; stored-state/recovery/numerical workflow passed **11/11** checks. Only **2/14** parameters pass the declared limited sampling-diagnostic flags. These are separate outcomes: no numerical/recovery failure is being hidden as a convergence issue.

## Original method and selected inputs

The entire upstream tree remains pinned to `4afaad4044b08721e7f1ce29cba3b0d912636dce`, with all 19 tracked files unchanged. Original program name `template_nofg_28t.py`, original backend name `template_AET_nofg.h5`, model definitions, priors, original initialization statements and original sampler-constructor nodes are preserved. Exact source text and line correspondence are archived. New adapters stay under project-owned `scripts/reproduction/`; identical working source is under ignored `runs/taiji-sgwb/template-mini/demos/`.

Original preprocessing and full response calculations from earlier stages remain the data source. No raw download, FFT or full sky ORF was rerun, and no upstream output was substituted for local calculations. Original data had known foreground truth subtracted; this experiment does not implement unknown Galactic foreground marginalization.

| Item | Original/full-year setting | Mini experiment |
| --- | --- | --- |
| Weekly segments | 52 | 8 exact original segments: [0, 7, 15, 22, 29, 36, 44, 51] |
| Frequency bins | 4426 after original masks | 512: 292 original bins below/equal 3 mHz plus 220 distributed higher-frequency bins |
| Actual covariance points | 230152 | 4096 (1.7797% of original) |
| Data and model | Full A/E/T, off-diagonal complex covariance, flexing-arm responses | Unchanged definitions; exact matching selected arrays |
| Noise/SGWB parameters | 6 ACC + 6 OMS + Omega0/alpha | All 14 retained; original priors |
| Link order | 12,13,23,21,31,32 | Unchanged |
| Bin/window weights | nperbin=6 and original Kaiser ENBW | Unchanged; no full-year rescaling or extra frequency weights |
| Temperatures / walkers | 6 / 62 | 6 / 32 |
| Default move | StretchMove(a=2), adaptive ladder | Unchanged; 32 walkers actually passed initialization/proposal execution |
| Parallel worker processes | 62 upstream, 4 full-data formal | One fork worker, numerical library threads=1 |
| Burn-in | 1000 | 300, unrecorded in production HDF |
| Saved production | 350, thin_by=12 | 1000, thin_by=1 |
| Seed | Upstream unspecified | 2026101310, fresh original uniform-prior draws |

The selected likelihood is precisely the original formula on selected cached inputs. The posterior target becomes `p(theta | selected data)`. It is **not** the full-year posterior; selection may weaken identifiability and broaden/shift finite-realization constraints. Frequencies are existing six-bin means, not new interpolated points or newly aggregated bins. Weeks are distributed across the year rather than treated as a new contiguous eight-week time axis. Selected response times and data axes agree exactly. ENBW correction is inherited as implemented, not newly statistically calibrated here.

## The five actual execution steps

1. **Prepare a separate experiment.** Read the verified full caches, select original indices and produce ignored `data/processed/taiji-sgwb/template-mini/selected-inputs.h5` (8278080 bytes). Selected input indexes/axes/order/full-source hashes and array hashes are archived. The formal state was paused at burn-in 108 during this mini experiment; it subsequently completed on 2026-10-15.
2. **Validate the selected likelihood.** Six actual prior/truth parameter probes compare the original function from the full-loader namespace with the exact original function from the mini-loader namespace, independent einsum model assembly and scaled Cholesky trace/logdet. Shapes, finiteness, Hermitian/positive covariances, original source hashes and selection readback pass 31/31. No prior restriction, true-noise fixing, covariance diagonalization or source likelihood rewrite was introduced.
3. **Measure 20 actual warmup transitions.** Stable median excluding the first five was **0.21199 s/update**. Measured budget gate estimated remaining sampling at about 271 s, well below the 2700 s cap. These transitions count toward the 300 mini burn updates; they are not discarded/repeated for timing.
4. **Complete the bounded short chain with a restart.** Continue burn to 300, save 500 production samples, cleanly exit the process, then reconstruct a new sampler from the paired checkpoint and append another 500. The selected dataset requires a fresh chain; the full-data burn108 checkpoint was not reused or overwritten.
5. **Analyze and report limitations.** Cold chain only: 1000 × 32 = 32000 stored parameter vectors. Original likelihood/prior recomputation, independent Cholesky, preserved prefix and all finite values pass 11/11. Quantile tables, SGWB sample distribution, traces/ACF, correlations and sampled spectrum were generated and visually checked. Numerical correctness and finite execution do not demonstrate convergence.

## Actual runtime and resource evidence

| Process phase | Parent PID | Wall time | End burn | End production |
| --- | --- | --- | --- | --- |
| benchmark | 15031 | 6.100 s | 20 | 0 |
| first | 15051 | 168.830 s | 300 | 500 |
| resume | 15314 | 101.778 s | 300 | 1000 |

Successful phase wall times sum to **276.708 s**, about **4.61 min**. Preparation and analysis/rendering are separate. The run stayed well within the 45-minute hard cap. Later transitions remained around 0.2 s despite varied valid-proposal call counts.

Largest sampled parent RSS was **292.1 MiB**; parent-plus-descendant RSS sum peaked at **308.5 MiB**. The sum double-counts fork-shared pages and is not physical RAM consumption. Samples were approximately once per second and can miss short peaks. Only one process computes likelihoods; the parent manages the chain/HDF. The formal run was paused during this mini experiment; its later completion is recorded separately in [current status](status-and-cluster-handoff.md).

## Recovery and numerical evidence

A separate process loaded production step 500 using the unchanged external HDF key-order adapter and complete state NPZ/JSON. Coordinates, log likelihood/prior, beta ladder, both RNG streams, temperature adaptation and move counters match the saved state. Saved initial production prefix, likelihoods and betas remain identical after appending to 1000. This verifies faithful readback/resumption; the mini experiment did not run a second entire uninterrupted 1000-step control. Earlier real full-grid Stage 8 does provide the independent exact split-versus-continuous control, and the new burn/production checkpoint helper has a separate exact synthetic test.

Five actually stored cold/hot states around startup, restart and final updates were independently reevaluated. Original likelihood/stored values and independent Cholesky agree within 1e-6 absolute; maximum observed Cholesky difference was **0**. Original prior values agree as well. Accepted production proposal counts are obtained from move history with burn counts subtracted; one saved row equals one actual proposal update because thin_by=1.

Original NumPy environment complex determinant warnings are captured and counted by the tested picklable dispatcher. The original function output is unchanged and nonfinite returns fail execution. Previous identity-matrix controls document why those warnings alone do not demonstrate a singular physical covariance.

## What the sampled distributions say, and what they do not

The cold production mean acceptance fraction is **0.29259**, with actual temperature exchanges. This is evidence of movement, not sufficient mixing.

| Parameter | Injection | Finite-chain median | Sample 16–84% range | Sample 2.5–97.5% range |
| --- | --- | --- | --- | --- |
| Omega0 | 1e-12 | 1.02968e-12 | [6.08218e-13, 1.74118e-12] | [3.43161e-13, 2.63329e-12] |
| alpha | 2/3 | 0.219566 | [-0.153221, 0.567226] | [-0.484828, 1.00989] |

These are **descriptive sample quantiles**, not calibrated or confirmed converged credible intervals. Inclusion of injection in either range is not a correctness test by itself. No comparison with the paper's full-year uncertainty is justified.

Omega0 walker-averaged IAT is about **53.69** saved updates; alpha about **38.40**. Length/IAT is about 18.6 and 26.0, below the 50*tau heuristic. Ensemble-mean traces show even slower evolution: tau roughly 136/138, heuristic mean ESS about 34/45. First/second-half means shift by about 0.64/0.59 sampled standard deviations for Omega0/alpha. Several noise parameters also fail the conservative mean/length/drift gates. Only OMS_23 and OMS_21 pass all limited flags in this run. These gates are diagnostics rather than formal tests of posterior calibration.

Per-walker normalized ACFs are averaged before the Sokal-window IAT estimate; ensemble-mean IAT/MCSE are also reported and explicitly heuristic. Raw stored count 32000 must not be called 32000 independent samples. R-hat is not computed from interacting walkers or temperatures in one ensemble. [Official ensemble-sampling autocorrelation guidance](https://emcee.readthedocs.io/en/stable/tutorials/autocorr/).

The SGWB corner plot and spectrum carry an explicit selected-data/unconfirmed-convergence label. The Omega(f) shaded band is a pointwise 16–84% finite-sample summary from all 32000 stored cold parameter vectors, not an extra sampling transition or a joint credible region. It does not assert recovery across the detector band. Diagonal/correlation plots are generated project diagnostics; original demo source supplies no corresponding posterior plotting program, so these are not copied upstream or paper figures.

## Evidence files and repeated execution

Portable evidence is in `results/taiji-sgwb/template-mini/`:

- `selection.json`, `preparation.json`, `source-loading.json`: exact chosen indexes, source/cache provenance and 31 checks.
- `benchmark/`, `first/`, `resume/`: original-named HDFs, state NPZ/JSON, source-node records, actual commands/PIDs/exit codes/timing/RSS and transition logs.
- `speed-check.json`, `sampling-run.json`: measured gating and execution scope.
- `analysis.json`, `status.json`, `posterior-parameters.csv`, `diagnostics.csv`, `posterior-cold-chain.npz`: numerical checks, sampled quantiles and diagnostic verdict.
- Four checked diagnostic PNGs plus `analysis-execution.txt`.
- `attempts/`: retained source-audit path typo and initial overlapping plot-title layout. The typo was in a new external checker after numeric probes, not upstream code; corrected without changing data/physics. Plot layout was re-rendered from unchanged saved chains without new MCMC.
- `audit.json`, `manifest.json`: artifact/source/cache/library integrity.

To repeat, archive this mini run/evidence into a separate experiment ID first. The sampler refuses to overwrite a fresh existing backend. Configuration changes invalidate checkpoint provenance deliberately. Use a separate directory/configuration for another seed rather than modifying this completed chain.

```bash
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/prepare-taiji-sgwb-mini.py
python3 scripts/reproduction/run-taiji-sgwb-mini.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/analyze-taiji-sgwb-mini.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-mini.py
```

No full-data long-chain restart or extra diagnostic-driven extension was performed as part of this mini experiment. A later, separately authorized full-data continuation completed the original template schedule. The user-prioritized end-to-end workflow is complete; rigorous posterior convergence/full paper reproduction remains separate work.

## Paper hardware statement

The paper states that its analysis pipeline requires approximately **O(10) hours using 64 AMD EPYC cores**, while its RJ analysis needs about **50 hours**. O(10) here describes elapsed-time order with an explicit hours unit, not an algorithmic complexity in data size. These paper timings are not benchmarks of this selected-data run. [Jiang and Huang, Section IV](https://arxiv.org/html/2601.00169v2).

## Analysis-only maintenance (2026-10-15)

The historical mini analysis recorded that the separate formal run was paused at that time. The formal run later completed. The current analyzer now checks before/after identity of the existing formal status, final artifacts and saved pause checkpoint instead of requiring a permanently paused live status. Its pre-update source is archived under `results/taiji-sgwb/template-mini/attempts/before-lifecycle-guard-update/analyzer.py`. Canonical mini samples, analysis JSON, figures and execution logs remain historical and unchanged. A redirected analysis-only check passes all 11 numerical checks and reproduces all four PNGs and posterior/diagnostic values exactly; the new evidence is in `results/repository-maintenance-20261015/`. No MCMC was launched.
