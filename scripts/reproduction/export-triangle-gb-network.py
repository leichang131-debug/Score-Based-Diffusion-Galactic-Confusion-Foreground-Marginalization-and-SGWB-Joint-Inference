"""Export final scientific sampler artifacts; retain binary checkpoints locally."""
import hashlib,json,shutil
from pathlib import Path
import h5py,numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/network'
WORK=ROOT/'runs/triangle-gb/network/Examples/Samples'
execution=json.loads((OUT/'execution.json').read_text());assert execution['execution_passed']
export=OUT/'Samples';export.mkdir(exist_ok=True)
records=[]
allowed={'.json','.hdf5','.h5','.png','.pdf','.log','.txt','.csv','.prior'}
for p in sorted(WORK.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(WORK);tracked=p.suffix.lower() in allowed
 records.append({'local_path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exported':tracked})
 if tracked:
  dest=export/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(OUT/'sampler-artifacts.json').write_text(json.dumps(records,indent=2)+'\n')
result_path=next((WORK/'gb_network_analysis_example_nessai').glob('result.hdf5'))
with h5py.File(result_path,'r') as f:
 def scalar(k):return np.asarray(f[k][()]).item()
 diagnostics={k:scalar(k) for k in ['final_p_value','final_ks_statistic','log_evidence','log_evidence_error','information','training_time','population_time','sampling_time','total_likelihood_evaluations'] if k in f}
 weights=np.asarray(f['log_posterior_weights']);weights=np.exp(weights-np.max(weights));weights/=np.sum(weights)
 diagnostics['nested_weight_effective_sample_size']=float(1/np.sum(weights**2))
 diagnostics['insertion_index_count']=len(f['insertion_indices'])
 diagnostics['nested_samples_count']=len(f['nested_samples'])
 diagnostics['posterior_samples_count']=len(f['posterior_samples'])
 diagnostics['insertion_indices_range']=[int(np.min(f['insertion_indices'])),int(np.max(f['insertion_indices']))]
 diagnostics['diagnostic_warning']=bool(diagnostics['final_p_value']<0.05)
 diagnostics['scope']='Final insertion-index uniformity diagnostic; a low p-value requires follow-up, a passing value does not prove posterior calibration.'
(OUT/'sampling-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
print(json.dumps(diagnostics,indent=2));print('Exported',sum(x['exported'] for x in records),'of',len(records),'sampler files; checkpoints/weights remain ignored locally.')
