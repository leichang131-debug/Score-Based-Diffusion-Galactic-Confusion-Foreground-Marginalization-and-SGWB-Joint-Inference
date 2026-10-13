"""Selected original bins/weeks, unchanged upstream likelihood and priors."""
import ast
import json
from pathlib import Path
import numpy as np
import h5py
from taiji_sgwb_likelihood import ROOT,load_original_likelihood
from taiji_sgwb_checkpoint import sha
from taiji_sgwb_response import execute_nodes
from taiji_sgwb_preprocessing import digest_array

CFG=ROOT/'configs/reproduction/taiji-sgwb/template-mini.json'
OUT=ROOT/'results/taiji-sgwb/template-mini'
WORK=ROOT/'runs/taiji-sgwb/template-mini'
CACHE=ROOT/'data/processed/taiji-sgwb/template-mini/selected-inputs.h5'
NAMES=['f_est','t_seg','acc_corr_factor','ro_corr_factor','spectrum_acc','spectrum_ro','orf','csd_est']


def subset(namespace,cfg):
    full=namespace['f_est'];low=np.flatnonzero(full<=cfg['retain_all_below_Hz']);high=np.flatnonzero(full>cfg['retain_all_below_Hz'])
    needed=cfg['frequency_points']-len(low)
    assert needed>0 and needed<=len(high)
    freq=np.concatenate((low,high[np.rint(np.linspace(0,len(high)-1,needed)).astype(int)]))
    week=np.array(cfg['week_indices'],dtype=int)
    assert len(np.unique(freq))==cfg['frequency_points'] and np.all(np.diff(freq)>0)
    chosen={}
    for k in NAMES:
        a=namespace[k]
        if k=='t_seg':chosen[k]=a[week]
        elif k in ('f_est','spectrum_acc','spectrum_ro'):chosen[k]=a[freq]
        else:chosen[k]=np.take(np.take(a,week,axis=-2),freq,axis=-1)
    return chosen,{'week_indices':week.tolist(),'frequency_indices':freq.tolist(),'all_low_frequency_bins_retained':int(len(low)),'high_frequency_selected':int(needed),'full_grid':[52,len(full)],'selected_grid':[len(week),len(freq)],'fraction_of_week_frequency_matrices':len(week)*len(freq)/(52*len(full)),'selection':'Exact original retained bins; no rebinning, interpolation, inverse-probability weights or full-year rescaling.'}


def load_mini():
    """Compile exact original imports/functions/priors against small cache only."""
    cfg=json.loads(CFG.read_text());source=ROOT/'external/taiji-sgwb/demos'/cfg['entry'];text=source.read_text();tree=ast.parse(text)
    imports=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='log_likelihood']
    settings=[];active=False
    for node in tree.body:
        names=[x.id for x in node.targets if isinstance(x,ast.Name)] if isinstance(node,ast.Assign) else []
        if 'nstep' in names:active=True
        if 'params0' in names:break
        if active:settings.append(node)
    ns={'__name__':'mini_original','__file__':str(WORK/'demos'/cfg['entry'])}
    execute_nodes(source,imports+functions+settings,ns)
    with h5py.File(CACHE,'r') as h:
        ns.update({k:h[k][()] for k in NAMES});ns.update(nperbin=int(h.attrs['nperbin']),win_bw=float(h.attrs['win_bw']))
        metadata=json.loads(h.attrs['metadata'])
    ns.update(nwalker=cfg['nwalkers'],ntemp=cfg['ntemps'],npool=cfg['processes'])
    for k in NAMES:ns[k].flags.writeable=False
    nodes=[{'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)} for n in imports+functions+settings]
    return ns,{'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'original_nodes':nodes,'cache_metadata':metadata}


def provenance():
    return {'upstream_commit':json.loads(CFG.read_text())['upstream_commit'],'source_sha256':sha(ROOT/'external/taiji-sgwb/demos/template_nofg_28t.py'),'config_sha256':sha(CFG),'selected_cache_sha256':sha(CACHE),'frozen_worker_sha256':sha(ROOT/'scripts/reproduction/run-taiji-sgwb-mini-worker.py'),'mini_loader_sha256':sha(Path(__file__))}
