"""Audit unchanged network execution and independent numerical identities."""
import base64,hashlib,json,subprocess
from pathlib import Path
import nbformat,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/network'
NAME='GB_network_PE_example_for_2609.16477.ipynb';SRC=ROOT/'external/triangle-gb'
p=ROOT/'notebooks/reproduction/triangle-gb/Examples'/NAME
a=nbformat.read(SRC/'Examples'/NAME,4);b=nbformat.read(p,4)
e=json.loads((OUT/'execution.json').read_text());d=json.loads((OUT/'diagnostics.json').read_text());s=json.loads((OUT/'sampling-diagnostics.json').read_text())
checks={'same_filename':p.name==NAME,'same_cell_count':len(a.cells)==len(b.cells),'unchanged_code_markdown_attachments':len(a.cells)==len(b.cells) and all(x.cell_type==y.cell_type and x.source==y.source and x.get('attachments',{})==y.get('attachments',{}) for x,y in zip(a.cells,b.cells)),'execution_passed':e['execution_passed'],'no_error_outputs':not e['error_outputs'],'all_nonempty_code_executed':all(c.execution_count is not None for c in b.cells if c.cell_type=='code' and c.source.strip()),'notebook_hash_matches':hashlib.sha256(p.read_bytes()).hexdigest()==e['executed_notebook_sha256'],'three_detectors_original_order':d['mission_list']==['TianQin','Taiji','LISA'],'four_year_original_time_grid':d['dt_seconds']==10 and d['time_axis']['shape']==[12623259] and d['Tobs_seconds']==126232590,'original_sampler':d['sampler_kwargs']['nlive']=='1000' and float(d['sampler_kwargs']['stopping'])==.1 and int(d['sampler_kwargs']['n_pool'])==d['cpu_count'],'posterior_finite':d['posterior_finite'] and d['posterior_loglikelihood_finite'] and d['posterior_logprior_finite'],'positive_finite_fisher_errors':all(np.isfinite(v) and v>0 for v in d['fisher_sigmas'].values()),'confusion_terms_zero':d['confusion_psd_zero'] and d['confusion_csd_zero'],'log_evidence_finite':bool(np.isfinite(d['log_evidence']) and np.isfinite(d['log_evidence_err'])),'snr_consistency':bool(np.isclose(d['snr_injected'],d['snr_recomputed'],rtol=1e-12)),'best_likelihood_recomputed':bool(np.isclose(d['best_posterior_log_likelihood'],d['best_recomputed_log_likelihood'],rtol=0,atol=1e-8))}
with np.load(OUT/'network-band.npz') as z:
 f=z['frequency_hz'];c=z['inverse_covariance'];h=z['signal'];n=z['noise']
 checks['all_band_arrays_finite']=all(np.isfinite(z[k]).all() for k in z.files)
 checks['six_channel_shapes']=h.shape==n.shape==z['data'].shape==(6,len(f)) and c.shape==(len(f),6,6)
 checks['data_signal_noise_identity']=np.array_equal(z['data'],h+n)
 checks['seeded_noise_reproduced']=np.array_equal(n,z['regenerated_noise'])
 checks['covariance_hermitian']=bool(np.allclose(c,c.conj().transpose(0,2,1),rtol=1e-14,atol=0))
 checks['positive_covariance']=bool(np.all(np.linalg.eigvalsh(c)>0))
 diag=np.diagonal(c,axis1=1,axis2=2);expected=np.zeros_like(c)
 for i in range(6):expected[:,i,i]=diag[:,i]
 checks['instrument_only_diagonal_covariance']=np.array_equal(c,expected)
 snr=float(np.sqrt(np.einsum('ik,kij,jk->',h.conj(),c,h).real))
 ll=float(-.5*np.einsum('ik,kij,jk->',n.conj(),c,n).real)
 checks['independent_snr']=bool(np.isclose(snr,d['snr_injected'],rtol=1e-12))
 checks['independent_truth_likelihood']=bool(np.isclose(ll,d['truth_log_likelihood'],rtol=1e-12))
 checks['frequency_spacing']=bool(np.allclose(np.diff(f),d['delta_f'],rtol=1e-8,atol=1e-18))
with np.load(OUT/'fisher.npz') as z:
 matrix=z['matrix'];scaled=z['scaled_matrix'];scales=np.sqrt(np.diag(matrix))
 sigmas=np.sqrt(np.diag(np.linalg.inv(scaled)))/scales
 checks['fisher_scaled_positive']=bool(np.all(np.linalg.eigvalsh(scaled)>0))
 checks['independent_scaled_fisher_errors']=bool(np.allclose(sigmas,[d['fisher_sigmas'][k] for k in z['parameter_names']],rtol=1e-6,atol=0))
with np.load(OUT/'likelihood-scans.npz') as z:
 checks['six_complete_finite_scans']=len(z.files)==12 and all(z[k].shape==(501,) and np.isfinite(z[k]).all() for k in z.files)
post=pd.read_csv(OUT/'posterior.csv');checks['posterior_export_count']=len(post)==d['posterior_samples']
for k,v in d['priors'].items():checks['posterior_prior_range_'+k]=bool(np.all((post[k]>=v['minimum'])&(post[k]<=v['maximum'])))
for name,pin in [('triangle-gb','cbc0a1b0cbf4ec05ec969fa39405394168c3e06c'),('triangle-simulator','ab796358e9a36c8987f6bb53a97230d603bfdfd5'),('triangle-bbh','f99b0a34ea8d085aff67220bdc165a746ba5ceda')]:
 src=ROOT/'external'/name
 checks[name+'_pin_clean']=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()==pin and not subprocess.check_output(['git','-C',str(src),'status','--porcelain'],text=True)
checks['module_origins']=all(Path(d['module_files'][name]).resolve()==(ROOT/relative).resolve() for name,relative in {'Triangle.Orbit':'external/triangle-simulator/Triangle/Orbit.py','Triangle_GB.TDIFly':'external/triangle-gb/Triangle_GB/TDIFly.py','Triangle_BBH.Fisher':'external/triangle-bbh/Triangle_BBH/Fisher.py'}.items())
for i in [11,18,21]:
 raw=next(base64.b64decode(o.data['image/png']) for o in b.cells[i].outputs if 'image/png' in o.get('data',{}))
 checks['local_figure_'+str(i)]=next(OUT.glob(f'cell-{i:02d}-*.png')).read_bytes()==raw
checks['sampler_hdf5_consistency']=s['posterior_samples_count']==d['posterior_samples'] and np.isclose(s['log_evidence'],d['log_evidence'],atol=1e-10,rtol=0)
checks['sampler_reached_original_stop']='Stopping with difference_log_evidence=0.100' in (OUT/'kernel-stream.txt').read_text()
report={'passed':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},'nonempty_code_cells':len(e['cell_timings']),'insertion_index_warning':s['diagnostic_warning'],'limitations':'Instrument noise only; original hidden psi scan panel; truth-centered Fisher priors; sampler unseeded; one run is not posterior calibration. Diagnostic warning is reported separately from execution integrity.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
files=[p,SRC/'Examples'/NAME,ROOT/'docs/reproduction/triangle-gb/network.md']
files+=list((ROOT/'scripts/reproduction').glob('*triangle-gb-network*.py'))+list((ROOT/'environments/triangle-gb').glob('requirements*'))
files+=[x for x in OUT.rglob('*') if x.is_file() and x.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps([{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(files)],indent=2)+'\n')
assert report['passed'],[k for k,v in checks.items() if not v]
