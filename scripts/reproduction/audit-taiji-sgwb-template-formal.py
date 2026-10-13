#!/usr/bin/env python3
"""Integrity manifest for live progress or completed formal evidence."""
import ast
import json
from pathlib import Path
import importlib.metadata
import base64
import numpy as np
from taiji_sgwb_likelihood import ROOT
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_formal_checkpoint import checkpoint_record,write_json

OUT=ROOT/'results/taiji-sgwb/template-formal'


def main():
    cfg=json.loads((ROOT/'configs/reproduction/taiji-sgwb/template-formal.json').read_text());root=ROOT/'runs/taiji-sgwb/template-formal'
    checks={}
    source=ROOT/'external/taiji-sgwb/demos/template_nofg_28t.py';text=source.read_text();call=ast.parse(text).body[-1].value
    kw={k.arg:ast.literal_eval(k.value) for k in call.keywords}
    checks['original_burn_and_thinning']=cfg['burn']==kw['burn']==1000 and cfg['thin_by']==kw['thin_by']==12
    checks['original_ensemble_and_saved_length']=cfg['ntemps']==6 and cfg['nwalkers']==62 and cfg['saved_samples']==350
    manifest=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text());checks['19_original_source_files_identical']=len(manifest['files'])==19 and all(sha(ROOT/x['repository_path'])==x['sha256'] for x in manifest['files'])
    test=json.loads((OUT/'checkpoint-interface-check.json').read_text());checks['unrecorded_burn_restore_test']=test['all_checks_pass']
    burn=json.loads((OUT/'initial-burn-check/validation.json').read_text());checks['real_burn_initial_states_validated']=burn['all_checks_pass']
    checkpoint,record=checkpoint_record(root);checks['checkpoint_pair_integrity']=True
    checks['current_source_config_provenance']=record['provenance']['source_sha256']==sha(source) and record['provenance']['config_sha256']==sha(ROOT/'configs/reproduction/taiji-sgwb/template-formal.json')
    checks['frozen_worker_adapters']=all(sha(ROOT/p)==s for p,s in record['provenance']['adapter_sha256'].items())
    checks['input_cache_integrity']=all(sha(ROOT/p)==s for p,s in record['provenance']['inputs'].items())
    data=np.load(checkpoint/'state.npz');checks['checkpoint_state_finite']=all(np.all(np.isfinite(data[k])) for k in data.files)
    installed=[];dist=importlib.metadata.distribution('eryn')
    for item in dist.files:
        if str(item).startswith('eryn/') and str(item).endswith('.py') and item.hash:
            installed.append(base64.urlsafe_b64encode(bytes.fromhex(sha(dist.locate_file(item)))).rstrip(b'=').decode()==item.hash.value)
    checks['installed_Eryn_source_unmodified']=bool(installed) and all(installed)
    if (OUT/'analysis.json').exists():
        analysis=json.loads((OUT/'analysis.json').read_text());checks['numerical_outcome_recorded_consistently']=analysis['numerical_checks_pass']==all(analysis['checks'].values())
        checks['complete_original_schedule']=analysis['sampling']['saved']==350 and analysis['sampling']['burn']==1000 and analysis['sampling']['thin_by']==12
    checks={k:bool(v) for k,v in checks.items()}
    write_json(OUT/'audit.json',{'scope':'Integrity/readiness only while running; not a convergence verdict.','checks':checks,'all_checks_pass':all(checks.values()),'latest_complete_checkpoint':checkpoint.name,'Eryn_files_checked':len(installed)})
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files += [ROOT/'scripts/reproduction'/n for n in ['taiji_sgwb_formal_checkpoint.py','run-taiji-sgwb-template-formal-worker.py','run-taiji-sgwb-template-formal.py','check-taiji-sgwb-formal-checkpoint.py','analyze-taiji-sgwb-template-formal.py','audit-taiji-sgwb-template-formal.py','check-taiji-sgwb-formal-burn.py']]
    files += [ROOT/'configs/reproduction/taiji-sgwb/template-formal.json',ROOT/'docs/reproduction/taiji-sgwb/template-formal.md']
    write_json(OUT/'manifest.json',{'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]})
    print(f'Formal evidence integrity: {sum(checks.values())}/{len(checks)} passed; sampling may still be running.')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
