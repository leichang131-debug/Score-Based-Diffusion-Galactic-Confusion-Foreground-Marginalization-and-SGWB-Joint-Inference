# Upstream source integration

Score-SDE reproduction is integrated as an unmodified Git submodule at commit `8c399ccd8079e5fe7e264f8a72ec97a598b33be1`. Its original Score-SDE submodule is pinned to `0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c`.

```bash
git submodule update --init --recursive
```

Triangle-Simulator is integrated at `ab796358e9a36c8987f6bb53a97230d603bfdfd5` with all five notebooks and bundled orbit/waveform data. Its GPL-3.0 license is preserved. The source checkout is shallow but contains the complete pinned file tree. Triangle-GB and TaijiSGWB remain source slots; their code has not been downloaded or deployed. Preserve upstream licenses and notices. Project-owned launch adapters live under `scripts/reproduction/`; upstream source is unchanged.
