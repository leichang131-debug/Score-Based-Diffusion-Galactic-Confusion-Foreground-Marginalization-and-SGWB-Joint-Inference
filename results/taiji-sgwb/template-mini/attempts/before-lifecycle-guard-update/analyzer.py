#!/usr/bin/env python3
"""Configured subset-chain diagnostics/quantiles; never a full-year inference claim."""
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from eryn.backends import HDFBackend
from taiji_sgwb_mini import ROOT,CFG,OUT,WORK,load_mini
from taiji_sgwb_likelihood import evaluate_original,stable_reference
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_formal_checkpoint import write_json


def acf(x):
    x=np.asarray(x,dtype=float);x=x-x.mean();n=len(x)
    f=np.fft.rfft(x,n=1<<((2*n-1).bit_length()));a=np.fft.irfft(f*np.conj(f))[:n]
    return a/a[0] if a[0]>0 else None


def iat_from_acf(a):
    if a is None:return {'tau':None,'adequate_length':False,'length_over_tau':0.,'reason':'constant trace'}
    series=2*np.cumsum(a)-1;idx=np.flatnonzero(np.arange(len(a))>=5*series);window=int(idx[0]) if len(idx) else len(a)-1
    raw=float(series[window]);tau=max(1.,raw)
    return {'tau':tau,'raw_tau':raw,'window':window,'length_over_tau':len(a)/tau,'adequate_length':bool(raw>0 and len(a)>=50*tau and window<len(a)-1)}


