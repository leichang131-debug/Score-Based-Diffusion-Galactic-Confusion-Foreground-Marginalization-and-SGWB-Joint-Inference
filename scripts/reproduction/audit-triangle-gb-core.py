"""Audit evidence integrity separately from the failed original-package acceptance."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/core-validation'
v=json.loads((OUT/'validation.json').read_text());r=json.loads((OUT/'run.json').read_text());i=json.loads((OUT/'tutorial-impact.json').read_text())
expected_failures={'fill_loop_wide_band','fill_vectorized_clipped_band','fill_vectorized_clipped_physical_signal','time_default_nonzero','time_FFT_vs_sparse_frequency_drop_one','time_FFT_sparse_convergence_4096'}
checks={'commands_completed':r['execution_completed'],'all_original_failures_retained':{c['name'] for c in v['checks'] if not c['passed']}==expected_failures,'correct_counts':len(v['checks'])==28 and v['passed_count']==22 and v['failed_count']==6,'package_acceptance_explicitly_false':v['all_checks_passed'] is False and r['package_acceptance_passed'] is False,'unique_check_names':len(set(c['name'] for c in v['checks']))==len(v['checks']),'actual_runtime_includes_imports':r['wall_seconds']>=sum(c['seconds_including_imports'] for c in r['commands']),'original_example2_likelihood_reproduced':i['example_2']['stored_original_truth_likelihood_matches'],'original_time_axis_hash_matches':i['example_2']['time_axis_hash_matches'],'network_truth_support_inside':i['network']['truth_support_fully_inside_band'],'network_truth_signal_reproduced':i['network']['recorded_signal_reproduced'],'figure_exists':(OUT/'consistency.png').stat().st_size>10000}
parsed=[json.loads(line) for line in (OUT/'execution.txt').read_text().splitlines() if line.startswith('{"name":')]
checks['log_records_match_json']=parsed==v['checks']
with np.load(OUT/'arrays.npz') as z:
 checks['arrays_finite']=all(np.isfinite(z[k]).all() for k in z.files)
 checks['network_exact_reference']=np.array_equal(z['network_band'],z['network_single_detector_reference'])
 checks['recorded_likelihood_matches']=np.allclose(z['likelihood'],z['likelihood_reference'],rtol=1e-8,atol=0)
 checks['boundary_failure_demonstrated']=not np.array_equal(z['clipped_fill_actual'],z['clipped_fill_reference'])
 checks['physical_boundary_failure_demonstrated']=not np.array_equal(z['physical_clipped_actual'],z['physical_clipped_reference'])
with np.load(OUT/'example-2-fill-impact.npz') as z:
 a=z['original_template'];b=z['proper_crop_reference'];rel=np.linalg.norm(a-b)/np.linalg.norm(b)
 checks['impact_relative_error_recomputed']=np.isclose(rel,i['example_2']['relative_template_error'],rtol=1e-14,atol=0)
 checks['impact_only_edges']=np.array_equal(a[:,:,1:-1],b[:,:,1:-1]) and not np.array_equal(a,b)
for name,pin in [('triangle-gb','cbc0a1b0cbf4ec05ec969fa39405394168c3e06c'),('triangle-simulator','ab796358e9a36c8987f6bb53a97230d603bfdfd5')]:
 path=ROOT/'external'/name
 checks[name+'_unchanged']=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==pin and not subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True)
report={'evidence_integrity_passed':all(checks.values()),'package_acceptance_passed':False,'checks':{k:bool(v) for k,v in checks.items()},'scope':'Successful audit confirms genuine retained failures, not successful package acceptance.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['evidence_integrity_passed']
files=[x for x in OUT.iterdir() if x.is_file() and x.name!='manifest.json']
files+=list((ROOT/'scripts/reproduction').glob('*triangle-gb-core*.py'))+[ROOT/'docs/reproduction/triangle-gb/core-validation.md',ROOT/'external/triangle-gb/Triangle_GB/__init__.py',ROOT/'external/triangle-gb/Triangle_GB/TDIFly.py',ROOT/'external/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb',ROOT/'external/triangle-simulator/Triangle/TDI.py',ROOT/'external/triangle-simulator/Triangle/Orbit.py',ROOT/'external/triangle-simulator/Triangle/Constants.py']
files+=list((ROOT/'environments/triangle-gb').glob('requirements*'))
(OUT/'manifest.json').write_text(json.dumps([{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(files)],indent=2)+'\n')
