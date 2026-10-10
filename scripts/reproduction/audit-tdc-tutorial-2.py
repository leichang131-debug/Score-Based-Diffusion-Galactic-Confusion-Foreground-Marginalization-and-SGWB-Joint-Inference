"""Audit source correspondence and saved Tutorial 2 evidence without rerunning it."""
import hashlib
import json
from pathlib import Path
import subprocess
import nbformat
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'external/triangle-simulator'
OUT=ROOT/'results/tdc/tutorial-2'
NAME='2_Demo_More_Advanced_Noise_and_TDI_Simulation.ipynb'
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
 'static_image_identical':(SRC/'Figures/noise_types.png').read_bytes()==(executed_path.parent.parent/'Figures/noise_types.png').read_bytes(),
 'all_nonempty_code_cells_executed':all(c.execution_count is not None for c in executed.cells if c.cell_type=='code' and c.source.strip()),
 'no_error_outputs':not any(o.output_type=='error' for c in executed.cells for o in c.get('outputs',[])),
 'three_generated_figures':len(execution['generated_figures'])==3,
 'default_scale':diag['size']==400000 and diag['sample_rate_hz']==4 and diag['workers']==6 and diag['interpolation_order']==31 and diag['drop_points']==4000,
 'finite_four_tdi_methods':all(d['finite'] and d['shape']==[400000] for d in diag['methods'].values()),
 'path_method_identical_to_named_method':diag['differences']['method3']['identical_to_method1'],
 'finite_spectra':all(d['finite'] for d in diag['spectra'].values()),
 'execution_passed':execution['execution_passed'],
 'executed_notebook_hash_matches':hashlib.sha256(executed_path.read_bytes()).hexdigest()==execution['executed_notebook_sha256']}
noise=json.loads((OUT/'noise-diagnostics.json').read_text())
glitch=json.loads((OUT/'glitch-diagnostics.json').read_text())
checks['finite_modified_noise']=noise['X2']['finite'] and noise['spectrum']['finite'] and noise['theory']['finite'] and all(v['finite'] for v in noise['modified_readout_arrays'].values())
checks['finite_glitch']=all(glitch[k]['finite'] for k in ['X2','injected_acceleration','injected_ffd'])
checks['glitch_injection_config']=glitch['injection_time_seconds']==30000 and glitch['size']==400000
checks['finite_saved_subsets']=True
for filename in ['noise-spectra-selected.npz','method-spectra-selected.npz','glitch-window.npz']:
    with np.load(OUT/filename) as data:
        checks['finite_saved_subsets'] &= all(np.isfinite(data[k]).all() for k in data.files)
image_comparison=[]
checks['saved_images_match_executed_notebook']=True
import base64
for i,(a,b) in enumerate(zip(original.cells,executed.cells)):
    original_images=[base64.b64decode(o['data']['image/png']) for o in a.get('outputs',[]) if 'image/png' in o.get('data',{})]
    executed_images=[base64.b64decode(o['data']['image/png']) for o in b.get('outputs',[]) if 'image/png' in o.get('data',{})]
    if original_images:
        image_comparison.append({'cell_index':i,'reference_count':len(original_images),'local_count':len(executed_images),'byte_identical':[x==y for x,y in zip(original_images,executed_images)]})
    for j,o in enumerate(b.get('outputs',[])):
        if 'image/png' in o.get('data',{}):
            checks['saved_images_match_executed_notebook'] &= (OUT/f'cell-{i:02d}-output-{j}.png').read_bytes()==base64.b64decode(o['data']['image/png'])
files=[SRC/'Tutorials'/NAME,SRC/'uv.lock',ROOT/'environments/tdc/installed-macos-arm64.json']
files+=list((SRC/'OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))
files+=list((SRC/'Triangle').glob('*.py'))
files+=[executed_path,executed_path.parent.parent/'Figures/noise_types.png',
        ROOT/'scripts/reproduction/run-tdc-tutorial-2.py',ROOT/'scripts/reproduction/audit-tdc-tutorial-2.py',
        ROOT/'docs/reproduction/tdc/tutorial-2.md']
files+=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ('audit.json','manifest.json')]
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report={'passed':all(checks.values()),'reference_image_comparison':image_comparison,'checks':checks,'cell_count':len(executed.cells),'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in executed.cells),'source_commit':execution['source_commit'],'limitations':'Single stochastic realization; no claim of bitwise equality of regenerated stochastic figures or ensemble statistical calibration'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['passed']
