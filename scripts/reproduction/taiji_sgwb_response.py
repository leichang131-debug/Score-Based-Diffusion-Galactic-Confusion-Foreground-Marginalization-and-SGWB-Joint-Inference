"""Bounded execution of original response nodes and cache readback interfaces."""
import ast
from contextlib import AbstractContextManager
import hashlib
from pathlib import Path
import time


class ReuseOriginalGWResponse(AbstractContextManager):
    """Memoize unchanged calc_gw_response outputs only within one fixed block.

    calc_orf is never replaced. The original single-link/sky response functions
    and full nside=14 sky sum are used. All input arrays must match on reuse.
    """
    def __init__(self, detector):
        self.detector = detector
        self.original = detector.calc_gw_response
        self.cache = {}
        self.calls = 0
        self.hits = 0

    def __enter__(self):
        self.detector.calc_gw_response = self.call
        return self

    def call(self, longitude, latitude, f, t, tdi):
        import numpy as np
        key = id(tdi)
        inputs = tuple(np.asarray(a) for a in (longitude, latitude, f, t))
        if key in self.cache:
            previous, result = self.cache[key]
            assert all(np.array_equal(a, b) for a, b in zip(inputs, previous)), "Reuse input mismatch"
            self.hits += 1
            return result
        result = self.original(longitude, latitude, f, t, tdi)
        self.calls += 1
        self.cache[key] = (tuple(a.copy() for a in inputs), result)
        return result

    def __exit__(self, *args):
        del self.detector.calc_gw_response
        self.cache.clear()


def original_response_nodes(source):
    text = source.read_text()
    tree = ast.parse(text)
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    selected = []
    active = False
    for node in tree.body:
        targets = [n.id for n in node.targets if isinstance(n,ast.Name)] if isinstance(node,ast.Assign) else []
        if "orbit" in targets:
            active = True
        if active and isinstance(node,ast.FunctionDef) and node.name == "log_likelihood":
            break
        if active:
            selected.append(node)
    split = next(i for i,n in enumerate(selected) if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id == "orf" for t in n.targets))
    # RJ additionally initializes log_f_est before its likelihood function;
    # that belongs to Stage 7. Stage 6 ends at the original ORF loop.
    assert isinstance(selected[split+1],ast.For)
    return text, imports, selected[:split], selected[split:split+2]


def execute_nodes(source, nodes, namespace):
    timings = []
    for node in nodes:
        before = time.perf_counter()
        exec(compile(ast.Module(body=[node],type_ignores=[]), str(source), "exec"), namespace)
        timings.append({"line":node.lineno,"end_line":node.end_lineno,"seconds":time.perf_counter()-before})
    return timings


def initialize_original_response(source, frequency, preprocessing_metadata, project_root, control_times=None):
    text, imports, noise_nodes, orf_nodes = original_response_nodes(source)
    ns = {"PROJ_DIR": Path(project_root), "f_est": frequency,
          "nseg": int(preprocessing_metadata["nseg"]), "tperseg": float(preprocessing_metadata["tperseg"]),
          "ndrop_points": int(preprocessing_metadata["ndrop_points"]), "dt": float(preprocessing_metadata["dt"]),
          "ntdi": 3, "nf_est": len(frequency)}
    execute_nodes(source,imports,ns)
    ns["tdi_methods"] = ns["tdi_aet_from_tdi_x"](ns["tdi_X2"])
    timings = []
    for node in noise_nodes:
        timings.extend(execute_nodes(source,[node],ns))
        if control_times is not None and isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id == "t_seg" for t in node.targets):
            ns["t_seg"] = control_times
    record = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "noise_nodes": [{"line":n.lineno,"end_line":n.end_lineno,"source":ast.get_source_segment(text,n)} for n in noise_nodes],
        "orf_nodes": [{"line":n.lineno,"end_line":n.end_lineno,"source":ast.get_source_segment(text,n)} for n in orf_nodes],
        "original_noise_node_timings":timings,
        "control_time_override": None if control_times is None else control_times.tolist(),
        "adaptation": "Original noise nodes on supplied grid; exact original ORF allocation/loop nodes per time-frequency block. Local PROJ_DIR and control/block namespace axes supplied externally; full-grid times use the original formula."}
    return ns, orf_nodes, record


def original_orf_block(source, nodes, namespace, frequency, times, reuse=True):
    block = dict(namespace)
    block.update(f_est=frequency,t_seg=times,nseg=len(times),nf_est=len(frequency))
    if reuse:
        with ReuseOriginalGWResponse(block["taiji"]) as memo:
            timings = execute_nodes(source,nodes,block)
            counts = {"original_GW_response_calls":memo.calls,"identical_input_reuses":memo.hits}
    else:
        timings = execute_nodes(source,nodes,block)
        counts = {"original_GW_response_calls":9,"identical_input_reuses":0}
    return block["orf"], {"node_timings":timings,**counts}


def load_response_cache(filename):
    """Return original response-array names, axes and model inputs for Stage 7."""
    import h5py
    with h5py.File(filename,"r") as h5:
        data = {name:h5[name][()] for name in ["f_est","t_seg","acc_corr_factor","ro_corr_factor","spectrum_acc","spectrum_ro","orf"]}
        data["metadata"] = dict(h5.attrs)
        return data
