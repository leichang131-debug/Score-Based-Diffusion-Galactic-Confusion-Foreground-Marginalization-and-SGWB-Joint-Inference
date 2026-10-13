"""Load exact upstream likelihood definitions against verified Stage 5/6 caches."""
import ast
import hashlib
from pathlib import Path
import sys
import warnings
import numpy as np
from taiji_sgwb_preprocessing import load_preprocessing_cache
from taiji_sgwb_response import load_response_cache, execute_nodes

ROOT = Path(__file__).resolve().parents[2]


def load_original_likelihood(entry, response=None):
    """Return original function/priors, without executing preprocessing or MCMC.

    Scientific function AST nodes are compiled unchanged. Cache arrays and local
    file paths are supplied externally. No replacement likelihood is installed.
    """
    source = ROOT / 'external/taiji-sgwb/demos' / entry
    working = ROOT / 'runs/taiji-sgwb/likelihood' / source.stem / 'demos' / entry
    working.parent.mkdir(parents=True, exist_ok=True)
    working.write_bytes(source.read_bytes())
    pre = load_preprocessing_cache(ROOT / 'data/processed/taiji-sgwb/preprocessing' / source.stem / 'preprocessing.h5')
    response = response if response is not None else load_response_cache(ROOT / 'data/processed/taiji-sgwb/response/response.h5')
    assert np.array_equal(pre['frequency'], response['f_est'])
    assert np.array_equal(pre['segment_center'], response['t_seg'])
    text = source.read_text(); tree = ast.parse(text)
    selected = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    selected += [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(e,ast.Name) and e.id=='f_analow' for e in t.elts) for t in n.targets)]
    # Exact function definitions and the original scalar/frequency initialization.
    selected += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('create_omega_interp_fun', 'log_likelihood')]
    ns = {'__file__': str(working), '__name__': 'stage7_original', **{k:v for k,v in response.items() if k != 'metadata'},
          'csd_est':pre['csd_est'], 'nperbin':pre['nperbin'], 'win_bw':pre['win_bw'],
          'f_analow':1e-4, 'f_anaupp':5e-2, 'npool':62}
    # Execute original log_f_est statement, before its use by the RJ function.
    selected += [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='log_f_est' for t in n.targets)]
    # Original sampler dimensions and prior definitions only; no random init/pool.
    active = False
    for n in tree.body:
        names = [t.id for t in n.targets if isinstance(t,ast.Name)] if isinstance(n,ast.Assign) else []
        if 'nstep' in names: active = True
        if 'params0' in names: break
        if active: selected.append(n)
    if entry.startswith("rj"):
        moves_active = False
        for n in tree.body:
            names = [t.id for t in n.targets if isinstance(t,ast.Name)] if isinstance(n,ast.Assign) else []
            if "noise_move" in names: moves_active = True
            if "pool" in names: break
            if moves_active: selected.append(n)
    execute_nodes(source, selected, ns)
    record = {'source': str(source.relative_to(ROOT)), 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'working_copy':str(working.relative_to(ROOT)), 'nodes':[{'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)} for n in selected],
              'adaptation':'Unchanged original imports/functions/prior nodes; verified cached globals supplied externally. No sampler run, pool or backend.'}
    return ns, record


def evaluate_original(namespace, params):
    """Call original function; observe its returned frame without editing code."""
    function = namespace['log_likelihood']; captured = {}
    def trace(frame, event, arg):
        if frame.f_code is not function.__code__: return None
        if event == 'return':
            for key in ('csd_hypo','ll_exp','ll_coef','omega_sgwb','log_omega_hypo'):
                if key in frame.f_locals: captured[key] = frame.f_locals[key]
        return trace
    before = sys.gettrace()
    try:
        sys.settrace(trace)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            value = function(params)
        captured["warnings"] = [{"category":w.category.__name__,"message":str(w.message)} for w in caught]
    finally: sys.settrace(before)
    return float(value), captured


def independent_model(namespace, acc, ro, omega):
    """Independent einsum assembly; return axes [week, frequency, i, j]."""
    from taijisgwb.constants import HUBBLE0
    signal_psd = 3*HUBBLE0**2/(2*np.pi**2)*omega/namespace['f_est']**3
    model = np.einsum('l,f,ijlwf->wfij', acc**2, namespace['spectrum_acc'], namespace['acc_corr_factor'])
    model += np.einsum('l,f,ijlwf->wfij', ro**2, namespace['spectrum_ro'], namespace['ro_corr_factor'])
    model += np.einsum('f,ijwf->wfij',signal_psd,namespace['orf'])
    return model


def stable_reference(model, data, nperbin, win_bw):
    """Scale-normalized Cholesky trace/logdet reference; no model regularization.

    Data is conj(z_i)*z_j, so its transpose is the covariance matching model.
    trace(solve(model, data.T)) equals the original elementwise contraction.
    """
    data = np.moveaxis(data,[0,1],[-2,-1]).swapaxes(-1,-2)
    scale = np.max(np.diagonal(model,axis1=-2,axis2=-1).real,axis=-1)
    normalized = model / scale[...,None,None]
    chol = np.linalg.cholesky(normalized)
    rhs = data / scale[...,None,None]
    y = np.linalg.solve(chol,rhs)
    solution = np.linalg.solve(chol.conj().swapaxes(-1,-2),y)
    trace = np.trace(solution,axis1=-2,axis2=-1).real
    logdet = 2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=-1) + 3*np.log(scale)
    exp = -nperbin*trace.sum(); coef = -nperbin*logdet.sum()
    eig = np.linalg.eigvalsh(normalized)
    return {'value':float((exp+coef)/win_bw),'ll_exp':float(exp),'ll_coef':float(coef),
            'minimum_scaled_eigenvalue':float(eig.min()),'maximum_condition_number':float(np.max(eig[...,-1]/eig[...,0])),
            'maximum_hermitian_error':float(np.max(np.abs(normalized-normalized.conj().swapaxes(-1,-2))))}
