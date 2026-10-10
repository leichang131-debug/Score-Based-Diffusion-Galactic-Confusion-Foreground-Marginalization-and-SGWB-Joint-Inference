"""Execute unchanged Tutorial 3, recording separate diagnostics and provenance."""
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
NAME = '3_Demo_GW_Injection.ipynb'
OUT = ROOT / 'results/tdc/tutorial-3'
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
shutil.copy2(SRC/'Figures/GWInjection.png', figdir/'GWInjection.png')
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
          'scope':'Unchanged original default Tutorial 3; no seed imposed',
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
            if i in [17,29,37]:
                stage={17:'gb',29:'mbhb',37:'emri'}[i]
                probe("import json, hashlib, platform\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\nstage={stage!r}\n"+r"""
def array_info(v):
    a=np.asarray(v)
    return {'shape':list(a.shape),'finite':bool(np.isfinite(a).all()),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
summary={'python':platform.python_version(),'size':size,'sample_rate_hz':float(fsample),'interpolation_order':interp_order,'workers':ncpu,'duration_seconds':float(data_time),
 'channels':{key:array_info(tdi.measurements[key]) for key in ['A2','E2','T2']},'raw_links':{k:array_info(v) for k,v in m1['sci_c'].items()}}
if stage=='gb':
    peaks={}
    for key in ['A2','E2','T2']:
        freqs,values=FFT_window(tdi.measurements[key][100:-100]/F_LASER,fsample=fsample,window_type='tukey',window_args_dict=dict(alpha=0.1))
        mask=(freqs>0.00984299-1e-5)&(freqs<0.00984299+1e-5)
        peaks[key]=float(freqs[mask][np.argmax(np.abs(values[mask]))])
    summary['peaks_hz']=peaks
    summary['source_f0_hz']=0.00984299
elif stage=='mbhb':
    summary['approximant']=approx
    summary['coalescence_time_seconds']=float(tc)
    summary['largest_A2_excursion_time_seconds']=float(tdi.measurements['time']['1'][1000:-1000][np.argmax(np.abs(tdi.measurements['A2'][1000:-1000]))])
else:
    summary['extrinsic_parameters']={'longitude':float(lam),'latitude':float(beta),'psi':float(psi)}
    summary['waveform_input']=array_info(waveform_data['h1'])
(output_dir/(stage+'-diagnostics.json')).write_text(json.dumps(summary,indent=2))
""")
        probe("import json, hashlib, platform\nfrom pathlib import Path\n"+f"output_dir=Path({str(OUT)!r})\n"+r"""
summary={'python':platform.python_version(),'size':size,'sample_rate_hz':float(fsample),'interpolation_order':interp_order,'workers':ncpu,'duration_seconds':float(data_time),'NSIDE':NSIDE,'NPIX':NPIX,'number_waveforms':len(gw),'drop_points':drop_points,'response_mc_samples':len(Response_arr),
 'channels':{key:array_info(tdi.measurements[key]) for key in ['X2','Y2','Z2']},'A2':array_info(A2_sgwb),'measured_psd':array_info(xf),'precise_response':array_info(Response_precise),'approximate_response':array_info(Response_approx)}
precise_theory=Response_precise*S_SGWB(plot_freqs)*2
approx_theory=Response_approx*S_SGWB(plot_freqs)*2
summary['bands']={}
for lo,hi in [(0.0003,0.001),(0.001,0.003),(0.003,0.01),(0.01,0.03)]:
    mask=(ff>=lo)&(ff<=hi)
    theory=np.interp(ff[mask],plot_freqs,precise_theory)
    summary['bands'][str((lo,hi))]={'bins':int(mask.sum()),'median_measured_over_precise_psd':float(np.median(xf[mask]/theory))}
selection=np.unique(np.geomspace(1,len(ff)-1,2000).astype(int))
np.savez_compressed(output_dir/'sgwb-spectra-selected.npz',frequency_hz=ff[selection],measured_A2_psd=xf[selection],precise_theory_at_selected=np.interp(ff[selection],plot_freqs,precise_theory),approx_theory_at_selected=np.interp(ff[selection],plot_freqs,approx_theory),theory_frequency_hz=plot_freqs,precise_response=Response_precise,approx_response=Response_approx)
(output_dir/'sgwb-diagnostics.json').write_text(json.dumps(summary,indent=2))
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
