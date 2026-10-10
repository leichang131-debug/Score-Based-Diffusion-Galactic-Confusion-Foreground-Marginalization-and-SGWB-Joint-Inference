"""Execute unchanged Tutorial 2, recording separate diagnostics and provenance."""
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
NAME = '2_Demo_More_Advanced_Noise_and_TDI_Simulation.ipynb'
OUT = ROOT / 'results/tdc/tutorial-2'
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
shutil.copy2(SRC/'Figures/noise_types.png', figdir/'noise_types.png')
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
          'scope':'Unchanged original default Tutorial 2; no seed imposed',
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
            if i==11:
                probe("import json, hashlib\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\n"+r"""
def array_info(v):
    a=np.asarray(v)
    return {'shape':list(a.shape),'finite':bool(np.isfinite(a).all()),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
mask=(f>=0.01)&(f<=0.1)&(PSD_X2>0)
summary={'size':size,'sample_rate_hz':float(fsample),'interpolation_order':interp_order,'workers':ncpu,'nbin':nbin,'drop_points':drop_points,'X2':array_info(tdi.measurements['X2']),
 'modified_readout_arrays':{k:array_info(v) for k,v in ifo.BasicNoise['ro_sci_c_noise'].items()},'spectrum':array_info(xf),'theory':array_info(PSD_X2),
 'median_asd_over_nominal_0p01_0p1_hz':float(np.median(np.sqrt(xf[mask])/(np.sqrt(PSD_X2[mask])*F_LASER)))}
(output_dir/'noise-diagnostics.json').write_text(json.dumps(summary,indent=2))
selection=np.unique(np.geomspace(1,len(f)-1,2000).astype(int))
np.savez_compressed(output_dir/'noise-spectra-selected.npz',frequency_hz=f[selection],modified_asd=np.sqrt(xf[selection]),nominal_asd=np.sqrt(PSD_X2[selection])*F_LASER)
""")
            if i==15:
                probe("import json\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\n"+r"""
glitch_time=tdi.measurements['time']['1'][drop_points:-drop_points]
glitch_values=tdi.measurements['X2'][drop_points:-drop_points]/F_LASER
window=(glitch_time>=glitch_injection_time-1000)&(glitch_time<=glitch_injection_time+1000)
peak=int(np.argmax(np.abs(glitch_values)))
summary={'size':size,'sample_rate_hz':float(fsample),'workers':ncpu,'interpolation_order':interp_order,'drop_points':drop_points,'injection_time_seconds':glitch_injection_time,
 'X2':array_info(tdi.measurements['X2']),'injected_acceleration':array_info(short_glitch_acc),'injected_ffd':array_info(short_glitch_ffd),
 'peak_time_seconds':float(glitch_time[peak]),'peak_ffd':float(glitch_values[peak]),'window_samples':int(window.sum())}
(output_dir/'glitch-diagnostics.json').write_text(json.dumps(summary,indent=2))
np.savez_compressed(output_dir/'glitch-window.npz',time_seconds=glitch_time[window],X2_ffd=glitch_values[window])
""")
        probe("import json, platform\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\n"+r"""
arrays={'method1':X2_method1,'method2':X2_method2,'method3':X2_method3,'method4':X2_method4}
ref=X2_method1[drop_points:-drop_points]
ref_rms=float(np.sqrt(np.mean(ref**2)))
summary={'python':platform.python_version(),'size':size,'sample_rate_hz':float(fsample),'interpolation_order':interp_order,'workers':ncpu,'drop_points':drop_points,
 'methods':{k:array_info(v) for k,v in arrays.items()},'differences':{},'spectra':{},'bands':{}}
curves={}
for key,value in arrays.items():
    diff=value[drop_points:-drop_points]-ref
    summary['differences'][key]={'identical_to_method1':bool(np.array_equal(value,X2_method1)),'max_abs_after_crop':float(np.max(np.abs(diff))), 'rms_after_crop':float(np.sqrt(np.mean(diff**2))), 'relative_rms':float(np.sqrt(np.mean(diff**2))/ref_rms)}
    freqs,power=PSD_window(ref if key=='method1' else diff,fsample,nbin=1,window_type='kaiser',window_args_dict=dict(beta=28))
    curves[key]=np.sqrt(power)
    summary['spectra'][key]=array_info(curves[key])
for low,high in [(0.001,0.01),(0.01,0.1),(0.1,0.3)]:
    mask=(freqs>=low)&(freqs<=high)&(curves['method1']>0)
    summary['bands'][str((low,high))]={k:float(np.median(v[mask]/curves['method1'][mask])) for k,v in curves.items() if k!='method1'}
selection=np.unique(np.geomspace(1,len(freqs)-1,2000).astype(int))
np.savez_compressed(output_dir/'method-spectra-selected.npz',frequency_hz=freqs[selection],**{k:v[selection] for k,v in curves.items()})
(output_dir/'diagnostics.json').write_text(json.dumps(summary,indent=2))
pool.close()
pool.join()
""")
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
