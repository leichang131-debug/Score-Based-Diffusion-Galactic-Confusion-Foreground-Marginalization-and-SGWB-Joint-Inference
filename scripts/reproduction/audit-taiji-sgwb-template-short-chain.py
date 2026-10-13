#!/usr/bin/env python3
"""Source, installed Eryn files, checkpoint and artifact integrity audit."""
import ast
import base64
import importlib.metadata
import json
from pathlib import Path
import subprocess
import numpy as np
from eryn.backends import HDFBackend
from taiji_sgwb_likelihood import ROOT
from taiji_sgwb_checkpoint import sha,RestartCompatibleHDFBackend,pack_rng

OUT=ROOT/'results/taiji-sgwb/template-short-chain'


def main():
    checks={};check=lambda k,x:checks.update({k:bool(x)})
    v=json.loads((OUT/'validation.json').read_text())
    check('all_chain_validation_checks_pass',v['all_checks_pass'] and all(v['checks'].values()))
    check('fixed_upstream_commit',subprocess.check_output(['git','-C',str(ROOT/'external/taiji-sgwb'),'rev-parse','HEAD']).decode().strip()==v['config']['upstream_commit'])
    check('original_source_clean',not subprocess.check_output(['git','-C',str(ROOT/'external/taiji-sgwb'),'status','--porcelain']).strip())
    sm=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text())
    check('all_19_original_files_preserved',len(sm['files'])==19 and all(sha(ROOT/x['repository_path'])==x['sha256'] for x in sm['files']))
    eryn=importlib.metadata.distribution('eryn');library_files=[]
    for item in eryn.files:
        if str(item).startswith('eryn/') and str(item).endswith('.py') and item.hash is not None:
            assert item.hash.mode=='sha256'
            actual=base64.urlsafe_b64encode(bytes.fromhex(sha(eryn.locate_file(item)))).rstrip(b'=').decode()
            library_files.append({'path':str(item),'matches_installed_RECORD':actual==item.hash.value})
    check('installed_Eryn_Python_files_unmodified',bool(library_files) and all(x['matches_installed_RECORD'] for x in library_files))
    for mode in ('initial','resume','continuous'):
        report=json.loads((OUT/mode/'worker.json').read_text());record=json.loads((OUT/mode/'source-execution.json').read_text());sidecar=json.loads((OUT/mode/'restart-state.json').read_text())
        filename=OUT/mode/'template_AET_nofg.h5'
        check(mode+'_original_backend_filename',report['backend']['filename']==filename.name)
        check(mode+'_backend_sidecar_bytes',sha(filename)==report['backend']['sha256']==sidecar['backend_sha256'] and filename.stat().st_size==report['backend']['bytes'])
        original=ROOT/record['likelihood_load_record']['source'];text=original.read_text();tree=ast.parse(text);nodes={n.lineno:n for n in tree.body}
        records=record['original_initialization_nodes']+record['original_sampler_constructor_nodes']+record['likelihood_load_record']['nodes']
        check(mode+'_all_recorded_source_nodes_exact',all(x['source']==ast.get_source_segment(text,nodes[x['line']]) and x['end_line']==nodes[x['line']].end_lineno for x in records))
        check(mode+'_same_named_byte_identical_working_copy',(ROOT/record['working_copy']).name==original.name and sha(ROOT/record['working_copy'])==sha(original))
        raw=HDFBackend(filename,read_only=True);adapted=RestartCompatibleHDFBackend(filename,read_only=True)
        a,b=raw.key_order,adapted.key_order
        check(mode+'_adapter_preserves_key_order_contents',set(a)==set(b) and all(np.array_equal(a[k],b[k]) and isinstance(b[k],list) for k in a))
        check(mode+'_adapter_preserves_chain_and_rng',np.array_equal(raw.get_log_like(),adapted.get_log_like()) and pack_rng(raw.random_state)==pack_rng(adapted.random_state))
        check(mode+'_checkpoint_summary_consistent',sidecar['state_summary']==report['final_state'])
        check(mode+'_raw_working_chain_ignored',subprocess.run(['git','check-ignore','--quiet','runs/taiji-sgwb/template-short-chain/'+('continuous' if mode=='continuous' else 'split')+'/template_AET_nofg.h5'],cwd=ROOT).returncode==0)
    failed=json.loads((OUT/'attempts/original-HDF-key-order/run.json').read_text())
    check('unmodified_HDF_restart_failure_preserved',failed['returncode']==1 and 'truth value of an array' in (OUT/'attempts/original-HDF-key-order/execution.txt').read_text())
    checks={k:bool(x) for k,x in checks.items()}
    result={'checks':checks,'all_checks_pass':all(checks.values()),'installed_Eryn_Python_file_checks':library_files,'scope':'Stored evidence and source/library integrity; external key-order type adapter does not patch installed Eryn or original TaijiSGWB.'}
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files += [ROOT/'scripts/reproduction'/n for n in ('taiji_sgwb_checkpoint.py','run-taiji-sgwb-template-worker.py','run-taiji-sgwb-template-short-chain.py','check-taiji-sgwb-template-short-chain.py','report-taiji-sgwb-template-short-chain.py','audit-taiji-sgwb-template-short-chain.py')]
    files += [ROOT/'configs/reproduction/taiji-sgwb/template-short-chain.json',ROOT/'docs/reproduction/taiji-sgwb/template-short-chain.md']
    (OUT/'manifest.json').write_text(json.dumps({'schema_version':1,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]},indent=2)+'\n')
    print(f'Stage 8 evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(files)} artifacts hashed; {len(library_files)} Eryn Python files checked against RECORD.')
    if not result['all_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
