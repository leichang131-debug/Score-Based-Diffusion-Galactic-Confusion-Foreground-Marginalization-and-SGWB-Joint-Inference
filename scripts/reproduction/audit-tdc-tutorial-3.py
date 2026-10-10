"""Check source correspondence and saved Tutorial 3 evidence without simulation."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import nbformat
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'external/triangle-simulator'
OUT=ROOT/'results/tdc/tutorial-3'
NAME='3_Demo_GW_Injection.ipynb'
path=ROOT/'notebooks/reproduction/triangle-simulator/Tutorials'/NAME
original=nbformat.read(SRC/'Tutorials'/NAME,as_version=4)
executed=nbformat.read(path,as_version=4)
execution=json.loads((OUT/'execution.json').read_text())
stages={s:json.loads((OUT/(s+'-diagnostics.json')).read_text()) for s in ['gb','mbhb','emri','sgwb']}
checks={
 'same_filename':path.name==NAME,
 'same_cell_count':len(original.cells)==len(executed.cells),
 'same_cell_types_and_sources':len(original.cells)==len(executed.cells) and all(a.cell_type==b.cell_type and a.source==b.source for a,b in zip(original.cells,executed.cells)),
 'same_markdown_attachments':all(a.get('attachments',{})==b.get('attachments',{}) for a,b in zip(original.cells,executed.cells)),
 'original_source_clean':not subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True),
 'pinned_commit':execution['source_commit']=='ab796358e9a36c8987f6bb53a97230d603bfdfd5',
 'static_image_identical':(SRC/'Figures/GWInjection.png').read_bytes()==(path.parent.parent/'Figures/GWInjection.png').read_bytes(),
 'all_nonempty_code_cells_executed':all(c.execution_count is not None for c in executed.cells if c.cell_type=='code' and c.source.strip()),
 'no_error_outputs':not any(o.output_type=='error' for c in executed.cells for o in c.get('outputs',[])),
 'seven_generated_figures':len(execution['generated_figures'])==7,
 'execution_passed':execution['execution_passed'],
 'executed_notebook_hash_matches':hashlib.sha256(path.read_bytes()).hexdigest()==execution['executed_notebook_sha256']}
expected={'gb':(3155814,0.1,15,31558149.763545603),'mbhb':(864000,1.0,15,864000),'emri':(86400,0.1,15,864000),'sgwb':(129600,0.1,11,1296000)}
for name,d in stages.items():
 size,rate,order,duration=expected[name]
 checks[name+'_original_scale']=d['size']==size and d['sample_rate_hz']==rate and d['interpolation_order']==order and d['duration_seconds']==duration and d['workers']==6
 checks[name+'_finite_channels']=all(x['finite'] and x['shape']==[size] for x in d['channels'].values())
 if name!='sgwb':checks[name+'_finite_raw_links']=all(x['finite'] and x['shape']==[size] for x in d['raw_links'].values())
checks['mbhb_original_backend']=stages['mbhb']['approximant']=='IMRPhenomT' and stages['mbhb']['coalescence_time_seconds']==432000
checks['sgwb_original_sky_and_mc']=stages['sgwb']['NSIDE']==5 and stages['sgwb']['NPIX']==300 and stages['sgwb']['number_waveforms']==300 and stages['sgwb']['response_mc_samples']==1024 and stages['sgwb']['drop_points']==100
checks['finite_sgwb_psd_and_responses']=all(stages['sgwb'][key]['finite'] for key in ['A2','measured_psd','precise_response','approximate_response'])
with np.load(OUT/'sgwb-spectra-selected.npz') as data:
 checks['finite_saved_spectral_subset']=all(np.isfinite(data[k]).all() for k in data.files)
comparison=[]
checks['saved_images_match_executed_notebook']=True
for i,(a,b) in enumerate(zip(original.cells,executed.cells)):
 ref=[base64.b64decode(o['data']['image/png']) for o in a.get('outputs',[]) if 'image/png' in o.get('data',{})]
 local=[base64.b64decode(o['data']['image/png']) for o in b.get('outputs',[]) if 'image/png' in o.get('data',{})]
 if ref:comparison.append({'cell_index':i,'reference_count':len(ref),'local_count':len(local),'byte_identical':[x==y for x,y in zip(ref,local)]})
 for j,o in enumerate(b.get('outputs',[])):
  if 'image/png' in o.get('data',{}):checks['saved_images_match_executed_notebook'] &= (OUT/f'cell-{i:02d}-output-{j}.png').read_bytes()==base64.b64decode(o['data']['image/png'])
files=[SRC/'Tutorials'/NAME,SRC/'uv.lock',ROOT/'environments/tdc/installed-macos-arm64.json',SRC/'GWData/Demo_EMRI_waveform_data.npz',path,path.parent.parent/'Figures/GWInjection.png',ROOT/'scripts/reproduction/run-tdc-tutorial-3.py',ROOT/'scripts/reproduction/audit-tdc-tutorial-3.py',ROOT/'docs/reproduction/tdc/tutorial-3.md']
files+=list((SRC/'OrbitData/MicroSateOrbitEclipticTCB').glob('*.dat'))+list((SRC/'Triangle').glob('*.py'))
files+=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ('audit.json','manifest.json')]
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report={'passed':all(checks.values()),'checks':checks,'reference_image_comparison':comparison,'cell_count':len(executed.cells),'nonempty_code_cells':sum(c.cell_type=='code' and bool(c.source.strip()) for c in executed.cells),'source_commit':execution['source_commit'],'limitations':'Single original-scale execution; random EMRI orientation/SGWB/response Monte Carlo are not bitwise reference replication or ensemble calibration'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['passed']
