"""Exercise pinned original CPU interfaces; report failures without patching upstream."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[key]='1'
os.environ['MPLCONFIGDIR']=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../runs/triangle-gb/matplotlib'))
import datetime,hashlib,json,platform,subprocess,time,traceback
from pathlib import Path
import numpy as np,nbformat
from Triangle_GB import TDIFly,TDIFlyGB,TDIFlyGBNetwork
from Triangle.Constants import *
from Triangle.Orbit import *
from Triangle.TDI import *
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/core-validation';OUT.mkdir(parents=True,exist_ok=True)
started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.perf_counter();records=[];arrays={}
def check(name,fn,scope):
 t=time.perf_counter()
 try:
  value=fn();passed=bool(value.pop('passed'));record={'name':name,'passed':passed,'scope':scope,'metrics':value}
 except Exception as e:record={'name':name,'passed':False,'scope':scope,'exception':repr(e),'traceback':traceback.format_exc()}
 record['seconds']=time.perf_counter()-t;records.append(record);print(json.dumps(record),flush=True)
def relative(a,b):return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(a),np.finfo(float).tiny))
def compare(a,b,tol=1e-8):
 r=relative(a,b);return {'passed':np.isfinite(r) and r<tol,'relative_error':r,'relative_tolerance':tol,'shape':list(np.shape(a))}
# Exactly the original network tutorial's analytic orbit configuration.
nb=nbformat.read(ROOT/'external/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb',4)
exec(nb.cells[2].source,globals())
X2_strings=TDIFly.X2_strings
Y2_strings=TDIStringManipulation.TDIStringCyc(X2_strings)
Z2_strings=TDIStringManipulation.TDIStringCyc(Y2_strings)
N=65536;dt=10.;times=np.arange(N)*dt;Tobs=N*dt;ns=128
params={'A':np.array([1e-22,1.2e-22,.8e-22]),'f0':np.array([2200,2204,2197])/Tobs,'fdot0':np.array([2e-17,3e-17,1e-17]),'phase0':np.array([.4,2.,5.]),'inclination':np.array([.8,1.2,.4]),'longitude':np.array([1.,2.,4.]),'latitude':np.array([.3,-.4,.6]),'psi':np.array([.2,1.,2.])}
g=TDIFlyGB(orbits[0],[X2_strings,Y2_strings,Z2_strings],times,Nsparse=ns,use_gpu=False)
check('actual_public_imports_and_origins',lambda:{'passed':Path(__import__('Triangle_GB.TDIFly',fromlist=['x']).__file__).resolve()==(ROOT/'external/triangle-gb/Triangle_GB/TDIFly.py').resolve(),'module_file':str(Path(__import__('Triangle_GB.TDIFly',fromlist=['x']).__file__).resolve())},'Package imports and actual pinned implementation')
batch=g(params,domain='frequency');starts=g.start_idx.copy();arrays['batch_frequency_response']=batch;arrays['start_indices']=starts
single=np.concatenate([g({k:v[j] for k,v in params.items()},domain='frequency') for j in range(3)],axis=1)
check('frequency_batch_vs_single',lambda:compare(batch,single),'Three sources, original CPU response')
check('frequency_shape_finite_nonzero',lambda:{'passed':batch.shape==(3,3,ns) and np.isfinite(batch).all() and np.linalg.norm(batch)>0,'shape':list(batch.shape)},'Original XYZ source/channel order')
# Synthetic complex values make boundary loss/overwrites independently observable.
synthetic=(np.arange(3*3*ns).reshape(3,3,ns)+1)*(1+2j)
full=g.fill_full_fftseries(synthetic,starts)
check('full_fft_fill_independent_scatter',lambda:{'passed':all(np.array_equal(full[:,j,starts[j]:starts[j]+ns],synthetic[:,j]) for j in range(3)) and np.count_nonzero(full)==synthetic.size,'filled_nonzero':int(np.count_nonzero(full))},'All sparse supports inside positive rFFT grid')
def band_reference(data,idx,lo,hi):
 out=np.zeros((data.shape[0],data.shape[1],hi-lo+1),complex)
 for j,s in enumerate(idx):
  k=np.arange(data.shape[2])+s;valid=(k>=lo)&(k<=hi);out[:,j,k[valid]-lo]=data[:,j,valid]
 return out
lo=int(min(starts)-5);hi=int(max(starts)+ns+5)
for name,func in [('vectorized',g.fill_fftseries),('loop',g.fill_fftseries_loop)]:
 check('fill_'+name+'_wide_band',lambda func=func:compare(func(synthetic,starts,lo,hi),band_reference(synthetic,starts,lo,hi),1e-14),'Wide band includes all supports; EndBound inclusive')
lo_cut=int(np.median(starts)+10);hi_cut=lo_cut+80
for name,func in [('vectorized',g.fill_fftseries),('loop',g.fill_fftseries_loop)]:
 check('fill_'+name+'_clipped_band',lambda func=func:compare(func(synthetic,starts,lo_cut,hi_cut),band_reference(synthetic,starts,lo_cut,hi_cut),1e-14),'Partial overlap: physical reference discards out-of-band values')
real_clipped=g.fill_fftseries(batch,starts,lo_cut,hi_cut);real_reference=band_reference(batch,starts,lo_cut,hi_cut)
check('fill_vectorized_clipped_physical_signal',lambda:compare(real_clipped,real_reference,1e-14),'Same partial-overlap check using actual original XYZ responses, not only synthetic values')
arrays['physical_clipped_actual']=real_clipped;arrays['physical_clipped_reference']=real_reference
arrays['synthetic_fill_input']=synthetic;arrays['clipped_fill_reference']=band_reference(synthetic,starts,lo_cut,hi_cut);arrays['clipped_fill_actual']=g.fill_fftseries(synthetic,starts,lo_cut,hi_cut)
# Parameter round-trips in the documented physical coordinate ranges.
check('full_parameter_roundtrip',lambda:compare(TDIFlyGB.ParamDict2Arr(TDIFlyGB.ParamArr2Dict(TDIFlyGB.ParamDict2Arr(params))),TDIFlyGB.ParamDict2Arr(params),1e-14),'log10(A), cos(inclination), sin(latitude) coordinates')
intpars={k:params[k] for k in ['f0','fdot0','longitude','latitude']}
check('intrinsic_parameter_roundtrip',lambda:compare(TDIFlyGB.IntParamDict2Arr(TDIFlyGB.IntParamArr2Dict(TDIFlyGB.IntParamDict2Arr(intpars))),TDIFlyGB.IntParamDict2Arr(intpars),1e-14),'Four intrinsic coordinates')
# Independent A/E/T linear transform.
ae=g.XYZtoAE(batch);aet=g.XYZtoAET(batch)
check('XYZ_to_AET_independent',lambda:compare(aet,np.array([(batch[2]-batch[0])/np.sqrt(2),(batch[0]-2*batch[1]+batch[2])/np.sqrt(6),(batch[0]+batch[1]+batch[2])/np.sqrt(3)]),1e-14),'Explicit orthonormal channel transform')
check('XYZ_to_AE_matches_AET',lambda:compare(ae,aet[:2],1e-14),'First two channels')
# Likelihood/SNR/mismatch checked against independently formed arrays.
lo=int(min(starts)-5);hi=int(max(starts)+ns+5)
h=g.fill_fftseries(ae,starts,lo,hi);S=1e-40
rng=np.random.default_rng(20261012);noise=(rng.normal(size=h[:,0].shape)+1j*rng.normal(size=h[:,0].shape))*1e-20
obs=h[:,0]+noise
like=g.Likelihood(obs,params,lo,hi,Tobs,S);expected=-2/(Tobs*S)*np.sum(abs(obs[:,None,:]-h)**2,axis=(0,2))
check('likelihood_explicit_residual',lambda:compare(like,expected,1e-8),'Original scalar fixed PSD and same inclusive frequency band')
check('SNR_explicit_integral',lambda:compare(g.SNR(h,params['f0'],Tobs,PSD=S),np.sqrt(4/(Tobs*S)*np.sum(abs(h)**2,axis=(0,2))),1e-14),'One-sided PSD, df=1/Tobs')
check('mismatch_explicit_overlap',lambda:compare(g.mismatch(h[:,0],h),1-np.real(np.sum(h[:,0,None,:].conj()*h,axis=(0,2)))/np.sqrt(np.sum(abs(h[:,0])**2)*np.sum(abs(h)**2,axis=(0,2))),1e-8),'Unweighted original mismatch normalization')
# F-statistic independently solve the four-real-amplitude least-squares problem.
bases=[]
for psi in [0.,PI/4]:
 q={k:params[k] for k in intpars};q.update(A=np.full(3,2.),phase0=np.zeros(3),psi=np.full(3,psi),inclination=np.full(3,PI/2))
 x=g(q,domain='frequency');x=g.fill_fftseries(g.XYZtoAE(x),g.start_idx.copy(),lo,hi);bases.extend([x,1j*x])
expectedF=[]
for j in range(3):
 b=np.array([x[:,j].ravel() for x in bases]).T;design=np.concatenate([b.real,b.imag],axis=0);d=np.concatenate([obs.real.ravel(),obs.imag.ravel()]);coeff=np.linalg.lstsq(design,d,rcond=None)[0];fit=design@coeff;expectedF.append(2/(Tobs*S)*np.dot(fit,fit))
check('Fstatistics_independent_lstsq',lambda:compare(g.Fstatistics(obs,intpars,lo,hi,Tobs,S),expectedF,1e-7),'Explicit real four-amplitude least squares; comparison to analytic F-statistic')
# Time path: test default independently, then explicit nonzero edge dropping.
time_default=g(params,domain='time')
check('time_default_nonzero',lambda:{'passed':np.isfinite(time_default).all() and np.linalg.norm(time_default)>0,'norm':float(np.linalg.norm(time_default)),'drop_points':g.drop_points},'Default drop_points=0 should retain a nonzero injected signal')
gtime=TDIFlyGB(orbits[0],[X2_strings,Y2_strings,Z2_strings],times,Nsparse=ns,use_gpu=False,drop_points=1)
td=gtime(params,domain='time');tdsingle=np.concatenate([gtime({k:v[j] for k,v in params.items()},domain='time') for j in range(3)],axis=1)
check('time_batch_vs_single_drop_one',lambda:compare(td,tdsingle),'Explicit drop_points=1; does not repair or replace default-zero failure')
check('time_drop_one_finite_nonzero',lambda:{'passed':np.isfinite(td).all() and all(np.linalg.norm(td[:,j])>0 for j in range(3)) and np.all(td[:,:,:1]==0) and np.all(td[:,:,-1:]==0),'shape':list(td.shape)},'Non-default existing time branch and documented dropped endpoints')
fd=gtime(params,domain='frequency');fd=gtime.fill_fftseries(gtime.XYZtoAE(fd),gtime.start_idx.copy(),lo,hi)
tfft=np.fft.rfft(gtime.XYZtoAE(td),axis=-1)*dt;band=tfft[:,:,lo:hi+1]
check('time_FFT_vs_sparse_frequency_drop_one',lambda:compare(band,fd,.01),'Engineering smoke tolerance 1% for finite-grid sparse approximation, drop_points=1; not a production accuracy bound')
arrays.update(likelihood=like,likelihood_reference=expected,time_FFT_band=band,sparse_FD_band=fd)
convergence=[]
for sparse_count in [512,1024,2048,4096]:
 candidate=TDIFlyGB(orbits[0],[X2_strings,Y2_strings,Z2_strings],times,Nsparse=sparse_count,use_gpu=False,drop_points=1)
 ct=candidate(params,domain='time');cf=candidate(params,domain='frequency');ci=candidate.start_idx.copy();clo=int(min(ci)-5);chi=int(max(ci)+sparse_count+5)
 cfd=candidate.fill_fftseries(candidate.XYZtoAE(cf),ci,clo,chi);cfft=np.fft.rfft(candidate.XYZtoAE(ct),axis=-1)*dt
 error=relative(cfft[:,:,clo:chi+1],cfd)
 convergence.append({'Nsparse':sparse_count,'relative_error':error,'band_start':clo,'band_end':chi,'drop_points':1})
check('time_FFT_sparse_convergence_4096',lambda:{'passed':convergence[-1]['relative_error']<.01,'relative_tolerance':.01,'series':convergence},'Original source at increasing sparse counts; retains the failed 128-point check; short rectangular observation with endpoint dropping')

# Full network vs independently instantiated original single-detector generators.
net=TDIFlyGBNetwork(orbits,[X2_strings,Y2_strings,Z2_strings],times,Nsparse=ns,use_gpu=False)
network=net.response_on_band(params,lo,hi);parts=[]
for orbit in orbits:
 one=TDIFlyGB(orbit,[X2_strings,Y2_strings,Z2_strings],times,Nsparse=ns,use_gpu=False);x=one(params,domain='frequency');parts.append(one.fill_fftseries(one.XYZtoAE(x),one.start_idx.copy(),lo,hi))
check('network_vs_single_detectors_order',lambda:compare(network,np.concatenate(parts,axis=0),1e-8),'TianQin A/E, Taiji A/E, LISA A/E, three sources')
net_single=np.concatenate([net.response_on_band({k:v[j] for k,v in params.items()},lo,hi) for j in range(3)],axis=1)
check('network_batch_vs_single_sources',lambda:compare(network,net_single,1e-8),'Three-detector original batched response')
def reject_time():
 try:net(params,domain='time')
 except NotImplementedError:return {'passed':True,'exception':'NotImplementedError'}
 return {'passed':False}
check('network_time_explicitly_unsupported',reject_time,'Declared interface restriction, not numerical validation of network time response')
arrays['network_band']=network;arrays['network_single_detector_reference']=np.concatenate(parts,axis=0)
# Auxiliary spectra tested away from DC and transfer-function zeros.
f=np.array([.0011,.0031,.0061])
check('auxiliary_PSDs_positive_finite',lambda:{'passed':all(np.isfinite(fun(f)).all() and np.all(fun(f)>0) for fun in [g.PSD_OMS,g.PSD_ACC,g.PSD_X2,g.PSD_A2])},'Positive-frequency smoke check; no claim about f=0 or all frequencies')
source_records=[]
for name,pin in [('triangle-gb','cbc0a1b0cbf4ec05ec969fa39405394168c3e06c'),('triangle-simulator','ab796358e9a36c8987f6bb53a97230d603bfdfd5')]:
 src=ROOT/'external'/name;actual=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip();clean=not subprocess.check_output(['git','-C',str(src),'status','--porcelain'],text=True)
 check(name+'_pin_clean',lambda actual=actual,pin=pin,clean=clean:{'passed':actual==pin and clean,'commit':actual,'clean':clean},'Source identity')
 source_records.append({'repository':name,'commit':actual,'clean':clean})
np.savez_compressed(OUT/'arrays.npz',**arrays)
report={'started_utc':started_utc,'host':platform.node(),'python':platform.python_version(),'numpy':np.__version__,'wall_seconds':time.perf_counter()-start,'configuration':{'Ntime':N,'dt_seconds':dt,'Nsparse':ns,'seed':20261012,'sources':{k:v.tolist() for k,v in params.items()},'mission_list':mission_list},'sources':source_records,'checks':records,'passed_count':sum(x['passed'] for x in records),'failed_count':sum(not x['passed'] for x in records),'all_checks_passed':all(x['passed'] for x in records),'scope':'Targeted CPU package verification; failures are retained; no upstream fixes, GPU or universal scientific accuracy claim.'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('SUMMARY',json.dumps({k:report[k] for k in ['wall_seconds','passed_count','failed_count','all_checks_passed']}))
