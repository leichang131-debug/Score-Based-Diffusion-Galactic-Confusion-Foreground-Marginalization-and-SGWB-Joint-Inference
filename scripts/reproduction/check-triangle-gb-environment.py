#!/usr/bin/env python3
"""Local CPU environment/interface checks, not full notebook reproduction."""
import datetime
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/triangle-gb/environment'
WORK = ROOT / 'runs/triangle-gb/workspace'
for key, folder in [('MPLCONFIGDIR', 'matplotlib'), ('IPYTHONDIR', 'ipython'),
                    ('JUPYTER_RUNTIME_DIR', 'jupyter-runtime')]:
    path = ROOT / 'runs/triangle-gb' / folder
    path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(key, str(path))
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ.setdefault(key, '1')


def main():
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Locally executed environment checks only; no upstream notebook or posterior sampling run.',
              'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'python': platform.python_version(), 'machine': platform.machine(),
              'platform': platform.platform(), 'checks': {}, 'versions': {}}

    def check(name, fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            report['checks'][name] = {'passed': True, 'detail': detail,
                                      'seconds': time.perf_counter() - t0}
            print('PASS', name, flush=True)
        except Exception as exc:
            report['checks'][name] = {'passed': False, 'error': repr(exc)}
            print('FAIL', name, repr(exc), flush=True)

    def identity():
        assert platform.python_version() == '3.11.14'
        assert platform.machine() == 'arm64'
        assert Path(sys.prefix).resolve() == (ROOT / 'environments/triangle-gb/.venv').resolve()
        return {'prefix': 'environments/triangle-gb/.venv', 'cpu': True}
    check('isolated_runtime', identity)
    modules = ['numpy', 'scipy', 'matplotlib', 'healpy', 'pycbc', 'lal', 'h5py',
               'tqdm', 'Triangle.Constants', 'Triangle.FFTTools', 'Triangle.Noise',
               'Triangle.Orbit', 'Triangle.Data', 'Triangle.TDI', 'Triangle.GW',
               'Triangle_GB', 'bilby', 'nessai', 'nessai_bilby', 'torch', 'glasflow',
               'ipykernel', 'nbclient', 'jupyterlab', 'Triangle_BBH.Fisher', 'WF4Py.waveforms']
    for name in modules:
        check('import_' + name, lambda name=name: {'module': importlib.import_module(name).__name__})
    for name in ['numpy', 'scipy', 'healpy', 'PyCBC', 'lalsuite', 'matplotlib',
                 'bilby', 'nessai', 'nessai-bilby', 'torch', 'glasflow', 'h5py',
                 'jupyterlab', 'ipykernel', 'Triangle', 'Triangle_GB', 'Triangle_BBH', 'WF4Py']:
        try:
            report['versions'][name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            report['versions'][name] = None

    def origins():
        for name, source in [('Triangle', 'triangle-simulator'), ('Triangle_GB', 'triangle-gb')]:
            module = importlib.import_module(name)
            assert Path(module.__file__).resolve().is_relative_to(ROOT / 'external' / source)
        return 'Both packages import from pinned editable source checkouts.'
    check('editable_source_origins', origins)

    def paths():
        examples = WORK / 'Triangle-GB/Examples'
        assert (examples / '../../Triangle-Simulator/OrbitData/MicroSateOrbitEclipticTCB').resolve().is_dir()
        assert (examples / 'LDCEqualArmOrbit/SCP1.dat').is_file()
        return 'Original relative orbit paths resolve in ignored working-copy directory.'
    check('workspace_orbit_paths', paths)

    def response():
        import numpy as np
        from Triangle.Orbit import Orbit
        from Triangle.TDI import TDIStringManipulation
        from Triangle_GB import TDIFly, TDIFlyGB, TDIFlyGBNetwork
        orbit = Orbit(OrbitDir=str(ROOT / 'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB'), max_rows=256)
        x = TDIFly.X2_strings
        y = TDIStringManipulation.TDIStringCyc(x)
        z = TDIStringManipulation.TDIStringCyc(y)
        times = np.arange(2048) * 10.0
        gen = TDIFlyGB(orbit, [x, y, z], times, Nsparse=128, use_gpu=False, drop_points=1)
        pars = dict(A=1e-22, f0=0.003, fdot0=1e-17, inclination=0.7,
                    longitude=1.2, latitude=0.3, phase0=0.2, psi=0.4)
        td = gen(pars, domain='time')
        fd = gen(pars, domain='frequency')
        assert td.shape == (3, 1, 2048) and fd.shape == (3, 1, 128)
        assert np.isfinite(td).all() and np.isfinite(fd).all()
        assert np.max(np.abs(td)) > 0 and np.max(np.abs(fd)) > 0
        net = TDIFlyGBNetwork([orbit, orbit], [x, y, z], times, Nsparse=128, use_gpu=False)
        network_fd = net(pars)
        assert isinstance(network_fd, list) and len(network_fd) == 2
        assert all(h.shape == (3, 1, 128) and np.isfinite(h).all() and
                   np.max(np.abs(h)) > 0 for h in network_fd)
        network_band = net.response_on_band(pars, StartBound=40, EndBound=80)
        assert network_band.shape == (4, 1, 41) and np.isfinite(network_band).all()
        return {'time_shape': list(td.shape), 'frequency_shape': list(fd.shape),
                'network_detector_shapes': [list(h.shape) for h in network_fd],
                'network_band_shape': list(network_band.shape), 'finite': True,
                'time_peak': float(np.max(np.abs(td))), 'frequency_peak': float(np.max(np.abs(fd))),
                'note': 'Small synthetic interface check; two identical orbits are not a physical detector network validation.'}
    check('small_cpu_response', response)

    def torch_flow():
        import torch
        from glasflow import RealNVP
        torch.manual_seed(42)
        flow = RealNVP(n_inputs=2, n_transforms=2, n_neurons=8, n_blocks_per_transform=1)
        x = torch.randn(8, 2)
        logp = flow.log_prob(x)
        loss = -logp.mean()
        loss.backward()
        assert torch.isfinite(logp).all()
        assert all(torch.isfinite(p.grad).all() for p in flow.parameters() if p.grad is not None)
        return {'device': str(x.device), 'log_prob_shape': list(logp.shape), 'finite_gradients': True}
    check('glasflow_torch_cpu_backward', torch_flow)

    def sampler():
        from bilby.core.sampler import get_sampler_class
        cls = get_sampler_class('nessai')
        assert cls.__module__.startswith('nessai_bilby')
        return {'registered_class': cls.__module__ + '.' + cls.__name__,
                'scope': 'Plugin discovery only; nested sampling not started.'}
    check('bilby_nessai_plugin', sampler)

    def kernel():
        import nbformat
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        from jupyter_client.kernelspec import KernelSpecManager
        kernel_root = ROOT / 'environments/triangle-gb/.venv/share/jupyter/kernels'
        ksm = KernelSpecManager(kernel_dirs=[str(kernel_root)])
        km = KernelManager(kernel_name='triangle-gb', kernel_spec_manager=ksm)
        nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(
            "import sys, json, numpy, Triangle_GB, bilby, h5py\n"
            "with h5py.File('/Users/taijidatacenter/workspace/TDCData/0_1_VGB_TDIXYZ.h5') as f:\n"
            "    assert isinstance(f, h5py.File) and f['time'][0] == 2000\n"
            "with h5py.File('/Users/taijidatacenter/workspace/TDCData/0_1_VGB_parameters.h5') as f:\n"
            "    assert isinstance(f, h5py.File) and len(f['A']) == 55\n"
            "with h5py.File('/Users/taijidatacenter/Downloads/LDCData/LDC2_sangria_training_v2.h5') as f:\n"
            "    assert isinstance(f, h5py.File) and len(f['sky/dgb/cat']) == 26000000\n"
            "assert sys.version_info[:2] == (3,11)\n"
            "print(json.dumps({'python': sys.version.split()[0], 'sum': int(numpy.arange(4).sum())}))")])
        try:
            result = NotebookClient(nb, km=km, timeout=120,
                resources={'metadata': {'path': str(WORK / 'Triangle-GB/Examples')}}).execute()
        finally:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
            km.cleanup_resources()
        assert result.cells[0].execution_count == 1
        assert not any(o.output_type == 'error' for o in result.cells[0].outputs)
        nbformat.write(result, OUT / 'kernel-smoke.ipynb')
        return 'Dedicated kernel executed a new synthetic import/array cell locally; upstream examples untouched.'
    check('dedicated_jupyter_kernel', kernel)
    prepared_inputs = [ROOT/'data/raw/triangle-gb'/name for name in
        ['0_1_VGB_TDIXYZ.h5','0_1_VGB_parameters.h5','LDC2_sangria_training_v2.h5']]
    cache = WORK/'Triangle-GB/Test/dgb_parameters.txt'
    report['all_five_example_input_files_available'] = all(p.is_file() for p in prepared_inputs) and cache.is_file()
    report['remaining_example_requirements'] = [
        'Original-scale complete notebook execution and scientific output audits remain pending.',
        'Example 1/2 original default orbit has documented boundary extrapolation; strict coverage is not a verified accuracy claim.',
        'Parameter-estimation multiprocessing budgets and posterior convergence require separate validation.']
    report['all_environment_checks_pass'] = all(c['passed'] for c in report['checks'].values())
    report['all_five_examples_ready'] = False
    report['elapsed_seconds'] = time.perf_counter() - started
    lock = ROOT / 'environments/triangle-gb/requirements-macos-arm64-py311.txt'
    report['requirements_sha256'] = hashlib.sha256(lock.read_bytes()).hexdigest()
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Environment checks:', sum(c['passed'] for c in report['checks'].values()), '/', len(report['checks']), flush=True)
    if not report['all_environment_checks_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
