#!/usr/bin/env python3
"""Cold-chain posterior and conservative single-ensemble sampling diagnostics."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator,LogFormatterMathtext,NullFormatter
from eryn.backends import HDFBackend
from taiji_sgwb_likelihood import ROOT,load_original_likelihood,evaluate_original,stable_reference
from taiji_sgwb_formal_checkpoint import write_json
from taiji_sgwb_checkpoint import sha

OUT=ROOT/'results/taiji-sgwb/template-formal'


def autocorrelation_time(x):
    """FFT ACF with Sokal 5*tau window; deliberately flags short estimates."""
    x=np.asarray(x);x=x-x.mean();n=len(x)
    if np.var(x)==0:return {'tau':None,'length_over_tau':0.,'adequate_length':False,'reason':'constant series'}
    nfft=1<<((2*n-1).bit_length());z=np.fft.rfft(x,n=nfft)
    ac=np.fft.irfft(z*np.conj(z),n=nfft)[:n];ac/=ac[0]
    tau_series=2*np.cumsum(ac)-1
    candidates=np.flatnonzero(np.arange(n)>=5*tau_series)
    window=int(candidates[0]) if len(candidates) else n-1
    tau=max(1.,float(tau_series[window]))
    return {'tau':tau,'window':window,'length_over_tau':n/tau,'adequate_length':bool(n>=50*tau and window<n-1)}


def main():
    root=ROOT/'runs/taiji-sgwb/template-formal';progress=json.loads((root/'progress.json').read_text());cfg=json.loads((ROOT/'configs/reproduction/taiji-sgwb/template-formal.json').read_text())
    assert progress['status']=='SAMPLING_COMPLETE' and progress['burn_done']==1000 and progress['production_saved']==350
    b=HDFBackend(root/'template_AET_nofg.h5',read_only=True);assert b.iteration==350
    chain=b.get_chain();cold=np.concatenate([chain[k][:,0,:,0,:] for k in ['acc','ro','sgwb']],axis=-1)
    assert cold.shape==(350,62,14) and np.all(np.isfinite(cold)) and np.all(np.isfinite(b.get_log_like())) and np.all(np.isfinite(b.get_log_prior()))
    truth=json.loads((ROOT/'results/taiji-sgwb/data/validation.json').read_text())['injected_parameters'];links=['12','13','23','21','31','32']
    labels=['ACC_'+l for l in links]+['OMS_'+l for l in links]+['Omega0','alpha']
    injected=np.array([truth['noise/ACC_noise_amplitudes/'+l] for l in links]+[truth['noise/OMS_noise_amplitudes/'+l] for l in links]+[truth['sgwb/omega0'],truth['sgwb/n']])
    flat=cold.reshape(-1,14);rows=[];diagnostics=[]
    for i,label in enumerate(labels):
        q=np.quantile(flat[:,i],[.025,.16,.5,.84,.975]);sd=float(flat[:,i].std())
        average=cold[:,:,i].mean(axis=1);iat=autocorrelation_time(average)
        # Ensemble-mean MCSE accounts for simultaneous walker covariance;
        # do not label 62 interactive walkers as independent chains.
        mcse=float(np.sqrt(np.var(average)*iat['tau']/350)) if iat['tau'] else None
        ess=min(len(flat),float(sd**2/mcse**2)) if mcse and mcse>0 else None
        shift=float(abs(cold[:175,:,i].mean()-cold[175:,:,i].mean())/sd) if sd>0 else None
        rows.append({'parameter':label,'truth':float(injected[i]),'q025':float(q[0]),'q16':float(q[1]),'median':float(q[2]),'q84':float(q[3]),'q975':float(q[4]),'truth_percentile':float(np.mean(flat[:,i]<=injected[i])),'truth_inside_95_percent':bool(q[0]<=injected[i]<=q[4])})
        diagnostics.append({'parameter':label,'ensemble_mean_iat_saved_units':iat,'heuristic_mean_MCSE':mcse,'heuristic_mean_ESS':ess,'half_chain_mean_shift_over_posterior_sd':shift,'adequate':bool(iat['adequate_length'] and ess is not None and ess>=500 and shift is not None and shift<.25)})
    with (OUT/'posterior-parameters.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    ns,_=load_original_likelihood('template_nofg_28t.py');checks={};recomputed=[]
    for step,temp,walker in [(0,0,0),(174,0,31),(349,0,0),(349,5,61)]:
        params=[chain[k][step,temp,walker,0,:] for k in ['acc','ro','sgwb']]
        ll,cap=evaluate_original(ns,params);ref=stable_reference(cap['csd_hypo'],ns['csd_est'],6,ns['win_bw'])
        err=abs(ll-b.get_log_like()[step,temp,walker]);recomputed.append({'step':step,'temp':temp,'walker':walker,'original_stored_error':err,'Cholesky_error':abs(ll-ref['value']),'condition_number':ref['maximum_condition_number']})
        checks[f'saved_{step}_{temp}_{walker}']=err<1e-6 and abs(ll-ref['value'])<1e-6 and ref['minimum_scaled_eigenvalue']>0
    sm=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text());checks['original_source_unchanged']=all(sha(ROOT[x['repository_path']])==x['sha256'] for x in sm['files'])
    checks['original_schedule_complete']=b.iteration==350 and progress['burn_done']==1000 and progress['transitions_done']==5200
    checks['all_chain_values_finite']=all(np.all(np.isfinite(x)) for x in chain.values()) and np.all(np.isfinite(b.get_log_like()))
    snapshot_fraction=b.accepted/350
    fraction=snapshot_fraction
    acceptance_method='Accepted final substep at each saved ensemble; not all 4200 proposal transitions'
    if (OUT/'burn-exit-state.json').exists():
        burn_state=json.loads((OUT/'burn-exit-state.json').read_text());final=json.loads((OUT/'final-state.json').read_text())
        numerator=np.array(final['moves'][0]['accepted'])-np.array(burn_state['moves'][0]['accepted'])
        denominator=final['moves'][0]['num_proposals']-burn_state['moves'][0]['num_proposals']
        assert denominator==4200
        fraction=numerator/denominator
        acceptance_method='All production StretchMove proposals; burn-in counts subtracted'
    assert np.all(fraction>=0) and np.all(fraction<=1)
    good=all(d['adequate'] for d in diagnostics)
    result={'status':'SAMPLING_COMPLETE_DIAGNOSTICS_PASS_LIMITED' if good else 'SAMPLING_COMPLETE_CONVERGENCE_NOT_CONFIRMED','scope':'Original schedule completed. Quantiles describe the sampled cold chain; reliability remains conditional on diagnostics. One ensemble is not independent-chain convergence or simulation calibration.','checks':{k:bool(x) for k,x in checks.items()},'numerical_checks_pass':bool(all(checks.values())),'posterior':rows,'parameter_diagnostics':diagnostics,'saved_state_recomputation':recomputed,'sampling':{'saved':350,'thin_by':12,'burn':1000,'cold_draws':21700,'ntemps':6,'nwalkers':62,'acceptance_method':acceptance_method,'saved_substep_acceptance_mean_cold':float(snapshot_fraction[0].mean()),'acceptance_mean_cold':float(fraction[0].mean()),'acceptance_per_temperature':fraction.mean(axis=1).tolist(),'swaps_accepted':b.swaps_accepted.tolist()},'R_hat':'Not reported: interacting walkers and temperatures are not independent chains. Independent seeded ensembles are needed.','IAT_note':'FFT/Sokal window on ensemble means; saved-step units. Monte Carlo ESS is heuristic and limited by 350 time steps. No thinning-benefit or coverage guarantee.','missing':'Independent ensembles, repeated-injection coverage and foreground marginalization are not part of this stage.'}
    write_json(OUT/'analysis.json',result)
    np.savez_compressed(OUT/'posterior-cold-chain.npz',cold_chain=cold,truth=injected,labels=np.array(labels),log_like_cold=b.get_log_like()[:,0,:],betas=b.get_betas())
    with plt.rc_context({'font.family':'serif','font.serif':['STIXGeneral','DejaVu Serif'],'mathtext.fontset':'stix','font.size':14,'axes.titlesize':11,'axes.labelsize':16,'legend.fontsize':12,'axes.grid':False,'axes.linewidth':.8,'lines.linewidth':1.0}):
        import corner
        fig=corner.corner(flat[:,12:14],bins=50,smooth=.9,labels=[r'$A_{\mathrm{ap}}$',r'$\gamma_{\mathrm{ap}}$'],truths=injected[12:14],truth_color='red',color='#ff9da7',quantiles=[.16,.84],levels=[.68,.95],plot_datapoints=False,fill_contours=True,show_titles=False,max_n_ticks=4,hist_kwargs={'histtype':'step','linewidth':1})
        for ax in fig.axes:
            ax.tick_params(axis='both',labelsize=13)
            for tick in ax.get_xticklabels()+ax.get_yticklabels():tick.set_rotation(45)
        fig.savefig(OUT/'posterior-sgwb.png',dpi=300,bbox_inches='tight');plt.close(fig)
        # Paper displays per-spacecraft arithmetic averages of the two MOSAs.
        # Average each joint posterior draw, never the marginal quantiles.
        pairs=[(0,1),(3,2),(4,5)];noise_rows=[]
        fig,axes=plt.subplots(3,2,figsize=(7,5.8))
        fig.subplots_adjust(left=.14,right=.98,bottom=.14,top=.98,hspace=.24,wspace=.3)
        for sc,pair in enumerate(pairs):
            for col,offset in enumerate([0,6]):
                unit=1e-15 if col==0 else 1e-12
                values=(flat[:,offset+pair[0]]+flat[:,offset+pair[1]])/(2*unit)
                true=(injected[offset+pair[0]]+injected[offset+pair[1]])/(2*unit)
                q=np.quantile(values,[.025,.16,.5,.84,.975]);ax=axes[sc,col]
                ax.hist(values,bins=50,density=True,histtype='step',color='#76b7b2',linewidth=1,label='template')
                ax.axvline(true,color='red',lw=1)
                kind='ACC' if col==0 else 'OMS'
                if sc==2:ax.set_xlabel(r'$A_i^{(\mathrm{acc})}\ (\mathrm{fm}/\mathrm{s}^2/\sqrt{\mathrm{Hz}})$' if col==0 else r'$A_i^{(\mathrm{oms})}\ (\mathrm{pm}/\sqrt{\mathrm{Hz}})$')
                if sc==0 and col==0:ax.legend(fontsize=10)
                ax.tick_params(labelsize=12)
                noise_rows.append({'parameter':f'{kind}_SC{sc+1}_average','links':[links[pair[0]],links[pair[1]]],'truth':float(true),'unit':'fm/s^2/sqrt(Hz)' if col==0 else 'pm/sqrt(Hz)','quantiles_025_16_50_84_975':q.tolist()})
        fig.text(.045,.55,'Density',rotation=90,va='center',fontsize=18)
        fig.savefig(OUT/'posterior-noise-spacecraft.png',dpi=300,bbox_inches='tight');plt.close(fig)
        write_json(OUT/'posterior-noise-spacecraft.json',{'definition':'Arithmetic MOSA amplitude averages computed draw by draw, as in paper Section IV.','parameters':noise_rows})
        fig,axes=plt.subplots(7,2,figsize=(11,15),layout='constrained')
        for j,ax in enumerate(axes.flat):
            ax.plot(np.arange(1,351),cold[:,::4,j],alpha=.25,lw=.5);ax.axhline(injected[j],color='red',ls='--');ax.set(xlabel='Saved production step',ylabel=labels[j])
        fig.suptitle('All 14 cold-chain traces; walkers belong to one interacting ensemble')
        fig.savefig(OUT/'production-traces-all.png',dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,6),layout='constrained');im=ax.imshow(np.corrcoef(flat.T),vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(14),labels,rotation=90,fontsize=8);ax.set_yticks(range(14),labels,fontsize=8);fig.colorbar(im,ax=ax,label='Sample correlation');ax.set_title('Cold-chain parameter correlations');fig.savefig(OUT/'parameter-correlation.png',dpi=160);plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
        for ax,j in zip(axes,[12,13]):
            scale=1e-12 if j==12 else 1
            ax.plot(np.arange(1,351),cold[:,::4,j]/scale,alpha=.3,lw=.5);ax.axhline(injected[j]/scale,color='k',ls='--');ax.set(xlabel='Saved production ensemble step',ylabel=labels[j]+(' / 1e-12' if j==12 else ''),title='After original 1000-transition burn-in');ax.grid(alpha=.2)
        fig.savefig(OUT/'production-traces.png',dpi=160);plt.close(fig)
        f=np.geomspace(1e-4,.05,150)
        omega=flat[:,12,None]*(f[None,:]/1e-3)**flat[:,13,None];q=np.quantile(omega,[.025,.16,.5,.84,.975],axis=0)
        truth_spectrum=injected[12]*(f/1e-3)**injected[13]
        fig,(ax,residual)=plt.subplots(2,1,figsize=(6.5,5.4),sharex=True,gridspec_kw={'height_ratios':[4,1]})
        fig.subplots_adjust(left=.16,right=.98,bottom=.15,top=.98,hspace=0)
        display=(f>=1e-3)&(f<=.04);ff=f[display];qq=q[:,display];tt=truth_spectrum[display]
        ax.fill_between(ff,qq[0],qq[4],color='#f28e2b',alpha=.75,label='template')
        ax.loglog(ff,tt,color='red',lw=1,label='injected');ax.set_ylabel(r'$\Omega_{\mathrm{gw}}$');ax.legend(loc='upper left')
        residual.fill_between(ff,qq[0]/tt-1,qq[4]/tt-1,color='#f28e2b',alpha=.75);residual.axhline(0,color='red',lw=1);residual.set(xlabel='frequency (Hz)',ylabel='error',xscale='log',xlim=(1e-3,.04))
        residual.xaxis.set_major_locator(LogLocator(base=10,subs=(1.,)));residual.xaxis.set_major_formatter(LogFormatterMathtext());residual.xaxis.set_minor_formatter(NullFormatter())
        fig.savefig(OUT/'posterior-spectrum.png',dpi=300,bbox_inches='tight');plt.close(fig)
        np.savez_compressed(OUT/'posterior-spectrum.npz',frequency=f,truth=truth_spectrum,quantiles=q,probabilities=np.array([.025,.16,.5,.84,.975]))
        write_json(OUT/'figure-provenance.json',{'source':'Actual completed full-data cold chain; no upstream figure or sample reuse.','style_reference':'arXiv:2601.00169v2 PDF pages 7,10,11 visually inspected. Serif/STIX fonts; Figure 3 pink 2.8, red truths, dashed 16/84% markers, 68/95% contours; Figure 8 cyan step histograms, 3x2 MOSA averages in fm/pm; Figure 6 orange template 95% band, red injection, contiguous 4:1 panels, fractional error, display 1-40 mHz. Axis limits for parameters adapt to actual samples; no clipping to force agreement. Diagnostic-only figures use the same typography.','cold_draws':len(flat),'spectrum_uses_all_cold_draws':True,'intervals':'Pointwise, not simultaneous bands. Contours enclose 68% and 95% sampled mass.','paper_mapping':{'posterior-sgwb.png':'Figure 3: 2.8 flexing-arm result only','posterior-noise-spacecraft.png':'Figure 8: spacecraft-averaged ACC/OMS amplitudes','posterior-spectrum.png':'Figure 6: template component only; RJMCMC not run'},'scope':'No EQ/2.9/RJMCMC/foreground-marginalization results; interpretation follows analysis.json.'})
    write_json(OUT/'status.json',{'status':result['status'],'sampling_complete':True,'numerical_checks_pass':result['numerical_checks_pass'],'posterior_convergence_confirmed':False,'diagnostic_flags_pass':good,'note':'Single-ensemble checks are limited; read analysis.json before interpreting intervals.'})
    print(result['status'],flush=True)
    if not result['numerical_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
