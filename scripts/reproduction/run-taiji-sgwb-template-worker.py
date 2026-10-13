#!/usr/bin/env python3
"""Full original-template short chain in one fresh process; no source patching."""
import argparse
import ast
import datetime
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import time
import warnings
from types import SimpleNamespace
import numpy as np
from taiji_sgwb_likelihood import ROOT,load_original_likelihood
from taiji_sgwb_response import execute_nodes
from taiji_sgwb_checkpoint import sha,save_sidecar,restore_sidecar,state_summary,RestartCompatibleHDFBackend

ORIGINAL=None
COUNTER=None
WARNING_COUNTER=None


def original_template_call(params):
    """Picklable dispatcher; original numerical function and parameters untouched."""
    with COUNTER.get_lock():COUNTER.value+=1
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',RuntimeWarning)
        value=ORIGINAL(params)
    # Record the known Stage 7 determinant warnings; do not alter outputs.
    if caught:
        with WARNING_COUNTER.get_lock():WARNING_COUNTER.value+=len(caught)
        for item in caught:
            if str(item.message) not in ('divide by zero encountered in det','invalid value encountered in det'):
                warnings.warn(str(item.message),item.category)
    if not np.isfinite(value):raise FloatingPointError('Original likelihood returned NaN/Inf')
    return value


