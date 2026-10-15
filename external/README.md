# Upstream source integration

Updated: 2026-10-15. All upstream scientific source remains unmodified and retains its original license. Project-owned path, cache, checkpoint and plotting adapters live outside the source directories.

| Component | Integration | Fixed upstream commit |
| --- | --- | --- |
| Score-SDE reproduction | Recursive submodule | `8c399ccd8079e5fe7e264f8a72ec97a598b33be1` |
| Nested original Score-SDE | Submodule inside the wrapper | `0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c` |
| Triangle-Simulator | Submodule | `ab796358e9a36c8987f6bb53a97230d603bfdfd5` |
| Triangle-GB | Submodule | `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c` |
| Triangle-BBH | Submodule, including bundled modified WF4Py | `f99b0a34ea8d085aff67220bdc165a746ba5ceda` |
| TaijiSGWB | Directly tracked fixed source snapshot, 19 original files | `4afaad4044b08721e7f1ce29cba3b0d912636dce` |

For components that remain submodules:

```bash
git submodule update --init --recursive
```

TaijiSGWB's `demos/` and `src/taijisgwb/` arrive with an ordinary clone; do not initialize that path as a submodule. [The lock](../configs/upstream/taiji-sgwb.json) and [source audit](../results/taiji-sgwb/source/README.md) record exact names, bytes, modes and the reconstructed Git tree. Other component source checkouts may be shallow but contain their complete pinned trees.

The four Triangle-Simulator tutorials and all five Triangle-GB examples have executed locally. Triangle-GB core checks retain six failures; example execution does not certify every interface. Triangle-BBH/WF4Py provide the installed Fisher dependency. See [Triangle-GB status](../docs/reproduction/triangle-gb/README.md).

TaijiSGWB source/environment/data/preprocessing/response/likelihood and template restart validation are complete. The full 2.8 template schedule and six figures are saved, with convergence unconfirmed. EQ-template/RJMCMC sampling and full-paper reproduction remain incomplete; see [current status](../docs/reproduction/taiji-sgwb/status-and-cluster-handoff.md).