def main():
    cfg=json.loads(CFG.read_text());progress=json.loads((WORK/'progress.json').read_text());assert progress['status']=='SAMPLING_COMPLETE'
    backend=HDFBackend(WORK/'template_AET_nofg.h5',read_only=True);N=int(backend.iteration);W=cfg['nwalkers']
    assert N==cfg['production_steps'] and progress['burn_done']==cfg['burn']
    chain=backend.get_chain();cold=np.concatenate([chain[k][:,0,:,0,:] for k in ['acc','ro','sgwb']],axis=-1);assert cold.shape==(N,W,14)
    flat=cold.reshape(-1,14);assert np.all(np.isfinite(flat))
    truth=json.loads((ROOT/'results/taiji-sgwb/data/validation.json').read_text())['injected_parameters'];links=['12','13','23','21','31','32']
    labels=['ACC_'+l for l in links]+['OMS_'+l for l in links]+['Omega0','alpha']
    injected=np.array([truth['noise/ACC_noise_amplitudes/'+l] for l in links]+[truth['noise/OMS_noise_amplitudes/'+l] for l in links]+[truth['sgwb/omega0'],truth['sgwb/n']])
    rows=[];diagnostics=[];acf_summary=[]
    for j,label in enumerate(labels):
        q=np.quantile(flat[:,j],[.025,.16,.5,.84,.975]);sd=float(flat[:,j].std());traces=[acf(cold[:,w,j]) for w in range(W)];valid=[a for a in traces if a is not None];averaged=np.mean(valid,axis=0) if valid else None
        iat=iat_from_acf(averaged);mean_iat=iat_from_acf(acf(cold[:,:,j].mean(axis=1)))
        mcse=float(np.sqrt(np.var(cold[:,:,j].mean(axis=1))*mean_iat['tau']/N)) if mean_iat['tau'] else None
        ess=min(len(flat),sd**2/mcse**2) if mcse and mcse>0 else None
        drift=float(abs(cold[:N//2,:,j].mean()-cold[N//2:,:,j].mean())/sd) if sd>0 else None
        diagnostics.append({'parameter':label,'walker_averaged_ACF_IAT':iat,'ensemble_mean_IAT':mean_iat,'heuristic_mean_MCSE':mcse,'heuristic_mean_ESS':ess,'half_chain_mean_drift_over_sd':drift,'limited_diagnostic_flags_pass':bool(iat['adequate_length'] and mean_iat['adequate_length'] and ess is not None and ess>=500 and drift is not None and drift<.25)})
        rows.append({'parameter':label,'truth':float(injected[j]),'q025':float(q[0]),'q16':float(q[1]),'median':float(q[2]),'q84':float(q[3]),'q975':float(q[4]),'truth_percentile':float(np.mean(flat[:,j]<=injected[j])),'truth_inside_95_percent':bool(q[0]<=injected[j]<=q[4])})
        acf_summary.append(averaged if averaged is not None else np.zeros(N))
    with (OUT/'posterior-parameters.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    with (OUT/'diagnostics.csv').open('w') as f:
        keys=['parameter','tau','length_over_tau','heuristic_mean_ESS','half_chain_mean_drift_over_sd','limited_flags_pass'];w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader()
        for d in diagnostics:w.writerow({'parameter':d['parameter'],'tau':d['walker_averaged_ACF_IAT']['tau'],'length_over_tau':d['walker_averaged_ACF_IAT']['length_over_tau'],'heuristic_mean_ESS':d['heuristic_mean_ESS'],'half_chain_mean_drift_over_sd':d['half_chain_mean_drift_over_sd'],'limited_flags_pass':d['limited_diagnostic_flags_pass']})
    bstart=json.loads((OUT/'burn-exit-move.json').read_text());bfinal=json.loads((OUT/'resume/state.json').read_text())
    denominator=bfinal['moves'][0]['num_proposals']-bstart['num_proposals'];assert denominator==N
    fractions=(np.array(bfinal['moves'][0]['accepted'])-np.array(bstart['accepted']))/denominator
    assert np.all(fractions>=0) and np.all(fractions<=1)
    ns,_=load_mini();recomputed=[];numerical_checks={}
    for step,temp,walker in [(0,0,0),(N//2-1,0,15),(N//2,5,31),(N-1,0,0),(N-1,5,31)]:
        params=[chain[k][step,temp,walker,0,:] for k in ['acc','ro','sgwb']];ll,cap=evaluate_original(ns,params);ref=stable_reference(cap['csd_hypo'],ns['csd_est'],6,ns['win_bw'])
        prior=sum(float(ns['priors'][k][j].logpdf(x)) for k,v in zip(['acc','ro','sgwb'],params) for j,x in enumerate(v))
        result={'step':step+1,'temperature':temp,'walker':walker,'stored_error':abs(ll-float(backend.get_log_like()[step,temp,walker])),'Cholesky_error':abs(ll-ref['value']),'prior_error':abs(prior-float(backend.get_log_prior()[step,temp,walker]))};recomputed.append(result)
        numerical_checks[f'saved_state_{step}_{temp}_{walker}']=result['stored_error']<1e-6 and result['Cholesky_error']<1e-6 and result['prior_error']<1e-10 and ref['minimum_scaled_eigenvalue']>0
    half=HDFBackend(OUT/'first/template_AET_nofg.h5',read_only=True)
    restored=json.loads((OUT/'resume/worker.json').read_text());numerical_checks['fresh_process_restore']=all(restored['restored_checks'].values()) and restored['start_state']['production_done']==cfg['restart_after_production']
    numerical_checks['stored_prefix_preserved']=all(np.array_equal(half.get_chain()[k],chain[k][:cfg['restart_after_production']]) for k in chain) and np.array_equal(half.get_log_like(),backend.get_log_like()[:cfg['restart_after_production']]) and np.array_equal(half.get_betas(),backend.get_betas()[:cfg['restart_after_production']])
    numerical_checks['all_full_chain_numeric_fields_finite']=all(np.all(np.isfinite(x)) for x in chain.values()) and np.all(np.isfinite(backend.get_log_like())) and np.all(np.isfinite(backend.get_log_prior()))
    numerical_checks['configured_schedule_complete']=N==1000 and progress['burn_done']==300
    passed=all(d['limited_diagnostic_flags_pass'] for d in diagnostics)
    sm=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text());numerical_checks['all_original_19_files_unchanged']=all(sha(ROOT/x['repository_path'])==x['sha256'] for x in sm['files'])
    numerical_checks['full_formal_run_still_paused']=json.loads((ROOT/'results/taiji-sgwb/template-formal/status.json').read_text())['status']=='PAUSED_BY_USER'
    result={'status':'SUBSET_WORKFLOW_COMPLETE_DIAGNOSTICS_LIMITED_PASS' if passed else 'SUBSET_WORKFLOW_COMPLETE_CONVERGENCE_NOT_CONFIRMED','scope':cfg['scope'],'subset_posterior_target':'p(theta | selected 8 weeks and 512 original frequency bins), original priors and original weighted likelihood. Not p(theta | full original data).','numerical_checks':{k:bool(v) for k,v in numerical_checks.items()},'all_numerical_checks_pass':bool(all(numerical_checks.values())),'posterior':rows,'diagnostics':diagnostics,'recomputed_saved_states':recomputed,'sampling':{'burn':cfg['burn'],'stored_production':N,'thin_by':1,'cold_draws':len(flat),'ntemps':6,'nwalkers':W,'mean_production_acceptance_by_temperature':fractions.mean(axis=1).tolist(),'swaps_accepted':backend.swaps_accepted.tolist()},'R_hat':'Not computed for interacting walkers in a single ensemble. Independent initialized ensembles are required.','interpretation':'Quantiles and bands describe this finite selected-data sample. Failed length/mixing/drift checks prohibit claiming a reliable converged posterior; no extension beyond the approved small experiment.','MCSE_note':'Ensemble-mean MCSE/ESS are heuristic. Standard walker-averaged ACF/IAT is also reported; number of stored draws is not the number of independent draws.'}
    write_json(OUT/'analysis.json',result)
    np.savez_compressed(OUT/'posterior-cold-chain.npz',cold_chain=cold,truth=injected,labels=np.array(labels),log_like_cold=backend.get_log_like()[:,0,:],betas=backend.get_betas(),walker_averaged_acf=np.array(acf_summary),acceptance_fraction=fractions)
    # Explicit subset labeling; no full-year or converged-posterior label.
    with plt.rc_context({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8}):
        fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
        for ax,j in zip(axes[:2],[12,13]):
            scale=1e-12 if j==12 else 1;ax.plot(np.arange(1,N+1),cold[:,::4,j]/scale,lw=.5,alpha=.4);ax.axhline(injected[j]/scale,color='k',ls='--',label='Injection');ax.axvline(cfg['restart_after_production']+.5,color='red',ls=':',label='Restart');ax.set(xlabel='Stored production update',ylabel=labels[j]+(' / 1e-12' if j==12 else ''),title='Selected-data cold walkers');ax.legend();ax.grid(alpha=.2)
        for j in [0,6,12,13]:axes[2].plot(np.arange(min(200,N)),np.array(acf_summary)[j,:min(200,N)],label=labels[j])
        axes[2].set(xlabel='Lag [saved updates]',ylabel='Mean normalized walker ACF',title='Autocorrelation diagnostics');axes[2].legend();axes[2].grid(alpha=.2)
        fig.suptitle('Mini experiment: 8 weeks / 512 bins; convergence assessed separately',fontsize=12);fig.savefig(OUT/'sampling-diagnostics.png',dpi=170);plt.close(fig)
        import corner
        display=flat[:,12:14].copy();display[:,0]/=1e-12
        fig=corner.corner(display,labels=['Omega0 / 1e-12','alpha'],truths=[injected[12]/1e-12,injected[13]],quantiles=[.16,.5,.84],show_titles=True,title_fmt='.3g',title_kwargs={'fontsize':10});fig.subplots_adjust(top=.84);fig.suptitle('Selected-data sample distribution\n'+('Limited flags pass; no calibration claim' if passed else 'Convergence not confirmed'),fontsize=11,y=.99);fig.savefig(OUT/'sgwb-sample-distribution.png',dpi=170,bbox_inches='tight');plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,6),layout='constrained');im=ax.imshow(np.corrcoef(flat.T),vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(14),labels,rotation=90);ax.set_yticks(range(14),labels);ax.set_title('Selected-data sampled parameter correlations');fig.colorbar(im,ax=ax,label='Correlation');fig.savefig(OUT/'parameter-correlations.png',dpi=170);plt.close(fig)
        f=np.geomspace(1e-4,.05,150);selected=flat;omega=selected[:,12,None]*(f[None,:]/1e-3)**selected[:,13,None];q=np.quantile(omega,[.16,.5,.84],axis=0)
        fig,ax=plt.subplots(figsize=(7,4),layout='constrained');ax.fill_between(f,q[0],q[2],alpha=.25,label='Pointwise 16–84% sampled band');ax.loglog(f,q[1],label='Sample median');ax.loglog(f,injected[12]*(f/1e-3)**injected[13],ls='--',label='Injection');ax.set(xlabel='Frequency [Hz]',ylabel='Omega(f)',title='Selected-data spectrum; finite-chain summary');ax.legend();ax.grid(alpha=.2);fig.savefig(OUT/'sampled-spectrum.png',dpi=170);plt.close(fig)
    write_json(OUT/'status.json',{'status':result['status'],'workflow_complete':True,'original_full_data_inference_complete':False,'subset_convergence_confirmed':False,'limited_diagnostic_flags_pass':passed,'numerical_checks_pass':result['all_numerical_checks_pass']})
    print(result['status']);print(f'Numerical workflow checks: {sum(numerical_checks.values())}/{len(numerical_checks)}; diagnostic flags pass: {sum(d["limited_diagnostic_flags_pass"] for d in diagnostics)}/14.')
    if not result['all_numerical_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
