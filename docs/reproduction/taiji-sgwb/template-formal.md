# TaijiSGWB Stage 9: original formal template schedule and posterior analysis

**Current state: PAUSED BY USER after 108 burn-in transitions, with no production samples.**

The compute processes exited normally; 19/19 static restore checks passed. See [the cluster migration plan](../../deployment/taiji-cluster-migration-plan.md). No new MCMC transition was made during validation. Read `results/taiji-sgwb/template-formal/status.json` and the timestamped progress snapshot for published status. The latest live local state is in ignored `runs/taiji-sgwb/template-formal/progress.json`. Posterior outputs will be created only after the entire original sampling schedule finishes. They must then be interpreted with the diagnostic assessment.

## Exact original schedule

The original `demos/template_nofg_28t.py` is pinned to `4afaad4044b08721e7f1ce29cba3b0d912636dce`. Its settings are retained: six temperatures, 62 walkers, original 14 parameters/priors, uniform prior initialization, default StretchMove (a=2), adaptive tempering, complete 52-week × 4426-frequency likelihood. The formal schedule is **1000 unrecorded burn-in transitions, then 350 saved production ensembles with thin_by=12**, for 5200 ensemble updates. Seed is externally fixed to 2026101309.

Four fork workers replace the upstream 62-worker pool to fit the Mac CPU/memory. Spectrum, data, sky integration and scientific source are unchanged. Original imports, likelihood, priors, initialization and constructor AST nodes are used through external cache/path adapters. The documented Stage 8 HDF key-order compatibility subclass and tested picklable dispatcher are reused. Known NumPy complex determinant warnings are counted; they do not change numerical values. All installed Eryn source files are audited against RECORD hashes.

The original `run_mcmc(..., burn=1000, thin_by=12)` is divided into calls to permit checkpoints, while keeping its kernel and storage semantics. Burn-in uses `run_mcmc(state, 0, burn=1, thin_by=1)`: original Eryn `sample(store=False)` advances the state and does not append to the production HDF. Production uses `run_mcmc(state, 1, burn=0, thin_by=12)` until exactly 350 records have been saved. No burn-in points are included in posterior quantiles.

## Executed initial checks

The first ten genuine formal burn-in updates completed on the full grid. They are part of the formal run, not a separate toy posterior. Their state, real PID, four pool PIDs, wall time, actual likelihood-call counts, log and exact original-source correspondence are preserved in `initial-burn-check/`. Two saved cold/hot states were reevaluated through the original likelihood and independent scaled Cholesky reference. This only validates the start and checkpoint inputs, not posterior convergence.

The separate `checkpoint-interface-check.json` is explicitly synthetic: it tests the new unrecorded-burn checkpoint path with a Gaussian target, six temperatures, 62 walkers, and original Eryn kernel. Split unrecorded burn and thinned production match uninterrupted execution exactly in 15/15 checks. The earlier real SGWB Stage 8 restart evidence remains intact.

The first progress-report attempt encountered a NumPy integer serialization error before any transition; its traceback is retained in `attempts/initial-progress-serialization/`. The empty run directory was archived in ignored `runs/`. Converting the counter to a native Python integer fixed reporting without changing any scientific calculation.

## Immutable checkpoint and recovery

Every ten burn-in transitions and every five saved production samples, a new immutable generation contains the latest complete State as non-pickled `state.npz`, a JSON sidecar with both MT19937 RNG streams, adaptive-temperature time, move counters, provenance and hashes, and a copy of the original-named `template_AET_nofg.h5`. An atomic pointer is published only after the generation is complete. Three generations are retained locally. Partial live HDF writes are not used for recovery.

On resume the complete generation is hash-verified, the HDF copy restores the production prefix, and the state restores unrecorded burn-in coordinates, masks, likelihood/prior, betas, both RNG streams and move history. Source/config/worker-adapter/input-cache hashes must match. The formal worker refuses to start fresh over an existing chain. A stop request is honored at a state boundary and saves a checkpoint.

```bash
# Graceful stop after current update; remove request before continuing.
touch runs/taiji-sgwb/template-formal/stop-requested
# After supervisor has exited, remove the request and its stale lock if needed
# only after checking saved PIDs are no longer running.
# Resume the complete original schedule:
python3 scripts/reproduction/run-taiji-sgwb-template-formal.py
```

The persistent supervisor reconstructs the formal worker from the ten-step checkpoint, records actual processes/resources and disables idle sleep while the worker runs. Closing the lid, power loss or OS termination can still interrupt computation; immutable checkpoints support subsequent recovery. No cluster deployment or remote compute is used.

## Synchronization and portable evidence

Live logs/progress/HDF/checkpoint generations stay in ignored `runs/`. The supervisor publishes timestamped portable progress evidence and pushes only its own results directory approximately hourly. At completion it copies the final original-named production HDF, logs, resources and terminal state, runs analysis and integrity audit, then commits/pushes the owned stage results. It does not commit unrelated staged changes. Network/push errors are recorded; completion must not be confused with successful synchronization.

Current published progress is a snapshot, not a continuously updated GitHub dashboard. The initial configuration, adapter/analysis programs, real initial checks and source evidence are committed with the launch record. Root README status links remain applicable throughout the run. New stages do not overwrite Stage 8 outputs.

## Completion analysis and limitations

After 1000+4200 updates have finished, `analyze-taiji-sgwb-template-formal.py` will:

