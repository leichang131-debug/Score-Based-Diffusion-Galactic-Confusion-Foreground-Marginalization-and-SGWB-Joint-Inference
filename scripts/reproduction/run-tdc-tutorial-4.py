"""Execute unchanged Tutorial 4, recording separate diagnostics and provenance."""
import base64
import copy
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'external/triangle-simulator'
NAME = '4_Demo_Simulation_for_Scientific_Data_Analysis.ipynb'
OUT = ROOT / 'results/tdc/tutorial-4'
NBOUT = ROOT / 'notebooks/reproduction/triangle-simulator/Tutorials'
for key, value in {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1',
                   'MPLCONFIGDIR':str(ROOT/'runs/tdc-setup/matplotlib'),
                   'JUPYTER_DATA_DIR':str(ROOT/'environments/tdc/.venv/share/jupyter'),
                   'JUPYTER_RUNTIME_DIR':str(ROOT/'runs/tdc-jupyter/runtime'),
                   'IPYTHONDIR':str(ROOT/'runs/tdc-jupyter/ipython')}.items():
    os.environ[key] = value
OUT.mkdir(parents=True, exist_ok=True)
NBOUT.mkdir(parents=True, exist_ok=True)
original = nbformat.read(SRC/'Tutorials'/NAME, as_version=4)
nb = copy.deepcopy(original)
nb.metadata.kernelspec={'display_name':'Triangle TDC — Python 3.9.19','language':'python','name':'triangle-tdc'}
for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.outputs=[]
        cell.execution_count=None
client = NotebookClient(nb, timeout=3600, kernel_name='triangle-tdc',
                        resources={'metadata':{'path':str(SRC/'Tutorials')}}, record_timing=True)
report = {'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'source_commit':subprocess.check_output(['git','-C',str(SRC),'rev-parse','HEAD'],text=True).strip(),
          'source_sha256':hashlib.sha256((SRC/'Tutorials'/NAME).read_bytes()).hexdigest(),
          'scope':'Unchanged original default Tutorial 4; no seed imposed',
          'cell_timings':[], 'resource_note':'Sum of RSS of runner and descendants; shared pages may be counted repeatedly; sampled every 2 seconds'}
stop=threading.Event()
samples=[]
start=time.perf_counter()
def monitor():
    while not stop.is_set():
        try:
            rows=[list(map(int,line.split())) for line in subprocess.check_output(['ps','-axo','pid,ppid,rss'],text=True).splitlines()[1:]]
            ids={os.getpid()}
            for _ in range(8): ids.update(pid for pid,ppid,rss in rows if ppid in ids)
            samples.append([round(time.perf_counter()-start,3),sum(rss for pid,ppid,rss in rows if pid in ids),len(ids)])
        except Exception: pass
        stop.wait(2)
thread=threading.Thread(target=monitor,daemon=True);thread.start()

def probe(code):
    cell=nbformat.v4.new_code_cell(code)
    index=len(nb.cells);nb.cells.append(cell)
    try: client.execute_cell(cell,index)
    finally: nb.cells.pop()

try:
    assert report['source_commit']=='ab796358e9a36c8987f6bb53a97230d603bfdfd5'
    with client.setup_kernel():
        for i,cell in enumerate(list(nb.cells)):
            if cell.cell_type!='code' or not cell.source.strip():continue
            print('START cell',i,flush=True);t=time.perf_counter()
            client.execute_cell(cell,i)
            report['cell_timings'].append({'cell_index':i,'seconds':time.perf_counter()-t,'execution_count':cell.execution_count})
            nbformat.write(nb,NBOUT/NAME)
            print('DONE cell',i,'seconds',report['cell_timings'][-1]['seconds'],flush=True)
            if i == 3:
                probe("_tutorial4_initial_pool = pool")
            if i in [27,36,42,48,56]:
                probe("import json, hashlib, platform\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\nstage_cell={i}\n"+r"""
def array_info(v):
    a=np.asarray(v)
    return {'shape':list(a.shape),'finite':bool(np.isfinite(a).all()),'sha256':hashlib.sha256(a.tobytes()).hexdigest(),'rms':float(np.sqrt(np.mean(np.abs(a)**2)))}
summary={'python':platform.python_version(),'start_method':multiprocessing.get_start_method(),'cpu_count':multiprocessing.cpu_count()}
if stage_cell==27:
    summary.update(size=size,sample_rate_hz=float(fsample),duration_seconds=float(data_time),interpolation_order=interp_order,default_noise=default_noise,TDI_method=TDI_method,source_count=len(gw),sky_count=NPIX,workers=ncpu,channels={k:array_info(tdi.measurements[k]) for k in ['A2','E2','T2']},raw_links={k:array_info(v) for k,v in m1['sci_c'].items()})
    stage='combined'
elif stage_cell==36:
    summary.update(response_samples=len(tcb_times),duration_seconds=float(Tobs),dt_seconds=float(dt),source_count=N_GB,parameters=GB_params_list,responses=[array_info(v) for v in results])
    stage='fast-gb'
elif stage_cell==42:
    summary.update(response_samples=len(tcb_times),approximant=approximant if 'approximant' in globals() else approx,parameters=MBHB_params,response=array_info(results))
    stage='fast-mbhb'
elif stage_cell==48:
    summary.update(response_samples=len(tcb_times),response=array_info(results))
    stage='fast-emri'
else:
    summary.update(orbit_time_seconds=float(orbit_time),frequency=array_info(plot_freqs),X2=array_info(plot_sens_X),A2=array_info(plot_sens_A),positive=bool((plot_sens_X>0).all() and (plot_sens_A>0).all()))
    np.savez_compressed(output_dir/'sensitivity.npz',frequency_hz=plot_freqs,X2=plot_sens_X,A2=plot_sens_A)
    stage='sensitivity'
(output_dir/(stage+'-diagnostics.json')).write_text(json.dumps(summary,indent=2)+'\n')
""")
        probe("_tutorial4_initial_pool.close(); _tutorial4_initial_pool.join()")
    report['execution_passed']=True
except Exception as exc:
    report['execution_passed']=False;report['error']=repr(exc)
    raise
finally:
    stop.set();thread.join(timeout=5)
    report['wall_seconds']=time.perf_counter()-start
    report['peak_sampled_process_tree_rss_kib']=max((row[1] for row in samples),default=0)
    report['source_cells_unchanged']=len(nb.cells)==len(original.cells) and all(a.cell_type==b.cell_type and a.source==b.source and a.get('attachments',{})==b.get('attachments',{}) for a,b in zip(nb.cells,original.cells))
    images=[]
    for i,cell in enumerate(nb.cells):
        for j,out in enumerate(cell.get('outputs',[])):
            if 'image/png' in out.get('data',{}):
                name=f'cell-{i:02d}-output-{j}.png';(OUT/name).write_bytes(base64.b64decode(out.data['image/png']));images.append(name)
    report['generated_figures']=images
    report['error_outputs']=[i for i,c in enumerate(nb.cells) for o in c.get('outputs',[]) if o.output_type=='error']
    nbformat.write(nb,NBOUT/NAME)
    report['executed_notebook_sha256']=hashlib.sha256((NBOUT/NAME).read_bytes()).hexdigest()
    (OUT/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'resources.csv').open('w') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['elapsed_seconds','process_tree_rss_kib','process_count']);writer.writerows(samples)
    print('RESULT',json.dumps(report),flush=True)
