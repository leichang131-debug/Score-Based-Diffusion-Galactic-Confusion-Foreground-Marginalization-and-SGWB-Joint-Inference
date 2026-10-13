#!/usr/bin/env python3
"""Stage 7: actual full-grid original likelihood versus independent numerics."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time
import warnings
import numpy as np
from taiji_sgwb_likelihood import ROOT, load_original_likelihood, evaluate_original, independent_model, stable_reference
from taiji_sgwb_response import load_response_cache
from taijisgwb.waveform import calc_omega_powerlaw
from taijisgwb.utils import psd_from_omega, omega_from_psd
from taijisgwb.constants import HUBBLE0

OUT = ROOT/'results/taiji-sgwb/likelihood'
SEED = 26010169


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()


def relative(a,b): return float(np.linalg.norm(a-b)/np.linalg.norm(b))


def main():
    start=time.perf_counter(); OUT.mkdir(parents=True,exist_ok=True)
    checks={}; observations=[]; rows=[]
    check=lambda name, passed:checks.update({name:bool(passed)})
    response=load_response_cache(ROOT/'data/processed/taiji-sgwb/response/response.h5')
    namespaces={}
    records={}
    for entry in ('template_nofg_28t.py','rj_nofg_28t.py'):
        ns, record=load_original_likelihood(entry,response)
        namespaces[Path(entry).stem]=ns;records[Path(entry).stem]=record
        write(OUT/Path(entry).stem/'source-execution.json',record)
        working=ROOT/record['working_copy']
        check(Path(entry).stem+'_byte_identical_working_copy',sha(working)==record['sha256'])
    template=namespaces['template_nofg_28t']; rj=namespaces['rj_nofg_28t']
    check('two_entry_data_arrays_identical',np.array_equal(template['csd_est'],rj['csd_est']))
    check('full_week_frequency_grid',template['csd_est'].shape==(3,3,52,4426))
    link_order=['12','13','23','21','31','32']
    check('response_link_order',json.loads(response['metadata']['link_order'])==link_order)
    truth=json.loads((ROOT/'results/taiji-sgwb/data/validation.json').read_text())['injected_parameters']
    acc=np.array([truth['noise/ACC_noise_amplitudes/'+l] for l in link_order])
    ro=np.array([truth['noise/OMS_noise_amplitudes/'+l] for l in link_order])
    omega0=truth['sgwb/omega0']; alpha=truth['sgwb/n']; freq=template['f_est']
    omega=omega0*(freq/1e-3)**alpha
    check('powerlaw_formula',np.allclose(calc_omega_powerlaw(freq,omega0,alpha),omega,rtol=8*np.finfo(float).eps,atol=0))
    psd=3*HUBBLE0**2/(2*np.pi**2)*omega/freq**3
    check('omega_to_strain_psd_formula',np.allclose(psd_from_omega(freq,omega),psd,rtol=8*np.finfo(float).eps,atol=0))
    check('omega_psd_roundtrip',np.allclose(omega_from_psd(freq,psd_from_omega(freq,omega)),omega,rtol=8*np.finfo(float).eps,atol=0))
    check('template_dimensions_and_original_priors',template['ndim']=={'acc':6,'ro':6,'sgwb':2} and all(np.isfinite(template['priors'][branch][i].logpdf(x)) for branch, values in [('acc',acc),('ro',ro),('sgwb',[omega0,alpha])] for i,x in enumerate(values)))
    check('rj_dimensions_and_leaf_limits',rj['ndim']=={'acc':6,'ro':6,'sgwb_knot':2,'sgwb_edge':2} and rj['nleaf_min']['sgwb_knot']==1 and rj['nleaf_max']['sgwb_knot']==16)
    rng=np.random.default_rng(SEED); numerical_warnings=[]
    def evaluate(label,ns,params,aa,rr,om):
        t=time.perf_counter(); value, cap=evaluate_original(ns,params); original_seconds=time.perf_counter()-t
        numerical_warnings.extend([{'label':label,**w} for w in cap['warnings']])
        model=cap['csd_hypo']
        expected=independent_model(ns,aa,rr,om)
        ref=stable_reference(model,ns['csd_est'],ns['nperbin'],ns['win_bw'])
        err=relative(model,expected)
        tolerance=1e-6
        scale=np.max(np.diagonal(model,axis1=-2,axis2=-1).real,axis=-1)
        with warnings.catch_warnings(record=True) as dw:
            warnings.simplefilter('always',RuntimeWarning)
            determinant=np.linalg.det(model)
        with warnings.catch_warnings(record=True) as sw:
            warnings.simplefilter('always',RuntimeWarning)
            sign,ld=np.linalg.slogdet(model/scale[...,None,None])
            normalized_det=np.linalg.det(model/scale[...,None,None])
        robust_det=np.exp(ld+3*np.log(scale))
        determinant_error=float(np.max(np.abs(determinant.real/robust_det-1)))
        check(label+'_determinant_finite_positive',np.all(np.isfinite(determinant)) and np.all(determinant.real>0))
        check(label+'_determinant_scaled_reference',determinant_error<1e-11 and np.max(np.abs(sign-1))<1e-12)
        check(label+'_scaled_determinant_finite',np.all(np.isfinite(normalized_det)) and np.all(normalized_det.real>0))
        check(label+'_finite',np.isfinite(value) and np.all(np.isfinite(model)))
        check(label+'_independent_model',err<1e-12)
        check(label+'_cholesky_positive',ref['minimum_scaled_eigenvalue']>0)
        check(label+'_hermitian',ref['maximum_hermitian_error']<1e-12)
        check(label+'_likelihood_reference',abs(value-ref['value'])<tolerance and abs(cap['ll_exp']-ref['ll_exp'])<1e-6+1e-12*abs(ref['ll_exp']) and abs(cap['ll_coef']-ref['ll_coef'])<1e-6+1e-12*abs(ref['ll_coef']))
        rows.append({'label':label,'original_log_likelihood':value,'reference_log_likelihood':ref['value'],'absolute_error':abs(value-ref['value']),'model_relative_L2':err,'original_seconds':original_seconds,'minimum_determinant_real':float(determinant.real.min()),'maximum_determinant_real':float(determinant.real.max()),'max_determinant_relative_error':determinant_error,'raw_determinant_warning_count':len(dw),'normalized_determinant_warning_count':len(sw),**{k:v for k,v in ref.items() if k!='value'}})
        print(f'{label}: LL={value:.9f}, reference error={abs(value-ref["value"]):.3g}, cond_max={ref["maximum_condition_number"]:.3g}',flush=True)
        return value,model
    truth_ll,truth_model=evaluate('template_truth',template,[acc,ro,np.array([omega0,alpha])],acc,ro,omega)
    # Full actual prior box probes, not tiny synthetic/subsampled likelihoods.
    for i in range(8):
        aa=rng.uniform(.75,1.25,6)*3e-15;rr=rng.uniform(.75,1.25,6)*8e-12
        oo=rng.uniform(1e-14,5e-11);al=rng.uniform(-1,2)
        evaluate(f'template_prior_{i}',template,[aa,rr,np.array([oo,al])],aa,rr,oo*(freq/1e-3)**al)
    for i,(oo,al) in enumerate([(1e-14,-1),(5e-11,2)]):
        evaluate(f'template_boundary_{i}',template,[np.full(6,2.25e-15),np.full(6,1e-11),np.array([oo,al])],np.full(6,2.25e-15),np.full(6,1e-11),oo*(freq/1e-3)**al)
    # Exact power law is a straight line in the original log10 interpolation.
    def knots_on_powerlaw(n):
        x=np.linspace(np.log10(rj['f_analow']),np.log10(rj['f_anaupp']),n+2)
        y=np.log10(omega0)+alpha*(x-np.log10(1e-3))
        return np.column_stack((x[1:-1],y[1:-1])),np.array([[y[0],y[-1]]])
    rj_values=[]
    for n in (1,2,4,8,16):
        knots,edge=knots_on_powerlaw(n)
        interp=rj['create_omega_interp_fun'](knots,edge)
        check(f'rj_{n}_knots_powerlaw_interpolation',np.max(np.abs(interp(rj['log_f_est'])-np.log10(omega)))<1e-12)
        params=[acc[None,:],ro[None,:],knots,edge]
        value,_=evaluate(f'rj_powerlaw_{n}',rj,params,acc,ro,10**interp(rj['log_f_est']))
        rj_values.append(value)
        check(f'rj_{n}_template_equivalence',abs(value-truth_ll)<1e-6)
        perm=rng.permutation(n)
        check(f'rj_{n}_unsorted_knots_supported',np.allclose(rj['create_omega_interp_fun'](knots[perm],edge)(rj['log_f_est']),interp(rj['log_f_est']),rtol=0,atol=1e-12))
    # Additional original RJ prior draws: explicit bounds rejection is expected.
    rj_prior_probes=[]
    for n in (1,2,4,8,16):
        for rep in range(3):
            kk=np.column_stack((rng.uniform(-4,np.log10(.05),n),rng.uniform(-14,-9,n)))
            ee=rng.uniform(-14,-9,(1,2))
            aa=rng.uniform(.75,1.25,6)*3e-15;rr=rng.uniform(.75,1.25,6)*8e-12
            params=[aa[None,:],rr[None,:],kk,ee]
            value=rj['log_likelihood'](params)
            check(f'rj_prior_{n}_{rep}_finite_or_original_rejection',np.isfinite(value))
            rejected=bool(value==-1e50)
            rj_prior_probes.append({'knots':n,'rep':rep,'original_bounds_rejection':rejected,'value':float(value)})
            if not rejected:
                om=10**rj['create_omega_interp_fun'](kk,ee)(rj['log_f_est'])
                evaluate(f'rj_prior_{n}_{rep}',rj,params,aa,rr,om)
    # Valid non-power-law shape through quadratic interpolation.
    knots,edge=knots_on_powerlaw(4); knots[:,1]+=np.array([.10,-.06,.08,-.02])
    curved=10**rj['create_omega_interp_fun'](knots,edge)(rj['log_f_est'])
    evaluate('rj_curved_spectrum',rj,[acc[None,:],ro[None,:],knots,edge],acc,ro,curved)
    # Original finite rejection sentinel; not negative infinity.
    check('rj_out_of_range_original_sentinel',rj['log_likelihood']([acc[None,:],ro[None,:],np.array([[-3.,-15.]]),np.array([[-15.,-15.]])])==-1e50)
    overshoot_knot=np.array([[-3.9,-9.],[-3.8,-14.]])
    overshoot_edge=np.array([[-14.,-14.]])
    overshoot=rj['create_omega_interp_fun'](overshoot_knot,overshoot_edge)(rj['log_f_est'])
    check('rj_quadratic_overshoot_rejected', (overshoot.min() < -14 or overshoot.max() > -9) and rj['log_likelihood']([acc[None,:],ro[None,:],overshoot_knot,overshoot_edge])==-1e50)
    duplicate_error=None
    try:rj['create_omega_interp_fun'](np.array([[-3.,-12.],[-3.,-12.]]),np.array([[-12.,-12.]]))
    except ValueError as e:duplicate_error=str(e)
    check('duplicate_knot_failure_recorded',duplicate_error is not None)
    observations.append({'kind':'original_input_limit','issue':'Exactly duplicated knot frequencies raise ValueError in original quadratic interpolation; no exception handling exists in original likelihood. Continuous prior probability is zero, but external starts must use distinct knots. Near-duplicate knots can overshoot and receive the original -1e50 sentinel.','duplicate_error':duplicate_error,'overshoot_log10_range':[float(overshoot.min()),float(overshoot.max())]})
    # Complex-conjugation counterexample: a naive trace(model^-1 * raw CSD)
    # is wrong, whereas transpose(raw CSD) yields the original contraction.
    z=np.array([1+2j,3-1j,.2+.7j]); d=np.outer(z.conj(),z)
    a=np.array([[2,.2+.4j,.1j],[.2-.4j,3,.2],[ -.1j,.2,1.]])
    inv=np.linalg.inv(a)
    element=float(np.sum(d*inv).real)
    right=float(np.trace(np.linalg.solve(a,d.T)).real)
    wrong=float(np.trace(np.linalg.solve(a,d)).real)
    check('complex_contraction_orientation',abs(element-right)<1e-12 and abs(element-wrong)>1e-2)
    # Diagnose warnings independently of physical data, including identity.
    warning_controls=[]
    for label,a in [('real_identity',np.eye(3)),('complex_identity',np.eye(3,dtype=complex)),('complex_positive_matrix',a)]:
        for function in (np.linalg.det,np.linalg.slogdet,np.linalg.cholesky):
            with warnings.catch_warnings(record=True) as cw:
                warnings.simplefilter('always',RuntimeWarning); result=function(a)
            warning_controls.append({'input':label,'function':function.__name__,'warnings':[str(w.message) for w in cw],'all_returned_values_finite':bool(all(np.all(np.isfinite(x)) for x in result)) if isinstance(result,tuple) else bool(np.all(np.isfinite(result)))})
    check('identity_warning_control_all_outputs_finite',all(x['all_returned_values_finite'] for x in warning_controls))
    check('real_identity_warning_free',all(not x['warnings'] for x in warning_controls if x['input']=='real_identity'))
    check('complex_identity_cholesky_warning_free',all(not x['warnings'] for x in warning_controls if x['input']=='complex_identity' and x['function']=='cholesky'))
    write(OUT/'determinant-warning-controls.json',{'numpy_version':np.__version__,'controls':warning_controls,'conclusion':'Complex det/slogdet warnings also reproduce on a positive identity matrix, independent of physical data and scaling. Exact backend cause unresolved; original function retained.'})
    # Asimov consistency: hypothetical data = model.T; perturbations cannot
    # improve expected likelihood. This is a model algebra test, not calibration.
    asimov=truth_model.swapaxes(-1,-2)
    asimov=np.moveaxis(asimov,[-2,-1],[0,1])
    asimov_ref=stable_reference(truth_model,asimov,6,template['win_bw'])['value']
    pert=independent_model(template,acc*1.08,ro*.94,omega*1.5)
    check('asimov_truth_beats_perturbed_model',stable_reference(pert,asimov,6,template['win_bw'])['value']<asimov_ref)
    # Connect actual Eryn compute interfaces with original priors/function.
    import eryn.ensemble
    interface={}
    for name,ns in namespaces.items():
        extra={'moves':ns['moves'],'rj_moves':True} if name.startswith('rj') else {}
        sampler=eryn.ensemble.EnsembleSampler(32,ns['ndim'],ns['log_likelihood'],ns['priors'],tempering_kwargs={'ntemps':1},nbranches=len(ns['branch_names']),branch_names=ns['branch_names'],nleaves_min=ns['nleaf_min'],nleaves_max=ns['nleaf_max'],**extra)
        params={key:np.zeros((1,32,ns['nleaf_max'][key],ns['ndim'][key])) for key in ns['branch_names']}
        params['acc'][:,:,0,:]=acc;params['ro'][:,:,0,:]=ro
        inds={key:np.ones(value.shape[:-1],dtype=bool) for key,value in params.items()}
        if name.startswith('template'):params['sgwb'][:,:,0,:]=[omega0,alpha]
        else:
            kk,ee=knots_on_powerlaw(1)
            params['sgwb_knot'][:,:,0,:]=kk[0];params['sgwb_edge'][:,:,0,:]=ee[0]
            inds['sgwb_knot'][:]=False;inds['sgwb_knot'][:,:,0]=True
        prior=sampler.compute_log_prior(params,inds=inds)
        t=time.perf_counter(); ll=sampler.compute_log_like(params,inds=inds)[0];seconds=time.perf_counter()-t
        check(name+'_eryn_prior_interface',prior.shape==(1,32) and np.all(np.isfinite(prior)))
        check(name+'_eryn_likelihood_interface',ll.shape==(1,32) and np.all(np.isfinite(ll)) and np.max(np.abs(ll-truth_ll))<1e-6)
        interface[name]={'nwalkers':32,'ntemps':1,'active_knot_leaves':1 if name.startswith('rj') else None,'log_like_shape':list(ll.shape),'maximum_error_from_direct_truth':float(np.max(np.abs(ll-truth_ll))),'evaluation_seconds':seconds,'MCMC_updates':0,'original_RJ_mode_enabled':name.startswith('rj'),'inactive_knot_storage':'zero placeholders masked out by original Eryn interface' if name.startswith('rj') else None}
    # Conditional amplitude scan: all 12 noise values and alpha held at truth.
    factors=np.geomspace(.3,3,13);scan=[];scan_seconds=[]
    for factor in factors:
        t=time.perf_counter();scan.append(template['log_likelihood']([acc,ro,np.array([omega0*factor,alpha])]))
        scan_seconds.append(time.perf_counter()-t)
    check('conditional_scan_all_finite',np.all(np.isfinite(scan)))
    diagnostic={}
    for i,name in enumerate('AET'):
        ratio=template['csd_est'][i,i].real/truth_model[...,i,i].real
        diagnostic[name]={'mean_data_model_diagonal_ratio':float(ratio.mean()),'median_data_model_diagonal_ratio':float(np.median(ratio))}
    np.savez_compressed(OUT/'spectral-summary.npz',frequency=freq,omega_truth=omega,psd_truth=psd,mean_model_auto=np.diagonal(truth_model,axis1=-2,axis2=-1).real.mean(axis=0).T,mean_data_auto=np.array([template['csd_est'][i,i].real.mean(axis=0) for i in range(3)]),scan_omega0=omega0*factors,scan_ll=np.array(scan),scan_seconds=np.array(scan_seconds))
    with (OUT/'likelihood-comparisons.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    import importlib.util
    spec=importlib.util.spec_from_file_location('stage7_report',ROOT/'scripts/reproduction/report-taiji-sgwb-likelihood.py')
    renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer);renderer.render()
    source_manifest=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text())
    check('all_original_19_file_hashes_preserved',all(sha(ROOT/item['repository_path'])==item['sha256'] for item in source_manifest['files']))
    inputs={}
    for p in [ROOT/'data/processed/taiji-sgwb/response/response.h5']+[ROOT/'data/processed/taiji-sgwb/preprocessing'/n/'preprocessing.h5' for n in namespaces]:inputs[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size}
    report={'schema_version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':SEED,'determinant_warning_note':'Unscaled NumPy complex det emits divide-by-zero/invalid RuntimeWarnings on this environment. All determinants are finite/positive and agree with scale-normalized slogdet; complex det/slogdet also warn on a unit identity matrix; Cholesky is warning-free. Exact backend cause is not established; original source is unchanged.', 'scope':'Both exact original likelihoods on complete 52 x 4426 grid; independent covariance/Cholesky checks, original priors and Eryn compute interfaces. No MCMC or posterior calibration.','checks':checks,'all_checks_pass':all(checks.values()),'comparisons':rows,'rj_prior_probes':rj_prior_probes,'interfaces':interface,'inputs':inputs,'truth_parameters':{'link_order':link_order,'acc':acc.tolist(),'ro':ro.tolist(),'omega0':omega0,'alpha':alpha},'conjugation_control':{'original_elementwise':element,'transpose_trace_reference':right,'incorrect_raw_trace':wrong},'truth_covariance_diagonal_diagnostic':diagnostic,'conditional_scan':{'points':len(scan),'scan_max_omega0':float(omega0*factors[np.argmax(scan)]),'truth_omega0':omega0,'median_original_call_seconds':float(np.median(scan_seconds)),'note':'Noise and slope fixed at injection; finite realization may shift maximum. This is not a marginalized posterior or parameter recovery verdict.'},'observations':observations,'original_runtime_warnings':numerical_warnings,'elapsed_seconds':time.perf_counter()-start}
    write(OUT/'validation.json',report)
    print(f'Stage 7: {sum(checks.values())}/{len(checks)} checks passed in {report["elapsed_seconds"]:.3f} s',flush=True)
    if not report['all_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
