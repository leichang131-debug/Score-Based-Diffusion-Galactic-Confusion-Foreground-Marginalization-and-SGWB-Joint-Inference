# Taiji laboratory cluster migration and execution plan

For all current deployment decisions and remaining work, use [status and cluster handoff](../reproduction/taiji-sgwb/status-and-cluster-handoff.md). The burn-108 commands, budgets and continuation plan below are preserved historical planning, not instructions to resume the completed run.

**Historical planning document from the burn-108 pause.** The local formal schedule was later resumed and completed on 2026-10-15; see [current results](../../results/taiji-sgwb/template-formal/README.md). The preserved burn-108 migration example and resource planning below remain historical, not current progress.

Status: planning and local preparation only. No cluster hostname, scheduler, account, partition or hardware inventory has been confirmed; no cluster login, environment installation or job submission has been performed. The local formal chain was deliberately stopped at a complete checkpoint after **108 burn-in transitions**, with zero production samples. Its state was restored into a newly constructed sampler without advancing it; **19/19 checks passed**. This is the same-platform restore result, not a claim that Linux migration is already validated.

## 1. Responsibilities and immediate boundaries

| Work | Local Mac | Cluster |
| --- | --- | --- |
| Original pinned source and Git history | Preserve and inspect | Clone the same commits/submodules |
| Environments | Keep working isolated Mac environments | Rebuild separate native Linux environments |
| Tutorials and interface checks | Lightweight execution and reading | Repeat a small platform compatibility check |
| SGWB development | Small synthetic examples, limited real checks, plotting | Full data/covariance calculations and long posterior chains |
| Sampling reliability | Understand diagnostics; inspect exported evidence | Independent initialized ensembles and diagnostic-driven extensions |
| Diffusion work later | Data shapes, unit interfaces, tiny smoke tests | GPU training and large experiments in a separate environment |
| Data/checkpoints | Preserve validated local copies | Managed data/scratch plus durable checkpoint storage |
| GitHub | Code, configurations, documentation, portable evidence | Return reviewed evidence through one designated sync process |

Local default: 1–2 processes and explicit small step limits; retain complete scientific inputs where possible. Small experiments prove mechanics or compare implementations; they do not claim long-chain inference accuracy. Do not keep the current 5200-transition schedule running on the Air. No Python environment, source checkout or prior results are removed.

## 2. Preserved state and migration bundle

Portable preserved checkpoint is `results/taiji-sgwb/template-formal/pause-checkpoint/`:

- `state.npz`: all 6 × 62 walker coordinates, branch masks, log likelihood/prior and betas.
- `state.json`: both RNG streams, adaptive temperature time, move accepted/proposal counters, source/config/adapter/input hashes and checkpoint identity.
- `template_AET_nofg.h5`: original-named backend, currently with **zero production rows** because burn-in is deliberately unrecorded.
- `validation.json`, `validation-execution.txt`: static restore and original/Cholesky likelihood checks, with no new transition.

**The HDF alone is insufficient to resume unrecorded burn-in.** Copy the complete paired state, original configuration and pointer layout. The local ignored working directory retains the latest three complete checkpoint generations and `latest-checkpoint.json`. Its `stop-requested` sentinel remains present to prevent accidental continuation. Remove such a sentinel only in a deliberately prepared continuation workspace.

The remaining original schedule is **892 burn-in transitions + 350 × 12 production transitions = 5092 transitions**, yielding 350 saved ensembles. Existing compute is recoverable; whether those 108 transitions are used for the principal cluster comparison will follow the cross-platform checks. Preserve this resumed chain as a separate identified experiment even if independent fresh runs become the main reported result.

The source stays in `external/taiji-sgwb/`, preserving all original file/directory names and bytes. Project-owned launch/validation/checkpoint adapters stay outside that subtree. Upstream pin remains `4afaad4044b08721e7f1ce29cba3b0d912636dce`; retain the original GPL license along with the source.

## 3. Information to confirm with the laboratory

Obtain these operational facts before choosing executable submission parameters:

