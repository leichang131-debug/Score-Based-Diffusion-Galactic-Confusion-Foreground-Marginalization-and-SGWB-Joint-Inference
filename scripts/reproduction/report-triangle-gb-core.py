"""Publish measured results and unresolved upstream issues without hiding failures."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/core-validation'
os.environ['MPLCONFIGDIR']=str(ROOT/'runs/triangle-gb/matplotlib')
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
v=json.loads((OUT/'validation.json').read_text());r=json.loads((OUT/'run.json').read_text());impact=json.loads((OUT/'tutorial-impact.json').read_text());checks={x['name']:x for x in v['checks']}
series=checks['time_FFT_sparse_convergence_4096']['metrics']['series'];fig,axes=plt.subplots(1,2,figsize=(11,4))
x=[128]+[s['Nsparse'] for s in series];y=[checks['time_FFT_vs_sparse_frequency_drop_one']['metrics']['relative_error']]+[s['relative_error'] for s in series]
axes[0].plot(x,np.array(y)*100,'o-');axes[0].axhline(1,color='red',ls='--',label='1% smoke-test criterion');axes[0].set_xscale('log',base=2);axes[0].set_xticks(x,labels=x);axes[0].set_xlabel('Sparse sample count');axes[0].set_ylabel('Relative norm difference (%)');axes[0].set_title('TD FFT vs sparse FD, drop_points=1');axes[0].legend(fontsize=8)
with np.load(OUT/'example-2-fill-impact.npz') as z:
 diff=np.linalg.norm(z['original_template']-z['proper_crop_reference'],axis=(0,1));axes[1].plot(np.arange(len(diff)),diff,'o-',ms=3)
axes[1].set_xlabel('Local frequency-bin index');axes[1].set_ylabel('Template difference norm');axes[1].set_title('Original Example 2: boundary-only difference')
for ax in axes:ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'consistency.png',dpi=180);plt.close(fig)
rows='\n'.join(f"| {c['name']} | {'PASS' if c['passed'] else 'FAIL'} | {c['metrics'].get('relative_error','—') if 'metrics' in c else c['exception']} |" for c in v['checks'])
e=impact['example_2'];convergence='\n'.join(f"| {a} | {b*100:.4f}% |" for a,b in zip(x,y))
text=f'''# Triangle-GB core CPU interface verification

## Outcome

The verification work completed locally. **{v['passed_count']} of {len(v['checks'])} checks passed; {v['failed_count']} failed. Package-wide acceptance did not pass.** Do not interpret script exit code zero, an evidence-integrity audit, or completion of five example notebooks as proof that every original interface is correct.

The checks use the pinned unmodified source, public imports, original three-detector analytic orbit configuration, three deterministic synthetic GB sources, 65,536 time samples at 10 seconds, and independently computed numerical references. This is a targeted small CPU test suite, not another full-scale tutorial or posterior rerun. Raw and real-waveform boundary probes make truncation defects observable.

Whole-process time including imports: {r['wall_seconds']:.3f} s for the two sequential commands. Core computational section: {v['wall_seconds']:.3f} s; actual command timings are in `run.json`. These timers have different scopes. No GPU, arbitrary-orbit accuracy, complete auxiliary-method coverage or posterior calibration is claimed.

## Passed paths

Original package imports and module origin; batched vs single-source frequency responses; full spectral scatter and vectorized wide-band filling; full/intrinsic parameter coordinate round-trips; explicit XYZ-to-A/E/T transform; likelihood from the explicit residual formula; SNR and mismatch normalization; F-statistic vs an independent real four-amplitude least-squares solution; non-default time response batch consistency; six-channel network vs three separately instantiated single-detector responses; network source batching; declared rejection of network time mode; positive-frequency auxiliary PSD smoke checks; source pins and clean checkouts.

Likelihood agreement relative error is {checks['likelihood_explicit_residual']['metrics']['relative_error']:.3e}; independent F-statistic relative error is {checks['Fstatistics_independent_lstsq']['metrics']['relative_error']:.3e}. Network/single-detector and batch/single-source responses match exactly in the selected configurations.

## Unresolved original issues

### 1. Default time-domain output is all zero

`TDIFlyGB.__call__(domain="time")` assigns `res[:, -self.drop_points:] = 0`. For the default `drop_points=0`, `-0` is zero and this clears the entire array. A nonzero injection therefore returns zero. With explicit `drop_points=1`, the original branch produces finite nonzero outputs and batch/single results agree. This is a diagnostic contrast, not a source repair and not approval to silently replace the default.

The first official example's independent time reference does not directly validate this package time branch. Frequency-domain tutorial calls do not execute this zeroing statement.

### 2. Vectorized partial-band fill overwrites boundary bins

`fill_fftseries` clips all indices to StartBound/EndBound before assignment, rather than discarding out-of-band samples. Repeated clipped indices overwrite the edge bins with out-of-band data. The synthetic partial-band probe and a real generated response both disagree with independent cropping; interior bins agree in the assessed original Example 2. Wide bands containing the complete support pass.

### 3. Loop fill fails on the tested wide band

When a source starts after StartBound, `fill_fftseries_loop` sets `temp_start_idx=StartBound-start_idx_event`, a negative offset. In the tested wide-band case this leads to an empty destination slice and a broadcast ValueError. The tested narrow overlapping case passes. It is not safe to recommend this helper as a universal replacement for vectorized filling.

### 4. Selected time/frequency accuracy criterion not met

Using explicit `drop_points=1`, the rectangular 7.59-day comparison does not achieve the predeclared 1% relative-norm smoke tolerance at either 128 or 4096 sparse points. Increasing resolution decreases the error:

| Nsparse | Relative norm difference |
|---:|---:|
{convergence}

These are **two failed precision checks**, not evidence of an additional proven algebraic bug. Sparse approximation, finite support, envelope endpoint discontinuity/aliasing, and endpoint dropping require a controlled window/observation/resolution study. The failure is not relabeled as success or erased by increasing the tolerance. This short test is not numerically comparable to the first tutorial's year-scale, differently constructed time-domain reference and mismatch metric.

## Impact on existing tutorials

Original Example 2, at its recorded injection and exact time-axis SHA-256: Nsparse=512, analyzed bins {e['band_indices']}, sparse start {e['sparse_start_indices']}. The original vectorized template differs from independent proper cropping by **{e['relative_template_error']*100:.4f}%** in relative norm. Interior bins are exactly equal. Original truth log likelihood is {e['original_truth_log_likelihood']:.9f}; mathematical-crop reference is {e['proper_crop_truth_log_likelihood']:.9f}; difference is **{e['log_likelihood_change']:.9f}**.

This confirms a real, small but nonzero boundary effect in that assessed template. It does not bound the effect at every posterior sample or prove posterior bias is negligible. Neither the original posterior nor its existing evidence is replaced. Examples 0, 1 and 3 also use vectorized filling; their actual boundary impacts have not been quantified in this milestone and should not be assumed zero.

For the network tutorial's original injection, its 1024-bin sparse support lies completely inside the analyzed band; the saved six-channel injected signal reproduces. That injection does not trigger the clipping defect. This is not a proof for every network posterior sample, and does not resolve posterior angle mode weights or calibration.

## Complete check ledger

| Check | Result | Relative error or exception |
|---|---|---|
{rows}

## Reproducibility and evidence

Run from the main repository:

```sh
environments/triangle-gb/.venv/bin/python scripts/reproduction/run-triangle-gb-core-validation.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/report-triangle-gb-core.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/audit-triangle-gb-core.py
```

`results/triangle-gb/core-validation/` retains all check statuses, exact test parameters/seeds, host/runtime/command records, stdout/stderr, band arrays, comparison figures, real tutorial boundary references and SHA-256 manifest. Package-level failures are separate from evidence-integrity audit status.

Upstream source remains pinned and clean. Fixes should be developed later as explicit reviewed patches or an upstream update, with before/after verification. These findings are not a claim that the five tutorial reproductions were fabricated or failed to run; they limit the numerical guarantees that can be inferred from those reproductions.
'''
(ROOT/'docs/reproduction/triangle-gb/core-validation.md').write_text(text)
