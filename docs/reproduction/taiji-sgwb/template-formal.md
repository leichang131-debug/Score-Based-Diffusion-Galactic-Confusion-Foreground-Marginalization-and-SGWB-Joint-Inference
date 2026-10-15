# TaijiSGWB Stage 9: original formal template schedule and posterior analysis

**Current state: original full-data schedule COMPLETE at 2026-10-15 06:13:36 Beijing time; 350 production ensembles saved. Numerical checks pass, posterior convergence remains unconfirmed.**

See [completed results and evidence](../../../results/taiji-sgwb/template-formal/README.md). Earlier pause/restart notes below are historical records, not the current state.

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


## Detached screen recovery after an unrecorded interruption (2026-10-14)

At 12:27 Beijing time the last progress file still said RUNNING at burn 610, timestamp 09:42, but the supervisor and all sampler PIDs were gone. No Python failure record or clean exit was present. System boot preceded the morning run; a reboot during sampling is not established. The exact cause remains unknown. The burn-610 paired checkpoint passed SHA verification and all saved arrays were finite. Do not interpret a stale RUNNING file as evidence of live computation.

A launchd trial failed because macOS Documents privacy denied file access. The job was unregistered; no privacy settings were changed. The working fallback is /usr/bin/screen session taiji-sgwb-formal, detached from the caller, containing run-taiji-sgwb-resilient.py. This wrapper refuses duplicate live samplers, archives only provably dead supervisor locks, and permits at most three supervisor-failure retries with 30-second backoff. Each retry uses the normal strictly verified immutable checkpoint; source, inputs, priors, kernels, scientific configuration, RNG and temperature recovery are unchanged. User stop-requested prevents further retries. Completed sampling is never automatically repeated; analysis/sync failures must be inspected separately. Five synthetic control-flow checks verify explicit stop, no resampling on completion, duplicate refusal, successful recovery after one failed supervisor, and bounded retries. These are control-flow tests, not generated posterior evidence.

The supervisor now uses caffeinate -is: idle sleep is inhibited, and system idle sleep is inhibited while on AC. Neither screen nor caffeinate prevents forced sleep, lid closure, logout, shutdown, loss of power or an OS kill. Keep AC connected and the lid open. A GUI-login/reboot auto-start service was not installed. No guarantee of uninterrupted computation or a fixed finish time is made. Periodic synchronization and original full-schedule postprocessing remain enabled.


## Native Terminal-owned restart after the second interruption

At 13:40 Beijing time, the tool-started screen server and all recovery/sampling processes had disappeared. The last logged burn update was 919 at 13:33, but only burn 910 was saved completely. No Python exception record was present; the termination cause is unproven. The original scheduled sampler is restored from burn 910, replaying unsaved updates rather than claiming them as persisted progress.

The new tracked launcher start-taiji-sgwb-background.command is opened with macOS LaunchServices in Terminal.app. Terminal starts a detached screen session; this changes the initiating application/process ownership rather than again using a tool-started Popen tree. Screen, bounded recovery and caffeinate remain enabled. No system-wide settings, full-disk access or login/reboot auto-start configuration were changed. Native terminal launch is a mitigation, not proof against future interruption. Runtime PIDs, timestamped sessions, latest checkpoint hashes and native-launch verification distinguish this attempt. Source/config/cache and frozen sampler adapters remain unchanged. Launch metadata now obtains restart offsets from the saved checkpoint, not the possibly stale progress file.


## Completed schedule and postprocessing repair (2026-10-15)

The original 5200 transitions completed at 06:13:36 Beijing time. HDF dimensions are acc/ro (350,6,62,1,6), sgwb (350,6,62,1,2); cold samples (350,62,14). The automatic external analyzer encountered a path-expression TypeError before rendering; the original error and source are archived. A path-only repair regenerated six figures, spectrum arrays, parameter tables and diagnostics without advancing MCMC or altering either HDF or final state (hash verified). All seven numerical checks pass; only two of fourteen conservative diagnostic flags pass, so the report explicitly retains CONVERGENCE_NOT_CONFIRMED. Final native-Terminal session runtime was 16.52 hours including supervision overhead; this excludes earlier interrupted attempts. No additional long-chain sampling was launched. See results/taiji-sgwb/template-formal/README.md and completion-summary.json for full scope, file inventory, and posterior summaries.


## Figure 3/4/6 detail review

The user supplied Figure 4 (2.8_EQ) rather than Figure 8 (2.8), which was the original noise plot reference. Actual 16/50/84% markers were added to the available 2.8 noise posterior, and the SGWB corner now explicitly labels 2.8 template. Figure 3 blue EQ and Figure 6 pink RJMCMC bands are unexecuted experiments, not missing plotting layers that can be recovered from the current power-law posterior. See results/taiji-sgwb/template-formal/paper-figure-correspondence.md for the exact mapping and unaltered sampling-artifact hashes.
