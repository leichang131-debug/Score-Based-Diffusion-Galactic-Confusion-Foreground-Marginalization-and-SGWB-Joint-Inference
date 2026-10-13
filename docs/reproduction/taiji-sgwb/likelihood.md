# TaijiSGWB Stage 7: spectral models and likelihood numerical validation

Completed on the local Mac CPU using the unchanged upstream code at `4afaad4044b08721e7f1ce29cba3b0d912636dce`: **206/206 checks passed**. Both original likelihoods were evaluated on the complete **52 weekly segments × 4426 retained frequency bins**, using the verified Stage 5/6 caches. This validates tested model algebra and numerical interfaces, not posterior convergence or statistical coverage.

## Original source correspondence

| Original file | Lines | Executed content |
| --- | --- | --- |
| `demos/template_nofg_28t.py` | 158–177 | Original `log_likelihood`, including six-link noise amplitudes, power-law spectrum, full matrix inverse and log determinant |
| `demos/rj_nofg_28t.py` | 164–169 | Original quadratic log-frequency/log-Omega interpolation |
| `demos/rj_nofg_28t.py` | 171–194 | Original RJ likelihood, bounds sentinel and covariance calculation (see exact recorded lines) |
| `src/taijisgwb/waveform.py` | `calc_omega_powerlaw` | Original Omega power law, referenced to 1 mHz |
| `src/taijisgwb/utils.py` | `psd_from_omega` | Original conversion from dimensionless Omega to strain PSD |

The exact line ranges and source text in the per-entry `source-execution.json` are authoritative. Original imports, spectrum-domain bounds, prior/dimension settings and RJ move definitions are compiled from their unchanged AST nodes. No original files are patched. Same-name, byte-identical working copies remain in ignored `runs/taiji-sgwb/likelihood/<entry>/demos/`.

The project adapter `taiji_sgwb_likelihood.py` supplies original-named cached globals; `evaluate_original()` calls the actual original function and observes its return-frame locals using Python tracing. It does not rewrite that function. `independent_model()` and `stable_reference()` are validation references only, not replacement inference functions.

## Model and complex-matrix conventions

Each week/frequency covariance is the sum of six independent ACC link contributions, six OMS/readout link contributions, and the isotropic SGWB response multiplied by strain PSD. Noise amplitudes are squared. The canonical link order is **12, 13, 23, 21, 31, 32**, not alphabetically sorted HDF5 keys. Both channels and all off-diagonal entries are retained.

Power-law spectrum: `Omega(f) = Omega0 * (f / 1e-3 Hz)**alpha`.

Strain PSD: `S_h(f) = 3*H0**2 / (2*pi**2*f**3) * Omega(f)`; the original Hubble constant is in inverse seconds. PSD↔Omega roundtrip and an independent formula agree to floating-point precision.

The data CSD convention is `D[i,j] = conjugate(z_i)*z_j`; the response/model covariance uses `C[i,j] = response_i*conjugate(response_j)`. The original elementwise sum `sum(D * inverse(C))` therefore equals `trace(solve(C, transpose(D)))`. It is not `trace(solve(C,D))`. An explicit complex positive-matrix counterexample is recorded to distinguish these expressions. No matrix is silently conjugated, discarded, symmetrized or regularized.

The original likelihood, omitting parameter-independent constants, is:

`logL = -(6 / window_ENBW) * sum_over_week_and_frequency[ trace(C^-1 * D^T) + log(det(C)) ]`.

The Kaiser-window ENBW is inherited unchanged from Stage 5. All 52 weekly matrices are used independently; annual means appear only in the diagnostic figure. A positive absolute log likelihood is expected for the original unnormalized density of dimensionful tiny covariances; likelihood differences are the relevant comparison.

## Independent checks and actual scope

- 19 full-grid valid parameter cases: injection, eight deterministic original template-prior draws, two opposite prior-corner probes, power-law RJ spectra with 1/2/4/8/16 interior knots, a curved RJ spectrum, and accepted RJ prior draws.
- Fifteen additional RJ prior draws across those knot counts: **13/15** received the original finite `-1e50` bounds sentinel; accepted cases underwent full independent checks. This small draw set is not a general rejection-rate estimate.
- Independent einsum covariance assembly: maximum relative L2 difference **9.73e-17**.
- Scaled Cholesky solves and log determinants agree with original inverse/determinant likelihood: maximum absolute log-likelihood difference **2.98e-08**, below the declared **1e-6 absolute** tolerance. Both exponential and log-determinant terms are checked separately.
- All tested full covariance matrices are Hermitian positive definite. Maximum normalized condition number **3.56069e+07**; minimum normalized eigenvalue **2.86296e-08**. This is conditioning evidence for tested cases, not a proof over the entire continuous prior.
- Original determinant outputs are finite and positive; maximum relative difference from independently scaled slogdet reconstruction **9.66e-13**.
- RJ log-space interpolation reproduces the template power law at every frequency for 1–16 knots; corresponding original likelihoods agree within 1e-6. Unsorted distinct knots work with original `assume_sorted=False`.
- An Asimov covariance test confirms the generating model has larger expected likelihood than an explicitly perturbed model. This tests algebra, not real-data coverage.
- Both actual Eryn `compute_log_prior` and `compute_log_like` interfaces ran with one temperature and 32 walkers. Template uses original fixed-dimensional mode; RJ uses original moves and `rj_moves=True`, which preserves the leaf axes and masks inactive knots. **No MCMC updates were performed**.

