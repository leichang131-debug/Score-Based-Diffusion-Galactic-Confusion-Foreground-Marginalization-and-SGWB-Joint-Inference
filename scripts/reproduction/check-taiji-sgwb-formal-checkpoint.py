#!/usr/bin/env python3
"""Synthetic kernel test of new unrecorded-burn checkpoint semantics."""
import json
from pathlib import Path
import tempfile
import numpy as np
from eryn.ensemble import EnsembleSampler
from eryn.prior import uniform_dist
from taiji_sgwb_likelihood import ROOT
from taiji_sgwb_checkpoint import RestartCompatibleHDFBackend,pack_rng
from taiji_sgwb_formal_checkpoint import save_checkpoint,checkpoint_record,restore_state


def toy_log_like(params):return -0.5*sum(float(np.sum(a*a)) for a in params)


def build(path):
    priors={k:{i:uniform_dist(-10,10) for i in range(d)} for k,d in [('acc',6),('ro',6),('sgwb',2)]}
    return EnsembleSampler(62,{'acc':6,'ro':6,'sgwb':2},toy_log_like,priors,tempering_kwargs={'ntemps':6},branch_names=['acc','ro','sgwb'],nbranches=3,nleaves_min={k:1 for k in priors},nleaves_max={k:1 for k in priors},backend=RestartCompatibleHDFBackend(path))


def fresh(path):
    np.random.seed(712601)
    coords={k:np.random.normal(size=(6,62,1,d)) for k,d in [('acc',6),('ro',6),('sgwb',2)]}
    return build(path),coords


def main():
    checks={}
    with tempfile.TemporaryDirectory(prefix='formal-checkpoint-',dir=ROOT/'runs/taiji-sgwb') as tmp:
        p=Path(tmp);ref=p/'reference';split=p/'split';ref.mkdir();split.mkdir()
        s,state=fresh(ref/'template_AET_nofg.h5');state=s.run_mcmc(state,3,burn=6,thin_by=12,progress=False)
        ref_arrays={**s.get_chain(),'log_like':s.get_log_like(),'log_prior':s.get_log_prior(),'betas':s.get_betas(),'accepted':s.backend.accepted,'swaps':s.backend.swaps_accepted}
        ref_rng=pack_rng(s.random_state);ref_global=pack_rng(np.random.get_state());ref_time=s.temperature_control.time
        s,state=fresh(split/'template_AET_nofg.h5');state=s.run_mcmc(state,0,burn=3,progress=False)
        checks['burn_never_stored']=s.iteration==0
        provenance={'synthetic_test_only':True}
        save_checkpoint(split,split/'template_AET_nofg.h5',s,state,3,provenance)
        checkpoint,record=checkpoint_record(split)
        # New sampler/controller and arbitrary disturbed RNG, then sidecar restore.
        np.random.seed(999);s=build(split/'template_AET_nofg.h5');state=restore_state(s,checkpoint,record,provenance)
        checks['restored_unrecorded_burn_time']=s.temperature_control.time==3
        state=s.run_mcmc(state,3,burn=3,thin_by=12,progress=False)
        actual={**s.get_chain(),'log_like':s.get_log_like(),'log_prior':s.get_log_prior(),'betas':s.get_betas(),'accepted':s.backend.accepted,'swaps':s.backend.swaps_accepted}
        for name in ref_arrays:checks['exact_'+name]=np.array_equal(ref_arrays[name],actual[name])
        checks['production_storage_only']=s.iteration==3
        checks['internal_rng_exact']=pack_rng(s.random_state)==ref_rng
        checks['global_rng_exact']=pack_rng(np.random.get_state())==ref_global
        checks['adaptation_time_exact']=s.temperature_control.time==ref_time==42
        # A new generation after production is also read-back verified.
        save_checkpoint(split,split/'template_AET_nofg.h5',s,state,6,provenance);p2,r2=checkpoint_record(split)
        checks['production_checkpoint_metadata']=r2['burn_done']==6 and r2['production_done']==3
    checks={k:bool(v) for k,v in checks.items()}
    out=ROOT/'results/taiji-sgwb/template-formal';out.mkdir(parents=True,exist_ok=True)
    value={'scope':'Synthetic Gaussian kernel test for unrecorded-burn and production checkpoint semantics only; not SGWB scientific inference. Real Stage 8 exact restart remains the scientific-interface reference.','checks':checks,'all_checks_pass':all(checks.values())}
    (out/'checkpoint-interface-check.json').write_text(json.dumps(value,indent=2)+'\n')
    print(f'Formal checkpoint interface: {sum(checks.values())}/{len(checks)} passed (synthetic).')
    if not value['all_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
