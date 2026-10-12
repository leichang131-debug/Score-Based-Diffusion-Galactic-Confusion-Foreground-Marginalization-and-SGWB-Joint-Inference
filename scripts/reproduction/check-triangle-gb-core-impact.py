"""Measure original band-fill boundary effects without altering tutorial outputs."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ['MPLCONFIGDIR']=str(ROOT/'runs/triangle-gb/matplotlib')
import json,time,hashlib,nbformat,numpy as np
from Triangle_GB import TDIFly,TDIFlyGB,TDIFlyGBNetwork
from Triangle.Constants import *
from Triangle.Orbit import *
from Triangle.TDI import *
OUT=ROOT/'results/triangle-gb/core-validation';start=time.perf_counter()
X2_strings=TDIFly.X2_strings;Y2_strings=TDIStringManipulation.TDIStringCyc(X2_strings);Z2_strings=TDIStringManipulation.TDIStringCyc(Y2_strings)
def cropped(data,idx,lo,hi):
 out=np.zeros((data.shape[0],data.shape[1],hi-lo+1),complex)
 for j,s in enumerate(idx):
  k=np.arange(data.shape[2])+s;valid=(k>=lo)&(k<=hi);out[:,j,k[valid]-lo]=data[:,j,valid]
 return out
v=json.loads((ROOT/'results/triangle-gb/example-2/diagnostics.json').read_text());t=np.arange(v['time_axis']['shape'][0])*v['dt_seconds']
assert hashlib.sha256(t.tobytes()).hexdigest()==v['time_axis']['sha256']
orbit=Orbit(OrbitDir=str(ROOT/'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB'))
g=TDIFlyGB(orbit,[X2_strings,Y2_strings,Z2_strings],t,Nsparse=v['Nsparse'],use_gpu=False)
with np.load(ROOT/'results/triangle-gb/example-2/parameter-estimation-band.npz') as z:freq=z['frequency_hz'];obs=z['data']
lo=int(round(freq[0]*v['Tobs_seconds']));hi=lo+len(freq)-1
p=v['true_parameters'];response=g(p,domain='frequency');ae=g.XYZtoAE(response);indices=g.start_idx.copy()
actual=g.fill_fftseries(ae,indices,lo,hi);reference=cropped(ae,indices,lo,hi)
ll_actual=float(-2/(v['Tobs_seconds']*v['PSDlevel'])*np.sum(abs(obs-actual[:,0])**2));ll_reference=float(-2/(v['Tobs_seconds']*v['PSDlevel'])*np.sum(abs(obs-reference[:,0])**2))
record={'example_2':{'time_axis_hash_matches':True,'source_parameters':'Original recorded injection','band_indices':[lo,hi],'sparse_start_indices':indices.tolist(),'Nsparse':v['Nsparse'],'relative_template_error':float(np.linalg.norm(actual-reference)/np.linalg.norm(reference)),'interior_bins_exactly_equal':bool(np.array_equal(actual[:,:,1:-1],reference[:,:,1:-1])),'original_truth_log_likelihood':ll_actual,'proper_crop_truth_log_likelihood':ll_reference,'log_likelihood_change':ll_reference-ll_actual,'stored_original_truth_likelihood_matches':bool(np.isclose(ll_actual,v['truth_log_likelihood'],rtol=0,atol=1e-8))}}
np.savez_compressed(OUT/'example-2-fill-impact.npz',original_template=actual,proper_crop_reference=reference,frequency_hz=freq)
del g,t,response,ae,actual,reference,orbit
# Original network settings and original saved injection.
nb=nbformat.read(ROOT/'external/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb',4);exec(nb.cells[2].source,globals())
v=json.loads((ROOT/'results/triangle-gb/network/diagnostics.json').read_text());t=np.arange(v['time_axis']['shape'][0])*v['dt_seconds'];assert hashlib.sha256(t.tobytes()).hexdigest()==v['time_axis']['sha256']
net=TDIFlyGBNetwork(orbits,[X2_strings,Y2_strings,Z2_strings],t,Nsparse=1024,use_gpu=False)
with np.load(ROOT/'results/triangle-gb/network/network-band.npz') as z:freq=z['frequency_hz'];signal=z['signal']
lo=int(round(freq[0]*v['Tobs_seconds']));hi=lo+len(freq)-1
actual=net.response_on_band(v['true_parameters'],lo,hi);indices=net.start_idx.copy()
record['network']={'band_indices':[lo,hi],'sparse_start_indices':indices.tolist(),'Nsparse':1024,'truth_support_fully_inside_band':bool(np.all(indices>=lo)&np.all(indices+1023<=hi)),'recorded_signal_reproduced':bool(np.allclose(actual[:,0],signal,rtol=1e-10,atol=0)),'scope':'Original injection only; not a re-evaluation of every posterior sample.'}
record['wall_seconds']=time.perf_counter()-start;record['scope']='Explicit original vs mathematical crop comparison; original results unchanged. Correct-crop values are diagnostic references, not replacement posterior samples.'
(OUT/'tutorial-impact.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