| Item | Why it is needed |
| --- | --- |
| SSH endpoint, account provisioning, jump host/VPN procedure | Access and permitted transfer method; credentials do not belong in the repository |
| Scheduler: Slurm, PBS or another system | Actual job submission/monitoring/signal/requeue interface |
| Project/account, CPU partitions and queue priorities | Valid resource request and expected queue time |
| Node architecture, CPUs, RAM, NUMA layout, maximum wall time | Native wheels, scaling plan and checkpoint frequency |
| Available Python/module versions and supported environment/container tools | Linux dependency lock and reproducible installation |
| Login/compute-node network access and package mirrors | Where to install/download; whether an offline wheelhouse is needed |
| Shared/project/scratch paths, quotas, cleanup policy and backup | Place data, live HDF and durable state appropriately |
| HDF5/file locking policy and local scratch availability | Reliable single-writer checkpoints and filesystem performance |
| Job timeout/preemption grace periods and accounting availability | Save before termination and measure real resource use |
| GPU model, CUDA/runtime policy and JAX support, for later diffusion | Separate future training environment; not needed by current NumPy SGWB inference |

Do not assume the system uses Slurm. If it does, use single-node `sbatch` allocations and job arrays only after the relevant account/partition fields are confirmed. Slurm submits a job but does not transfer the input files automatically; data staging is a separate step. [Official Slurm sbatch documentation](https://slurm.schedmd.com/sbatch.html).

## 4. Ordered work packages and acceptance gates

The following estimates are hands-on effort or compute allocations, excluding queue waits. They are planning estimates, not measured cluster runtime.

| Package | Work | Acceptance gate | Tentative effort |
| --- | --- | --- | --- |
| A | Confirm access, scheduler, storage and hardware | A valid CPU allocation and writable durable/scratch locations | 30–60 min after information arrives |
| B | Clone exact source and rebuild Linux SGWB environment | Package imports, original priors/functions, isolated interpreter and Linux dependency lock | 1–2 h if compatible modules/wheels are available |
| C | Stage verified data, caches and paired checkpoint | File sizes/SHA-256 match local evidence; scientific axes and metadata agree | 15–60 min, network dependent |
| D | Static numerical/restore checks and a tiny real job | Source unchanged, finite likelihoods, reference tolerance met, clean save/restart | 30–60 min plus short compute allocation |
| E | Test process counts on the allocated node | Measured throughput, memory, resource compliance and stable repeated timings | Budget 1–2 h for bounded benchmarks, subject to measured speed |
| F | Continue the paused chain and run independently initialized ensembles | Original schedules complete or diagnostic-required extensions recorded | Runtime determined only after Package E |
| G | Posterior diagnostics, comparisons and evidence return | Reproducible tables/plots, diagnostic verdict and hashes, synchronized research repo | 1–2 h analysis/review after sampling |

### Package B: native environment and platform lock

Use Python 3.11 initially, matching 3.11.14 if available. Keep original NumPy 1.26.4 and SciPy 1.13.1, and first test Eryn 1.2.6 plus the documented external HDF key-order adapter. Recreate h5py, healpy, matplotlib, corner, hatchling/editables and transitive dependencies on the actual Linux architecture; use the existing `requirements.in` as intent, not the Mac wheel/hash lock as a Linux lock. Record BLAS/LAPACK implementation, library/compiler versions, CPU architecture and package hashes.

A macOS ARM virtual environment must not be copied onto Linux. Recreate it natively, then resolve/freeze the platform-specific wheels and install the pinned original editable package without changing its source. If compute nodes cannot download packages, prepare a wheelhouse on an approved compatible Linux machine or login node. [Python venv documentation](https://docs.python.org/3/library/venv.html), [Python Packaging installation guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/).

Keep Score-SDE/JAX, Triangle tools and TaijiSGWB environments independent. Future CUDA/JAX deployment is a later work package and must not destabilize the pinned CPU SGWB environment.

### Package C: data and storage

Transfer or redownload-and-verify the official data, original orbit and verified processed caches; do not rerun full FFT or ORF simply to relocate identical verified arrays. Full current SGWB input/cache set is approximately **1.535 GB**: official HDF about 658 MB, two preprocessing caches about 223 MB each, response about 431 MB, plus a small orbit/checkpoint. The current template alone uses only one preprocessing cache, but retaining both supports later RJ work. Scientific inputs stay read-only; each job gets a separate writable output/checkpoint path.

Preserve official file names and the original hyphenated read alias `TDCII2-8.h5` to official `TDCII2.8.h5`. Verify checksums after transfer, not just successful file copying. Store bulk inputs outside Git. The exact code can resolve inputs by project-relative paths or declared data roots; do not introduce user-specific absolute paths into original source.

Proposed future layout (not created on a cluster):

```text
project/                  # exact repository clone and external pinned sources
shared-data/taiji-sgwb/    # immutable verified official inputs and processed caches
scratch/jobs/<run-id>/    # live job output, temporary work and local checkpoints
durable/runs/<run-id>/    # complete checkpoint pairs, logs and durable artifacts
```

A shared HDF backend is never concurrently written by two ensembles. Atomic rename must occur within one filesystem; copy a complete generation to durable storage before publishing its pointer. Scratch cleanup/timeout behavior must be confirmed.

### Package D: cross-platform equivalence and recovery

1. Audit all original source names/bytes/pins and imported package origins.
2. Compare selected actual covariance/spectrum/likelihood values against the local evidence. Use float64/complex128; the previous absolute likelihood reference tolerance is 1e-6, with separate covariance relative tolerances. Investigate any failure before production.
3. Verify the paused checkpoint hashes and rebuild the new sampler without advancing it. Check coordinates/masks, log likelihood/prior, both RNG streams, beta ladder and adaptation/move counters.
4. Recompute at least several of the saved log likelihood/prior values through the Linux original function. Record any BLAS/platform roundoff difference and its size; do not assume Mac/Linux trajectories must be bit-identical.
5. On a copied continuation branch, run 2–4 real transitions, save/exit/restart and compare against a same-platform seeded continuous control. The original paused Mac checkpoint remains immutable.

Restoring array/RNG state across architectures is a planned validation target, not yet a demonstrated result. Statistical consistency and identical scientific model/configuration are required; cross-OS floating-point kernels may yield divergent future stochastic trajectories. If values differ materially, stop and diagnose rather than disabling checks. Preserve a migration report even when independent fresh cluster chains are used as the primary inference result.

### Package E: computational efficiency without changing the science

Start with **one node** and the current four-worker baseline. Its local process pool does not distribute work across nodes and does not use a GPU. Consider **8 CPU cores / 32 GiB** as a conservative pilot request if the cluster permits it, then benchmark allocations for 8 and 16 workers; consider 32 only if useful and affordable. These RAM requests are tentative budgets, not measured requirements.

Keep OpenMP/BLAS threads at one per worker and bound worker processes to allocated CPUs, allowing capacity for parent/I/O. Each independent ensemble gets its own allocation/work directory. Do not jump directly to upstream 62 workers: full response-array bandwidth, NUMA placement and private intermediate arrays may limit scaling before CPU count does.

Use two benchmark views: a deterministic fixed-parameter likelihood workload to compare costs at equal call counts, then 10–30 genuine ensemble transitions to measure end-to-end kernel behavior. Report median and spread after startup, likelihood calls, seconds per call/transition, initialization and checkpoint overhead, parent/private/aggregate memory where available, and scheduler accounting. Do not confuse an RSS sum with physical memory. Stop bounded benchmarks once an adequate configuration is identified.

Extrapolate total compute only from sustained measured speed. For the paused chain, remaining time is approximately `5092 * measured_seconds_per_transition`, plus checkpoint and analysis overhead; queue time is separate. For independent fresh chains, use `5200 * measured_seconds_per_transition` per ensemble. Judge useful throughput by diagnostic quality/ESS per wall or core-hour, not only raw transition speed.

## 5. Adapter work required before concurrent cluster runs

Current v1 adapters are functional local programs but **not yet a general cluster interface**:

- `run-taiji-sgwb-python.sh` selects one project-local environment path.
- The formal worker reads a fixed configuration file and writes one fixed `runs/taiji-sgwb/template-formal/` directory.
- The local supervisor uses macOS idle-sleep inhibition and direct Git pushes; a compute-node job should use its scheduler and leave publishing to a designated login/workstation process.
- Checkpoint provenance includes the exact configuration and frozen adapter hashes, including the `processes=4` configuration.

Consequently, editing the config to 8/16 processes or rewriting frozen worker files makes a v1 restore fail **by design**. Do not simply relax that check. Preserve the frozen v1 source/config and current checkpoint. First test a native Linux four-worker v1 restoration with the same configuration and source hashes; absolute repository location can change because code/checkpoint paths are project-relative.

Develop a new external cluster runner afterward with explicit `--config`, `--work-dir`, data-root, seed/run-id and resume interfaces. Separate immutable scientific settings from execution resources in a documented versioned checkpoint schema. Require equality for model, data, priors, dimensions, RNG/state semantics and scientific inputs; record audited resource-only changes separately. Create an explicit migration adapter/report for any v1-to-v2 conversion, retain both original and converted state, and recheck saved likelihoods and recovery controls. Do not silently edit recorded hashes or retrofit the old checkpoint.

If conversion requires substantial changes, the more economical first production result is an independently initialized native Linux run with original science, while retaining the paused Mac chain for the demonstrated four-worker continuation. The 108 transitions do not justify a large unvalidated migration rewrite.

All original filenames, directories, source text and licenses stay unchanged. New environment/launcher/scheduler adapters and evidence remain project-owned separate files. No Linux launcher, scheduler submission script, v2 checkpoint schema or converted state is claimed to exist yet.

## 6. Formal independent ensembles and inference reliability

First run one native cluster baseline to establish behavior, then preferably **four separately initialized, independently seeded ensembles**, each preserving original six temperatures, 62 walkers, 14-dimensional prior and 1000+350*12 schedule. The migrated Mac chain can be an additional continuation comparison. Fresh ensembles must redraw coordinates from the original priors; copying one paused state and changing only the seed is not the planned initialization-diversity check.

Choose concurrent job count according to the actual allocation/quota rather than assuming four entire nodes are available. If Slurm is confirmed, separate jobs or a job array with explicit concurrency limit may be used. Do not allocate extra nodes to one ordinary multiprocessing pool expecting automatic distribution.

Collect acceptance by temperature, actual production move counts excluding burn, exchange counts, traces/rank plots, covariance/likelihood checks, 14-parameter posterior quantiles and Omega(f) bands. Use cold chains for parameter posterior summaries; temperature ladders are diagnostics, not independent posterior chains.

Interacting walkers within one ensemble must not be presented as independent chains for R-hat. A feasible multiple-ensemble check is predeclared fixed walker indices compared across independently seeded ensembles, supplemented by ensemble-level posterior/window comparisons and conservative MCSE/ESS. Do not flatten walkers into artificial time chains. Plan rank-normalized split/folded R-hat checks with a tentative 1.01 gate, bulk/tail ESS and quantitative Monte Carlo error targets, while recognizing that no single diagnostic proves convergence. Thresholds and precision goals should be agreed with the teachers before long resource-intensive extensions. [Vehtari et al., improved MCMC convergence diagnostics](https://arxiv.org/abs/1903.08008).

If original run lengths are insufficient, identify burn/nonstationarity, mixing, proposal efficiency or effective-sample limitations; extend only justified chains with recorded budgets. Repeated-injection calibration/coverage and unknown-foreground robustness belong to subsequent scientific validation. Do not require every injected parameter to fall inside every 68% or 95% interval on one dataset.

## 7. Evidence, synchronization and readiness definition

Each run must have source/submodule commit, native environment lock, hardware/BLAS details, original input/cache hashes, config/seed, scheduler job ID and resource allocation, exact command, timestamps/exit status, complete paired checkpoints and restore evidence, numerical validation, diagnostic outcome, posterior tables/figures and artifact hashes. Separate computation failure, incomplete schedule, completed-but-unconfirmed convergence and passed limited diagnostics.

Raw data, environment directories and live large files remain ignored. Portable summaries/plots/configuration/scripts and small terminal checkpoints can be committed; larger complete chains stay in laboratory storage with checked hashes and access paths recorded privately as appropriate. Synchronize durable data outside Git and publish evidence through one owner to prevent concurrent job commits/pushes colliding.

The next action after cluster information arrives is **Packages A–D**, not an immediate 62-worker long job. Cluster deployment is considered ready only after source/environment/data checks plus a real allocated-node save/restart test pass. Full scientific reproduction requires subsequent complete sampling and diagnostic assessment; current paused-local status does not assert either.

## Local pause record

Local compute worker, all four pool workers, persistent supervisor and idle-sleep inhibitor exited normally. The supervisor recorded return code 0 and published the intentional `STOPPED_AT_CHECKPOINT` status. It did not run posterior analysis because production has not started. A static restore check passed 19/19 without continuing the chain. The paired checkpoint is backed up in the repository; the latest complete local generation remains in the ignored working directory. Existing Mac environments, data, source and prior stage evidence remain preserved.
