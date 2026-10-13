#!/usr/bin/env python3
"""Prepare and validate selected data without running any MCMC."""
import json
import shutil
import time
import numpy as np
import h5py
from taiji_sgwb_mini import ROOT,CFG,OUT,WORK,CACHE,NAMES,subset,load_mini
from taiji_sgwb_likelihood import load_original_likelihood,evaluate_original,independent_model,stable_reference
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_preprocessing import digest_array
from taiji_sgwb_formal_checkpoint import write_json


def main():
    start=time.perf_counter();cfg=json.loads(CFG.read_text());OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    assert json.loads((ROOT/'results/taiji-sgwb/template-formal/status.json').read_text())['status']=='PAUSED_BY_USER'
    original,record=load_original_likelihood(cfg['entry']);arrays,selection=subset(original,cfg)
    source=ROOT/record['source'];working=WORK/'demos'/cfg['entry'];working.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,working)
    fullpaths=['data/processed/taiji-sgwb/response/response.h5','data/processed/taiji-sgwb/preprocessing/template_nofg_28t/preprocessing.h5']
    metadata={'selection':selection,'source_sha256':sha(source),'source_commit':cfg['upstream_commit'],'full_cache_sha256':{p:sha(ROOT/p) for p in fullpaths},'link_order':['12','13','23','21','31','32'],'channels':['A','E','T'],'nperbin':original['nperbin'],'win_bw':original['win_bw'],'known_foreground_subtracted':True,'scope':cfg['scope']}
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    with h5py.File(CACHE,'w') as h:
        for k,v in arrays.items():h[k]=v
        h.attrs['metadata']=json.dumps(metadata);h.attrs['nperbin']=original['nperbin'];h.attrs['win_bw']=original['win_bw']
    checks={'same_name_original_copy':working.name==source.name and sha(working)==sha(source),'all_selected_arrays_finite':all(np.all(np.isfinite(a)) for a in arrays.values()),'full_complex_AET_csd':arrays['csd_est'].shape==(3,3,8,512),'all_12_noise_factors':arrays['acc_corr_factor'].shape==(3,3,6,8,512) and arrays['ro_corr_factor'].shape==(3,3,6,8,512),'original_bin_and_window_weight':metadata['nperbin']==6,'no_full_year_rescaling':True}
    week=np.array(selection['week_indices']);freq=np.array(selection['frequency_indices'])
    checks['frequency_time_exact_original']=np.array_equal(arrays['f_est'],original['f_est'][freq]) and np.array_equal(arrays['t_seg'],original['t_seg'][week])
    for k in NAMES:checks['selected_original_'+k]=np.array_equal(arrays[k],subset(original,cfg)[0][k])
    original.update(arrays)
    ns,small_record=load_mini();checks['small_loader_exact_arrays']=all(np.array_equal(ns[k],arrays[k]) for k in NAMES)
    truth=json.loads((ROOT/'results/taiji-sgwb/data/validation.json').read_text())['injected_parameters'];links=metadata['link_order'];acc=np.array([truth['noise/ACC_noise_amplitudes/'+l] for l in links]);ro=np.array([truth['noise/OMS_noise_amplitudes/'+l] for l in links]);sgwb=np.array([truth['sgwb/omega0'],truth['sgwb/n']]);rng=np.random.default_rng(cfg['seed']);tests=[]
    for i in range(6):
        aa,rr,ss=(acc,ro,sgwb) if i==0 else (rng.uniform(.75,1.25,6)*3e-15,rng.uniform(.75,1.25,6)*8e-12,np.array([rng.uniform(1e-14,5e-11),rng.uniform(-1,2)]))
        params=[aa,rr,ss];ll,cap=evaluate_original(ns,params);original_value,_=evaluate_original(original,params);omega=ss[0]*(ns['f_est']/1e-3)**ss[1];model=independent_model(ns,aa,rr,omega);ref=stable_reference(cap['csd_hypo'],ns['csd_est'],6,ns['win_bw'])
        diff=float(np.linalg.norm(model-cap['csd_hypo'])/np.linalg.norm(model))
        checks[f'case_{i}_same_original_function']=ll==original_value
        checks[f'case_{i}_model_and_likelihood']=np.isfinite(ll) and diff<1e-12 and abs(ll-ref['value'])<1e-6 and ref['minimum_scaled_eigenvalue']>0
        tests.append({'case':i,'original_log_likelihood':ll,'Cholesky_error':abs(ll-ref['value']),'model_relative_error':diff,'minimum_scaled_eigenvalue':ref['minimum_scaled_eigenvalue'],'maximum_condition_number':ref['maximum_condition_number']})
    csd=np.moveaxis(arrays['csd_est'],[0,1],[-2,-1]);scale=np.max(np.diagonal(csd,axis1=-2,axis2=-1).real,axis=-1)
    checks['selected_data_hermitian']=np.max(np.abs(csd-csd.conj().swapaxes(-1,-2))/scale[...,None,None])<1e-12
    checks['selected_data_positive']=np.linalg.eigvalsh(csd/scale[...,None,None]).min()>0
    sm=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text());checks['all_19_original_files_preserved']=all(sha(ROOT/x['repository_path'])==x['sha256'] for x in sm['files'])
    checks={k:bool(v) for k,v in checks.items()};write_json(OUT/'selection.json',metadata);write_json(OUT/'source-loading.json',small_record)
    write_json(OUT/'preparation.json',{'scope':cfg['scope'],'checks':checks,'all_checks_pass':all(checks.values()),'numerical_tests':tests,'cache':{'path':str(CACHE.relative_to(ROOT)),'sha256':sha(CACHE),'bytes':CACHE.stat().st_size},'array_sha256':{k:digest_array(a) for k,a in arrays.items()},'seconds':time.perf_counter()-start})
    print(f'Mini preparation: {sum(checks.values())}/{len(checks)} passed; {selection["all_low_frequency_bins_retained"]} low-frequency + {selection["high_frequency_selected"]} high-frequency bins; cache {CACHE.stat().st_size} bytes.')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
