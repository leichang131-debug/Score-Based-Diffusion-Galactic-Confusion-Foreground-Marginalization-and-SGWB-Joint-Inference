# TaijiSGWB reproduction status and cluster handoff

Updated: 2026-10-15, Asia/Shanghai. This is the current status and execution boundary. Earlier burn-108 migration notes are historical; they do not describe the latest progress.

## Decision

Do not start further full-data long MCMC runs for 2.8_EQ template inference or 2.8 RJMCMC on the local MacBook Air. Preserve the working local environments, original sources, data, completed chains and evidence. Use the Mac for reading code, lightweight development and analysis of saved results. Subsequent full inference, diagnostic extensions and independent-seed experiments belong on an approved laboratory cluster/server. No cluster connection or job submission has occurred; no server configuration is assumed.

## Completed local work and remaining limits

| Component | What is actually complete | What is not established |
| --- | --- | --- |
| Source | All 19 original TaijiSGWB files preserved at upstream 4afaad4044b08721e7f1ce29cba3b0d912636dce | No separate upstream EQ demo or complete publication plotting suite is supplied |
| Environment | Independent macOS CPU environment, original imports and Eryn interfaces verified | Native Linux deployment and cross-platform numerical agreement not yet tested |
| Data | Official 2.8 realistic-orbit file and orbit, checksums and fields validated | 2.8_EQ not downloaded/validated; 2.9 variants not prepared |
| Preprocessing/response | Both original 2.8 demo preprocessing paths and full response cache validated | Existing realistic-orbit response cache must not be reused as the EQ response |
| Likelihood | Both template and RJ original likelihoods checked numerically | RJ likelihood/interface checks are not RJ sampling or restart validation |
| Template recovery | Same-platform short-chain uninterrupted/restarted comparison and real pause restoration validated | Mac-to-Linux restart equivalence not established |
| Full 2.8 template | 1000 burn + 350 x 12 production = 5200 transitions completed at 2026-10-15 06:13:36 Beijing time; six figures and full evidence saved | Posterior convergence not confirmed; only 2/14 conservative parameter diagnostic flags pass; no independent ensembles or repeated-injection calibration |
| 2.8_EQ template | Upstream EqualArmOrbit class identified | Dataset preparation, dedicated entry/configuration, numerical/restart validation and sampling not performed |
| 2.8 RJMCMC | Original rj_nofg_28t.py entry and inference components identified | Bounded real sampling, nested move/RJ state recovery, complete run and posterior spectral reconstruction not performed |
| Future research | Existing no-foreground pipeline provides a reference | Unknown Galactic foreground marginalization and score-based diffusion joint inference are not implemented by this reproduction |

The completed template run is a real local computation, not copied upstream output. Its HDF, source correspondence, four numerical likelihood rechecks, state/RNG records, logs, resources, quantile tables, six plots and integrity manifests are preserved. Automatic postprocessing encountered a path typo; the failure and pre-fix code remain archived. Corrected postprocessing used unchanged chains and final-state files (hash verified). Completion of this schedule must not be reported as completion of all paper experiments or proof of posterior convergence.

## Paper figures still incomplete

- Figure 3: the actual 2.8 template result is available. The blue 2.8_EQ comparison remains to be computed.
- Figure 4: the EQ noise posterior remains to be computed. Adding its quantile-marker convention to the available 2.8 plot does not reproduce the EQ dataset experiment.
- Figure 6: the template spectrum is available. The pink RJMCMC interpolation band remains to be computed.
- 2.9/2.9_EQ and associated phase-transition figures are optional additional paper-reproduction scope to agree with the teachers, not completed or silently scheduled tasks.

See [figure correspondence](../../../results/taiji-sgwb/template-formal/paper-figure-correspondence.md).

## Cluster work packages and gates

