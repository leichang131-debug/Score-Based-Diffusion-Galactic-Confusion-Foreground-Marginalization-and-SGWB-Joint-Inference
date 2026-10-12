#!/usr/bin/env python3
"""Audit full response cache, original source nodes and exact block coverage."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
import h5py
import numpy as np
from taiji_sgwb_response import original_response_nodes
from taiji_sgwb_preprocessing import digest_array

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"results/taiji-sgwb/response"


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as file:
        while b:=file.read(8*1024*1024):h.update(b)
    return h.hexdigest()


def main():
    v=json.loads((OUT/"validation.json").read_text())
    run=json.loads((OUT/"run.json").read_text())
    checks={"worker_success":run["returncode"]==0,
        "all_response_checks_pass":v["all_checks_pass"] and all(v["checks"].values()),
        "actual_resource_samples":run["peak_sampled_worker_rss_kib"]>0 and run["monitoring_error"] is None,
        "original_sky_settings_preserved":v["original_sky_nside"]==14 and v["original_sky_pixels"]==2352}
    source_manifest=json.loads((ROOT/"results/taiji-sgwb/source/manifest.json").read_text())
    checks["all_original_sources_preserved"]=all(sha(ROOT/f["repository_path"])==f["sha256"] for f in source_manifest["files"])
    checks["original_source_clean"]=not subprocess.check_output(["git","-C",str(ROOT/"external/taiji-sgwb"),"status","--porcelain"]).strip()
    for entry in ["template_nofg_28t.py","rj_nofg_28t.py"]:
        source=ROOT/"external/taiji-sgwb/demos"/entry
        working=ROOT/"runs/taiji-sgwb/response"/Path(entry).stem/"demos"/entry
        record=json.loads((OUT/Path(entry).stem/"source-execution.json").read_text())
        text,_,noise,orf=original_response_nodes(source)
        expected=lambda nodes:[{"line":n.lineno,"end_line":n.end_lineno,"source":ast.get_source_segment(text,n)} for n in nodes]
        checks[Path(entry).stem+"_original_response_nodes_match"]=record["noise_nodes"]==expected(noise) and record["orf_nodes"]==expected(orf)
        checks[Path(entry).stem+"_same_name_byte_identical_copy"]=working.name==entry and sha(source)==sha(working)==record["source_sha256"]
    blocks=json.loads((OUT/"block-timings.json").read_text())["blocks"]
    coverage=np.zeros((52,4426),dtype=np.uint8)
    for b in blocks:
        coverage[b["time_start"]:b["time_stop"],b["frequency_start"]:b["frequency_stop"]]+=1
    bt,bf=v["config"]["block_time"],v["config"]["block_frequency"]
    expected_blocks=((52+bt-1)//bt)*((4426+bf-1)//bf)
    checks["all_grid_points_computed_once"]=len(blocks)==expected_blocks and np.all(coverage==1)
    checks["reuse_only_three_original_channels"]=all(b["original_GW_response_calls"]==3 and b["identical_input_reuses"]==6 for b in blocks)
    cache=ROOT/v["cache"]["path"]
    checks["full_cache_hash_matches"]=sha(cache)==v["cache"]["sha256"] and cache.stat().st_size==v["cache"]["bytes"]
    checks["full_cache_ignored"]=subprocess.run(["git","check-ignore","--quiet",v["cache"]["path"]],cwd=ROOT).returncode==0
    array_checks={}
    with h5py.File(cache,"r") as h:
        for name,digest in v["array_hashes"].items():
            array_checks[name]=digest_array(h[name][()])==digest
        checks["full_array_hashes_match"]=all(array_checks.values())
        summary=np.load(OUT/"response-summary.npz")
        original_orf=h["orf"][()]
        check_mean=np.linalg.norm(summary["mean_orf"]-original_orf.mean(axis=2))/np.linalg.norm(summary["mean_orf"])
        checks["summary_matches_full_cache_to_roundoff"]=check_mean<=32*np.finfo(float).eps and np.array_equal(summary["frequency"],h["f_est"][()])
        checks["original_link_order_recorded"]=json.loads(h.attrs["link_order"])==["12","13","23","21","31","32"]
        with h5py.File(ROOT/"data/processed/taiji-sgwb/preprocessing/template_nofg_28t/preprocessing.h5","r") as pre:
            checks["cache_grid_matches_preprocessing"]=np.array_equal(h["f_est"][()],pre["frequency"][()]) and np.array_equal(h["t_seg"][()],pre["segment_center"][()])
    checks={k:bool(p) for k,p in checks.items()}
    result={"scope":"Saved response/source/cache integrity only; no full ORF recomputation or physical likelihood/sampling.",
        "checks":checks,"array_checks":array_checks,"all_checks_pass":all(checks.values())}
    (OUT/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    files=[p for p in OUT.rglob("*") if p.is_file() and p.name!="manifest.json"]
    files += [ROOT/"scripts/reproduction"/n for n in ["taiji_sgwb_response.py","check-taiji-sgwb-response.py","run-taiji-sgwb-response.py","report-taiji-sgwb-response.py","audit-taiji-sgwb-response.py"]]
    files += [ROOT/"configs/reproduction/taiji-sgwb/response-macos.json",ROOT/"docs/reproduction/taiji-sgwb/response.md"]
    entries=[{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(files)]
    (OUT/"manifest.json").write_text(json.dumps({"schema_version":1,"files":entries},indent=2)+"\n")
    print(f"Response evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(entries)} artifacts hashed.")
    if not result["all_checks_pass"]:raise SystemExit(1)


if __name__=="__main__":main()