def write(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    global ORIGINAL,COUNTER,WARNING_COUNTER
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['initial','resume','continuous'],required=True)
    args=parser.parse_args();start=time.perf_counter()
    cfgpath=ROOT/'configs/reproduction/taiji-sgwb/template-short-chain.json';cfg=json.loads(cfgpath.read_text())
    out=ROOT/'results/taiji-sgwb/template-short-chain'/args.mode;out.mkdir(parents=True,exist_ok=True)
    runroot=ROOT/'runs/taiji-sgwb/template-short-chain'; case=runroot/('continuous' if args.mode=='continuous' else 'split');case.mkdir(parents=True,exist_ok=True)
    filename=case/'template_AET_nofg.h5';sidecar=case/'restart-state.json'
    if args.mode!='resume' and filename.exists():raise FileExistsError('Refuse to overwrite existing chain; archive it before starting a new experiment')
    ns,record=load_original_likelihood(cfg['entry']);ORIGINAL=ns['log_likelihood']
    assert ns['ntemp']==cfg['preserve_original_ntemps']==6 and ns['nwalker']==cfg['preserve_original_nwalkers']==62
    working=case/'demos'/cfg['entry'];working.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/record['source'],working)
    source=ROOT/record['source'];text=source.read_text();tree=ast.parse(text)
    # Original prior-draw initialization statements, names and dimensions intact.
    init=[];active=False
    for node in tree.body:
        names=[x.id for x in node.targets if isinstance(x,ast.Name)] if isinstance(node,ast.Assign) else []
        if 'params0' in names:active=True
        if 'pool' in names:break
        if active:init.append(node)
    original_setup=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in ('pool','backend','sampler') for x in n.targets)]
    ctx=multiprocessing.get_context('fork')
    COUNTER=ctx.Value('q',0);WARNING_COUNTER=ctx.Value('q',0)
    # Original pool/backend/sampler constructor nodes: externally route path,
    # bound process count, and supply a picklable dispatcher to exact function.
    ns.update(npool=cfg['processes'],result_outdir=case,backend_name=filename.name,log_likelihood=original_template_call)
    np.random.seed(cfg['seed'])
    if args.mode!='resume':execute_nodes(source,init,ns)
    # Execute the original explicit fork start-method call, as on upstream.
    for n in tree.body:
        if isinstance(n,ast.Expr) and 'multiprocessing.set_start_method' in ast.get_source_segment(text,n):execute_nodes(source,[n],ns)
    # External namespace proxy changes HDF key-order readback types only.
    original_eryn=ns['eryn']
    ns['eryn']=SimpleNamespace(ensemble=original_eryn.ensemble,backends=SimpleNamespace(HDFBackend=RestartCompatibleHDFBackend))
    execute_nodes(source,original_setup,ns);sampler=ns['sampler'];pool=ns['pool']
    inputs={p:sha(ROOT/p) for p in ['data/processed/taiji-sgwb/response/response.h5','data/processed/taiji-sgwb/preprocessing/template_nofg_28t/preprocessing.h5']}
    provenance={'upstream_commit':cfg['upstream_commit'],'source_sha256':sha(source),'config_sha256':sha(cfgpath),'input_sha256':inputs}
    before=None;restored=None
    if args.mode=='resume':
        before={'iteration':int(sampler.iteration),'sampler_rng_sha256':state_summary(sampler)['sampler_rng_sha256'],'temperature_adaptation_time_before_sidecar':int(sampler.temperature_control.time)}
        restore_sidecar(sampler,filename,sidecar,provenance);restored=state_summary(sampler);state=sampler.get_last_sample()
    else:state=ns['params0']
    initial_steps=cfg['initial_saved_steps'];total=initial_steps if args.mode=='initial' else cfg['resume_saved_steps'] if args.mode=='resume' else initial_steps+cfg['resume_saved_steps']
    start_iteration=int(sampler.iteration);timings=[]
    try:
        for index in range(total):
            t=time.perf_counter();count=COUNTER.value
            state=sampler.run_mcmc(state,1,burn=cfg['burn'],thin_by=cfg['thin_by'],progress=False)
            assert np.all(np.isfinite(state.log_like)) and np.all(np.isfinite(state.log_prior))
            assert all(np.all(np.isfinite(x)) for x in state.branches_coords.values())
            summary=state_summary(sampler)
            timings.append({'iteration':int(sampler.iteration),'seconds':time.perf_counter()-t,'likelihood_calls':int(COUNTER.value-count),'numpy_det_warning_count_total':int(WARNING_COUNTER.value),'cold_log_like_min':float(state.log_like[0].min()),'cold_log_like_max':float(state.log_like[0].max()),'cold_log_like_median':float(np.median(state.log_like[0])),'temperature_adaptation_time':summary['temperature_adaptation_time']})
            checkpoint=save_sidecar(sampler,filename,sidecar,provenance)
            print(f'{args.mode}: saved iteration {sampler.iteration}; step {timings[-1]["seconds"]:.3f} s; calls {timings[-1]["likelihood_calls"]}; temp_time {summary["temperature_adaptation_time"]}',flush=True)
        pool.close();pool.join()
    except BaseException:
        pool.terminate();pool.join();raise
    shutil.copyfile(filename,out/filename.name);shutil.copyfile(sidecar,out/sidecar.name)
    chain=sampler.backend.get_chain();last=state_summary(sampler)
    # Export compact original numeric arrays for independent restart comparison.
    np.savez_compressed(out/'chain-arrays.npz',**{'chain_'+k:v for k,v in chain.items()},**{'inds_'+k:v for k,v in sampler.backend.get_inds().items()},log_like=sampler.backend.get_log_like(),log_prior=sampler.backend.get_log_prior(),betas=sampler.backend.get_betas(),accepted=sampler.backend.accepted,swaps_accepted=sampler.backend.swaps_accepted)
    source_nodes=lambda nodes:[{'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)} for n in nodes]
    write(out/'source-execution.json',{'likelihood_load_record':record,'working_copy':str(working.relative_to(ROOT)),'initialization_executed':args.mode!='resume','original_initialization_nodes':source_nodes(init),'original_sampler_constructor_nodes':source_nodes(original_setup),'overrides':{'npool':cfg['processes'],'HDF_adapter':'RestartCompatibleHDFBackend: only convert key_order ndarray values to lists on readback; original Eryn files unmodified.','backend_path':str(filename.relative_to(ROOT)),'log_likelihood':'Picklable dispatcher delegating directly to original function; captures known warnings and counts calls, rejects nonfinite outputs.','burn':cfg['burn'],'thin_by':cfg['thin_by'],'nsteps':total},'unchanged':{'ntemps':ns['ntemp'],'nwalkers':ns['nwalker'],'dimensions':ns['ndim'],'prior_initialization':'original uniform prior draws','move_class':type(sampler.moves[0]).__name__,'stretch_a':sampler.moves[0].a,'adaptive_tempering':sampler.temperature_control.adaptive}})
    result={'mode':args.mode,'pid':os.getpid(),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':provenance,'config':cfg,'start_iteration':start_iteration,'end_iteration':int(sampler.iteration),'steps':timings,'before_restore':before,'restored_state':restored,'final_state':last,'pool_process_pids':[p.pid for p in pool._pool],'likelihood_calls_total':int(COUNTER.value),'known_determinant_warnings_captured':int(WARNING_COUNTER.value),'chain_shapes':{k:list(v.shape) for k,v in chain.items()},'all_chain_values_finite':all(np.all(np.isfinite(x)) for x in chain.values()),'backend':{'filename':filename.name,'sha256':sha(filename),'bytes':filename.stat().st_size},'worker_seconds':time.perf_counter()-start,'scope':'Real full-grid template short chain only; no convergence, coverage or scientific parameter-recovery claim.'}
    write(out/'worker.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
