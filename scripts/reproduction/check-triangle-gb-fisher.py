#!/usr/bin/env python3
"""Check original imports, an analytically soluble Fisher problem and original network Fisher/pre-prior cells."""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/triangle-gb/fisher'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'runs/triangle-gb/matplotlib'))
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(k,'1')
import numpy as np


def main():
    OUT.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    report={'scope':'Prerequisite/interface checks, including original network preparation and Fisher/prior cells; no likelihood scans or nested sampling.', 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{}}
    def check(name,fn):
        t=time.perf_counter();detail=fn();report['checks'][name]={'passed':True,'seconds':time.perf_counter()-t,'detail':detail};print('PASS',name,flush=True);return detail
    def imports():
        from Triangle_BBH.Fisher import MultiChannelFisher
        result={}
        for module in ['Triangle_BBH','Triangle_BBH.Fisher','Triangle_BBH.Utils','Triangle_BBH.Waveform','Triangle_BBH.Response','WF4Py','WF4Py.waveforms']:
            m=importlib.import_module(module);assert Path(m.__file__).resolve().is_relative_to(ROOT/'external/triangle-bbh');result[module]=str(Path(m.__file__).resolve().relative_to(ROOT))
        return result
    check('original_import_and_all_autoloaded_modules',imports)
    def analytic():
        from Triangle_BBH.Fisher import MultiChannelFisher
        f=np.linspace(0.001,0.01,64)
        d1=np.array([np.ones(64),0.3*np.ones(64)],dtype=complex)
        d2=np.array([0.2+1j*f/f[-1],np.linspace(0.1,1.0,64)],dtype=complex)
        inv=np.broadcast_to(np.array([[2.0,0.4],[0.4,1.5]]),(64,2,2)).copy()
        def waveform(params,freqs):return params['a']*d1+params['b']*d2
        m=MultiChannelFisher(waveform,dict(a=1.2,b=0.7),dict(a=-1e-3,b=-1e-3),f,inv,verbose=0)
        m.auto_test_step(threshold=1e-3);m.calculate_Fisher();m.calculate_errors()
        derivatives=[d1,d2]
        expected=np.array([[np.real(np.einsum('if,fij,jf->',a.conj(),inv,b)) for b in derivatives] for a in derivatives])
        assert np.allclose(m.Fisher,expected,rtol=1e-8,atol=1e-9)
        assert np.allclose(m.CovMatrix,np.linalg.inv(expected),rtol=1e-8,atol=1e-9)
        assert all(np.isfinite(v) and v>0 for v in m.param_errors.values())
        return {'Fisher':m.Fisher.tolist(),'expected_Fisher':expected.tolist(),'CovMatrix':m.CovMatrix.tolist(),'param_errors':m.param_errors,'tuned_steps':m.analyze_param_step_dict,'condition_number':float(np.linalg.cond(m.Fisher))}
    check('analytic_correlated_two_channel_fisher_and_errors',analytic)
    def latex():
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        assert shutil.which('latex') and shutil.which('dvipng')
        with matplotlib.rc_context({'text.usetex':True,'font.family':'serif'}):
            fig,ax=plt.subplots();ax.plot([0,1],[0,1]);ax.set_xlabel(r'$f\,[\mathrm{Hz}]$');fig.savefig(OUT/'latex-render-check.png',dpi=90);plt.close(fig)
        return {'latex':shutil.which('latex'),'dvipng':shutil.which('dvipng'),'real_png_render':True}
    check('original_network_tex_plotting_prerequisite',latex)
    def network():
        p=ROOT/'external/triangle-gb/Examples/GB_network_PE_example_for_2609.16477.ipynb'
        nb=json.loads(p.read_text());ns={'__name__':'triangle_gb_network_preflight'};executed=[]
        for i in [0,2,4,5,7,9,11,13,15,17]:
            s=''.join(nb['cells'][i]['source']);exec(compile(s,p.name+':cell'+str(i),'exec'),ns)
            executed.append({'cell_zero_based':i,'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'modified':False})
        m=ns['mcf'];errors={k:float(v) for k,v in m.param_errors.items()}
        assert m.Fisher.shape==(8,8) and np.isfinite(m.Fisher).all() and np.isfinite(m.CovMatrix).all()
        assert all(np.isfinite(v) and v>0 for v in errors.values())
        # Check the resulting priors can actually be sampled before an expensive sampler run.
        prior_samples=ns['priors'].sample(size=8)
        assert all(np.isfinite(v).all() for v in prior_samples.values())
        return {'original_cells':executed,'Fisher_shape':list(m.Fisher.shape),'condition_number':float(np.linalg.cond(m.Fisher)), 'param_errors':errors, 'sampled_priors_finite':True,'likelihood_at_truth':float(ns['like'].log_likelihood()),'note':'Original four-year grid and Fisher/prior preparation only; no scan or sampler cells executed.'}
    check('original_network_fisher_and_prior_preparation',network)
    report['all_checks_pass']=True;report['elapsed_seconds']=time.perf_counter()-start
    report['bbh_commit']=subprocess.check_output(['git','-C',str(ROOT/'external/triangle-bbh'),'rev-parse','HEAD'],text=True).strip()
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fisher checks:',len(report['checks']),'passed',flush=True)


if __name__=='__main__':main()
