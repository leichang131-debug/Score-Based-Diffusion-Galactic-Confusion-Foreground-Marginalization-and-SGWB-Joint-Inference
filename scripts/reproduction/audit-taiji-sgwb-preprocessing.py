#!/usr/bin/env python3
"""Audit source correspondence and saved Stage 5 arrays without FFT execution."""
from taiji_sgwb_source import source_is_pristine, source_pin
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
import h5py
import numpy as np
from taiji_sgwb_preprocessing import digest_array

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/preprocessing"


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8*1024*1024):
            value.update(block)
    return value.hexdigest()


def main():
    run = json.loads((OUT / "run.json").read_text())
    checks = {"two_successful_local_runs": run["success"] and len(run["runs"]) == 2 and all(r["returncode"] == 0 for r in run["runs"]),
              "both_independent_arrays_match": all(run["array_hash_parity"].values()),
              "worker_resource_samples_present": all(r["peak_sampled_worker_rss_kib"] > 0 and r["monitoring_error"] is None for r in run["runs"])}
    all_sources = json.loads((ROOT / "results/taiji-sgwb/source/manifest.json").read_text())
    checks["all_original_package_files_unchanged"] = all(sha(ROOT / f["repository_path"]) == f["sha256"] for f in all_sources["files"])
    for entry in ["template_nofg_28t.py", "rj_nofg_28t.py"]:
        case = Path(entry).stem
        folder = OUT / case
        result = json.loads((folder / "validation.json").read_text())
        execution = json.loads((folder / "source-execution.json").read_text())
        source = ROOT / "external/taiji-sgwb/demos" / entry
        working = ROOT / "runs/taiji-sgwb/preprocessing" / case / "demos" / entry
        text = source.read_text()
        expected = []
        for node in ast.parse(text).body:
            if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id == "orbit" for t in node.targets):
                break
            expected.append({"line": node.lineno, "end_line": node.end_lineno, "source": ast.get_source_segment(text,node)})
        checks[case + "_exact_original_prefix_nodes"] = execution["executed_nodes"] == expected
        checks[case + "_same_name_and_exact_working_copy"] = working.name == source.name and sha(source) == sha(working) == result["source_sha256"]
        checks[case + "_all_numeric_checks_pass"] = len(result["checks"]) == 20 and result["all_checks_pass"] and all(result["checks"].values())
        cache = ROOT / result["cache"]["path"]
        checks[case + "_cache_file_hash_matches"] = sha(cache) == result["cache"]["sha256"] and cache.stat().st_size == result["cache"]["bytes"]
        checks[case + "_cache_ignored"] = subprocess.run(["git","check-ignore","--quiet",result["cache"]["path"]],cwd=ROOT).returncode == 0
        with h5py.File(cache,"r") as h5:
            arrays = {"frequency": h5["frequency"][()], "CSD": h5["csd_est"][()], "STFT": h5["strain_segs"][()]}
            checks[case + "_saved_array_hashes_match"] = all(digest_array(v) == result["arrays"][k] for k,v in arrays.items())
            checks[case + "_all_weeks_retained"] = arrays["CSD"].shape == (3,3,52,4426) and bool(h5.attrs["weekly_matrices_preserved"])
            preview = np.load(folder / "spectral-summary.npz")
            expected_mean = arrays["CSD"].mean(axis=2)
            mean_error = float(np.linalg.norm(preview["mean_csd"]-expected_mean)/np.linalg.norm(expected_mean))
            checks[case + "_portable_summary_matches_cache_to_roundoff"] = np.array_equal(preview["frequency"], arrays["frequency"]) and mean_error <= 32*np.finfo(np.float64).eps
        del arrays
        checks[case + "_plot_matches_original_local_output"] = sha(folder / "asd_AET_nofg.png") == sha(working.parent / "asd_AET_nofg.png")
    first = json.loads((OUT / "attempts/template_nofg_28t/validation.json").read_text())
    checks["initial_exact_zero_failure_retained"] = not first["all_checks_pass"] and not first["checks"]["diagonal_positive_and_real"]
    final = json.loads((OUT / "template_nofg_28t/validation.json").read_text())
    checks["roundoff_criterion_did_not_change_arrays"] = first["arrays"] == final["arrays"]
    checks["upstream_worktree_clean"] = source_is_pristine()
    checks = {name: bool(passed) for name, passed in checks.items()}
    report = {"scope": "Saved source/array/evidence integrity only; no FFT rerun or physical parameter inference.",
              "checks": checks, "all_checks_pass": all(checks.values())}
    (OUT / "audit.json").write_text(json.dumps(report,indent=2)+"\n")
    files = [p for p in OUT.rglob("*") if p.is_file() and p.name != "manifest.json"]
    files += [ROOT / "scripts/reproduction" / n for n in ["taiji_sgwb_preprocessing.py", "check-taiji-sgwb-preprocessing.py", "run-taiji-sgwb-preprocessing.py", "audit-taiji-sgwb-preprocessing.py"]]
    files += [ROOT / "docs/reproduction/taiji-sgwb/preprocessing.md"]
    entries = [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(files)]
    (OUT / "manifest.json").write_text(json.dumps({"schema_version":1,"files":entries},indent=2)+"\n")
    print(f"Stage 5 evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(entries)} portable artifacts hashed.")
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
