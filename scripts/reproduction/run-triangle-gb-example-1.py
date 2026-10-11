"""Execute the unchanged default Example 1 in a fresh local kernel."""
import base64, copy, csv, datetime, hashlib, json, os, platform, subprocess, threading, time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[2]
NAME='1_TDIFlyGB_Rapid_Search(CPU).ipynb'
SRC=ROOT/'external/triangle-gb'
OUT=ROOT/'results/triangle-gb/example-1'
NBOUT=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
WORK=ROOT/'runs/triangle-gb/workspace/Triangle-GB/Examples'
for k,v in {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','MPLCONFIGDIR':str(ROOT/'runs/triangle-gb/matplotlib'),'IPYTHONDIR':str(ROOT/'runs/triangle-gb/ipython'),'JUPYTER_DATA_DIR':str(ROOT/'environments/triangle-gb/.venv/share/jupyter'),'JUPYTER_RUNTIME_DIR':str(ROOT/'runs/triangle-gb/jupyter-runtime')}.items():os.environ[k]=v
OUT.mkdir(parents=True,exist_ok=True);NBOUT.parent.mkdir(parents=True,exist_ok=True)
original=nbformat.read(SRC/'Examples'/NAME,as_version=4);nb=copy.deepcopy(original)
nb.metadata.kernelspec={'display_name':'Triangle-GB — Python 3.11.14 (CPU)','language':'python','name':'triangle-gb'}
for c in nb.cells:
 if c.cell_type=='code':c.outputs=[];c.execution_count=None
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.node(),'machine':platform.machine(),'source_commit':subprocess.check_output(['git','-C',str(SRC),'rev-parse','HEAD'],text=True).strip(),'source_sha256':hashlib.sha256((SRC/'Examples'/NAME).read_bytes()).hexdigest(),'cell_timings':[],'scope':'Original full VGB rapid-search defaults; fresh outputs; no source edits or imposed seed','resource_note':'Runner and descendant RSS sum sampled every 2 seconds; shared pages may be counted repeatedly.'}
assert report['source_commit']=='cbc0a1b0cbf4ec05ec969fa39405394168c3e06c'
stop=threading.Event();samples=[];start=time.perf_counter()
def monitor():
 while not stop.is_set():
  try:
   rows=[list(map(int,x.split())) for x in subprocess.check_output(['ps','-axo','pid,ppid,rss'],text=True).splitlines()[1:]]
   ids={os.getpid()}
   for _ in range(8):ids.update(pid for pid,ppid,rss in rows if ppid in ids)
   samples.append([round(time.perf_counter()-start,3),sum(rss for pid,ppid,rss in rows if pid in ids),len(ids)])
  except Exception:pass
  stop.wait(2)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
