"""Project adapter for the unchanged original Stage 5 preprocessing prefix."""
import ast
import hashlib
from pathlib import Path
import time


def digest_array(array):
    import numpy as np
    a = np.ascontiguousarray(array)
    return hashlib.sha256(memoryview(a).cast("B")).hexdigest()


def execute_original_preprocessing(source_file, working_file, project_root):
    """Execute exact original AST nodes up to, but excluding, orbit creation.

    Only PROJ_DIR is overridden after its original assignment. __file__ points
    to an identical same-name working copy, routing original output paths there.
    No algorithm settings, source nodes or scientific computations are changed.
    """
    text = source_file.read_text()
    assert working_file.name == source_file.name
    assert working_file.read_bytes() == source_file.read_bytes()
    ns = {"__file__": str(working_file), "__name__": "__main__"}
    records, snapshots, nodes = [], {}, []
    mask_count = 0
    stopped = False
    for node in ast.parse(text).body:
        names = [n.id for n in node.targets if isinstance(n, ast.Name)] if isinstance(node, ast.Assign) else []
        if "orbit" in names:
            stopped = True
            break
        code = ast.get_source_segment(text, node)
        before = time.perf_counter()
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_file), "exec"), ns)
        seconds = time.perf_counter() - before
        if "PROJ_DIR" in names:
            ns["PROJ_DIR"] = Path(project_root)
        records.append({"line": node.lineno, "end_line": node.end_lineno, "seconds": seconds})
        nodes.append({"line": node.lineno, "end_line": node.end_lineno, "source": code})
        if "strain_segs" in names:
            snapshots["allocated_STFT_shape"] = list(ns["strain_segs"].shape)
        if "csd_est" in names:
            shape = list(ns["csd_est"].shape)
            if "np.conj" in code:
                snapshots["raw_CSD_shape"] = shape
            elif "np.mean" in code:
                snapshots["merged_CSD_shape"] = shape
            elif code.strip() == "csd_est = csd_est[..., mask]":
                mask_count += 1
                snapshots[f"masked_CSD_shape_{mask_count}"] = shape
                if mask_count == 1:
                    snapshots["band_frequency"] = ns["f_est"].copy()
                    snapshots["band_CSD"] = ns["csd_est"]
        if "f_est" in names and "np.mean" in code:
            snapshots["merged_frequency"] = ns["f_est"].copy()
    assert stopped and mask_count == 2
    return ns, snapshots, {"original_source": str(source_file), "working_copy": str(working_file),
        "source_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        "runtime_override": {"name": "PROJ_DIR", "value": str(project_root)},
        "stop_before": "orbit = InterpolationOrbit(...)", "source_nodes_unchanged": True,
        "scientific_settings_unchanged": True, "executed_nodes": nodes, "node_timings": records}


def load_preprocessing_cache(filename):
    """Read the verified inputs for later response and likelihood stages.

    Returns final CSD axes [channel_i, channel_j, week, frequency], with
    CSD[i,j] = 2*mean(conj(STFT[i])*STFT[j]) over six raw frequency bins.
    The matrices are retained separately for every week; no year averaging.
    Raw STFT arrays remain in HDF5 and are not loaded by this helper.
    """
    import h5py
    with h5py.File(filename, "r") as h5:
        return {"frequency": h5["frequency"][()], "csd_est": h5["csd_est"][()],
                "segment_center": h5["segment_center"][()],
                "nperbin": int(h5.attrs["nperbin"]), "win_bw": float(h5.attrs["win_bw"]),
                "tperseg": float(h5.attrs["tperseg"]), "metadata": dict(h5.attrs)}
