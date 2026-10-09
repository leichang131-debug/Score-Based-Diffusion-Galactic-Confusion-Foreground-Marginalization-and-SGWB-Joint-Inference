# Teacher repository structure, source parity and evidence audit

Audit date: 2026-10-09. Source completeness and execution coverage are distinct: all upstream files are present, while this project has executed the original CIFAR-10 VP-SDE/DDPM++ small-scale workflow rather than every algorithm or dataset in the original repository.

## Complete source parity

The teacher's current remote HEAD/main and the local pinned wrapper both equal `8c399ccd8079e5fe7e264f8a72ec97a598b33be1`. Its original Score-SDE Git link points to `0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c`.

- Teacher wrapper: **19 tracked files**, plus the original-repository Git link.
- Original Score-SDE: **74 tracked files**.
- Total: **93 files individually matched to their Git blobs**, with SHA-256 records, no missing or modified file, and both worktrees clean.
- The parent Git link and both `.gitmodules` source URLs are checked. Future remote changes require a new audit; this result is dated, not a permanent claim about an evolving branch.

For every upstream path `P`, the exact project path is `external/score-sde-reproduction/P`. Original-repository paths appear below `external/score-sde-reproduction/score_sde/`. The [93-file map](source-file-map.csv) is exhaustive; the following table is a workflow index.

| Teacher component | Exact preserved location | Project support / execution coverage |
| --- | --- | --- |
| `README.md`, `REPRODUCE_CN.md` | Same names under `external/score-sde-reproduction/` | Preserved reference and reproduction instructions |
| `.gitignore`, `.gitmodules` | Same names under the wrapper | Source boundary and pinned original repository |
| `setup_env.sh` | Wrapper root | Local environment setup and CPU launcher supply platform-specific execution settings |
| `compat_patch.py` | Wrapper root | Imported unchanged by every real original-network stage; extra Estimator-import bootstrap is separate |
| `run_train.py` | Wrapper root | Original wrapper imported; training stages call its original `run_lib.train`; general CLI launcher retained |
| `compute_cifar10_stats.py` | Wrapper root | Fully preserved; not executed; uses random-weight Inception, not standard pretrained metric features |
| `plot_loss.py` | Wrapper root | Original `extract_losses` executed to audit all three local TensorBoard runs; final merged plotting/export remains pending |
| `score_sde/` | Complete nested submodule | All models, SDEs, losses, samplers, configurations, evaluation, likelihood and demo files preserved; selected VP/DDPM++ path executed |
| `exp/vp_cifar10_ncsnpp/loss_history.npz` | Exact same relative path under wrapper | Teacher reference data: 4,281 training and 2,141 evaluation records; last logged training label 214000 |
| `exp/vp_cifar10_ncsnpp/loss_curve.png` | Exact same relative path under wrapper | Teacher reference figure; not a project-generated result |
| `exp/vp_cifar10_ncsnpp/samples/iter_{50000,100000,150000,200000}_host_0/{sample.np,sample.png}` | All eight files preserved at original paths | Teacher reference samples; separate from our update-200 samples |

A recursive clone is required to populate both source levels:

```bash
git clone --recurse-submodules https://github.com/leichang131-debug/Score-Based-Diffusion-Galactic-Confusion-Foreground-Marginalization-and-SGWB-Joint-Inference.git
# For an existing checkout:
git submodule update --init --recursive
```

GitHub browsing follows the pinned submodule links. A parent-repository ZIP alone does not include the nested source contents. Copying a second model source tree into `src/` would create divergent duplicates; the research `src/sgwb_diffusion/` directories are currently future-work placeholders.

## Configuration and entry-point alignment

The three local configurations derive from the unchanged original `configs/vp/cifar10_ddpmpp_continuous.py`. The evidence audit checks every configuration key and permits differences only in training/evaluation batch size, jitted-step grouping, iteration budget, output frequencies and automatic snapshot sampling. All network, objective, Adam, learning-rate/warmup, EMA and sampler fields remain the same.

Project-owned diagnostic wrappers time completed `pmap` calls and verify saves/restores. The 200-update runner names checkpoints with actual `state.step` to avoid quotient-index collisions, then saves a final preemption checkpoint at 200. These are explicit execution/output adaptations, not edits to the upstream network or algorithm. Python 3.12 dependencies and the TF-GAN Estimator-import bootstrap are documented separately in the environment guide.

The repository contains CLI evaluation and Inception-support code, but standard FID/IS/KID, likelihood/BPD, other SDEs/models/datasets and controllable generation have not been validated by these smoke stages. Presence of a module does not constitute its reproduction.

## Evidence completeness

The unchanged teacher loss reader extracted all local TensorBoard records:

| Run | Training records | Validation records | Original loop labels |
| --- | ---: | ---: | --- |
| Original 20-update check | 20 | 4 | 0–19 |
| Restart and continuation | 2 | 2 | 20–21 |
| Continuation to 200 | 178 | 8 | 22–199 |
| Total | **200** | **14** | **0–199, continuous and unique** |

Step/value checks against published stage JSON records passed. Console formatting accounts for maximum rounding differences below 0.000006. Actual completed updates equal loop labels plus one. The last training observation is update 200; the last validation observation is update 181, so their ratio must not be called a same-update final ratio.

- [Source audit](source-audit.json): exact file coverage and current remote snapshot.
- [Evidence audit](evidence-audit.json): scalar counts, configuration differences, log/event file hashes, checkpoint/sample checksum verification.
- [20-update report](original-20-updates.md), [typed continuation](resume-check.md), [200-update benchmark](original-200-updates.md), [EMA sampling](sampling-check.md).
- Raw TensorBoard event files, console logs and model checkpoints remain in ignored local `runs/` directories. Published hashes and records support review, but a new clone cannot read those local files until artifacts are provided.

### Final publication package

The [final report](final-report.md) completes the publication work: merged four-field NPZ/CSV, full and late warmup loss views, normalized completed-stage logs, byte-identical TensorBoard copies, runtime/issue ledgers and linked restoration/sampling evidence. The package is under `results/score-sde/final-summary/` and can regenerate its plots without local model checkpoints or CIFAR-10.

Original model checkpoints remain local; their checksums and typed restoration evidence are published. This remains a small-scale workflow reproduction, without convergence, standard image metrics or reproduction of the teacher's 214k numerical results.

The teacher plotting script's overfitting label is a heuristic based on recent train/eval averages. It is not a statistically supported overfitting assessment for this short, batch-one, changing-validation-frequency run.

## Redundancy assessment

No project-owned model implementation duplicates the teacher source. The original Git submodule and its nested submodule are the canonical source, including algorithms that were not exercised in this stage.

There is avoidable helper-level repetition across project diagnostics: serialized-state hashing/finite checks, model-state template construction and loss parsing. These can later be consolidated into a shared utility while preserving the documented assertions and comparing existing state hashes. The stage-specific scripts and configurations represent different experiments and should retain clear entry points.

`sampling-validation.json` and `results/score-sde/original-200-sampling/summary.json` are currently byte-identical. The documentation file is the canonical detailed record; the results copy is a convenience mirror. The audit checks equality. A later publication cleanup can replace the mirror with a concise summary/link.

Failed diagnostic-attempt directories, caches and large old checkpoints are local generated artifacts, not committed source. They can be archived according to research needs; their presence does not change source parity. Future TDC/SGWB placeholder directories belong to the broader research repository and are not duplicated Score-SDE code.
