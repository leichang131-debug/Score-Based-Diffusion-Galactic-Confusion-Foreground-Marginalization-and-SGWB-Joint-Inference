"""Audit unchanged Tutorial 4 sources and locally generated numerical evidence."""
import base64, hashlib, json, subprocess
from pathlib import Path
import nbformat
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'external/triangle-simulator'
OUT=ROOT/'results/tdc/tutorial-4'
NAME='4_Demo_Simulation_for_Scientific_Data_Analysis.ipynb'
path=ROOT/'notebooks/reproduction/triangle-simulator/Tutorials'/NAME
original=nbformat.read(SRC/'Tutorials'/NAME,4)
executed=nbformat.read(path,4)
e=json.loads((OUT/'execution.json').read_text())
d={s:json.loads((OUT/(s+'-diagnostics.json')).read_text()) for s in ['combined','fast-gb','fast-mbhb','fast-emri','sensitivity']}
checks={
 'original_filename':path.name==NAME,
 'same_cell_count':len(original.cells)==len(executed.cells),
 'same_sources_and_types':len(original.cells)==len(executed.cells) and all(a.source==b.source and a.cell_type==b.cell_type for a,b in zip(original.cells,executed.cells)),
 'same_attachments':all(a.get('attachments',{})==b.get('attachments',{}) for a,b in zip(original.cells,executed.cells)),
 'source_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),
 'pinned_commit':e['source_commit']=='ab796358e9a36c8987f6bb53a97230d603bfdfd5',
 'source_hash':hashlib.sha256((SRC/'Tutorials'/NAME).read_bytes()).hexdigest()==e['source_sha256'],
 'executed_hash':hashlib.sha256(path.read_bytes()).hexdigest()==e['executed_notebook_sha256'],
 'all_nonempty_code_executed':all(c.execution_count is not None for c in executed.cells if c.cell_type=='code' and c.source.strip()),
 'execution_passed':e['execution_passed'],
 'no_error_outputs':not e['error_outputs'],
 'six_figures':len(e['generated_figures'])==6,
 'fork_used':all(v['start_method']=='fork' for v in d.values())}
c=d['combined'];g=d['fast-gb'];m=d['fast-mbhb'];r=d['fast-emri'];s=d['sensitivity']
checks['original_combined_scale']=c['size']==86400 and c['sample_rate_hz']==0.1 and c['duration_seconds']==864000 and c['interpolation_order']==31 and c['workers']==6
checks['original_combined_sources_and_noise']=c['source_count']==303 and c['sky_count']==300 and c['default_noise'] and c['TDI_method']=='fast_michelson'
checks['combined_finite_channels']=all(v['finite'] and v['shape']==[86400] for v in c['channels'].values())
checks['combined_six_finite_links']=len(c['raw_links'])==6 and all(v['finite'] and v['shape']==[86400] for v in c['raw_links'].values())
checks['original_fast_gb_scale']=g['response_samples']==864000 and g['duration_seconds']==8640000 and g['dt_seconds']==10 and g['source_count']==100 and len(g['parameters'])==100
checks['all_100_gb_responses_finite']=len(g['responses'])==100 and all(v['finite'] and v['shape']==[864000] for v in g['responses'])
checks['fast_mbhb_original_backend_parameters']=m['approximant']=='IMRPhenomT' and m['parameters']['coalescence_time']==50 and m['parameters']['chirp_mass']==400000
for name,stage in [('mbhb',m),('emri',r)]: checks['fast_'+name+'_finite_shape']=stage['response_samples']==864000 and stage['response']['shape']==[864000] and stage['response']['finite']
checks['sensitivity_finite_positive']=s['positive'] and all(s[k]['finite'] and s[k]['shape']==[512] for k in ['frequency','X2','A2'])
with np.load(OUT/'sensitivity.npz') as a:
 checks['saved_sensitivity_finite']=all(np.isfinite(a[k]).all() for k in a.files)
 checks['original_frequency_range']=bool(np.isclose(a['frequency_hz'][0],1e-4) and np.isclose(a['frequency_hz'][-1],1))
comparison=[];checks['image_exports_match']=True
for i,(a,b) in enumerate(zip(original.cells,executed.cells)):
 ref=[base64.b64decode(o['data']['image/png']) for o in a.get('outputs',[]) if 'image/png' in o.get('data',{})]
 local=[base64.b64decode(o['data']['image/png']) for o in b.get('outputs',[]) if 'image/png' in o.get('data',{})]
 if ref:comparison.append({'cell_index':i,'reference_count':len(ref),'local_count':len(local),'byte_identical':[x==y for x,y in zip(ref,local)]})
 for j,o in enumerate(b.get('outputs',[])):
  if 'image/png' in o.get('data',{}):checks['image_exports_match'] &= (OUT/f'cell-{i:02d}-output-{j}.png').read_bytes()==base64.b64decode(o['data']['image/png'])
checks['local_hardware_evidence']=json.loads((OUT/'local-processes.json').read_text())['hardware']==['Apple M5','17179869184']
files=[SRC/'Tutorials'/NAME,SRC/'uv.lock',SRC/'GWData/Demo_EMRI_waveform_data.npz',ROOT/'environments/tdc/installed-macos-arm64.json',path,ROOT/'scripts/reproduction/run-tdc-tutorial-4.py',ROOT/'scripts/reproduction/audit-tdc-tutorial-4.py',ROOT/'docs/reproduction/tdc/tutorial-4.md']
files+=list((SRC/'Triangle').glob('*.py'))+list((SRC/'OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))
files+=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['audit.json','manifest.json']]
(OUT/'manifest.json').write_text(json.dumps([{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)],indent=2)+'\n')
report={'passed':all(checks.values()),'checks':checks,'reference_image_comparison':comparison,'cell_count':len(executed.cells),'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in executed.cells),'limitations':'Original default branches only; one random realization; no inference or statistical calibration.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
