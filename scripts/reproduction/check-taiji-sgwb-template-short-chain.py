#!/usr/bin/env python3
"""Validate real saved/restored chain against continuous same-seed control."""
import json
from pathlib import Path
import numpy as np
import h5py
from eryn.backends import HDFBackend
from taiji_sgwb_likelihood import ROOT,load_original_likelihood,evaluate_original,stable_reference
from taiji_sgwb_checkpoint import sha

OUT=ROOT/'results/taiji-sgwb/template-short-chain'


def main():
    checks={};check=lambda k,x:checks.update({k:bool(x)})
    cases={m:json.loads((OUT/m/'worker.json').read_text()) for m in ('initial','resume','continuous')}
    runs={m:json.loads((OUT/m/'run.json').read_text()) for m in cases}
    cfg=json.loads((ROOT/'configs/reproduction/taiji-sgwb/template-short-chain.json').read_text())
    arrays={m:np.load(OUT/m/'chain-arrays.npz') for m in cases}
    for mode,w in cases.items():
        check(mode+'_successful_process_exit',runs[mode]['returncode']==0 and runs[mode]['process_exited_and_reaped'])
        with (OUT/mode/'resources.csv').open() as f:
            import csv
            resource=list(csv.DictReader(f))
        check(mode+'_two_worker_pool_observed',w['config']['processes']==2 and len(runs[mode]['observed_child_pids'])>=2 and sum(int(x['family_process_count'])==3 for x in resource if float(x['seconds'])>=2)>=5 and max(int(x['family_process_count']) for x in resource if float(x['seconds'])>=2)==3)
        check(mode+'_resource_sampling',runs[mode]['peak_parent_rss_kib']>0 and runs[mode]['monitoring_error'] is None)
        check(mode+'_original_ensemble_size',w['config']['preserve_original_ntemps']==6 and w['config']['preserve_original_nwalkers']==62)
        check(mode+'_all_numeric_arrays_finite',all(np.all(np.isfinite(arrays[mode][k])) for k in arrays[mode].files))
        check(mode+'_finite_real_likelihood_and_prior',np.all(np.isfinite(arrays[mode]['log_like'])) and np.all(np.isfinite(arrays[mode]['log_prior'])))
        check(mode+'_actual_proposals_and_calls',all(x['likelihood_calls']>0 for x in w['steps']))
        check(mode+'_backend_file_integrity',sha(OUT/mode/w['backend']['filename'])==w['backend']['sha256'])
        b=HDFBackend(OUT/mode/w['backend']['filename'],read_only=True)
        check(mode+'_separate_process_HDF_readback',b.iteration==w['end_iteration'] and np.array_equal(b.get_log_like(),arrays[mode]['log_like']))
        check(mode+'_backend_equals_NPZ_all_fields',all(np.array_equal(b.get_chain()[key],arrays[mode]['chain_'+key]) and np.array_equal(b.get_inds()[key],arrays[mode]['inds_'+key]) for key in b.branch_names) and np.array_equal(b.get_log_prior(),arrays[mode]['log_prior']) and np.array_equal(b.get_betas(),arrays[mode]['betas']) and np.array_equal(b.accepted,arrays[mode]['accepted']) and np.array_equal(b.swaps_accepted,arrays[mode]['swaps_accepted']))
        record=json.loads((OUT/mode/'source-execution.json').read_text())
        check(mode+'_default_original_move',record['unchanged']['move_class']=='StretchMove' and record['unchanged']['stretch_a']==2.0 and record['unchanged']['adaptive_tempering'])
        check(mode+'_working_original_identical',sha(ROOT/record['working_copy'])==w['provenance']['source_sha256'])
    check('initial_0_to_4',cases['initial']['start_iteration']==0 and cases['initial']['end_iteration']==4)
    check('resume_4_to_8',cases['resume']['start_iteration']==4 and cases['resume']['end_iteration']==8)
    check('continuous_0_to_8',cases['continuous']['start_iteration']==0 and cases['continuous']['end_iteration']==8)
    check('three_distinct_process_PIDs',len({x['pid'] for x in runs.values()})==3)
    check('initial_exit_precedes_resume_start',runs['initial']['ended_utc']<=runs['resume']['started_utc'])
    check('saved_restored_state_all_fields_exact',cases['initial']['final_state']==cases['resume']['restored_state'])
    check('adaptation_time_restored',cases['resume']['before_restore']['temperature_adaptation_time_before_sidecar']==0 and cases['resume']['restored_state']['temperature_adaptation_time']==cases['initial']['final_state']['temperature_adaptation_time']>0)
    check('sampler_rng_restored_from_original_HDF',cases['resume']['before_restore']['sampler_rng_sha256']==cases['initial']['final_state']['sampler_rng_sha256'])
    comparisons={}
    for name in arrays['resume'].files:
        split=arrays['resume'][name];ref=arrays['continuous'][name]
        exact=np.array_equal(split,ref)
        comparisons[name]={'shape':list(split.shape),'bitwise_equal':bool(exact),'max_absolute_difference':float(np.max(np.abs(split.astype(float)-ref.astype(float))))}
        check('resumed_equals_continuous_'+name,exact)
        if name.startswith('chain_') or name.startswith('inds_') or name in ('log_like','log_prior','betas'):
            check('initial_equals_continuous_prefix_'+name,np.array_equal(arrays['initial'][name],ref[:4]))
            check('resume_preserves_saved_prefix_'+name,np.array_equal(arrays['initial'][name],split[:4]))
    check('final_rng_temperature_move_state_exact',cases['resume']['final_state']==cases['continuous']['final_state'])
    check('accepted_some_proposals',np.sum(arrays['resume']['accepted'])>0)
    check('accepted_some_temperature_swaps',np.sum(arrays['resume']['swaps_accepted'])>0)
    check('accepted_counts_appended_not_reset',np.all(arrays['resume']['accepted']>=arrays['initial']['accepted']))
    check('temperature_ladder_valid',np.all(arrays['resume']['betas'][:,0]==1) and np.all(np.diff(arrays['resume']['betas'],axis=1)<=0) and np.all(arrays['resume']['betas']>=0))
    check('all_branches_present',all('chain_'+name in arrays['resume'].files for name in ('acc','ro','sgwb')))
    # Re-evaluate six actually saved states using original function and original
    # prior densities in this independent process, plus Cholesky reference.
    ns,_=load_original_likelihood('template_nofg_28t.py');recomputed=[]
    for step,temp,walker in [(0,0,0),(0,5,61),(3,0,31),(4,5,12),(7,0,0),(7,5,61)]:
        params=[arrays['resume']['chain_'+name][step,temp,walker,0,:] for name in ('acc','ro','sgwb')]
        original,cap=evaluate_original(ns,params)
        expected=arrays['resume']['log_like'][step,temp,walker]
        prior=sum(float(ns['priors'][name][i].logpdf(x)) for name,value in zip(('acc','ro','sgwb'),params) for i,x in enumerate(value))
        ref=stable_reference(cap['csd_hypo'],ns['csd_est'],ns['nperbin'],ns['win_bw'])
        row={'step':step+1,'temperature_index':temp,'walker':walker,'stored':float(expected),'original':original,'reference':ref['value'],'prior_absolute_error':abs(prior-arrays['resume']['log_prior'][step,temp,walker]),'reference_absolute_error':abs(ref['value']-expected),'maximum_condition_number':ref['maximum_condition_number']};recomputed.append(row)
        check(f'saved_state_{step}_{temp}_{walker}_likelihood_prior',abs(original-expected)<1e-6 and row['prior_absolute_error']<1e-10 and row['reference_absolute_error']<1e-6 and ref['minimum_scaled_eigenvalue']>0)
    # Chain movement and acceptance are diagnostics only, never convergence.
    accepted=arrays['resume']['accepted'];iters=cases['resume']['end_iteration']
    fraction=accepted/iters
    diagnostics={'saved_steps':iters,'transitions_per_temperature_walker':iters,'total_ensemble_walker_transition_attempts':iters*6*62,'acceptance_mean_all_temperatures':float(fraction.mean()),'acceptance_mean_cold':float(fraction[0].mean()),'walkers_with_at_least_one_accepted_proposal':int(np.sum(accepted>0)),'total_temperature_swaps_accepted':float(np.sum(arrays['resume']['swaps_accepted'])),'median_step_seconds_resume':float(np.median([x['seconds'] for x in cases['resume']['steps']])),'warnings':'Known environment complex-det warnings are recorded as counts by the dispatcher; source outputs are unchanged.','convergence':'NOT ASSESSED: eight steps, no burn-in, insufficient for ESS/R-hat/credible intervals or unbiasedness.'}
    source_manifest=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text())
    check('all_original_19_files_unchanged',len(source_manifest['files'])==19 and all(sha(ROOT/x['repository_path'])==x['sha256'] for x in source_manifest['files']))
    check('all_3_run_provenance_identical',cases['initial']['provenance']==cases['resume']['provenance']==cases['continuous']['provenance'])
    check('input_caches_unchanged',all(sha(ROOT/p)==h for p,h in cases['initial']['provenance']['input_sha256'].items()))
    value={'schema_version':1,'scope':'Actual original-template short chain, real process exit/restart, exact seeded continuous control and saved-state numerical checks; not a converged posterior.','checks':checks,'all_checks_pass':all(checks.values()),'array_comparisons':comparisons,'recomputed_saved_states':recomputed,'diagnostics':diagnostics,'config':cfg}
    (OUT/'validation.json').write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(f'Stage 8 validation: {sum(checks.values())}/{len(checks)} passed. Exact restart vs continuous comparisons: {sum(x["bitwise_equal"] for x in comparisons.values())}/{len(comparisons)}.')
    if not value['all_checks_pass']:
        print('Failed:',[k for k,x in checks.items() if not x]);raise SystemExit(1)

if __name__=='__main__':main()
