# TaijiSGWB Stage 8: original template short chain, save, exit and resume

Completed locally: **88/88 validation checks passed**. The restored chain agrees **bit for bit in all 11 exported arrays** with an independently started, same-seed continuous control. Final sampler RNG, global NumPy RNG, temperature adaptation counter, ladder and move counters also match exactly.

This is a real MCMC execution/restart test using the full Stage 5/6 grid. It is not a converged posterior or reproduction of the paper's parameter uncertainties. Eight short steps cannot support ESS, R-hat, credible intervals or a coverage claim.

## Original method and external short-run settings

The pinned upstream is `4afaad4044b08721e7f1ce29cba3b0d912636dce`. All 19 tracked original files remain byte-identical. Original `template_nofg_28t.py` function/priors/dimensions, uniform prior initialization statements and pool/backend/sampler constructor AST nodes are executed unchanged. Same-name copies of the original program are in ignored `runs/taiji-sgwb/template-short-chain/<case>/demos/`.

| Setting | Upstream | This short-chain check |
| --- | --- | --- |
| Likelihood input | Weekly A/E/T covariance, foreground truth subtracted | Identical full 52 × 4426 grid, loaded from verified caches |
| Branches/dimensions | acc 6, ro 6, sgwb 2; one leaf each | Unchanged |
| Temperatures | 6 | Unchanged |
| Walkers per temperature | 62 | Unchanged |
| Move | Default Eryn StretchMove, a=2 | Unchanged |
| Tempering | Original default adaptive ladder | Unchanged; adaptation state checkpointed |
| Worker processes | 62 | 2, fork, single-thread numerical libraries |
| Saved samples | 350, thin_by=12 | First 4, then resumed 4; thin_by=1 |
| Burn-in transitions | 1000 | 0 for the restart smoke test |
| Initialization | Uniform draws from all original priors | Same original statements; fixed external seed 20261013 |
| Backend filename | template_AET_nofg.h5 | Identical filename, separate initial/resume/continuous evidence folders |

Short-run iteration counts, burn and thinning are supplied to the original sampler externally. The final original demo's 350-step run call is not executed verbatim, and the two-worker dispatcher delegates to the unchanged original numerical likelihood. It counts calls, rejects nonfinite returns, and captures/counts the already diagnosed NumPy complex determinant warnings; it does not change a likelihood value or a prior. Spectrum/response resolution is not reduced.

The original long-run call would mean 1000 unrecorded burn transitions plus 350 × 12 = 4200 subsequent transitions, with 350 saved ensembles. This experiment records eight transitions per walker and temperature; it does not reproduce that workload.

## Actual process sequence

| Phase | Stored iteration range | Parent PID | Wall time | Full-grid likelihood calls |
| --- | --- | --- | --- | --- |
| initial | 0 → 4 | 2399 | 60.003 s | 1124 |
| resume | 4 → 8 | 2595 | 49.892 s | 920 |
| continuous | 0 → 8 | 2687 | 108.007 s | 2044 |

The initial parent exited and was reaped before the resume process began. The resumed worker reconstructed a new pool, original sampler and backend, read the last saved sample, restored the sidecar state, and appended four more samples. It did not redraw initial coordinates or repeat burn-in. The continuous control started independently from the same original seeded prior initialization and ran eight steps without restarting its sampler.

Successful phase wall times sum to **217.902 s**. They exclude the first failed original-backend restart, code investigation, validation reruns, plotting and documentation. The measured median resumed transition was **12.016 s**. This is two-worker full-grid local timing, not a predicted cluster speed or convergence time.

Sampled parent RSS peaks were **0.678 GiB**. The largest parent-plus-descendant RSS sum was **2.147 GiB**; fork-shared pages are counted multiple times, so this sum is not physical RAM consumption. Sampling was approximately once per second and can miss shorter peaks. Bootstrap shells temporarily appear in descendant PID inventories; sustained post-bootstrap samples show the parent and two pool workers.

## What is saved and restored

The original HDF backend stores branch coordinates, active-leaf masks, log likelihood/prior, inverse temperatures, acceptance and swap counters, and the sampler's internal RNG. `restart-state.json` additionally stores:

- Global NumPy MT19937 state, used by the original temperature-swap implementation.
- Temperature adaptation time and ladder.
- Per-move accepted counts, proposal count and time, preserving diagnostic history.
- Backend SHA-256, source/config/input-cache hashes and a summary of state-array hashes.

No pickle is used. JSON sidecar writes use a temporary file and atomic replacement. Resume rejects a mismatched backend checksum or provenance rather than silently continuing an inconsistent checkpoint. HDF and JSON are a paired checkpoint; this test covers clean save/exit, not crash recovery during an interrupted write. The preserved initial backend/sidecar pair provides a known consistent restore point.

On resume, the initial sidecar summary and the restored summary agree exactly, including all coordinates, masks, likelihood/prior, beta ladder and both RNG identities. The adaptive time was initially zero in the newly constructed controller and explicitly restored to four; it reached eight at the end. Move acceptance/proposal history is restored externally as well.

