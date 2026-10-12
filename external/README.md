# Upstream source integration

Score-SDE reproduction is integrated as an unmodified Git submodule at commit `8c399ccd8079e5fe7e264f8a72ec97a598b33be1`. Its original Score-SDE submodule is pinned to `0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c`.

```bash
git submodule update --init --recursive
```

Triangle-Simulator is integrated at `ab796358e9a36c8987f6bb53a97230d603bfdfd5` with all five notebooks and bundled orbit/waveform data. Its GPL-3.0 license is preserved. The source checkout is shallow but contains the complete pinned file tree. Triangle-GB is now a complete unmodified submodule pinned to `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`, including its package, five examples, orbit files and GPL-3.0 license. Its independent environment is installed; full example execution remains pending. TaijiSGWB is integrated as a complete, unmodified submodule pinned to `4afaad4044b08721e7f1ce29cba3b0d912636dce`. Both original `demos/` programs and all `src/taijisgwb/` modules retain their names, paths and byte content. Source integration and independent macOS environment deployment are complete; official 2.8 data and orbit preparation are complete with 24/24 checks; both original preprocessing prefixes have completed with 20/20 checks each; the complete original response grid is cached with 32/32 checks; physical likelihood and inference remain pending. See [Stage 6](../docs/reproduction/taiji-sgwb/response.md). See [Stage 5](../docs/reproduction/taiji-sgwb/preprocessing.md). See [input evidence](../docs/reproduction/taiji-sgwb/data-preparation.md). See [environment evidence](../docs/reproduction/taiji-sgwb/environment-setup.md). See [source preservation evidence](../results/taiji-sgwb/source/README.md). Preserve upstream licenses and notices. Project-owned launch adapters live under `scripts/reproduction/`; upstream source is unchanged.

Triangle-BBH is pinned at `f99b0a34ea8d085aff67220bdc165a746ba5ceda` to provide the GB network Fisher dependency. Its complete 80-file tree and bundled modified WF4Py are preserved with original licenses; both are installed editable in the Triangle-GB CPU environment.
