# Paper figure correspondence and detail review

The reference screenshots are Figures 3, 4 and 6 of arXiv:2601.00169v2. Current formal inference is only the original 2.8 flexing-arm template experiment. A completed 350-ensemble chain for that experiment is not the complete collection of experiments in these paper figures.

| Reference | What it contains | Present locally | Difference and action |
| --- | --- | --- | --- |
| Figure 3 | Blue 2.8_EQ and pink 2.8 template posteriors, red injection, 16/84% marginal markers, 68/95% joint contours | Pink 2.8 posterior and all of its stated markers/contours | Blue EQ posterior is a different dataset experiment, not a drawing option. Added an explicit 2.8 template legend. No EQ curve fabricated. |
| Figure 4 | ACC/OMS spacecraft averages inferred from **2.8_EQ**, with cyan 16/50/84% dashed markers and red truth | Spacecraft averages from **2.8**, originally styled after Figure 8's template component | Missing quantile markers were a genuine available-data plotting omission relative to this screenshot. Added actual draw-derived 16/50/84% dashed lines. Data remain 2.8, not relabeled EQ. |
| Figure 6 | Orange 2.8 template 95% spectrum band, pink 2.8 RJMCMC interpolation 95% band, red injection and relative-error panel | Orange template, red injection, 95% band and relative-error panel | Pink interpolation is a different posterior/model from rj_nofg_28t.py. It cannot be generated from the fixed power-law template chain. No RJ chain has completed. |

Within each actually available result, the original sample quantiles, two joint contour levels, physical units, red truth lines, frequency scaling and fractional error are retained. Minor axis-range, binning, smoothing and typography differences can still arise because final publication plotting scripts are not all provided and samples differ. Styling agreement is not a claim of identical posterior numbers or verified convergence.

To reproduce the reference panels in full requires three distinct analyses: (1) 2.8 template, now completed with convergence unconfirmed; (2) 2.8_EQ template, not yet executed; and (3) 2.8 RJMCMC interpolation, not yet executed. All three need their own data/model configuration, sampler diagnostics and traceable outputs. No extra long sampling was started during this review.

Before-refinement plots are preserved under attempts/before-paper-detail-review/. Native HDF, final state and exported cold samples are unchanged, verified against paper-detail-review-input-hashes.json. The noise quantiles are saved numerically in posterior-noise-spacecraft.json. The archived original automatic-analysis error remains a separate earlier incident.
