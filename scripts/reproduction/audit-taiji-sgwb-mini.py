#!/usr/bin/env python3
"""Original-source, actual local mini execution, restore and evidence audit."""
import ast
import datetime
import base64
import importlib.metadata
import json
from pathlib import Path
import subprocess
import numpy as np
import h5py
from eryn.backends import HDFBackend
from taiji_sgwb_mini import ROOT,CFG,OUT,WORK,CACHE,NAMES
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_preprocessing import digest_array
from taiji_sgwb_formal_checkpoint import write_json


def main():
    cfg=json.loads(CFG.read_text());prep=json.loads((OUT/'preparation.json').read_text());analysis=json.loads((OUT/'analysis.json').read_text());checks={}
    check=lambda k,v:checks.update({k:bool(v)})
    check('all_preparation_checks',prep['all_checks_pass'] and all(prep['checks'].values()))
    check('all_analysis_numerical_checks',analysis['all_numerical_checks_pass'] and all(analysis['numerical_checks'].values()))
    check('selected_cache_file_hash',sha(CACHE)==prep['cache']['sha256'] and CACHE.stat().st_size==prep['cache']['bytes'])
    with h5py.File(CACHE,'r') as h:
        check('selected_cache_array_hashes',all(digest_array(h[k][()])==prep['array_sha256'][k] for k in NAMES))
        metadata=json.loads(h.attrs['metadata']);check('bin_window_not_rescaled',int(h.attrs['nperbin'])==6 and float(h.attrs['win_bw'])==metadata['win_bw'])
        check('link_and_channel_order',metadata['link_order']==['12','13','23','21','31','32'] and metadata['channels']==['A','E','T'])
    check('full_input_caches_unchanged',all(sha(ROOT/p)==v for p,v in metadata['full_cache_sha256'].items()))
    check('subset_cache_ignored',subprocess.run(['git','check-ignore','--quiet',str(CACHE.relative_to(ROOT))],cwd=ROOT).returncode==0)
    manifest=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text());check('all_original_19_files',len(manifest['files'])==19 and all(sha(ROOT/f['repository_path'])==f['sha256'] for f in manifest['files']))
    check('original_tree_clean',not subprocess.check_output(['git','-C',str(ROOT/'external/taiji-sgwb'),'status','--porcelain']).strip())
    source=ROOT/'external/taiji-sgwb/demos/template_nofg_28t.py';text=source.read_text();nodes={n.lineno:n for n in ast.parse(text).body}
    pids=[];wall=0
    for mode in ['benchmark','first','resume']:
        run=json.loads((OUT/mode/'run.json').read_text());w=json.loads((OUT/mode/'worker.json').read_text());record=json.loads((OUT/mode/'source-execution.json').read_text());pids.append(run['pid']);wall+=run['wall_seconds']
        check(mode+'_actual_successful_process',run['returncode']==0 and run['pid']==w['pid'] and run['peak_parent_rss_kib']>0)
        check(mode+'_original_constructor_and_initializer_nodes',all(n['source']==ast.get_source_segment(text,nodes[n['line']]) for n in record['constructor_nodes']+record['original_initialization_nodes']))
        check(mode+'_original_likelihood_nodes',all(n['source']==ast.get_source_segment(text,nodes[n['line']]) for n in record['original_likelihood_record']['original_nodes']))
        check(mode+'_default_original_move',record['move']=='StretchMove' and record['stretch_a']==2.0)
        check(mode+'_backend_hash',sha(OUT/mode/'template_AET_nofg.h5')==w['backend_sha256']==w['checkpoint']['backend_sha256'])
        check(mode+'_state_npz_hash',sha(OUT/mode/'state.npz')==w['checkpoint']['npz_sha256'])
        check(mode+'_original_config_and_cache_provenance',w['checkpoint']['provenance']['config_sha256']==sha(CFG) and w['checkpoint']['provenance']['selected_cache_sha256']==sha(CACHE))
        check(mode+'_finite_transition_times',all(r['seconds']>0 and r['likelihood_calls']>0 for r in w['steps']))
    check('three_independent_process_PIDs',len(set(pids))==3)
    first=json.loads((OUT/'first/run.json').read_text());resume=json.loads((OUT/'resume/run.json').read_text())
    resume_start_estimate=datetime.datetime.fromisoformat(resume['ended_utc'])-datetime.timedelta(seconds=resume['wall_seconds'])
    check('first_exit_precedes_derived_resume_start',datetime.datetime.fromisoformat(first['ended_utc'])<=resume_start_estimate)
    check('only_fresh_prior_initialization_once',json.loads((OUT/'benchmark/source-execution.json').read_text())['initialization_executed'] and not json.loads((OUT/'first/source-execution.json').read_text())['initialization_executed'] and not json.loads((OUT/'resume/source-execution.json').read_text())['initialization_executed'])
    check('completed_mini_schedule',HDFBackend(OUT/'resume/template_AET_nofg.h5',read_only=True).iteration==1000 and json.loads((WORK/'progress.json').read_text())['burn_done']==300)
    check('sampling_within_wall_budget',wall<cfg['sampling_wall_budget_seconds'])
    check('posteriors_not_mislabelled_full_data',analysis['scope']==cfg['scope'] and not json.loads((OUT/'status.json').read_text())['original_full_data_inference_complete'])
    # The user subsequently resumed the formal run. Audit immutable historical
    # pause evidence rather than requiring its live status to remain paused.
    pause=ROOT/'results/taiji-sgwb/template-formal/pause-checkpoint'
    record=json.loads((pause/'state.json').read_text())
    check('original_formal_108_checkpoint_preserved',record['burn_done']==108 and record['production_done']==0 and sha(pause/'state.npz')==record['npz_sha256'] and sha(pause/'template_AET_nofg.h5')==record['backend_sha256'] and analysis['numerical_checks']['full_formal_run_still_paused'])
    library=[];dist=importlib.metadata.distribution('eryn')
    for item in dist.files:
        if str(item).startswith('eryn/') and str(item).endswith('.py') and item.hash:library.append(base64.urlsafe_b64encode(bytes.fromhex(sha(dist.locate_file(item)))).rstrip(b'=').decode()==item.hash.value)
    check('installed_Eryn_unmodified',bool(library) and all(library))
    write_json(OUT/'audit.json',{'checks':checks,'all_checks_pass':all(checks.values()),'sample_run_wall_seconds_sum':wall,'installed_Eryn_files_checked':len(library),'scope':'Subset workflow integrity and execution evidence; not an inference convergence verdict.'})
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files += [ROOT/'scripts/reproduction'/n for n in ['taiji_sgwb_mini.py','prepare-taiji-sgwb-mini.py','run-taiji-sgwb-mini-worker.py','run-taiji-sgwb-mini.py','analyze-taiji-sgwb-mini.py','audit-taiji-sgwb-mini.py']]
    files += [CFG,ROOT/'docs/reproduction/taiji-sgwb/template-mini.md']
    write_json(OUT/'manifest.json',{'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
    print(f'Mini workflow evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(files)} artifacts hashed.')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
