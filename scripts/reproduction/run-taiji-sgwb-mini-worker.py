#!/usr/bin/env python3
"""One-CPU selected-data workflow, original kernel, fresh prior initialization."""
import argparse
import ast
import datetime
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
import numpy as np
from taiji_sgwb_mini import ROOT,CFG,OUT,WORK,CACHE,load_mini,provenance
from taiji_sgwb_checkpoint import RestartCompatibleHDFBackend,sha,pack_rng
from taiji_sgwb_response import execute_nodes
from taiji_sgwb_formal_checkpoint import write_json,save_checkpoint,checkpoint_record,restore_state

spec=importlib.util.spec_from_file_location('mini_template_dispatch',ROOT/'scripts/reproduction/run-taiji-sgwb-template-worker.py');DISPATCH=importlib.util.module_from_spec(spec);sys.modules[spec.name]=DISPATCH;spec.loader.exec_module(DISPATCH)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['benchmark','first','resume'],required=True);args=parser.parse_args()
    cfg=json.loads(CFG.read_text());start=time.perf_counter();WORK.mkdir(parents=True,exist_ok=True);out=OUT/args.mode;out.mkdir(parents=True,exist_ok=True)
    backend=WORK/'template_AET_nofg.h5';ns,record=load_mini();DISPATCH.ORIGINAL=ns['log_likelihood'];source=ROOT/record['source'];text=source.read_text();tree=ast.parse(text)
    init=[];active=False
    for n in tree.body:
        names=[t.id for t in n.targets if isinstance(t,ast.Name)] if isinstance(n,ast.Assign) else []
        if 'params0' in names:active=True
        if 'pool' in names:break
        if active:init.append(n)
    setup=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['pool','backend','sampler'] for t in n.targets)]
    for n in tree.body:
        if isinstance(n,ast.Expr) and 'multiprocessing.set_start_method' in ast.get_source_segment(text,n):execute_nodes(source,[n],ns)
    ctx=multiprocessing.get_context('fork');DISPATCH.COUNTER=ctx.Value('q',0);DISPATCH.WARNING_COUNTER=ctx.Value('q',0)
    np.random.seed(cfg['seed']);prov=provenance();burn_done=0;restore=None
    if args.mode=='benchmark':
        if backend.exists():raise FileExistsError('Refuse to overwrite mini experiment')
        execute_nodes(source,init,ns)
    else:
        p,restore=checkpoint_record(WORK);assert restore['provenance']==prov;burn_done=restore['burn_done'];shutil.copyfile(p/backend.name,backend)
    eryn=ns['eryn'];ns.update(result_outdir=WORK,backend_name=backend.name,log_likelihood=DISPATCH.original_template_call,eryn=SimpleNamespace(ensemble=eryn.ensemble,backends=SimpleNamespace(HDFBackend=RestartCompatibleHDFBackend)))
    execute_nodes(source,setup,ns);sampler=ns['sampler'];pool=ns['pool']
    state=restore_state(sampler,p,restore,prov) if restore else ns['params0']
    start_state={'burn_done':burn_done,'production_done':int(sampler.iteration),'temperature_time':int(sampler.temperature_control.time),'sampler_rng':pack_rng(sampler.random_state),'global_rng':pack_rng(np.random.get_state())}
    phase_rows=[];budget_spent=json.loads((WORK/'progress.json').read_text()).get('sampling_wall_total',0) if restore else 0
    restored_checks={}
    if restore:
        saved=np.load(p/'state.npz')
        restored_checks={'coordinates':all(np.array_equal(state.branches_coords[k],saved['coords_'+k]) for k in ns['branch_names']),'log_like':np.array_equal(state.log_like,saved['log_like']),'log_prior':np.array_equal(state.log_prior,saved['log_prior']),'betas':np.array_equal(state.betas,saved['betas']),'temperature_time':sampler.temperature_control.time==restore['temperature_time'],'sampler_rng':pack_rng(sampler.random_state)==restore['sampler_rng'],'global_rng':pack_rng(np.random.get_state())==restore['numpy_rng'],'move_counters':all(m.num_proposals==r['num_proposals'] and np.array_equal(m.accepted,np.array(r['accepted'])) for m,r in zip(sampler.moves,restore['moves']))}
        assert all(restored_checks.values())
    def snapshot(status):
        write_json(WORK/'progress.json',{'status':status,'mode':args.mode,'pid':os.getpid(),'pool_pids':[p.pid for p in pool._pool],'burn_done':burn_done,'production_done':int(sampler.iteration),'sampling_wall_total':budget_spent+time.perf_counter()-start,'process_likelihood_calls':int(DISPATCH.COUNTER.value),'known_warning_count':int(DISPATCH.WARNING_COUNTER.value),'scope':cfg['scope'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    def save_if_missing():
        directory=WORK/'checkpoints'/f'burn-{burn_done:04d}-production-{sampler.iteration:04d}'
        if not directory.exists():save_checkpoint(WORK,backend,sampler,state,burn_done,prov)
    target_burn=cfg['first_speed_check_at'] if args.mode=='benchmark' else cfg['burn']
    target_prod=0 if args.mode=='benchmark' else cfg['restart_after_production'] if args.mode=='first' else cfg['production_steps']
    status='RUNNING';snapshot(status)
    try:
        while burn_done<target_burn or sampler.iteration<target_prod:
            t=time.perf_counter();calls=DISPATCH.COUNTER.value;phase='burn' if burn_done<target_burn else 'production'
            if phase=='burn':state=sampler.run_mcmc(state,0,burn=1,thin_by=1,progress=False);burn_done+=1
            else:state=sampler.run_mcmc(state,1,burn=0,thin_by=1,progress=False)
            assert np.all(np.isfinite(state.log_like)) and np.all(np.isfinite(state.log_prior))
            row={'phase':phase,'burn_done':burn_done,'production_done':int(sampler.iteration),'seconds':time.perf_counter()-t,'likelihood_calls':int(DISPATCH.COUNTER.value-calls),'cold_median_log_like':float(np.median(state.log_like[0]))};phase_rows.append(row)
            boundary=burn_done if phase=='burn' else sampler.iteration
            if boundary%cfg['checkpoint_every']==0:save_if_missing();snapshot(status);print(f'{args.mode} {phase}: burn={burn_done}, stored={sampler.iteration}; {row["seconds"]:.4f} s',flush=True)
            if phase=='burn' and burn_done==cfg['burn']:
                write_json(WORK/'burn-exit-move.json',{'accepted':sampler.moves[0].accepted.tolist(),'num_proposals':int(sampler.moves[0].num_proposals)})
            if budget_spent+time.perf_counter()-start>cfg['sampling_wall_budget_seconds'] or (WORK/'stop-requested').exists():status='BUDGET_OR_USER_STOP';break
        if status=='RUNNING':status='BENCHMARK_COMPLETE' if args.mode=='benchmark' else 'MIDCHAIN_CHECKPOINT' if args.mode=='first' else 'SAMPLING_COMPLETE'
        save_if_missing();snapshot(status);pool.close();pool.join()
    except BaseException:
        pool.terminate();pool.join();raise
    cp,checkpoint=checkpoint_record(WORK);shutil.copyfile(backend,out/backend.name);shutil.copyfile(cp/'state.json',out/'state.json');shutil.copyfile(cp/'state.npz',out/'state.npz')
    if (WORK/'burn-exit-move.json').exists():shutil.copyfile(WORK/'burn-exit-move.json',OUT/'burn-exit-move.json')
    source_nodes=lambda nodes:[{'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)} for n in nodes]
    write_json(out/'source-execution.json',{'original_likelihood_record':record,'original_initialization_nodes':source_nodes(init),'initialization_executed':args.mode=='benchmark','constructor_nodes':source_nodes(setup),'overrides':{'nwalker':32,'ntemp':6,'npool':1,'data':'Exact selected original week/frequency arrays; no likelihood reweighting','burn':300,'production_steps':1000,'thin_by':1},'move':type(sampler.moves[0]).__name__,'stretch_a':sampler.moves[0].a})
    write_json(out/'worker.json',{'mode':args.mode,'pid':os.getpid(),'start_state':start_state,'end_burn':burn_done,'end_production':int(sampler.iteration),'status':status,'steps':phase_rows,'wall_seconds':time.perf_counter()-start,'restored_checks':{k:bool(v) for k,v in restored_checks.items()},'likelihood_calls':int(DISPATCH.COUNTER.value),'known_det_warning_count':int(DISPATCH.WARNING_COUNTER.value),'checkpoint':checkpoint,'backend_sha256':sha(out/backend.name),'scope':cfg['scope']})
    if args.mode=='benchmark':
        speed=float(np.median([r['seconds'] for r in phase_rows[5:]]));remaining=cfg['burn']-burn_done+cfg['production_steps'];estimated=speed*remaining
        write_json(OUT/'speed-check.json',{'warm_iterations_excluded':5,'measured_updates':len(phase_rows),'median_seconds_per_transition':speed,'estimated_remaining_seconds':estimated,'budget_seconds':cfg['sampling_wall_budget_seconds'],'budget_fit':bool(estimated+time.perf_counter()-start<=cfg['sampling_wall_budget_seconds']),'note':'Measured subset one-worker estimate, may vary with acceptance and sustained speed; budget checked during execution.'})
    print(status,flush=True)

if __name__=='__main__':main()