## Real Eryn restart issue and bounded compatibility adapter

The first attempt with the unmodified Eryn 1.2.6 HDF backend failed during `EnsembleSampler` reconstruction: `if self.key_order != self.backend.key_order` compares dictionary values returned as NumPy arrays, which produces an ambiguous-array-truth `ValueError`. The initial saved backend remained intact. The complete failed command/traceback/resources are retained under `attempts/original-HDF-key-order/`.

`RestartCompatibleHDFBackend` in `taiji_sgwb_checkpoint.py` subclasses the original HDF backend. It converts only the `key_order` dictionary's ndarray values to Python lists on readback, preserving order and numeric contents. All writing, chain storage, RNG readback and statistical calculations are inherited unchanged. A local namespace proxy routes the original backend-constructor AST to this subclass; it does not overwrite the actual `eryn.backends.HDFBackend` module object. **No installed Eryn file or Jiang Yang source is patched.** Initial evidence uses the plain original backend; the resumed and continuous runs use this adapter. Their numeric trajectories agree exactly.

The integrity audit verifies all installed Eryn Python files with hashes present in distribution RECORD, and separately verifies raw-vs-adapted key order contents, saved chain values and RNG. Consequently, this establishes a correct restart through the documented adapter; it does not establish that an unadapted upstream command can restart successfully on this environment.

A verification-only resource check initially treated the transient bootstrap descendant count as the sampler pool size, then also counted cache loading before the pool existed. The corrected check requires sustained two-worker samples after startup. Both failed validation records are retained under `attempts/resource-bootstrap-check/`. No sampling rerun or numerical change was needed for this evidence-classification correction.

## Numerical and restart evidence

All 11 arrays are identical between the final resumed chain and continuous control: acc/ro/sgwb coordinates, three leaf-mask arrays, log likelihood, log prior, betas, accepted proposals and accepted temperature swaps. Maximum absolute difference is **zero in every array**. The initial four-step prefix also matches both the continuous prefix and the preserved final resumed prefix. Final RNG/adaptation/move summaries agree exactly.

Six saved real states spanning steps 1, 4, 5 and 8 and both cold/hot temperatures are reevaluated in an independent validation process. Original full-grid likelihoods and original prior densities agree with stored values; the independent Cholesky reference agrees within 1e-6 absolute log likelihood. All sampled/stored coordinates and likelihood/prior values are finite.

Acceptance mean across temperatures/walkers was **0.308468**, cold-chain mean **0.350806**. **349/372** walkers accepted at least one proposal, and **683** temperature exchanges were accepted. These establish actual movement/exchanges, not adequate mixing or convergence.

The trace plot shows selected cold walkers, the cold-walker likelihood median, amplitude trajectories and temperature ladder. Walker medians and selected traces are execution diagnostics. They are not posterior estimates or credible bands. With only eight steps and starts drawn throughout the broad original prior, amplitudes have not settled around the injection; this is expected at this stage and must not be presented as parameter recovery.

## Evidence and repeatability

Portable evidence under `results/taiji-sgwb/template-short-chain/` contains:

- `initial/`, `resume/`, `continuous/`: original-named complete HDF backends, paired JSON sidecars, compact chain arrays, exact source nodes/settings, worker results and per-process command/PID/time/RSS logs.
- `validation.json`: all checks, exact array comparisons and saved-state recomputations.
- `validation-execution.txt`, `run.json`: final verification outcome and successful phase timing.
- `short-chain-traces.png`, `report-execution.txt`: actual diagnostics rendered from saved arrays.
- `attempts/`: retained original restart failure and resource-check failures.
- `audit.json`, `manifest.json`: source/library/cache/backend integrity and hashes.

The raw data and large Stage 5/6 caches remain in ignored locations. Only the small-chain backends and portable evidence are tracked. Each original-named HDF backend is approximately 6.67 MB, including upstream allocation/chunk overhead.

To create a new experiment, archive the existing short-chain run/evidence directories first; the worker refuses to overwrite an existing fresh chain. Then run:

```bash
python3 scripts/reproduction/run-taiji-sgwb-template-short-chain.py
```

For a consistent initial checkpoint whose resume/control has not yet been completed, the runner supports `--start-at resume`, reusing the completed initial evidence. It appends from the active checkpoint; do not use it on this completed eight-step experiment to claim the same fixed 4+4 comparison.

Saved evidence can be independently rechecked without MCMC:

```bash
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/check-taiji-sgwb-template-short-chain.py
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-template-short-chain.py
```

Reusable checkpoint interfaces are `save_sidecar()`, `restore_sidecar()` and `RestartCompatibleHDFBackend`. Later long-run workers must carry the same pairing/provenance checks and persist both RNG streams and tempering state, with new formal-run configurations recorded separately. **Stage 9 has since completed its original full-data template schedule and posterior diagnostics, with convergence unconfirmed.** RJ sampling and EQ/paper comparisons remain incomplete; see [current status](status-and-cluster-handoff.md).