client=NotebookClient(nb,timeout=7200,kernel_name='triangle-gb',resources={'metadata':{'path':str(WORK)}},record_timing=True)
try:
 with client.setup_kernel():
  for i,c in enumerate(list(nb.cells)):
   if c.cell_type!='code' or not c.source.strip():continue
   print('START cell',i,flush=True);t=time.perf_counter();client.execute_cell(c,i)
   report['cell_timings'].append({'cell_index':i,'seconds':time.perf_counter()-t,'execution_count':c.execution_count})
   nbformat.write(nb,NBOUT);print('DONE cell',i,report['cell_timings'][-1]['seconds'],flush=True)
  probe=nbformat.v4.new_code_cell("import json, hashlib, platform\nfrom pathlib import Path\n"+f"out=Path({str(OUT)!r})\n"+'''
def info(v):
 a=np.asarray(v)
 return {'shape':list(a.shape),'dtype':str(a.dtype),'finite':bool(np.isfinite(a).all()),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
def plain(v):
 a=np.asarray(v)
 return float(a) if a.ndim==0 else a.tolist()
true_int={k:true_gb_parameters[k] for k in ['f0','fdot0','longitude','latitude']}
args=dict(data=data_channels_fd,StartBound=band_idx[0]+1,EndBound=band_idx[-1]+1,Tobs=Tobs,S=PSDlevel)
true_F=gb_tdifly_generator.Fstatistics(intrinsic_parameters=true_int,**args)
best_F=gb_tdifly_generator.Fstatistics(intrinsic_parameters=searched_int_params,**args)
residual=data_channels_fd-searched_wf
summary={'python':platform.python_version(),'numpy':np.__version__,'scipy':__import__('scipy').__version__,'cpu_count':multiprocessing.cpu_count(),'start_method':multiprocessing.get_start_method(),'dt_seconds':plain(dt),'Tobs_seconds':plain(Tobs),'Nsparse':gb_tdifly_generator.Nsparse,'source_index':analyze_gb_idx,'time_axis':info(data_time),'td':info(data_channels_td),'band_frequency':info(data_frequency),'band_data':info(data_channels_fd),'recovered_waveform':info(searched_wf),'residual':info(residual),'PSDlevel':plain(PSDlevel),'band_width_hz':band_width,'band_first_index':int(band_idx[0]),'band_last_index':int(band_idx[-1]),'priors':intrinsic_param_priors.tolist(),'true_parameters':{k:plain(v) for k,v in true_gb_parameters.items()},'searched_parameters':{k:plain(v) for k,v in searched_params.items()},'parameter_absolute_differences':{k:plain(abs(v-true_gb_parameters[k])) for k,v in searched_params.items()},'optimizer':{'success':bool(DE_result.success),'message':str(DE_result.message),'fun':float(DE_result.fun),'nit':int(DE_result.nit),'nfev':int(DE_result.nfev),'x':DE_result.x.tolist(),'population_shape':list(DE_result.population.shape),'population_energy_std':float(np.std(DE_result.population_energies))},'true_F':true_F.tolist(),'best_F':best_F.tolist(),'per_channel_residual_over_data_l2':(np.linalg.norm(residual,axis=1)/np.linalg.norm(data_channels_fd,axis=1)).tolist(),'data_weighted_norm':float(4*np.sum(abs(data_channels_fd)**2)/Tobs/PSDlevel),'residual_weighted_norm':float(4*np.sum(abs(residual)**2)/Tobs/PSDlevel),'module_files':{name:__import__(name,fromlist=['x']).__file__ for name in ['Triangle.GW','Triangle.Orbit','Triangle_GB.TDIFly']}}
(out/'diagnostics.json').write_text(json.dumps(summary,indent=2)+'\\n')
np.savez_compressed(out/'search-band.npz',frequency_hz=data_frequency,data=data_channels_fd,recovered_waveform=searched_wf,residual=residual,population=DE_result.population,population_energies=DE_result.population_energies)
''')
  nb.cells.append(probe)
  try:client.execute_cell(probe,len(nb.cells)-1)
  finally:nb.cells.pop()
 report['execution_passed']=True
except Exception as exc:
 report['execution_passed']=False;report['error']=repr(exc);raise
finally:
 stop.set();thread.join(timeout=5);report['wall_seconds']=time.perf_counter()-start
 report['peak_sampled_process_tree_rss_kib']=max((r[1] for r in samples),default=0)
 report['source_cells_unchanged']=len(nb.cells)==len(original.cells) and all(a.cell_type==b.cell_type and a.source==b.source and a.get('attachments',{})==b.get('attachments',{}) for a,b in zip(nb.cells,original.cells))
 images=[]
 for i,c in enumerate(nb.cells):
  for j,o in enumerate(c.get('outputs',[])):
   if 'image/png' in o.get('data',{}):
    name=f'cell-{i:02d}-output-{j}.png';(OUT/name).write_bytes(base64.b64decode(o.data['image/png']));images.append(name)
 report['generated_figures']=images
 report['error_outputs']=[i for i,c in enumerate(nb.cells) for o in c.get('outputs',[]) if o.output_type=='error']
 nbformat.write(nb,NBOUT);nbformat.write(nb,WORK/NAME)
 report['executed_notebook_sha256']=hashlib.sha256(NBOUT.read_bytes()).hexdigest()
 (OUT/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
 with (OUT/'resources.csv').open('w') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['elapsed_seconds','process_tree_rss_kib','process_count']);w.writerows(samples)
 print('RESULT',json.dumps(report),flush=True)
