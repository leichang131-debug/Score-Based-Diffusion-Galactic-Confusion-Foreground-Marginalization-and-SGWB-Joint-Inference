# Fresh ten-parameter posteriors in the paper Figure 8 style

The [combined corner plot](10para_corner.png) overlays the three newly sampled posteriors. The single-configuration plots use the same comparison axes. All corner plots include the paper's component spectrum inset.

| Configuration | Posterior plot | Fresh samples |
| --- | --- | ---: |
| Static equal-arm frequency domain | [fit_079](fit_079_corner.png) | 5,926 |
| Equal-arm time domain | [fit_081](fit_081_corner.png) | 5,615 |
| Unequal-arm time domain | [fit_083](fit_083_corner.png) | 5,581 |

The [component spectrum plot](component_spectra.png) and its [3,419-bin table](component_spectra.csv) show the injected `Omega_DWD`, `Omega_ast`, and `Omega_SW` curves and the Taiji XX equivalent noise curve, matching the definition of the paper inset. The calculation uses the verified archived equal-arm time-domain response and noise-transfer tables and the injection parameters shared by all three fresh fits. These curves show the injection and instrument context. The corner contours and marginal densities come from the fresh samples.

All labels, ticks and legends use Matplotlib's LaTeX renderer. The adapter uses upstream cells 03, 41, and 43 for typography, spectrum construction, and drawing. It retains the paper's red, green and purple layers, black truth lines, KDE diagonals, 39.3% and 86.5% two-dimensional contours, and 320 dpi PNG output. The comparison ranges are shared across all rendered layers. The fixed manuscript windows for the two sound-wave parameters exclude a small number of tail draws from the displayed ranges. Counts and input/output hashes are recorded in [provenance.json](provenance.json). The HDF5 archives still contain every saved posterior draw. Legend text identifies configurations only.


## Side-by-side comparison with the paper

[Open the full-resolution Figure 8 comparison](figure-8-comparison.png). The left panel is the [replay from the authors' archived samples](../../reference-replay/README.md), verified pixel-for-pixel against [Figure 8 of the arXiv v2 paper](https://arxiv.org/html/2608.11276v2#S3.SS3). The right panel uses the three new production runs. Both panels retain their full resolution and native axes. Red denotes static equal-arm FD, green denotes equal-arm TD, and purple denotes unequal-arm TD. Black lines mark the shared injected values.

Direct comparison of the archived and fresh `pe/trace` samples shows that, across the 30 configuration–parameter pairs, median shifts are within about 5% of the archived central 68% interval half-width. The central 68% interval widths also differ by at most about 5%. The clearest tail difference is the unequal-arm sound-wave peak frequency. Its full-sample standard deviation falls from 0.04137 to 0.03415 dex, while its central 68% interval changes from [−2.30959, −2.26306] to [−2.30952, −2.26281] in `log10(f_p/Hz)`. The fresh rendering passes a common range to all three layers, which can change tick placement and contour binning. The spectrum inset is pixel-identical between panels. The Bayes factors on the left come from the paper's archived full and null fits. The fresh panel shows the ten-parameter results without Bayes-factor annotations.

From the repository root, after extracting the [formal run archives](../README.md) and preparing the official replay data with the author's `get_data.py`, run:

```sh
environments/taiji-sgwb-time-domain/.venv/bin/python \
  scripts/reproduction/taiji-sgwb-time-domain/plot-fresh-figure-8.py \
  runs/taiji-sgwb-time-domain/formal-unpacked/production \
  runs/taiji-sgwb-time-domain/fresh-figure-8
```

The environment needs `latex` and `dvipng` on its path. The code records source and sample hashes without changing the pinned upstream files.
