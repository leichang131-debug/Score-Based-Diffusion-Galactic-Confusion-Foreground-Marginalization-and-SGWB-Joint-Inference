#!/usr/bin/env python3
"""Original 1000-burn/350-thinned template schedule with recoverable checkpoints."""
import argparse
import ast
import datetime
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import time
from types import SimpleNamespace
import numpy as np
import runpy
from taiji_sgwb_likelihood import ROOT,load_original_likelihood
from taiji_sgwb_response import execute_nodes
from taiji_sgwb_checkpoint import sha,RestartCompatibleHDFBackend
from taiji_sgwb_formal_checkpoint import write_json,save_checkpoint,checkpoint_record,restore_state

# Reuse the tested dispatcher without modifying Stage 8 files or package source.
import importlib.util
spec=importlib.util.spec_from_file_location('taiji_template_dispatch',ROOT/'scripts/reproduction/run-taiji-sgwb-template-worker.py')
import sys
DISPATCH=importlib.util.module_from_spec(spec);sys.modules[spec.name]=DISPATCH;spec.loader.exec_module(DISPATCH)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--transition-limit',type=int);args=parser.parse_args()
    cfgpath=ROOT/'configs/reproduction/taiji-sgwb/template-formal.json';cfg=json.loads(cfgpath.read_text())
    root=ROOT/'runs/taiji-sgwb/template-formal';root.mkdir(parents=True,exist_ok=True)
    backend=root/'template_AET_nofg.h5';start=time.perf_counter();burn_done=0
    if not args.resume and backend.exists():raise FileExistsError('Existing formal chain; use --resume or archive it')
    ns,record=load_original_likelihood(cfg['entry']);DISPATCH.ORIGINAL=ns['log_likelihood']
    assert ns['nwalker']==cfg['nwalkers']==62 and ns['ntemp']==cfg['ntemps']==6 and ns['nstep']==cfg['saved_samples']==350
    source=ROOT/record['source'];text=source.read_text();tree=ast.parse(text)
    working=root/'demos'/cfg['entry'];working.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,working)
    original_final=tree.body[-1]
    assert ast.get_source_segment(text,original_final).endswith('burn=1000, thin_by=12, progress=True)')
    init=[];active=False
    for node in tree.body:
        names=[x.id for x in node.targets if isinstance(x,ast.Name)] if isinstance(node,ast.Assign) else []
        if 'params0' in names:active=True
        if 'pool' in names:break
        if active:init.append(node)
    setup=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('pool','backend','sampler') for t in n.targets)]
    for n in tree.body:
        if isinstance(n,ast.Expr) and 'multiprocessing.set_start_method' in ast.get_source_segment(text,n):execute_nodes(source,[n],ns)
    ctx=multiprocessing.get_context('fork');DISPATCH.COUNTER=ctx.Value('q',0);DISPATCH.WARNING_COUNTER=ctx.Value('q',0)
    np.random.seed(cfg['seed'])
    if not args.resume:execute_nodes(source,init,ns)
    inputs={p:sha(ROOT/p) for p in ['data/processed/taiji-sgwb/response/response.h5','data/processed/taiji-sgwb/preprocessing/template_nofg_28t/preprocessing.h5']}
    # Formal checkpoint implementation and dispatcher are part of restore provenance.
    scripts=['scripts/reproduction/taiji_sgwb_formal_checkpoint.py','scripts/reproduction/run-taiji-sgwb-template-formal-worker.py','scripts/reproduction/run-taiji-sgwb-template-worker.py','scripts/reproduction/taiji_sgwb_checkpoint.py']
    provenance={'source_sha256':sha(source),'config_sha256':sha(cfgpath),'upstream_commit':cfg['upstream_commit'],'inputs':inputs,'adapter_sha256':{p:sha(ROOT/p) for p in scripts}}
    restore=None
    if args.resume:
        p,restore=checkpoint_record(root);assert restore['provenance']==provenance
        # Restore the last complete immutable pair, not a possibly partial live HDF.
        shutil.copyfile(p/'template_AET_nofg.h5',backend);burn_done=restore['burn_done']
    eryn=ns['eryn'];ns.update(npool=cfg['processes'],result_outdir=root,backend_name=backend.name,log_likelihood=DISPATCH.original_template_call,eryn=SimpleNamespace(ensemble=eryn.ensemble,backends=SimpleNamespace(HDFBackend=RestartCompatibleHDFBackend)))
    execute_nodes(source,setup,ns);sampler=ns['sampler'];pool=ns['pool']
    state=restore_state(sampler,p,restore,provenance) if restore else ns['params0']
    nodes=lambda values:[{'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)} for n in values]
    write_json(root/'source-execution.json',{'likelihood':record,'initialization_nodes':nodes(init),'constructor_nodes':nodes(setup),'original_final_call':ast.get_source_segment(text,original_final),'working_copy':str(working.relative_to(ROOT)),'adaptation':'Original kernel and burn/store semantics; segmented calls permit immutable checkpoints. Pool size=4; external HDF key-order readback adapter and tested picklable dispatcher. No source or installed Eryn patch.','provenance':provenance})
    steps_in_process=0;timings=[];status='RUNNING'
    def progress(phase,seconds,calls):
        done=int(burn_done+sampler.iteration*cfg['thin_by']);remaining=cfg['burn']+cfg['saved_samples']*cfg['thin_by']-done
        record={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'phase':phase,'pid':os.getpid(),'pool_pids':[p.pid for p in pool._pool],'burn_done':burn_done,'production_saved':int(sampler.iteration),'production_target':cfg['saved_samples'],'transitions_done':done,'transitions_target':5200,'latest_seconds':seconds,'latest_likelihood_calls':calls,'process_likelihood_calls':int(DISPATCH.COUNTER.value),'known_determinant_warning_count':int(DISPATCH.WARNING_COUNTER.value),'process_wall_seconds':time.perf_counter()-start,'checkpoint':json.loads((root/'latest-checkpoint.json').read_text()) if (root/'latest-checkpoint.json').exists() else None,'remaining_transitions':remaining,'convergence':'NOT ASSESSED until completed analysis','provenance':provenance}
        if timings:record['median_recent_seconds_per_transition']=float(np.median(timings[-20:]));record['estimated_remaining_hours']=remaining*record['median_recent_seconds_per_transition']/3600
        if hasattr(state,'log_like'):record.update(cold_log_like_median=float(np.median(state.log_like[0])),cold_log_like_max=float(state.log_like[0].max()))
        write_json(root/'progress.json',record)
    progress('initializing',0,0)
    try:
        # Original burn-in: sample(store=False, thin_by=1), no HDF chain rows.
        while burn_done<cfg['burn']:
            t=time.perf_counter();before=DISPATCH.COUNTER.value
            state=sampler.run_mcmc(state,0,burn=1,thin_by=1,progress=False)
            burn_done+=1;steps_in_process+=1;seconds=time.perf_counter()-t;timings.append(seconds)
            assert sampler.iteration==0 and np.all(np.isfinite(state.log_like)) and np.all(np.isfinite(state.log_prior))
            if burn_done%cfg['burn_checkpoint_every']==0:save_checkpoint(root,backend,sampler,state,burn_done,provenance)
            progress('burn-in',seconds,int(DISPATCH.COUNTER.value-before))
            print(f'burn {burn_done}/{cfg["burn"]}: {seconds:.3f} s; calls {DISPATCH.COUNTER.value-before}',flush=True)
            if (root/'stop-requested').exists() or args.transition_limit and steps_in_process>=args.transition_limit:
                status='STOPPED_AT_CHECKPOINT';save_checkpoint(root,backend,sampler,state,burn_done,provenance) if burn_done%cfg['burn_checkpoint_every'] else None;break
        if status=='RUNNING':
            while sampler.iteration<cfg['saved_samples']:
                t=time.perf_counter();before=DISPATCH.COUNTER.value
                state=sampler.run_mcmc(state,1,burn=0,thin_by=cfg['thin_by'],progress=False)
                seconds=time.perf_counter()-t;timings.append(seconds/cfg['thin_by']);steps_in_process+=cfg['thin_by']
                assert np.all(np.isfinite(state.log_like)) and np.all(np.isfinite(state.log_prior))
                if sampler.iteration%cfg['production_checkpoint_every']==0:save_checkpoint(root,backend,sampler,state,burn_done,provenance)
                progress('production',seconds,int(DISPATCH.COUNTER.value-before));print(f'production {sampler.iteration}/{cfg["saved_samples"]}: {seconds:.3f} s',flush=True)
                if (root/'stop-requested').exists() or args.transition_limit and steps_in_process>=args.transition_limit:
                    status='STOPPED_AT_CHECKPOINT'
                    if sampler.iteration%cfg['production_checkpoint_every']:save_checkpoint(root,backend,sampler,state,burn_done,provenance)
                    break
        if status=='RUNNING':status='SAMPLING_COMPLETE'
        progress('complete' if status=='SAMPLING_COMPLETE' else 'checkpoint-stop',0,0)
        pool.close();pool.join()
    except BaseException as e:
        status='FAILED';progress('exception',0,0);write_json(root/'failure.json',{'error':repr(e),'last_complete_checkpoint':json.loads((root/'latest-checkpoint.json').read_text()) if (root/'latest-checkpoint.json').exists() else None});pool.terminate();pool.join();raise
    print(status,flush=True)

if __name__=='__main__':main()
