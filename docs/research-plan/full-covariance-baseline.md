# Full-covariance Taiji baseline plan

Liang et al. provide the primary reference for the current joint-inference study. The first deliverable is Figure 8 from fresh sampling, with a numerical comparison to the authors' archived results and a runtime comparison across the three detector configurations. See [the paper](https://arxiv.org/abs/2608.11276v2) and [the pinned upstream manifest](https://github.com/Eric-Friedman-666/taiji-sgwb-time-domain/blob/e5ebd75639c3433717ff2cafe52e7f2f5a3f34bb/reference/inference_manifest.json).

| Configuration | Full model | No sound waves | Simulation seed |
| --- | --- | --- | --- |
| Static FD equal arm | fit_079 | fit_078 | 2026060255 |
| TD equal arm | fit_081 | fit_080 | 2026069815 |
| TD unequal arm | fit_083 | fit_082 | 2026069415 |

1. Integrate the fixed upstream tree with its original names, vendored Triangle-Simulator, license, and notices. Record the source hash and environment separately.
2. Replay the archived Figure 8 for a reference. Rebuild one production input bundle per configuration and verify the masks, matrix conventions, 360 segments, 3419 retained bins, and truth log likelihood. Pair each full fit and null fit using the same bundle.
3. Measure compilation and warmed likelihood latency, and verify restart in a short pilot. Use the production sampler settings from the manifest for formal runs. Keep pilot settings and timing reports tied to their own run IDs.
4. Run the three full fits and three null fits. Record sampler seed, backend, precision, CPU allocation, wall time, likelihood calls, peak RAM and GPU memory where applicable, checkpoints, and evidence uncertainty. Use a common backend and comparable resource allocation for the primary timing comparison. Report cache construction and reuse separately, and accumulate active sampling time across resumed sessions.
5. Produce Figure 8 from the six fresh results. Record the exact HDF5 sources and plotting revision. Report parameter summaries, termination and evidence diagnostics, timing, and comparison against the archived posteriors. Retain large products on research storage with hashes and retrieval information.

The next experiment after baseline reproduction will assess controlled foreground or detector mismatch. The earlier Route B and Jiang TaijiSGWB work remain documented as references for subsequent research.
