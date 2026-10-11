"""Audit the unchanged local rapid-search notebook, optimization and input identity."""
import base64,hashlib,io,json,subprocess
from pathlib import Path
import nbformat
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];NAME='1_TDIFlyGB_Rapid_Search(CPU).ipynb'
SRC=ROOT/'external/triangle-gb';OUT=ROOT/'results/triangle-gb/example-1'
p=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
a=nbformat.read(SRC/'Examples'/NAME,as_version=4);b=nbformat.read(p,as_version=4)
e=json.loads((OUT/'execution.json').read_text());d=json.loads((OUT/'diagnostics.json').read_text())
checks={'same_filename':p.name==NAME,'same_cell_count':len(a.cells)==len(b.cells),'same_code_and_markdown':len(a.cells)==len(b.cells) and all(x.cell_type==y.cell_type and x.source==y.source for x,y in zip(a.cells,b.cells)),'same_attachments':all(x.get('attachments',{})==y.get('attachments',{}) for x,y in zip(a.cells,b.cells)),'upstream_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),'execution_success':e['execution_passed'],'all_nonempty_code_cells_executed':all(c.execution_count is not None for c in b.cells if c.cell_type=='code' and c.source.strip()),'no_errors':not e['error_outputs'],'four_local_figures':len(e['generated_figures'])==4,'notebook_hash_matches':hashlib.sha256(p.read_bytes()).hexdigest()==e['executed_notebook_sha256'],'original_full_scale':d['dt_seconds']==10 and d['Nsparse']==512 and d['source_index']==4 and d['td']['shape']==[2,3147175] and d['band_data']['shape']==[2,157] and d['recovered_waveform']['shape']==[2,157],'finite_waveforms':all(d[k]['finite'] for k in ['time_axis','td','band_frequency','band_data','recovered_waveform','residual']),'positive_finite_psd':bool(np.isfinite(d['PSDlevel']) and d['PSDlevel']>0),'optimizer_success':d['optimizer']['success'],'search_inside_bounds':bool(np.all((np.array(d['optimizer']['x'])>=0)&(np.array(d['optimizer']['x'])<=1))),'finite_recovered_parameters':bool(all(np.isfinite(v) for v in d['searched_parameters'].values())),'objective_recomputed':bool(np.isclose(-d['optimizer']['fun'],d['best_F'][0],rtol=1e-12)),'best_F_not_worse_than_truth':bool(d['best_F'][0]>=d['true_F'][0]*(1-1e-6)),'upstream_objective_neighborhood':bool(np.isclose(d['optimizer']['fun'],-3126.0335911147595,rtol=1e-3))}
with np.load(OUT/'search-band.npz') as z:
 checks['saved_arrays_finite']=all(np.isfinite(z[k]).all() for k in z.files)
 checks['residual_matches_data_minus_waveform']=bool(np.array_equal(z['residual'],z['data']-z['recovered_waveform']))
 data_norm=4*np.sum(abs(z['data'])**2)/d['Tobs_seconds']/d['PSDlevel']
 residual_norm=4*np.sum(abs(z['residual'])**2)/d['Tobs_seconds']/d['PSDlevel']
 checks['F_residual_identity']=bool(np.isclose((data_norm-residual_norm)/2,d['best_F'][0],rtol=1e-10))
 checks['residual_power_reduced']=bool(residual_norm<data_norm)
sim=ROOT/'external/triangle-simulator'
checks['simulator_pin_and_clean']=subprocess.check_output(['git','-C',str(sim),'rev-parse','HEAD'],text=True).strip()=='ab796358e9a36c8987f6bb53a97230d603bfdfd5' and not subprocess.check_output(['git','-C',str(sim),'status','--porcelain'],text=True)
checks['actual_module_origins']=all(Path(d['module_files'][name]).resolve()==(ROOT/relative).resolve() for name,relative in {'Triangle.GW':'external/triangle-simulator/Triangle/GW.py','Triangle.Orbit':'external/triangle-simulator/Triangle/Orbit.py','Triangle_GB.TDIFly':'external/triangle-gb/Triangle_GB/TDIFly.py'}.items())
inputs=[]
for name,size,md5,sha in [('0_1_VGB_TDIXYZ.h5',100707680,'01b91a77eef8ae14b12473fa11b9f5ce','766b50adaabe7dfca1a7cff853845a920f5467b2ffb7ef6e064231ba1ed6bdb3'),('0_1_VGB_parameters.h5',7904,'53ac143f8537996bf73c2dcd2419f4f4','484862f47179b295f8750a5733ee93d912b9a717faef88cecc7d011ad439ce9e')]:
 raw=ROOT/'data/raw/triangle-gb'/name;blob=raw.read_bytes();m=hashlib.md5(blob).hexdigest();h=hashlib.sha256(blob).hexdigest()
 checks[f'input_identity_{name}']=len(blob)==size and m==md5 and h==sha
 inputs.append({'path':str(raw.relative_to(ROOT)),'bytes':len(blob),'md5':m,'sha256':h})
figures=[]
for i in [7,10,15,26]:
 ref=next(o.data['image/png'] for o in a.cells[i].outputs if 'image/png' in o.get('data',{}))
 local=next(o.data['image/png'] for o in b.cells[i].outputs if 'image/png' in o.get('data',{}))
 raw=base64.b64decode(local);png=next(OUT.glob(f'cell-{i:02d}-*.png'))
 checks[f'figure_{i}_matches_local_notebook']=png.read_bytes()==raw
 r=np.asarray(Image.open(io.BytesIO(base64.b64decode(ref))));v=np.asarray(Image.open(io.BytesIO(raw)))
 figures.append({'cell_index':i,'reference_shape':list(r.shape),'local_shape':list(v.shape),'pixel_equal':bool(np.array_equal(r,v))})
report={'passed':all(checks.values()),'checks':checks,'inputs':inputs,'figure_comparison':figures,'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in b.cells),'source_commit':e['source_commit'],'reference_objective':-3126.0335911147595,'local_objective':d['optimizer']['fun'],'limitations':'Unseeded single differential-evolution run: iteration counts and parameters need not be identical. Objective-neighborhood check is a reference sanity check, not proof of a global optimum. Original F-statistic maximizes linear amplitudes rather than computing a Bayesian marginal posterior. Orbit extrapolation and constant estimated PSD remain original defaults.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
files=[p,SRC/'Examples'/NAME,ROOT/'scripts/reproduction/run-triangle-gb-example-1.py',ROOT/'scripts/reproduction/audit-triangle-gb-example-1.py',ROOT/'docs/reproduction/triangle-gb/example-1.md',ROOT/'scripts/reproduction/triangle_gb_path_adapter.py',ROOT/'results/triangle-gb/data/validation.json']
files+=list((SRC/'Triangle_GB').glob('*.py'))+list((sim/'Triangle').glob('*.py'))+list((sim/'OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))+list((ROOT/'environments/triangle-gb').glob('requirements*'))
files+=[x for x in OUT.iterdir() if x.is_file() and x.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps([{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(files)],indent=2)+'\n')
assert report['passed']
