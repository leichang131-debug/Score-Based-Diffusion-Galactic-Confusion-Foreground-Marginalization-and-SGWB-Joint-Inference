"""Audit full Sangria reconstruction, source correspondence and selected catalog conventions."""
import base64,hashlib,json,subprocess
from pathlib import Path
import h5py,nbformat,numpy as np
ROOT=Path(__file__).resolve().parents[2];NAME='3_LDC2a_GB_Reconstruction.ipynb'
SRC=ROOT/'external/triangle-gb';OUT=ROOT/'results/triangle-gb/example-3';sim=ROOT/'external/triangle-simulator'
p=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
a=nbformat.read(SRC/'Examples'/NAME,as_version=4);b=nbformat.read(p,as_version=4)
e=json.loads((OUT/'execution.json').read_text());d=json.loads((OUT/'diagnostics.json').read_text())
checks={'same_filename':p.name==NAME,'same_cell_count':len(a.cells)==len(b.cells),'same_code_and_markdown':len(a.cells)==len(b.cells) and all(x.cell_type==y.cell_type and x.source==y.source for x,y in zip(a.cells,b.cells)),'same_attachments':all(x.get('attachments',{})==y.get('attachments',{}) for x,y in zip(a.cells,b.cells)),'upstream_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),'execution_success':e['execution_passed'],'all_nonempty_cells_executed':all(c.execution_count is not None for c in b.cells if c.cell_type=='code' and c.source.strip()),'no_errors':not e['error_outputs'],'notebook_hash_matches':hashlib.sha256(p.read_bytes()).hexdigest()==e['executed_notebook_sha256'],'four_local_figures':len(e['generated_figures'])==4,'original_full_data':d['GB_TYPE']=='dgb' and d['catalog_shape']==[26000000,1] and d['cache_shape']==[26000000,8] and d['td']['shape']==[3,6307200] and d['dt_seconds']==5,'original_response_settings':d['Nsparse']==512 and d['orbit_pn_order']==0,'reference_band_and_count':d['source_count']==39 and np.isclose(d['center_hz'],0.0040001634350846995,rtol=0,atol=1e-18) and d['band_frequency']['shape']==[315] and d['template']['shape']==[2,315],'finite_data_and_response':all(d[k]['finite'] for k in ['time_axis','td','fd','band_frequency','band_data','template','residual']),'finite_selected_parameters':d['selected_parameters_finite'],'finite_mismatch':bool(np.isfinite(d['mismatch_unweighted']))}
inputs=[]
for relative,size,md5,sha in [('data/raw/triangle-gb/LDC2_sangria_training_v2.h5',3082321484,'b8369cb5c06bcf984ef8057198683250','f54ca61355d0c6208fbea5fc1b2dcce7332025de264fef33ebe87dea657c7ee6'),('runs/triangle-gb/workspace/Triangle-GB/Test/dgb_parameters.txt',5218391053,None,'38177fda2a108b1076055237e737a4d2a3ef03ce5aeba7994e87014f138aa3c3')]:
 raw=ROOT/relative;h=hashlib.sha256();m=hashlib.md5()
 with raw.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk);m.update(chunk)
 checks['identity_'+raw.name]=raw.stat().st_size==size and h.hexdigest()==sha and (md5 is None or m.hexdigest()==md5)
 inputs.append({'path':relative,'bytes':raw.stat().st_size,'md5':m.hexdigest(),'sha256':h.hexdigest()})
 checks['ignored_'+raw.name]=subprocess.run(['git','check-ignore','-q',relative]).returncode==0
with np.load(OUT/'reconstruction-band.npz') as z:
 checks['saved_arrays_finite']=all(np.isfinite(z[k]).all() for k in z.files)
 checks['residual_identity']=bool(np.array_equal(z['residual'],z['data']-z['template']))
 checks['band_limits']=bool(np.all((z['frequency_hz']>d['FMIN'])&(z['frequency_hz']<d['FMAX'])))
 mismatch=1-np.real(np.sum(np.conj(z['data'])*z['template']))/np.sqrt(np.sum(abs(z['data'])**2)*np.sum(abs(z['template'])**2))
 checks['independent_mismatch']=bool(np.isclose(mismatch,d['mismatch_unweighted'],atol=1e-14,rtol=0))
 with h5py.File(ROOT/'data/raw/triangle-gb/LDC2_sangria_training_v2.h5','r') as f:
  catalog=f['sky/dgb/cat'][z['source_indices']][:,0]
  fields={'A':'Amplitude','f0':'Frequency','fdot0':'FrequencyDerivative','phase0':'InitialPhase','inclination':'Inclination','longitude':'EclipticLongitude','latitude':'EclipticLatitude','psi':'Polarization'}
  for k,field in fields.items():
   values=catalog[field].copy()
   if k=='psi':values+=np.pi/2
   if k=='phase0':values*=-1
   checks['selected_catalog_and_conversion_'+k]=bool(np.array_equal(z['parameters_'+k],values))
checks['simulator_pin_and_clean']=subprocess.check_output(['git','-C',str(sim),'rev-parse','HEAD'],text=True).strip()=='ab796358e9a36c8987f6bb53a97230d603bfdfd5' and not subprocess.check_output(['git','-C',str(sim),'status','--porcelain'],text=True)
checks['actual_module_origins']=all(Path(d['module_files'][name]).resolve()==(ROOT/relative).resolve() for name,relative in {'Triangle.Orbit':'external/triangle-simulator/Triangle/Orbit.py','Triangle_GB.TDIFly':'external/triangle-gb/Triangle_GB/TDIFly.py'}.items())
for i in [7,10,19,25]:
 raw=next(base64.b64decode(o.data['image/png']) for o in b.cells[i].outputs if 'image/png' in o.get('data',{}))
 checks[f'figure_{i}_matches_local_notebook']=next(OUT.glob(f'cell-{i:02d}-*.png')).read_bytes()==raw
report={'passed':all(checks.values()),'checks':checks,'inputs':inputs,'source_commit':e['source_commit'],'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in b.cells),'limitations':'Original band reconstruction uses catalog truth for 39 sources; no search or posterior inference, no reconstruction of all 26 million sources. Nonzero residual also includes sources outside the selected catalog band and response/window approximations. Orbit negative-start extrapolation remains original; no posterior calibration claim.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
files=[p,SRC/'Examples'/NAME,ROOT/'scripts/reproduction/run-triangle-gb-example-3.py',ROOT/'scripts/reproduction/audit-triangle-gb-example-3.py',ROOT/'docs/reproduction/triangle-gb/example-3.md',ROOT/'scripts/reproduction/triangle_gb_path_adapter.py',ROOT/'results/triangle-gb/sangria/validation.json',ROOT/'results/triangle-gb/sangria/download-provenance.json']
files+=list((SRC/'Triangle_GB').glob('*.py'))+list((SRC/'Examples/LDCEqualArmOrbit').glob('*.dat'))+list((sim/'Triangle').glob('*.py'))+list((ROOT/'environments/triangle-gb').glob('requirements*'))
files+=[x for x in OUT.iterdir() if x.is_file() and x.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps([{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(files)],indent=2)+'\n')
assert report['passed']
