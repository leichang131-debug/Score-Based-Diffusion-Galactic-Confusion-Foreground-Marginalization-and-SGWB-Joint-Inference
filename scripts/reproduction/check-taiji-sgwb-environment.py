#!/usr/bin/env python3
"""Check original imports and small CPU interfaces; never run full demos."""
import ast
import datetime
import hashlib
import importlib
import importlib.metadata as metadata
import json
import multiprocessing
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "external/taiji-sgwb"
OUT = ROOT / "results/taiji-sgwb/environment"
WORK = ROOT / "runs/taiji-sgwb/environment-check"
WORK.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(WORK / "matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
for name in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ.setdefault(name, "1")


def toy_log_likelihood(params):
    """A synthetic Gaussian, not the SGWB likelihood."""
    import numpy as np
    return -0.5 * sum(float(np.sum(np.asarray(branch) ** 2)) for branch in params)


def square(value):
    return value * value


def backend_readback(filename):
    import numpy as np
    from eryn.backends import HDFBackend
    backend = HDFBackend(filename, read_only=True)
    state = backend.get_last_sample()
    assert backend.iteration == 3
    assert np.isfinite(state.log_like).all()
    return {"iteration": int(backend.iteration), "branches": list(backend.get_chain()),
            "finite_last_state": True}


def main():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Stage 2 environment/import and small synthetic CPU interface checks only. No TDC dataset, full demo, SGWB posterior or scientific calibration.",
              "python": platform.python_version(), "machine": platform.machine(),
              "platform": platform.platform(), "executable": str(Path(sys.executable).relative_to(ROOT)),
              "checks": {}, "versions": {}}

    def check(name, fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            report["checks"][name] = {"passed": True, "detail": detail, "seconds": time.perf_counter() - t0}
            print("PASS", name, flush=True)
        except Exception as exc:
            report["checks"][name] = {"passed": False, "error": repr(exc), "seconds": time.perf_counter() - t0}
            print("FAIL", name, repr(exc), flush=True)

    def identity():
        assert platform.python_version() == "3.11.14" and platform.machine() == "arm64"
        assert Path(sys.prefix).resolve() == (ROOT / "environments/taiji-sgwb/.venv").resolve()
        assert not sys.flags.no_site
        return {"prefix": "environments/taiji-sgwb/.venv", "CPU": True}
    check("isolated_runtime", identity)

    def imports(filename):
        path = SOURCE / "demos" / filename
        source = path.read_text()
        nodes = [n for n in ast.parse(source).body if isinstance(n, (ast.Import, ast.ImportFrom))]
        namespace = {}
        for node in nodes:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
        return {"source": "external/taiji-sgwb/demos/" + filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "statements": [ast.get_source_segment(source, n) for n in nodes],
                "executed_import_statements": len(nodes), "demo_body_executed": False}
    for name in ["template_nofg_28t.py", "rj_nofg_28t.py"]:
        check("original_imports_" + name, lambda name=name: imports(name))
    for p in sorted((SOURCE / "src/taijisgwb").rglob("*.py")):
        relative = p.relative_to(SOURCE / "src").with_suffix("")
        module = ".".join(relative.parts)
        if module.endswith(".__init__"):
            module = module[:-9]
        check("import_" + module, lambda module=module: {"module": importlib.import_module(module).__name__})

    def origins():
        import taijisgwb
        assert Path(taijisgwb.__file__).resolve().is_relative_to(SOURCE)
        direct = json.loads(metadata.distribution("taijisgwb").read_text("direct_url.json"))
        assert direct["dir_info"]["editable"]
        assert Path(unquote(urlparse(direct["url"]).path)).resolve() == SOURCE.resolve()
        return {"module": str(Path(taijisgwb.__file__).relative_to(ROOT)), "editable": True}
    check("original_editable_package", origins)

    def pipeline():
        import numpy as np
        from scipy.signal import windows, ShortTimeFFT
        from taijisgwb.detector.tdi import aet_from_xyz, tdi_X2, tdi_aet_from_tdi_x
        from taijisgwb.detector.noise import TaijiNoisePSD
        from taijisgwb.waveform import calc_omega_powerlaw, calc_omega_dbpowerlaw
        from taijisgwb.utils import psd_from_omega, omega_from_psd
        x = np.random.default_rng(20261012).normal(size=(3, 512))
        aet = np.asarray(aet_from_xyz(*x))
        assert aet.shape == x.shape and np.allclose(np.sum(x*x), np.sum(aet*aet))
        stft = ShortTimeFFT(windows.kaiser(128, beta=14), 128, 0.1, fft_mode="onesided", scale_to="psd")
        z = stft.stft_detrend(aet[0], "constant", p0=0, p1=4, k_offset=64)
        assert z.shape == (65, 4) and np.isfinite(z).all()
        f = np.array([0.001, 0.003, 0.01])
        omega = calc_omega_powerlaw(f, 1e-12, 2/3)
        assert np.allclose(omega_from_psd(f, psd_from_omega(f, omega)), omega, rtol=1e-14, atol=0)
        pt = calc_omega_dbpowerlaw(f, 1e-10, 0.0002, 0.15, 0.65)
        assert np.all(pt > 0) and np.isfinite(pt).all()
        assert np.all(TaijiNoisePSD.calc_psd_acc(f) > 0) and np.all(TaijiNoisePSD.calc_psd_ro(f) > 0)
        assert len(tdi_aet_from_tdi_x(tdi_X2)) == 3
        return {"AET_shape": list(aet.shape), "STFT_shape": list(z.shape), "synthetic": True}
    check("original_numeric_interfaces", pipeline)

    def orbit_io():
        import numpy as np
        import h5py
        from taijisgwb.detector.orbit import EqualArmOrbit, InterpolationOrbit
        from taijisgwb.detector.constants import MOSA_LABELS, SC_LABELS
        orbit = EqualArmOrbit()
        t = np.arange(8, dtype=float) * 86400
        xyz = orbit.calc_sc_position(t)
        file = WORK / "synthetic-orbit.hdf5"
        with h5py.File(file, "w") as h5:
            group = h5.create_group("tcb")
            group["t"] = t
            for label, values in orbit.calc_ltt(t).items():
                group["l_" + label] = values
            for label in SC_LABELS:
                arr = np.empty(len(t), dtype=[("x", "f8"), ("y", "f8"), ("z", "f8")])
                for index, axis in enumerate("xyz"):
                    arr[axis] = xyz[label][:, index]
                group["sc_" + label] = arr
        loaded = InterpolationOrbit(file)
        for label in MOSA_LABELS:
            assert np.allclose(loaded.calc_ltt(t)[label], orbit.calc_ltt(t)[label])
        for label in SC_LABELS:
            assert np.allclose(loaded.calc_sc_position(t)[label], xyz[label])
        return {"file": str(file.relative_to(ROOT)), "synthetic": True, "samples": len(t)}
    check("hdf5_orbit_interface", orbit_io)

    def response():
        import numpy as np
        from taijisgwb import Interferometer
        from taijisgwb.detector.orbit import EqualArmOrbit
        from taijisgwb.detector.tdi import tdi_X2, tdi_aet_from_tdi_x
        t = np.array([100000., 200000.])
        f = np.array([0.001, 0.003, 0.005])
        detector = Interferometer(EqualArmOrbit())
        a, e, _ = tdi_aet_from_tdi_x(tdi_X2)
        acc = detector.calc_noise_acc_corr_factor(f, t, a).to_array
        ro = detector.calc_noise_ro_corr_factor(f, t, a, e).to_array
        auto = detector.calc_orf(f, t, a)
        cross = detector.calc_orf(f, t, a, e)
        reverse = detector.calc_orf(f, t, e, a)
        for array in [acc, ro, auto, cross, reverse]:
            assert np.isfinite(array).all()
        assert acc.shape == (6, 2, 3) and auto.shape == (2, 3)
        assert np.all(auto > 0)
        assert np.allclose(cross, reverse.conj(), rtol=1e-12, atol=1e-20)
        return {"noise_shape": list(acc.shape), "ORF_shape": list(auto.shape),
                "sky_nside": 14, "synthetic_equal_arm": True, "full_year_run": False}
    check("original_response_interfaces", response)

    def fork():
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(2) as pool:
            values = pool.map(square, [1, 2, 3])
        assert values == [1, 4, 9]
        return {"start_method": "fork", "workers": 2}
    check("fork_pool", fork)

    def fixed_sampler():
        import numpy as np
        import eryn.ensemble
        import eryn.prior
        import eryn.backends
        np.random.seed(20261012)
        names = ["acc", "ro", "sgwb"]
        ndim = dict(zip(names, [6, 6, 2]))
        priors = {name: {d: eryn.prior.uniform_dist(-5., 5.) for d in range(ndim[name])} for name in names}
        params = {name: np.random.uniform(-1., 1., (2, 32, 1, ndim[name])) for name in names}
        filename = WORK / "template-interface.h5"
        filename.unlink(missing_ok=True)
        backend = eryn.backends.HDFBackend(str(filename))
        with multiprocessing.get_context("fork").Pool(2) as pool:
            sampler = eryn.ensemble.EnsembleSampler(32, ndim, toy_log_likelihood, priors,
                tempering_kwargs=dict(ntemps=2), nbranches=3, branch_names=names,
                nleaves_min={n: 1 for n in names}, nleaves_max={n: 1 for n in names}, pool=pool, backend=backend)
            sampler.run_mcmc(params, 3, burn=0, thin_by=1, progress=False)
        chains = backend.get_chain()
        assert backend.iteration == 3 and all(np.isfinite(c).all() for c in chains.values())
        raw = subprocess.check_output([sys.executable, str(Path(__file__).resolve()), "--read-backend", str(filename)])
        readback = json.loads(raw.decode())
        return {"synthetic_gaussian": True, "physical_parameters": False,
                "branches": ndim, "ntemps": 2, "nwalkers": 32, "stored_steps": 3,
                "chain_shapes": {n: list(c.shape) for n, c in chains.items()}, "separate_process_readback": readback}
    check("template_sampler_hdf5_readback", fixed_sampler)

    def rj_sampler():
        import numpy as np
        import eryn.ensemble
        import eryn.prior
        import eryn.moves
        import eryn.state
        np.random.seed(20261013)
        names = ["acc", "ro", "sgwb_knot", "sgwb_edge"]
        ndim = dict(zip(names, [6, 6, 2, 2]))
        maximum = dict(zip(names, [1, 1, 3, 1]))
        minimum = {name: 1 for name in names}
        priors = {name: {d: eryn.prior.uniform_dist(-5., 5.) for d in range(ndim[name])} for name in names}
        params = {name: np.random.uniform(-1., 1., (2, 32, maximum[name], ndim[name])) for name in names}
        inds = {name: np.ones((2, 32, maximum[name]), dtype=bool) for name in names}
        inds["sgwb_knot"][:, :, 1:] = False
        noise_move = eryn.moves.StretchMove(live_dangerously=True,
            gibbs_sampling_setup={names[0]: None, names[1]: None})
        cov = {names[2]: np.diag([0.02, 0.01])**2, names[3]: np.diag([0.02, 0.02])**2}
        sgwb_move = eryn.moves.GaussianMove(cov, gibbs_sampling_setup={names[2]: None, names[3]: None})
        moves = eryn.moves.CombineMove([noise_move, sgwb_move])
        sampler = eryn.ensemble.EnsembleSampler(32, ndim, toy_log_likelihood, priors,
            tempering_kwargs=dict(ntemps=2), nbranches=4, branch_names=names,
            nleaves_max=maximum, nleaves_min=minimum, moves=moves, rj_moves=True)
        state = eryn.state.State(params, log_prior=sampler.compute_log_prior(params, inds=inds),
            log_like=sampler.compute_log_like(params, inds=inds)[0], inds=inds)
        sampler.run_mcmc(state, 8, burn=0, thin_by=1, progress=False)
        counts = sampler.get_inds()["sgwb_knot"].sum(axis=-1)
        assert counts.min() >= 1 and counts.max() <= 3
        assert counts.max() > 1
        assert np.isfinite(sampler.get_log_like()).all()
        return {"synthetic_gaussian": True, "physical_spectrum": False, "stored_steps": 8,
                "nleaves_min": int(counts.min()), "nleaves_max": int(counts.max()),
                "original_move_classes": ["StretchMove", "GaussianMove", "CombineMove"], "rj_moves": True}
    check("rj_sampler_original_move_interfaces", rj_sampler)

    def plot():
        import numpy as np
        import matplotlib.pyplot as plt
        from taijisgwb.plotlib import plot_corner
        # Exercise the original module import; save a basic headless figure.
        fig, ax = plt.subplots()
        ax.plot(np.arange(8), np.arange(8)**2)
        file = WORK / "headless.png"
        fig.savefig(file)
        plt.close(fig)
        assert file.stat().st_size > 0 and callable(plot_corner)
        return {"backend": "Agg", "file": str(file.relative_to(ROOT)), "bytes": file.stat().st_size}
    check("headless_plot_write", plot)

    def source():
        status = subprocess.check_output(["git", "-C", str(SOURCE), "status", "--porcelain"]).decode().strip()
        pin = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"]).decode().strip()
        assert not status and pin == "4afaad4044b08721e7f1ce29cba3b0d912636dce"
        return {"pin": pin, "clean": True}
    check("upstream_source_unchanged", source)
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
        report["versions"][dist.metadata["Name"]] = dist.version
    report["elapsed_seconds"] = time.perf_counter() - start
    report["all_checks_pass"] = all(c["passed"] for c in report["checks"].values())
    (OUT / "check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Environment checks: {sum(c['passed'] for c in report['checks'].values())}/{len(report['checks'])} passed.", flush=True)
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--read-backend":
        print(json.dumps(backend_readback(sys.argv[2])))
    else:
        main()
