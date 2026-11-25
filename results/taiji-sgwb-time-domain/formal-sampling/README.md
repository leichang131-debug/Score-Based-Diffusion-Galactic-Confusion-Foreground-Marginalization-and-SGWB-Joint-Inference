# Formal ten-parameter sampling for Figure 8

All three production fits finished on the NVIDIA A800 80 GB PCIe with Bilby 2.6.0, Dynesty 2.1.5, and JAX 0.4.30. They used the fixed upstream [source snapshot](../../../external/taiji-sgwb-time-domain/README.md), the original production settings `nlive=1000`, `dlogz=0.1`, and `walks=64`, and sampler seed `20261017`. All three input bundles passed the upstream truth-likelihood checks.

| Configuration | Server archive | Production wall time | Likelihood calls | Nested iterations | Weighted nested rows | Posterior rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Static equal-arm frequency domain | [fit_079](archives/fit_079.tar.gz) | 10 h 08 m 06 s | 22,399,823 | 56,385 | 57,385 | 5,926 |
| Equal-arm time domain | [fit_081](archives/fit_081.tar.gz) | 12 h 49 m 26 s | 21,896,249 | 56,743 | 57,743 | 5,615 |
| Unequal-arm time domain | [fit_083](archives/fit_083.tar.gz) | 58 h 16 m 35 s | 23,746,939 | 56,144 | 57,144 | 5,581 |

The three production runs total **81 h 14 m 07 s** and **68,043,011** likelihood calls. Wall time is the time recorded by each launcher for its production sampler subprocess, including its startup and final output. The download, input generation, warm benchmarks, and fit_079 pilot are separate. The [runtime CSV](runtime.csv) records precise durations, Bilby's internal sampling times, UTC+08:00 timestamps, evidence values, benchmark timings, and input bundle hashes.

Each fit archive preserves `production/<fit_id>/` from the server, including the Bilby JSON with the posterior and nested samples, Dynesty's weighted result pickle, the final `posterior.h5`, the saved sampler checkpoint, and three available checkpoint plots. The [evidence archive](archives/evidence.tar.gz) contains the formal logs and completion records, three input checks, both backend benchmarks for each configuration, the installed Linux package list, input preparation logs, and the actual launch and benchmark code.

The archive SHA-256 values were generated on the server and verified locally. Local readback confirmed that each Dynesty likelihood count agrees with the Bilby JSON and campaign record, each ten-parameter HDF5 posterior is finite and has the recorded shape, and evidence values agree across the saved formats. These checks establish the integrity of the newly sampled products. Comparison to the authors' archived posteriors and the matched null runs `fit_078`, `fit_080`, and `fit_082` remain separate steps for reproducing the full Figure 8 annotations.

The [fresh posterior and component spectrum plots](posterior-figures/README.md) use the paper layout and label the configurations without Bayes factors.

## Verify and extract

Run from the repository root:

```sh
src=results/taiji-sgwb-time-domain/formal-sampling/archives
out=runs/taiji-sgwb-time-domain/formal-unpacked
mkdir -p "$out"
(cd "$src" && shasum -a 256 -c SHA256SUMS)
for file in "$src"/*.tar.gz; do
  tar -xzf "$file" -C "$out"
done
environments/taiji-sgwb-time-domain/.venv/bin/python \
  scripts/reproduction/taiji-sgwb-time-domain/summarize-formal-sampling.py \
  "$out" "$out/runtime.csv"
```

The HDF5 posterior samples in `pe/trace` are readable after extraction. The `tables` and `frequency` groups retain relative links to the production input bundles, which remain on research storage. Restore those inputs at the recorded link targets to access these groups. Use the archived Linux environment and matching inputs when inspecting sampler checkpoints for a restart.