1. Verify the original schedule, complete finite 350 × 6 × 62 chain, original-source preservation and several actual stored likelihoods against independent Cholesky calculations.
2. Analyze the **cold chain only**, retaining all 14 original parameters and original link order 12,13,23,21,31,32. Export medians, 16/84 and 2.5/97.5 percentiles, injection percentile and truth inclusion flags. Simultaneous 95% truth inclusion across 14 parameters is not assumed.
3. Report acceptance by temperature, accepted exchanges, production traces, parameter correlations, a two-parameter SGWB corner plot, and pointwise sampled Omega(f) bands. Spectrum bands are not a joint credible region over the entire curve.
4. Estimate ensemble-mean ACF/IAT with a Sokal window, assess the 50*tau time-length requirement, use a covariance-aware heuristic mean MCSE/ESS, and compare first/second-half mean drift to posterior standard deviation. These single-ensemble diagnostics can flag a run as insufficient, but cannot establish rigorous convergence or calibration.
5. Explicitly avoid treating interacting walkers or temperatures as independent chains for R-hat. Independently seeded ensembles and repeated-injection coverage tests are still needed for stronger claims.

A completed schedule can produce `SAMPLING_COMPLETE_CONVERGENCE_NOT_CONFIRMED`. If the limited checks pass, the label is `SAMPLING_COMPLETE_DIAGNOSTICS_PASS_LIMITED`, not proven convergence. Quantiles always describe the obtained samples; their scientific reliability depends on diagnostics. No burn-in/startup traces will be presented as final posterior results.

This remains the upstream oracle-foreground-subtraction baseline. It does not implement unknown Galactic foreground marginalization, diffusion training, RJ spectral reconstruction or all cases in the paper. Those remain separate subsequent work.

## Commands and interfaces

```bash
# Inspect current local state:
cat runs/taiji-sgwb/template-formal/progress.json
# Inspect published state:
cat results/taiji-sgwb/template-formal/status.json
# Recheck source/checkpoint/evidence integrity:
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/audit-taiji-sgwb-template-formal.py
# Completed posterior analysis only (requires exactly original full schedule):
bash scripts/reproduction/run-taiji-sgwb-python.sh scripts/reproduction/analyze-taiji-sgwb-template-formal.py
```

Reusable programs: `run-taiji-sgwb-template-formal-worker.py` for original inference, `taiji_sgwb_formal_checkpoint.py` for paired burn/production recovery, `run-taiji-sgwb-template-formal.py` for persistent execution/evidence synchronization, and `analyze-taiji-sgwb-template-formal.py` for completion diagnostics. Bulk physical inputs are shared with the previous verified stages and remain ignored.


## Resumed full-data run and figure delivery (2026-10-13)

The user authorized resuming the immutable burn-0108-production-0000 checkpoint. The scientific configuration and four frozen worker/checkpoint adapters remain unchanged. The supervisor now records the actual restart offset and preserves previous launch, runtime and resource evidence under timestamped sessions rather than silently overwriting it. Sampling still targets exactly 1000 burn transitions plus 350 saved production ensembles at thin_by=12.

On completion, the analyzer produces six figures from the actual cold chain: SGWB corner (68%/95% contours), spacecraft-averaged ACC/OMS noise marginals, SGWB traces, all 14 parameter traces, the parameter correlation matrix, and the template spectrum with pointwise 68%/95% intervals and relative deviation from injection. Noise averages are computed separately for each joint draw using pairs 12/13, 21/23, and 31/32. All 21700 cold draws are used for spectrum quantiles. Arrays, parameter tables, figure provenance, source hashes, saved-state likelihood rechecks and acceptance/autocorrelation/drift diagnostics accompany the plots. These samples are correlated, not 21700 independent draws.

The paper comparison is limited to the flexing-arm 2.8 template result: Figure 3's 2.8 component, the noise summaries associated with Figure 8, and Figure 6's template component. Layout and shading are external postprocessing, not changes to upstream source. EQ, 2.9 and RJMCMC are separate experiments. The upstream demo does not itself contain all publication plotting scripts. No convergence or exact numerical agreement is promised solely from reaching the prescribed run length.

A plot-only readiness check renders all six figures from existing selected-data mini samples in ignored runs/; these are explicitly smoke-test images and never substituted for formal figures. postprocessing-readiness.json records the plotting check. Formal analysis refuses to operate before the full original schedule completes. Hourly Git synchronization covers only owned formal evidence; network failures are logged and sampling continues. Closing this chat does not stop the detached supervisor. Keep the laptop powered, lid open, and avoid sleep/restart; caffeinate inhibits idle sleep while the sampling worker lives.

Paper-style refinement: visually checked PDF pages 7, 10 and 11 of arXiv:2601.00169v2. Figure 3 uses pink for the actual 2.8 result, red true-value lines, 16/84% dashed markers and 68/95% contours. Figure 8 uses cyan outlined density histograms in a 3-by-2 layout and physical fm/pm units. Figure 6 uses an orange template 95% band, a red injected spectrum, adjacent 4:1 panels, fractional error (not percent), and a 1–40 mHz display. Serif/STIX typography is shared. Statistical limits adapt to actual results; no data are changed or hidden to force agreement. Pointwise 68% and 95% values across the full 0.1–50 mHz range remain in posterior-spectrum.npz. Auxiliary diagnostics are clearly separate from publication figures.

## Overnight user pause at burn 337 (2026-10-13, Beijing time)

After resuming at burn 108, the full-data sampler advanced to burn 337 and saved an immutable checkpoint when the user requested an overnight battery pause. Production still has zero samples. All sampling workers, supervisor and idle-sleep inhibitor exited. The latest paired state is also backed up under overnight-pause-checkpoint/; a new sampler restored all states and both RNG streams with 19/19 checks passing without advancing a transition. Remaining schedule: 663 burn transitions plus 4200 production transitions. Earlier burn-108 evidence remains preserved. stop-requested remains present; do not resume automatically overnight. The next continuation requires user authorization and removing the sentinel before starting the detached supervisor with --resume semantics.
