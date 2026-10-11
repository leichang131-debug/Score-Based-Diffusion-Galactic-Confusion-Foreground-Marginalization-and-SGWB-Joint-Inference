"""Audit locally executed Example 0 and its correspondence to the pinned source."""
import base64,hashlib,io,json,subprocess
from pathlib import Path
import nbformat
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];NAME='0_TDIFlyGB_Compare_TD_FD_Waveforms(CPU).ipynb'
SRC=ROOT/'external/triangle-gb';OUT=ROOT/'results/triangle-gb/example-0'
p=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
a=nbformat.read(SRC/'Examples'/NAME,as_version=4);b=nbformat.read(p,as_version=4)
e=json.loads((OUT/'execution.json').read_text());d=json.loads((OUT/'diagnostics.json').read_text())
checks={'same_filename':p.name==NAME,'same_cell_count':len(a.cells)==len(b.cells),'same_code_and_markdown':all(x.cell_type==y.cell_type and x.source==y.source for x,y in zip(a.cells,b.cells)),'same_attachments':all(x.get('attachments',{})==y.get('attachments',{}) for x,y in zip(a.cells,b.cells)),'upstream_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),'execution_success':e['execution_passed'],'all_nonempty_code_cells_executed':all(c.execution_count is not None for c in b.cells if c.cell_type=='code' and c.source.strip()),'no_errors':not e['error_outputs'],'two_local_figures':len(e['generated_figures'])==2,'notebook_hash_matches':hashlib.sha256(p.read_bytes()).hexdigest()==e['executed_notebook_sha256'],'original_full_scale':d['dt_seconds']==10 and d['Nsparse']==1024 and d['td']['shape']==[3,3155814] and d['td_fft_band']['shape']==[3,631] and d['fd_template_band']['shape']==[3,631],'all_waveforms_finite':all(d[k]['finite'] for k in ['time_axis','td','fd_full','band_frequency','td_fft_band','fd_template_band']),'upstream_displayed_mismatch_agreement':bool(np.isclose(d['mismatch'][0],0.00036493,atol=5e-9,rtol=0))}
with np.load(OUT/'waveform-band.npz') as z:
 checks['saved_band_finite']=all(np.isfinite(z[k]).all() for k in z.files)
 independently=1-np.real(np.sum(np.conj(z['td_fft'])*z['fd_template']))/np.sqrt(np.sum(abs(z['td_fft'])**2)*np.sum(abs(z['fd_template'])**2))
 checks['mismatch_formula_consistent']=bool(np.allclose(independently,d['mismatch'][0],atol=1e-14,rtol=0))
sim=ROOT/'external/triangle-simulator'
checks['simulator_pin_and_clean']=subprocess.check_output(['git','-C',str(sim),'rev-parse','HEAD'],text=True).strip()=='ab796358e9a36c8987f6bb53a97230d603bfdfd5' and not subprocess.check_output(['git','-C',str(sim),'status','--porcelain'],text=True)
checks['actual_module_origins']=all(Path(d['module_files'][name]).resolve()==(ROOT/relative).resolve() for name,relative in {'Triangle.GW':'external/triangle-simulator/Triangle/GW.py','Triangle.Orbit':'external/triangle-simulator/Triangle/Orbit.py','Triangle_GB.TDIFly':'external/triangle-gb/Triangle_GB/TDIFly.py'}.items())
figures=[]
for i in [9,14]:
 ref=next(o.data['image/png'] for o in a.cells[i].outputs if 'image/png' in o.get('data',{}))
 local=next(o.data['image/png'] for o in b.cells[i].outputs if 'image/png' in o.get('data',{}))
 raw=base64.b64decode(local)
 png=next(OUT.glob(f'cell-{i:02d}-*.png'))
 checks[f'figure_{i}_matches_local_notebook']=png.read_bytes()==raw
 r=np.asarray(Image.open(io.BytesIO(base64.b64decode(ref))));v=np.asarray(Image.open(io.BytesIO(raw)))
 figures.append({'cell_index':i,'reference_shape':list(r.shape),'local_shape':list(v.shape),'pixel_equal':bool(np.array_equal(r,v)),'note':'Original plotting source retained; one-pixel canvas/layout differences are not waveform disagreement.'})
report={'figure_comparison':figures,'passed':all(checks.values()),'checks':checks,'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in b.cells),'source_commit':e['source_commit'],'mismatch':d['mismatch'],'independent_mismatch':float(independently),'reference_mismatch_display':0.00036493,'limitations':'Single default source and band. Original mismatch is unweighted across A/E/T, not PSD-weighted inference accuracy. Orbit boundary extrapolation remains part of upstream defaults. Pixel equality across plotting versions is not required.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
files=[p,SRC/'Examples'/NAME,ROOT/'scripts/reproduction/run-triangle-gb-example-0.py',ROOT/'scripts/reproduction/audit-triangle-gb-example-0.py',ROOT/'docs/reproduction/triangle-gb/example-0.md']
files+=list((SRC/'Triangle_GB').glob('*.py'))+list((ROOT/'external/triangle-simulator/Triangle').glob('*.py'))+list((ROOT/'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))
files+=list((ROOT/'environments/triangle-gb').glob('requirements*'))
files+=[x for x in OUT.iterdir() if x.is_file() and x.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps([{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(files)],indent=2)+'\n')
assert report['passed']
