"""Independent fresh-kernel checks of original preparation cells; no sampler rerun."""
import copy,json,os,time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/network'
for k,v in {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','MPLCONFIGDIR':str(ROOT/'runs/triangle-gb/matplotlib'),'IPYTHONDIR':str(ROOT/'runs/triangle-gb/ipython'),'JUPYTER_DATA_DIR':str(ROOT/'environments/triangle-gb/.venv/share/jupyter'),'JUPYTER_RUNTIME_DIR':str(ROOT/'runs/triangle-gb/jupyter-runtime')}.items():os.environ[k]=v
nb=copy.deepcopy(nbformat.read(ROOT/'external/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb',4));nb.cells=nb.cells[:18]
for c in nb.cells:
 if c.cell_type=='code':c.outputs=[];c.execution_count=None
probe=nbformat.v4.new_code_cell('import json\nfrom pathlib import Path\nout=Path('+repr(str(OUT))+')\n'+'''
def zeros(v):
 return all(zeros(x) for x in v.values()) if isinstance(v,dict) else bool(np.all(np.asarray(v)==0))
fisher=np.asarray(mcf.Fisher)
scale=np.sqrt(np.diag(fisher));rescaled=fisher/scale[:,None]/scale[None,:]
scans={};peaks={}
for key in ['f0','A','longitude','latitude','inclination','psi']:
 grid=np.linspace(priors[key].minimum,priors[key].maximum,501)
 vals=[]
 for v in grid:
  like.parameters=true_gb_parameters.copy();like.parameters[key]=v;vals.append(like.log_likelihood())
 vals=np.asarray(vals);vals-=vals.max();scans[key+'_grid']=grid;scans[key+'_relative_logl']=vals
 peaks[key]={'truth':float(true_gb_parameters[key]),'grid_peak':float(grid[np.argmax(vals)]),'finite':bool(np.isfinite(vals).all())}
np.savez_compressed(out/'likelihood-scans.npz',**scans)
np.savez_compressed(out/'fisher.npz',matrix=fisher,scaled_matrix=rescaled,parameter_names=np.array(mcf.analyze_param_names))
s={'confusion_psd_zero':zeros(conf_psd_band),'confusion_csd_zero':zeros(conf_csd_band),'fisher_finite':bool(np.isfinite(fisher).all()),'fisher_raw_condition_number':float(np.linalg.cond(fisher)),'fisher_scaled_condition_number':float(np.linalg.cond(rescaled)),'fisher_scaled_eigenvalues':np.linalg.eigvalsh(rescaled).tolist(),'scan_peaks':peaks,'scope':'Independent original preparation cells and six 501-point scans; no sampling rerun; raw Fisher condition number depends on parameter units.'}
(out/'physical-validation.json').write_text(json.dumps(s,indent=2)+'\\n')
''');nb.cells.append(probe)
start=time.perf_counter();client=NotebookClient(nb,timeout=3600,kernel_name='triangle-gb',resources={'metadata':{'path':str(ROOT/'runs/triangle-gb/network/Examples')}})
client.execute();print('Independent validation seconds',time.perf_counter()-start)
if (OUT/'diagnostics.json').exists():
 d=json.loads((OUT/'diagnostics.json').read_text());p=json.loads((OUT/'physical-validation.json').read_text())
 for k in ['confusion_psd_zero','confusion_csd_zero']:d[k]=p[k]
 d['confusion_zero_check_provenance']='validate-triangle-gb-network-physics.py: recursively check the nested CSD dictionaries in a fresh kernel.'
 (OUT/'diagnostics.json').write_text(json.dumps(d,indent=2)+'\n')
