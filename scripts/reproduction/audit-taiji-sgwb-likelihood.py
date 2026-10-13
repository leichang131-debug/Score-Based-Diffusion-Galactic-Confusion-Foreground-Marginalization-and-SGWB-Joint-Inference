#!/usr/bin/env python3
"""Audit saved Stage 7 evidence, original AST/source and prior cache provenance."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from taiji_sgwb_likelihood import ROOT

OUT=ROOT/'results/taiji-sgwb/likelihood'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()


def main():
    v=json.loads((OUT/'validation.json').read_text());run=json.loads((OUT/'run.json').read_text())
    checks={'worker_success':run['returncode']==0,'all_numerical_checks_pass':v['all_checks_pass'] and all(v['checks'].values()),'real_local_resource_samples':run['peak_sampled_worker_rss_kib']>0 and run['monitoring_error'] is None,'no_MCMC_claim':all(x['MCMC_updates']==0 for x in v['interfaces'].values())}
    sm=json.loads((ROOT/'results/taiji-sgwb/source/manifest.json').read_text())
    checks['all_19_original_files_preserved']=len(sm['files'])==19 and all(sha(ROOT/item['repository_path'])==item['sha256'] for item in sm['files'])
    checks['original_source_clean']=not subprocess.check_output(['git','-C',str(ROOT/'external/taiji-sgwb'),'status','--porcelain']).strip()
    checks['original_pin']=subprocess.check_output(['git','-C',str(ROOT/'external/taiji-sgwb'),'rev-parse','HEAD']).decode().strip()=='4afaad4044b08721e7f1ce29cba3b0d912636dce'
    for entry in ('template_nofg_28t.py','rj_nofg_28t.py'):
        name=Path(entry).stem;record=json.loads((OUT/name/'source-execution.json').read_text());source=ROOT/record['source'];working=ROOT/record['working_copy']
        checks[name+'_same_name_identical_source']=source.name==working.name==entry and sha(source)==sha(working)==record['sha256']
        text=source.read_text();nodes={n.lineno:n for n in ast.parse(text).body}
        checks[name+'_exact_original_AST_nodes']=all(n['line'] in nodes and n['end_line']==nodes[n['line']].end_lineno and n['source']==ast.get_source_segment(text,nodes[n['line']]) for n in record['nodes'])
        checks[name+'_original_likelihood_in_record']=any(n['source'].startswith('def log_likelihood(') for n in record['nodes'])
        x=v['interfaces'][name];checks[name+'_actual_Eryn_interface']=x['log_like_shape']==[1,32] and x['maximum_error_from_direct_truth']<1e-6 and x['original_RJ_mode_enabled']==name.startswith('rj')
    for path,expected in v['inputs'].items():
        p=ROOT/path;name=p.parent.name if 'preprocessing' in path else 'response'
        prior=ROOT/'results/taiji-sgwb'/('preprocessing/'+name if 'preprocessing' in path else 'response')/'validation.json'
        prior_cache=json.loads(prior.read_text())['cache']
        checks[name+'_unchanged_input_cache']=sha(p)==expected['sha256']==prior_cache['sha256'] and p.stat().st_size==expected['bytes']==prior_cache['bytes']
        checks[name+'_bulk_cache_ignored']=subprocess.run(['git','check-ignore','--quiet',path],cwd=ROOT).returncode==0
    with (OUT/'likelihood-comparisons.csv').open() as f:rows=list(csv.DictReader(f))
    checks['CSV_matches_validation']=len(rows)==len(v['comparisons']) and all(row['label']==ref['label'] and float(row['original_log_likelihood'])==ref['original_log_likelihood'] and float(row['absolute_error'])==ref['absolute_error'] for row,ref in zip(rows,v['comparisons']))
    summary=np.load(OUT/'spectral-summary.npz')
    checks['portable_spectra_finite']=all(np.all(np.isfinite(summary[k])) for k in summary.files)
    checks['portable_scan_count']=summary['scan_ll'].shape==(13,) and len(v['rj_prior_probes'])==15
    wc=json.loads((OUT/'determinant-warning-controls.json').read_text())
    checks['identity_warning_evidence']=any(x['input']=='complex_identity' and x['function']=='det' and x['warnings'] and x['all_returned_values_finite'] for x in wc['controls'])
    checks['initial_interface_failure_retained']=json.loads((OUT/'attempts/initial-interface-check/run.json').read_text())['returncode']==1
    checks['determinant_investigation_retained']=json.loads((OUT/'attempts/determinant-warning-investigation/run.json').read_text())['returncode']==1
    checks={k:bool(x) for k,x in checks.items()}
    result={'scope':'Evidence/source/cache integrity only; no physical likelihood recomputation or posterior sampling.','checks':checks,'all_checks_pass':all(checks.values())}
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files += [ROOT/'scripts/reproduction'/n for n in ('taiji_sgwb_likelihood.py','check-taiji-sgwb-likelihood.py','run-taiji-sgwb-likelihood.py','audit-taiji-sgwb-likelihood.py','report-taiji-sgwb-likelihood.py')]
    files += [ROOT/'docs/reproduction/taiji-sgwb/likelihood.md']
    (OUT/'manifest.json').write_text(json.dumps({'schema_version':1,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]},indent=2)+'\n')
    print(f'Stage 7 evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(files)} artifacts hashed.')
    if not result['all_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
