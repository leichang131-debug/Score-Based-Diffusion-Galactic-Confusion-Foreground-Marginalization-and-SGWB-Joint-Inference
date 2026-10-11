"""Execute the unchanged default Example 0 in a fresh local kernel."""
import base64, copy, csv, datetime, hashlib, json, os, platform, subprocess, threading, time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[2]
NAME='0_TDIFlyGB_Compare_TD_FD_Waveforms(CPU).ipynb'
SRC=ROOT/'external/triangle-gb'
OUT=ROOT/'results/triangle-gb/example-0'
NBOUT=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
WORK=ROOT/'runs/triangle-gb/workspace/Triangle-GB/Examples'
for k,v in {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','MPLCONFIGDIR':str(ROOT/'runs/triangle-gb/matplotlib'),'IPYTHONDIR':str(ROOT/'runs/triangle-gb/ipython'),'JUPYTER_DATA_DIR':str(ROOT/'environments/triangle-gb/.venv/share/jupyter'),'JUPYTER_RUNTIME_DIR':str(ROOT/'runs/triangle-gb/jupyter-runtime')}.items():os.environ[k]=v
OUT.mkdir(parents=True,exist_ok=True);NBOUT.parent.mkdir(parents=True,exist_ok=True)
original=nbformat.read(SRC/'Examples'/NAME,as_version=4);nb=copy.deepcopy(original)
nb.metadata.kernelspec={'display_name':'Triangle-GB — Python 3.11.14 (CPU)','language':'python','name':'triangle-gb'}
for c in nb.cells:
 if c.cell_type=='code':c.outputs=[];c.execution_count=None
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.node(),'machine':platform.machine(),'source_commit':subprocess.check_output(['git','-C',str(SRC),'rev-parse','HEAD'],text=True).strip(),'source_sha256':hashlib.sha256((SRC/'Examples'/NAME).read_bytes()).hexdigest(),'cell_timings':[],'scope':'Original full one-year default; fresh outputs; no source edits or imposed seed','resource_note':'Runner and descendant RSS sum sampled every 2 seconds; shared pages may be counted repeatedly.'}
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
h1=gb_response_fd_band;h2=gb_response_fd_band_tdifly
mismatch=gb_response_generator_tdifly.mismatch(h1=h1,h2=h2[:,np.newaxis,:])
rel=np.linalg.norm(h2-h1,axis=1)/np.linalg.norm(h1,axis=1)
summary={'python':platform.python_version(),'numpy':np.__version__,'dt_seconds':dt,'Tobs_seconds':Tobs,'Nsparse':gb_response_generator_tdifly.Nsparse,'parameters':gb_parameters,'time_axis':info(tcb_times),'td':info(gb_response_td),'fd_full':info(gb_response_fd),'band_frequency':info(band_frequency),'td_fft_band':info(h1),'fd_template_band':info(h2),'mismatch':np.asarray(mismatch).tolist(),'per_channel_relative_l2_difference':rel.tolist(),'band_width_hz':band_width,'first_time':float(tcb_times[0]),'last_time':float(tcb_times[-1]),'module_files':{name:__import__(name,fromlist=['x']).__file__ for name in ['Triangle.GW','Triangle.Orbit','Triangle_GB.TDIFly']}}
(out/'diagnostics.json').write_text(json.dumps(summary,indent=2)+'\\n')
np.savez_compressed(out/'waveform-band.npz',frequency_hz=band_frequency,td_fft=h1,fd_template=h2,mismatch=mismatch)
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