## Diagnostics and limitations

The conditional 13-point amplitude scan fixes all twelve noise values and the slope to injection. Its grid maximum is `9.48683298e-13`, versus injected `1e-12`. A coarse conditional maximum is not a marginalized posterior estimate, an unbiasedness check or an uncertainty interval.

Annual mean data/model diagonal ratios are A=0.99995478, E=1.00021611, T=1.00064302. These are descriptive checks; no posterior calibration follows. Data still has the known foreground truth subtracted, exactly as upstream. Unknown-foreground marginalization is not implemented by this reproduction.

On this NumPy 1.26.4 macOS environment, complex `det` and `slogdet` emit divide-by-zero/invalid warnings even for a complex unit identity matrix; real identity controls and complex Cholesky do not. The actual determinant/likelihood outputs remain finite and agree with independent controls. Rescaling does not remove those complex determinant warnings. The precise backend cause remains unresolved. Warnings are retained, not suppressed in the original code; neither a source change nor an environment change was made. Subsequent chains must monitor finite likelihoods and covariance conditioning.

Exactly repeated interior frequencies raise `ValueError` in upstream quadratic interpolation. Continuous independent frequencies have zero exact-collision probability mathematically; external initialization must nevertheless check uniqueness. Quadratic interpolation can overshoot the allowed log-Omega range even when all node ordinates lie inside the prior; the original likelihood rejects this using `-1e50`. No original exception guard or boundary behavior was changed.

The original likelihood uses bin/ENBW weighting; this stage verifies the implemented formula, not the statistical adequacy of treating the retained bins as independent. Posterior uncertainty calibration requires later simulation/coverage studies.

## Runtime and evidence

Final worker wall time: **18.258 s**; sampled peak worker RSS **1.736 GiB** at 0.5 s intervals. Median original full-grid template call in the conditional scan: **0.0918 s**. These cached, serial timings exclude data downloads and ORF generation, and do not predict parallel long-chain speed.

Earlier attempts are retained: the first external interface check omitted original RJ mode and consequently squeezed a leaf axis; determinant investigation initially assumed normalized determinant warnings would disappear, disproved by identity controls; a later report serialization attempt encountered a NumPy Boolean and was corrected to a Python Boolean. These issues did not alter upstream scientific code. `attempts/pre-determinant-diagnostics/` retains the intermediate successful narrower check before added diagnostics.

The diagnostic was re-rendered from the saved numerical summary with explicit font sizes, matching channel colors and gaps across removed notch bands. `report-execution.txt` records this presentation-only pass; numerical arrays and original source were unchanged. The renderer is also used by future checker runs.

Portable evidence is in `results/taiji-sgwb/likelihood/`: validation JSON, comparison CSV, exact source records, command/PID/timing/RSS logs, determinant identity controls, diagnostic NPZ/PNG, retained attempts and integrity manifest. Existing complete data/response caches remain ignored; their SHA-256 values match their earlier stage evidence.

## Repeat and use the interface

```bash
python3 scripts/reproduction/run-taiji-sgwb-likelihood.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-likelihood.py
```

The reusable loader is `load_original_likelihood("template_nofg_28t.py")` or `load_original_likelihood("rj_nofg_28t.py")`, returning a namespace and source record. Template direct arguments are `[acc(6,), ro(6,), sgwb(2,)]`; RJ direct arguments are `[acc(1,6), ro(1,6), knots(K,2), edge(1,2)]` with 1≤K≤16. Returned namespace contains `log_likelihood`, original `priors`, dimensions/leaf limits and verified cached globals. It supplies the serial numerical interface; multi-process execution and restart persistence are still to be exercised in the next stage.

Next is **Stage 8: original-template short chain, save, stop and restart continuation**. Formal template posterior diagnostics, RJ spectral reconstruction, paper comparisons and uncertainty calibration remain pending.
