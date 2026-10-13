#!/usr/bin/env python3
"""Verify the latest user-requested overnight checkpoint without advancing MCMC."""
import json
import shutil
import tempfile
import datetime
from pathlib import Path
import numpy as np
from eryn.ensemble import EnsembleSampler
from taiji_sgwb_likelihood import ROOT,load_original_likelihood,evaluate_original,stable_reference
from taiji_sgwb_checkpoint import sha,RestartCompatibleHDFBackend,pack_rng
from taiji_sgwb_formal_checkpoint import checkpoint_record,restore_state,write_json


def main():
    root=ROOT/'runs/taiji-sgwb/template-formal';out=ROOT/'results/taiji-sgwb/template-formal/overnight-pause-checkpoint';out.mkdir(parents=True,exist_ok=True)
    checkpoint,record=checkpoint_record(root)
    for name in ['state.npz','state.json','template_AET_nofg.h5']:shutil.copyfile(checkpoint/name,out/name)
    progress=json.loads((root/'progress.json').read_text())
    checks={'paused_after_update':progress['status']=='STOPPED_AT_CHECKPOINT' and progress['burn_done']==record['burn_done']==record['burn_done'],'production_not_started':record['production_done']==0,'checkpoint_array_hash':sha(out/'state.npz')==record['npz_sha256'],'checkpoint_backend_hash':sha(out/'template_AET_nofg.h5')==record['backend_sha256']}
    ns,_=load_original_likelihood('template_nofg_28t.py')
    with tempfile.TemporaryDirectory(prefix='pause-restore-',dir=ROOT/'runs/taiji-sgwb') as tmp:
        backend=Path(tmp)/'template_AET_nofg.h5';shutil.copyfile(out/backend.name,backend)
        sampler=EnsembleSampler(62,ns['ndim'],ns['log_likelihood'],ns['priors'],tempering_kwargs={'ntemps':6},branch_names=ns['branch_names'],nbranches=3,nleaves_min=ns['nleaf_min'],nleaves_max=ns['nleaf_max'],backend=RestartCompatibleHDFBackend(backend))
        state=restore_state(sampler,out,record,record['provenance']);data=np.load(out/'state.npz')
        for k,a in state.branches_coords.items():checks['restored_coords_'+k]=np.array_equal(a,data['coords_'+k])
        for k,a in state.branches_inds.items():checks['restored_inds_'+k]=np.array_equal(a,data['inds_'+k])
        for k in ['log_like','log_prior','betas']:checks['restored_'+k]=np.array_equal(getattr(state,k),data[k])
        checks['sampler_rng_exact']=pack_rng(sampler.random_state)==record['sampler_rng'];checks['global_rng_exact']=pack_rng(np.random.get_state())==record['numpy_rng']
        checks['adaptive_time_exact']=sampler.temperature_control.time==record['temperature_time']==record['burn_done']
        checks['move_counters_exact']=all(m.num_proposals==r['num_proposals'] and m.time==r['time'] and np.array_equal(m.accepted,np.array(r['accepted'])) for m,r in zip(sampler.moves,record['moves']))
        params=[state.branches_coords[k][0,0,0,:] for k in ['acc','ro','sgwb']]
        ll,cap=evaluate_original(ns,params);ref=stable_reference(cap['csd_hypo'],ns['csd_est'],6,ns['win_bw'])
        checks['paused_likelihood_original_reference']=abs(ll-state.log_like[0,0])<1e-6 and abs(ll-ref['value'])<1e-6
        checks['no_new_chain_steps']=sampler.iteration==0 and progress['burn_done']==record['burn_done']
    checks={k:bool(v) for k,v in checks.items()}
    write_json(out/'validation.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Restore actual paused burn-in into a new sampler without advancing any MCMC transition. Mac-to-Linux portability not yet tested.','checks':checks,'all_checks_pass':all(checks.values()),'burn_done':record['burn_done'],'production_done':record['production_done'],'remaining_burn':1000-record['burn_done'],'remaining_production_transitions':350*12,'original_likelihood_recompute_error':float(abs(ll-state.log_like[0,0])),'Cholesky_error':float(abs(ll-ref['value']))})
    print(f'Pause/restore evidence: {sum(checks.values())}/{len(checks)} passed; no new transitions.')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
