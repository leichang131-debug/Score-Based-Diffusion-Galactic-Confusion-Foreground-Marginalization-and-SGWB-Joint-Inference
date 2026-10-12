#!/usr/bin/env python3
"""Validate complete official HDF5 inputs and the original demo read interfaces."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/data"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "runs/taiji-sgwb/matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
for name in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ.setdefault(name, "1")
import h5py
import numpy as np


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def scan_dataset(ds):
    result = {"shape": list(ds.shape), "dtype": str(ds.dtype), "numeric_fields": {}}
    names = list(ds.dtype.names) if ds.dtype.names else [None]
    for name in names:
        dtype = ds.dtype[name] if name else ds.dtype
        if not np.issubdtype(dtype, np.number):
            continue
        stats = {"count": 0, "nan": 0, "inf": 0, "minimum": None, "maximum": None}
        if ds.ndim == 0:
            chunks = [ds[()]]
        else:
            axis = int(np.argmax(ds.shape))
            def blocks():
                for start in range(0, ds.shape[axis], 65536):
                    sel = [slice(None)] * ds.ndim
                    sel[axis] = slice(start, start + 65536)
                    yield ds[tuple(sel)]
            chunks = blocks()
        for block in chunks:
            values = np.asarray(block[name] if name else block)
            stats["count"] += int(values.size)
            stats["nan"] += int(np.isnan(values).sum())
            stats["inf"] += int(np.isinf(values).sum())
            finite = values[np.isfinite(values)]
            if finite.size:
                if np.iscomplexobj(finite):
                    finite = np.abs(finite)
                lo, hi = float(finite.min()), float(finite.max())
                stats["minimum"] = lo if stats["minimum"] is None else min(stats["minimum"], lo)
                stats["maximum"] = hi if stats["maximum"] is None else max(stats["maximum"], hi)
        result["numeric_fields"][name or "values"] = stats
    if not result["numeric_fields"] and ds.size == 1:
        value = ds[()]
        result["value"] = value.decode() if isinstance(value, bytes) else str(value)
    return result


def original_read(filename, data_path):
    """Execute original imports, HDF5 read and trimming/AET nodes only."""
    path = ROOT / "external/taiji-sgwb/demos" / filename
    text = path.read_text()
    tree = ast.parse(text)
    namespace = {"strain_file": data_path}
    executed = []
    selected = {"tdi_names", "ntdi", "dt", "fsample", "ndrop_points", "time", "strain_AET2"}
    for node in tree.body:
        run = isinstance(node, (ast.Import, ast.ImportFrom))
        if isinstance(node, ast.With) and "h5py.File(strain_file" in ast.get_source_segment(text, node):
            run = True
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in selected for t in node.targets):
            run = True
        if run:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
            executed.append({"line": node.lineno, "source": ast.get_source_segment(text, node)})
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "strain_AET2" for t in node.targets) and "ndrop_points" in ast.get_source_segment(text, node):
            break
    aet = np.asarray(namespace["strain_AET2"])
    assert aet.shape == (3, len(namespace["time"])) and np.isfinite(aet).all()
    return namespace, {"source": str(path.relative_to(ROOT)), "sha256": sha256(path),
                       "executed_nodes": executed, "AET_shape": list(aet.shape),
                       "all_AET_finite": True, "full_demo_executed": False}


def main():
    started = time.perf_counter()
    report = {"schema_version": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Complete official 2.8 input and orbit validation; original read/AET/trim interfaces only. No response-grid construction or inference.",
              "checks": {}, "issues": []}
    raw = ROOT / "data/raw/taiji-sgwb"
    data_path = raw / "TDCII2.8.h5"
    orbit_path = raw / "MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5"
    download = json.loads((OUT / "download.json").read_text())
    inventories = {}
    for kind, path in [("data", data_path), ("orbit", orbit_path)]:
        assert sha256(path) == download[kind]["sha256"]
        report["checks"][kind + "_sha256_matches_download"] = True
        inventory = {}
        with h5py.File(path, "r") as h5:
            def visit(name, obj):
                if isinstance(obj, h5py.Dataset):
                    inventory[name] = scan_dataset(obj)
            h5.visititems(visit)
        inventories[kind] = inventory
        report["checks"][kind + "_complete_numeric_scan_finite"] = all(
            s["nan"] == 0 and s["inf"] == 0 for d in inventory.values() for s in d["numeric_fields"].values())
        print("SCANNED", kind, len(inventory), "datasets", flush=True)
    (OUT / "hdf5-inventory.json").write_text(json.dumps(inventories, indent=2) + "\n")
    with h5py.File(data_path, "r") as h5:
        required = ["data/time", "data/XYZ", "data/foreground", "data/noise", "data/sgwb"]
        report["checks"]["all_original_and_component_fields_exist"] = all(k in h5 for k in required)
        t = h5["data/time"][()]
        n = len(t)
        dt = float(t[1] - t[0])
        report["checks"]["time_strictly_increasing_uniform"] = bool(np.all(np.diff(t) == dt) and dt > 0)
        report["checks"]["time_origin_matches_original_segment_formula"] = bool(t[0] == 0)
        report["checks"]["all_component_shapes_match_XYZ"] = all(h5[k].shape == (3, n) for k in required[1:])
        report["checks"]["sampling_matches_official_generation"] = dt == 5.
        stats = {"total_sum_squared_error": 0., "total_sum_squared_reference": 0.,
                 "residual_sum_squared_error": 0., "residual_sum_squared_reference": 0.,
                 "total_max_abs_error": 0., "residual_max_abs_error": 0.}
        for start in range(0, n, 65536):
            sl = (slice(None), slice(start, start+65536))
            xyz, fg, noise, sgwb = [h5["data/" + name][sl] for name in ["XYZ", "foreground", "noise", "sgwb"]]
            total = sgwb + noise + fg
            residual = xyz - fg
            target = noise + sgwb
            e1, e2 = xyz-total, residual-target
            for prefix, err, reference in [("total", e1, total), ("residual", e2, target)]:
                stats[prefix+"_sum_squared_error"] += float(np.sum(err*err))
                stats[prefix+"_sum_squared_reference"] += float(np.sum(reference*reference))
                stats[prefix+"_max_abs_error"] = max(stats[prefix+"_max_abs_error"], float(np.max(np.abs(err))))
        for prefix in ["total", "residual"]:
            ratio = np.sqrt(stats[prefix+"_sum_squared_error"] / stats[prefix+"_sum_squared_reference"])
            stats[prefix+"_relative_L2_error"] = float(ratio)
            report["checks"][prefix+"_component_identity"] = bool(ratio < 1e-12)
        report["component_identities"] = stats
        parameters = {}
        def params(name, obj):
            if isinstance(obj, h5py.Dataset):
                value = obj[()]
                values = np.asarray(value)
                parameters[name] = values.item() if values.size == 1 else values.tolist()
        h5["data/parameters"].visititems(params)
        report["injected_parameters"] = parameters
        report["checks"]["powerlaw_injection_matches_baseline"] = parameters["sgwb/omega0"] == 1e-12 and np.isclose(parameters["sgwb/n"], 2/3)
        acc = {k: v for k, v in parameters.items() if "ACC_noise_amplitudes" in k}
        oms = {k: v for k, v in parameters.items() if "OMS_noise_amplitudes" in k}
        report["checks"]["six_ACC_and_six_OMS_injections"] = len(acc) == len(oms) == 6
        report["checks"]["noise_truth_inside_original_priors"] = all(.75*3e-15 <= v <= 1.25*3e-15 for v in acc.values()) and all(.75*8e-12 <= v <= 1.25*8e-12 for v in oms.values())
        report["time_axis"] = {"samples": n, "first_seconds": float(t[0]), "last_seconds": float(t[-1]),
                               "dt_seconds": dt, "sampling_Hz": 1/dt, "nyquist_Hz": .5/dt}
        np.savez_compressed(OUT / "input-preview.npz", time=t[:128], XYZ=h5["data/XYZ"][:, :128],
                            foreground=h5["data/foreground"][:, :128], noise=h5["data/noise"][:, :128], sgwb=h5["data/sgwb"][:, :128])
    alias = ROOT / "runs/taiji-sgwb/workspace/data/TDCII2-8.h5"
    report["original_read_interfaces"] = []
    trim_time = None
    for name in ["template_nofg_28t.py", "rj_nofg_28t.py"]:
        ns, evidence = original_read(name, alias)
        report["original_read_interfaces"].append(evidence)
        trim_time = ns["time"]
        report["checks"]["original_read_" + name] = evidence["all_AET_finite"]
        del ns
    nperseg = int(7*86400 / dt)
    nseg = len(trim_time) // nperseg
    tperseg = nperseg * dt
    centers = (np.arange(nseg)+.5) * tperseg + int(2000/dt)*dt
    from taijisgwb.detector.orbit import InterpolationOrbit
    from taijisgwb.detector.constants import MOSA_LABELS, SC_LABELS
    orbit = InterpolationOrbit(orbit_path)
    ot = orbit.t_sample
    report["checks"]["orbit_time_strictly_increasing"] = bool(np.all(np.diff(ot) > 0))
    report["checks"]["orbit_covers_full_data_time"] = bool(ot[0] <= t[0] and ot[-1] >= t[-1])
    report["checks"]["orbit_covers_trimmed_data_time"] = bool(ot[0] <= trim_time[0] and ot[-1] >= trim_time[-1])
    report["checks"]["orbit_covers_all_original_segment_centers"] = bool(np.all((centers >= ot[0]) & (centers <= ot[-1])))
    ltt = orbit.calc_ltt(centers)
    positions = orbit.calc_sc_position(centers)
    arms = orbit.calc_arm_vector(centers)
    report["checks"]["original_orbit_interpolation_finite"] = all(np.isfinite(ltt[m]).all() and np.all(ltt[m] > 0) and np.isfinite(arms[m]).all() for m in MOSA_LABELS) and all(np.isfinite(positions[s]).all() for s in SC_LABELS)
    orbit_details = {"first_seconds": float(ot[0]), "last_seconds": float(ot[-1]), "samples": len(ot),
        "all_centers": centers.tolist(), "light_travel_time_seconds": {m: {"minimum": float(ltt[m].min()), "maximum": float(ltt[m].max())} for m in MOSA_LABELS},
        "structured_tt_fields_read_by_original_scipy_interface": True,
        "no_extrapolation_at_original_analysis_times": report["checks"]["orbit_covers_all_original_segment_centers"]}
    report["orbit"] = orbit_details
    flo = 1/tperseg
    nperbin = int(1e-5/flo)
    f = np.arange(nperseg//2+1) * flo
    nbin = len(f)//nperbin
    f = f[:nbin*nperbin].reshape(-1,nperbin).mean(axis=-1)
    f = f[(f >= 1e-4) & (f < 5e-2)]
    f = f[~(((f >= 2.35e-2) & (f < 2.65e-2)) | ((f >= 4.7e-2) & (f < 5.2e-2)))]
    report["original_analysis_geometry"] = {"trim_each_end_points": int(2000/dt), "trim_each_end_seconds": 2000,
        "trimmed_samples": len(trim_time), "weekly_samples": nperseg, "full_week_segments": nseg,
        "unused_tail_samples": len(trim_time)-nseg*nperseg, "original_frequency_bins_per_combined_bin": nperbin,
        "actual_combined_bin_spacing_Hz": nperbin*flo, "retained_frequency_bins": len(f),
        "first_retained_frequency_Hz": float(f[0]), "last_retained_frequency_Hz": float(f[-1]),
        "geometry_only_no_STFT_executed": True}
    report["checks"]["positive_nonempty_analysis_grid"] = bool(nseg > 0 and nperbin > 0 and len(f) > 0 and np.all(f > 0))
    np.savez_compressed(OUT / "analysis-grid.npz", frequency=f, segment_center=centers, orbit_time=ot,
                        **{"ltt_"+m: ltt[m] for m in MOSA_LABELS})
    for folder in ["external/taiji-sgwb", "external/triangle-simulator"]:
        report["checks"]["clean_" + folder.split("/")[-1]] = not subprocess.check_output(["git", "-C", str(ROOT/folder), "status", "--porcelain"]).strip()
    report["checks"] = {name: bool(passed) for name, passed in report["checks"].items()}
    report["all_checks_pass"] = all(report["checks"].values())
    report["elapsed_seconds"] = time.perf_counter() - started
    (OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Data checks: {sum(report['checks'].values())}/{len(report['checks'])} passed", flush=True)
    print(json.dumps({"time_axis": report["time_axis"], "geometry": report["original_analysis_geometry"], "all_checks_pass": report["all_checks_pass"]}, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
