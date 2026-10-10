"""Audit source correspondence and saved Tutorial 1 evidence without rerunning it."""
import hashlib
import json
from pathlib import Path
import subprocess
import nbformat
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'external/triangle-simulator'
OUT=ROOT/'results/tdc/tutorial-1'
NAME='1_Demo_Laser_Interferometry_and_TDI.ipynb'
original=nbformat.read(SRC/'Tutorials'/NAME,as_version=4)
executed_path=ROOT/'notebooks/reproduction/triangle-simulator/Tutorials'/NAME
executed=nbformat.read(executed_path,as_version=4)
execution=json.loads((OUT/'execution.json').read_text())
diag=json.loads((OUT/'diagnostics.json').read_text())
checks={
 'same_filename':executed_path.name==NAME,
 'same_cell_count':len(original.cells)==len(executed.cells),
 'same_cell_types_and_sources':len(original.cells)==len(executed.cells) and all(a.cell_type==b.cell_type and a.source==b.source for a,b in zip(original.cells,executed.cells)),
 'same_markdown_attachments':all(a.get('attachments',{})==b.get('attachments',{}) for a,b in zip(original.cells,executed.cells)),
 'original_source_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),
 'static_image_identical':(SRC/'Figures/constellation.png').read_bytes()==(executed_path.parent.parent/'Figures/constellation.png').read_bytes(),
 'all_nonempty_code_cells_executed':all(c.execution_count is not None for c in executed.cells if c.cell_type=='code' and c.source.strip()),
 'no_error_outputs':not any(o.output_type=='error' for c in executed.cells for o in c.get('outputs',[])),
 'four_generated_figures':len(execution['generated_figures'])==4,
 'default_scale':diag['size']==400000 and diag['sample_rate_hz']==4 and diag['workers']==6 and diag['interpolation_order']==31 and diag['tdi_order']==31 and diag['drop_points']==4000,
 'finite_measurements_and_tdi':all(d['finite'] and d['shape']==[400000] for d in list(diag['raw'].values())+[diag['X2'],diag['X2_q'],diag['corrected_X2']]),
 'finite_spectra':all(d['finite'] for d in diag['spectra'].values()),
 'execution_passed':execution['execution_passed'],
 'executed_notebook_hash_matches':hashlib.sha256(executed_path.read_bytes()).hexdigest()==execution['executed_notebook_sha256']}
with np.load(OUT/'spectra-selected.npz') as data:
 checks['finite_saved_spectral_subset']=all(np.isfinite(data[k]).all() for k in data.files)
files=[SRC/'Tutorials'/NAME,SRC/'uv.lock',ROOT/'environments/tdc/installed-macos-arm64.json']
files+=list((SRC/'OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))
files+=list((SRC/'Triangle').glob('*.py'))
files+=[executed_path,executed_path.parent.parent/'Figures/constellation.png',
        ROOT/'scripts/reproduction/run-tdc-tutorial-1.py',ROOT/'scripts/reproduction/audit-tdc-tutorial-1.py',
        ROOT/'docs/reproduction/tdc/tutorial-1.md']
files+=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ('audit.json','manifest.json')]
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report={'passed':all(checks.values()),'checks':checks,'cell_count':len(executed.cells),'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in executed.cells),'source_commit':execution['source_commit'],'limitations':'Single stochastic realization; no claim of bitwise equality of regenerated stochastic figures or ensemble statistical calibration'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['passed']