1. **Confirm access and resources.** Obtain the account, connection method, scheduler, CPU architecture, available cores/RAM, storage policy, job wall-time limit and transfer method. Initial inference uses CPU; a GPU is not required by the current NumPy/Eryn sampler. Future diffusion training is a separate workload/environment.
2. **Rebuild a native environment.** Clone the research repository and pinned submodules. Rebuild the Python 3.11 environment with the recorded scientific versions where compatible; record Linux-native package/BLAS details. Do not copy the Mac virtual environment as an executable Linux environment.
3. **Transfer and verify artifacts.** Stage official raw inputs, preprocessing and response caches, fixed configuration and completed 2.8 reference chain. Verify sizes and SHA-256 against existing evidence. The completed chain is a comparison artifact; do not accidentally relaunch its finished schedule. For a deliberate continuation use a new identified run/configuration, retain the original terminal chain, and validate the full paired state rather than relying on HDF alone.
4. **Verify cluster numerical interfaces.** Run original imports, cached-grid checks, representative prior/likelihood evaluations and original-versus-independent covariance checks. Treat cross-platform floating-point differences using documented numerical tolerances; do not promise bitwise-identical future MCMC trajectories.
5. **Prepare the EQ experiment.** Download official TDCII2.8_EQ.h5 under its original filename; verify official MD5, local SHA-256, fields, timing and injected parameters. Configure the original EqualArmOrbit consistently with data generation and build a distinct response cache. Verify any segment-averaging speedup against the corresponding likelihood and weighting before adopting it. Preserve full relevant CSD terms; equal arms alone do not establish equal noise or diagonal covariance.
6. **Validate short sampling and recovery for each model.** The EQ run must pass save/exit/restart checks. RJ requires active knot masks, branch dimensions, both RNG streams, temperature state and nested CombineMove/RJ proposal state. The current fixed-template checkpoint serializer is not sufficient as-is. Preserve 62 walkers separately from CPU pool size; the RJ upstream nwalker=npool assignment must not inadvertently reduce the ensemble when limiting workers.
7. **Benchmark on the assigned node.** Compare bounded 4/8/16-worker runs as resources permit, with one numerical-library thread per worker initially. Record warm/stable per-update cost, likelihood calls, RSS and node allocation. For RJ also record knot counts and move acceptance. Choose the full-run budget from these measurements; no cluster speed is currently measured.
8. **Run declared full experiments.** Establish separate configs, seeds, directories and original-named outputs for EQ template and 2.8 RJMCMC. An initial EQ template schedule can match the completed template reference; the original RJ schedule is 2000 burn + 350 x 15 production = 7250 transitions. Checkpoints, scheduler termination handling and one designated result-sync process are required. Do not run two writers against one HDF.
9. **Assess scientific reliability.** Check trace stability, autocorrelation/MCSE/ESS and move/temperature mixing. For RJ inspect knot-count mixing and reconstruct spectra using only each draw's active knots plus boundary values. Plan independent seeded ensembles and justified extensions within an agreed compute budget. Walkers within an ensemble are not independent chains. Decide whether to extend/repeat the current 2.8 template reference only after cluster tests and diagnostic review; do not automatically extend locally.
10. **Return results and compare figures.** Save all-temperature chains, final paired states, original source/config/data hashes, environment and scheduler metadata, logs/resources, numerical checks, diagnostics, quantiles and plotting provenance. Combine only independently computed results with correct dataset/model legends. Distinguish sampling failure, a completed schedule with unconfirmed convergence, and adequately validated inference.

## Runtime statements

The completed local 2.8 production phase took about 16.22 hours for 4200 updates, approximately 13.90 seconds/update. The last uninterrupted native-Terminal continuation session took 16.52 hours; this excludes earlier attempts. Earlier local EQ/RJ time ranges were unmeasured planning scenarios, not promises and not cluster estimates. No cluster runtime or rental expenditure is committed. Hardware inventory and bounded benchmarks must precede a new full-run estimate. Reaching a scheduled step count does not guarantee sufficient effective samples.

## Code preservation and outputs

Keep external/taiji-sgwb/ byte-identical to the pinned upstream, with original directories, Python names and license. Put project-owned configurations, loaders, path adapters and scheduler scripts outside that subtree. Keep raw/bulk data and environments ignored. Retain meaningful portable evidence and correctly licensed code in Git; preserve bulk cluster chains in verified durable storage with an explicit file inventory.

The prior process interruptions have no established root cause. Native Terminal-owned execution eventually completed the local reference, but this does not prove the earlier failures were caused by the coding tool, heat, battery or another specific mechanism. Cluster scheduling/checkpointing improves manageability; it is not an absolute no-interruption guarantee.

## Suggested meeting statement

The original full-data 2.8 template pipeline has completed on the Mac, including its prescribed 5200 updates, posterior plots and auditable local evidence. Numerical checks pass, while conservative diagnostics do not yet establish sufficient convergence. The remaining EQ template and RJMCMC comparisons have code foundations but have not been sampled. We propose moving their deployment validation, full runs, independent-seed checks and any necessary extensions to the laboratory cluster, after confirming resources and benchmarking. These steps complete the reference pipeline before introducing unknown-foreground marginalization and the score-based model.

## Evidence links

- [Completed template report](../../../results/taiji-sgwb/template-formal/README.md)
- [Completion summary](../../../results/taiji-sgwb/template-formal/completion-summary.json)
- [Diagnostics](../../../results/taiji-sgwb/template-formal/analysis.json)
- [SHA-256 artifact manifest](../../../results/taiji-sgwb/template-formal/manifest.json)
- [Historical migration plan](../../deployment/taiji-cluster-migration-plan.md)
