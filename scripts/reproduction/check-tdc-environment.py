"""Validate the shared CPU environment, not full tutorial reproduction."""
import hashlib
import datetime
import importlib
import importlib.metadata
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "external/triangle-simulator"
OUT = ROOT / "results/tdc/environment"


def square(x):
    return x * x


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "runs/tdc-setup/matplotlib"))
    os.environ.setdefault("IPYTHONDIR", str(ROOT / "runs/tdc-setup/ipython"))
    start = time.perf_counter()
    report = {"scope": "Shared environment smoke checks; full tutorials not executed",
              "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "python": platform.python_version(), "machine": platform.machine(),
              "platform": platform.platform(), "source_commit": subprocess.check_output(
                  ["git", "-C", str(SRC), "rev-parse", "HEAD"], text=True).strip(),
              "checks": {}, "versions": {}}

    def check(name, fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            report["checks"][name] = {"passed": True, "detail": detail,
                                      "seconds": time.perf_counter() - t0}
            print("PASS", name, flush=True)
        except Exception as exc:
            report["checks"][name] = {"passed": False, "error": repr(exc),
                                      "seconds": time.perf_counter() - t0}
            print("FAIL", name, repr(exc), flush=True)

    def provenance():
        assert platform.python_version() == "3.9.19"
        assert platform.machine() == "arm64"
        assert report["source_commit"] == "ab796358e9a36c8987f6bb53a97230d603bfdfd5"
        status = subprocess.check_output(["git", "-C", str(SRC), "status", "--porcelain"], text=True)
        assert not status
        notebooks = sorted((SRC / "Tutorials").glob("*.ipynb"))
        assert len(notebooks) == 5
        return {"source_clean": True,
                "notebooks": [{"path": str(p.relative_to(SRC)),
                               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in notebooks],
                "uv_lock_sha256": hashlib.sha256((SRC / "uv.lock").read_bytes()).hexdigest(),
                "requirements_sha256": hashlib.sha256((ROOT / "environments/tdc/requirements-upstream.txt").read_bytes()).hexdigest()}
    check("python_source_and_notebook_provenance", provenance)

    def imports():
        modules = ["numpy", "scipy", "matplotlib", "healpy", "pycbc", "h5py",
                   "tqdm", "jupyterlab", "ipykernel", "nbclient", "lal", "lalsimulation",
                   "Triangle"]
        result = {}
        for name in modules:
            mod = importlib.import_module(name)
            result[name] = "imported"
            if name == "Triangle":
                assert Path(mod.__file__).resolve().is_relative_to(SRC)
        for module in sorted((SRC / "Triangle").glob("*.py")):
            if module.stem != "__init__":
                importlib.import_module("Triangle." + module.stem)
        return result
    check("imports_and_editable_source", imports)

    import numpy as np
    import h5py
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from scipy.interpolate import CubicSpline

    def numerical():
        x = np.linspace(0, 1, 128)
        y = np.sin(2 * np.pi * x)
        recovered = np.fft.irfft(np.fft.rfft(y), n=len(y))
        assert np.max(np.abs(recovered - y)) < 1e-12
        assert np.all(np.isfinite(CubicSpline(x, y)(x)))
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set(xlabel="Time (s)", ylabel="Synthetic amplitude",
               title="Environment check: synthetic signal")
        fig.savefig(OUT / "synthetic-numerical-check.png", dpi=120)
        plt.close(fig)
        return {"fft_max_error": float(np.max(np.abs(recovered - y)))}
    check("fft_interpolation_and_plot", numerical)

    from pycbc.waveform import get_td_waveform
    for approximant in ["IMRPhenomT", "SEOBNRv4_opt"]:
        def waveform(approximant=approximant):
            hp, hc = get_td_waveform(approximant=approximant, mass1=30, mass2=30,
                                    delta_t=1 / 1024, f_lower=30)
            assert len(hp) > 0 and len(hp) == len(hc)
            assert np.isfinite(hp.numpy()).all() and np.isfinite(hc.numpy()).all()
            return {"length": len(hp), "delta_t": hp.delta_t,
                    "scope": "Backend smoke check using small stellar masses, not tutorial MBHB physics"}
        check("waveform_" + approximant, waveform)

    def data():
        files = sorted((SRC / "OrbitData").rglob("*.dat")) + sorted((SRC / "GWData").glob("*.np*"))
        result = []
        for path in files:
            arrays = np.load(path) if path.suffix in (".npy", ".npz") else np.loadtxt(path)
            if isinstance(arrays, np.lib.npyio.NpzFile):
                shapes = {key: list(arrays[key].shape) for key in arrays.files}
                assert all(np.isfinite(arrays[key]).all() for key in arrays.files)
                arrays.close()
            else:
                shapes = list(arrays.shape)
                assert np.isfinite(arrays).all()
            result.append({"path": str(path.relative_to(SRC)), "bytes": path.stat().st_size,
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "shapes": shapes})
        assert result
        return result
    check("bundled_data_readability", data)

    def orbit():
        from Triangle.Orbit import Orbit
        obj = Orbit(str(SRC / "OrbitData/MicroSateOrbitEclipticTCB"))
        sample_times = np.array([1000., 10000., 100000.])
        ltt = {key: fn(sample_times) for key, fn in obj._LTTfunctions.items()}
        assert len(ltt) == 6
        assert all(np.isfinite(values).all() and (values > 0).all() for values in ltt.values())
        return {"orbit_rows": obj.N, "time_range_seconds": [float(obj.tdata[0]), float(obj.tdata[-1])],
                "sample_times_seconds": sample_times.tolist(),
                "light_travel_times_seconds": {k: v.tolist() for k, v in ltt.items()}}
    check("triangle_orbit_light_travel_time", orbit)

    def hdf5():
        with tempfile.TemporaryDirectory(dir=ROOT / "runs/tdc-setup") as tmp:
            with h5py.File(Path(tmp) / "synthetic.h5", "w") as f:
                group = f.create_group("eta")
                for link in ["12", "23", "31", "21", "32", "13"]:
                    group[link] = np.zeros(32)
                group["time"] = np.arange(32.)
            with h5py.File(Path(tmp) / "synthetic.h5", "r") as f:
                assert set(f["eta"].keys()) == {"12", "23", "31", "21", "32", "13", "time"}
                from Triangle.Data import read_dict_from_h5
                recovered = read_dict_from_h5(f["/"])
                assert recovered["eta"]["time"].shape == (32,)
                assert np.isfinite(recovered["eta"]["12"]).all()
        return "Synthetic HDF5 roundtrip only; actual Tutorial 5 data pending teacher confirmation"
    check("synthetic_hdf5_interface", hdf5)

    def pool():
        with mp.get_context("spawn").Pool(2) as workers:
            answer = workers.map(square, [1, 2, 3, 4])
        assert answer == [1, 4, 9, 16]
        return {"start_method": "spawn", "workers": 2, "result": answer,
                "scope": "Generic process test; full Triangle notebook pool workloads not executed"}
    check("cpu_multiprocessing", pool)

    def kernel():
        import nbformat
        from nbclient import NotebookClient
        nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(
            "import sys, numpy, Triangle\nassert sys.version_info[:3] == (3,9,19)\nprint('TDC_KERNEL_OK')")])
        NotebookClient(nb, timeout=120, kernel_name="triangle-tdc",
                       resources={"metadata": {"path": str(SRC / "Tutorials")}}).execute()
        text = "".join(o.get("text", "") for o in nb.cells[0].outputs)
        assert "TDC_KERNEL_OK" in text
        return "Fresh registered Jupyter kernel executed NumPy/Triangle import cell in Tutorials directory"
    check("fresh_jupyter_kernel", kernel)

    for dist in importlib.metadata.distributions():
        report["versions"][dist.metadata["Name"]] = dist.version
    report["seconds"] = time.perf_counter() - start
    report["passed"] = all(x["passed"] for x in report["checks"].values())
    (OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Overall:", report["passed"], flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
