"""Execute unchanged Tutorial 1, recording separate diagnostics and provenance."""
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
NAME = '1_Demo_Laser_Interferometry_and_TDI.ipynb'
OUT = ROOT / 'results/tdc/tutorial-1'
NBOUT = ROOT / 'notebooks/reproduction/triangle-simulator/Tutorials'
for key, value in {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1',
                   'MPLCONFIGDIR':str(ROOT/'runs/tdc-setup/matplotlib'),
                   'JUPYTER_DATA_DIR':str(ROOT/'environments/tdc/.venv/share/jupyter'),
                   'JUPYTER_RUNTIME_DIR':str(ROOT/'runs/tdc-jupyter/runtime'),
                   'IPYTHONDIR':str(ROOT/'runs/tdc-jupyter/ipython')}.items():
    os.environ[key] = value
OUT.mkdir(parents=True, exist_ok=True)
NBOUT.mkdir(parents=True, exist_ok=True)
figdir = NBOUT.parent/'Figures'
figdir.mkdir(exist_ok=True)
shutil.copy2(SRC/'Figures/constellation.png', figdir/'constellation.png')
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
          'scope':'Unchanged original default Tutorial 1; no seed imposed',
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
            if i==16:
                probe("import json\nfrom pathlib import Path\n"+f"Path({str(OUT/'offset-diagnostics.json')!r}).write_text(json.dumps({{'size':size,'fsample':fsample,'ltt':{{k:{{'shape':list(np.asarray(v).shape),'finite':bool(np.isfinite(v).all()),'min':float(np.min(v)),'max':float(np.max(v))}} for k,v in m1['ltt'].items()}}}},indent=2))")
        probe("import json, hashlib, platform\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\n"+'''
def array_info(v):
    a=np.asarray(v)
    return {'shape':list(a.shape),'finite':bool(np.isfinite(a).all()),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
summary={'python':platform.python_version(),'sample_rate_hz':float(fsample),'size':size,'interpolation_order':interp_order,'tdi_order':tdi_interp_order,'workers':ncpu,'drop_points':drop_points,
         'raw':{k:array_info(v) for k,v in m1['sci_c'].items()},
         'X2':array_info(tdi.measurements['X2']), 'X2_q':array_info(tdi.measurements['X2_q']),
         'corrected_X2':array_info(tdi.measurements['X2']-tdi.measurements['X2_q'])}
curves={}
for key,values in {'raw':m1['sci_c']['12'],'before_clock':tdi.measurements['X2'],'after_clock':tdi.measurements['X2']-tdi.measurements['X2_q']}.items():
    freq,power=PSD_window(values[drop_points:-drop_points],fsample,nbin=1,window_type='kaiser',window_args_dict=dict(beta=28))
    curves[key]=np.sqrt(power)
curves['theory_secondary']=np.sqrt(PSD.PSD_X2_unequal(freq,arms))*F_LASER
curves['theory_clock']=np.sqrt(ResidualClockNoise(freqs=freq,a=tdi.measurements['a'],b=tdi.measurements['b'],channel='X2'))
summary['spectra']={k:array_info(v) for k,v in curves.items()}
summary['bands']={}
for low,high in [(1e-3,1e-2),(1e-2,1e-1),(1e-1,0.3)]:
    mask=(freq>=low)&(freq<=high)&(curves['theory_secondary']>0)&(curves['raw']>0)
    summary['bands'][str((low,high))]={'points':int(mask.sum()),
      'median_raw_over_corrected_asd':float(np.median(curves['raw'][mask]/curves['after_clock'][mask])),
      'median_corrected_over_theory_asd':float(np.median(curves['after_clock'][mask]/curves['theory_secondary'][mask]))}
selection=np.unique(np.geomspace(1,len(freq)-1,2000).astype(int))
np.savez_compressed(output_dir/'spectra-selected.npz',frequency_hz=freq[selection],**{k:v[selection] for k,v in curves.items()})
(output_dir/'diagnostics.json').write_text(json.dumps(summary,indent=2))
pool.close()
pool.join()
''')
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
