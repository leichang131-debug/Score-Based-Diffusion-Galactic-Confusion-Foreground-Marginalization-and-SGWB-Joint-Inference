#!/usr/bin/env python3
"""Numerical validation of real first-ten unrecorded formal burn-in states."""
import json
import numpy as np
from taiji_sgwb_likelihood import ROOT,load_original_likelihood,evaluate_original,stable_reference
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_formal_checkpoint import write_json


def main():
    out=ROOT/'results/taiji-sgwb/template-formal/initial-burn-check'
    record=json.loads((out/'state.json').read_text());data=np.load(out/'state.npz');progress=json.loads((out/'progress.json').read_text())
    checks={'ten_real_burn_no_production':record['burn_done']==progress['burn_done']==10 and record['production_done']==progress['production_saved']==0,'exact_snapshot_hash':sha(out/'state.npz')==record['npz_sha256'],'all_arrays_finite':all(np.all(np.isfinite(data[k])) for k in data.files),'four_pool_workers':len(progress['pool_pids'])==4,'six_temperatures_62_walkers':data['log_like'].shape==(6,62)}
    ns,_=load_original_likelihood('template_nofg_28t.py');values=[]
    for temp,walker in [(0,0),(5,61)]:
        params=[data['coords_'+name][temp,walker,0,:] for name in ['acc','ro','sgwb']]
        ll,cap=evaluate_original(ns,params);ref=stable_reference(cap['csd_hypo'],ns['csd_est'],6,ns['win_bw'])
        prior=sum(float(ns['priors'][k][i].logpdf(x)) for k,v in zip(['acc','ro','sgwb'],params) for i,x in enumerate(v))
        value={'temperature':temp,'walker':walker,'stored_original_absolute_error':abs(ll-float(data['log_like'][temp,walker])),'Cholesky_absolute_error':abs(ll-ref['value']),'prior_absolute_error':abs(prior-float(data['log_prior'][temp,walker]))};values.append(value)
        checks[f'saved_state_{temp}_{walker}']=value['stored_original_absolute_error']<1e-6 and value['Cholesky_absolute_error']<1e-6 and value['prior_absolute_error']<1e-10 and ref['minimum_scaled_eigenvalue']>0
    checks={k:bool(v) for k,v in checks.items()};write_json(out/'validation.json',{'scope':'Real unrecorded formal burn-in only; no production posterior yet.','checks':checks,'all_checks_pass':all(checks.values()),'recomputed':values})
    print(f'Formal real burn-in: {sum(checks.values())}/{len(checks)} passed.')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
