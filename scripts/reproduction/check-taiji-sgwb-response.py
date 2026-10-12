#!/usr/bin/env python3
"""Original noise/ORF response computation with bounded blocks and controls."""
import argparse
import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/response"
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"runs/taiji-sgwb/matplotlib"))
os.environ.setdefault("MPLBACKEND","Agg")
for k in ["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"]:
    os.environ.setdefault(k,"1")
import h5py
import numpy as np
from taiji_sgwb_response import initialize_original_response, original_orf_block, original_response_nodes, execute_nodes, load_response_cache
from taiji_sgwb_preprocessing import digest_array


def file_hash(p):
    value=hashlib.sha256()
    with p.open("rb") as s:
        while b:=s.read(8*1024*1024): value.update(b)
    return value.hexdigest()


def relative(a,b):
    return float(np.linalg.norm(a-b)/np.linalg.norm(b))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",default="configs/reproduction/taiji-sgwb/response-macos.json")
    args=parser.parse_args()
    config=json.loads((ROOT/args.config).read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    checks,details={},{ }
    def check(name,passed,detail=None):
        checks[name]=bool(passed)
        if detail is not None:details[name]=detail
        print("PASS" if passed else "FAIL",name,flush=True)
        if not passed:raise AssertionError(name)
    entries=["template_nofg_28t.py","rj_nofg_28t.py"]
    previous=[json.loads((ROOT/"results/taiji-sgwb/preprocessing"/Path(e).stem/"validation.json").read_text()) for e in entries]
    check("both_preprocessing_inputs_identical",previous[0]["arrays"]==previous[1]["arrays"] and previous[0]["settings"]==previous[1]["settings"])
    check("verified_preprocessing_cache",file_hash(ROOT/previous[0]["cache"]["path"])==previous[0]["cache"]["sha256"])
    with h5py.File(ROOT/previous[0]["cache"]["path"],"r") as h:
        frequency=h["frequency"][()];times=h["segment_center"][()]
    orbit_record=json.loads((ROOT/"results/taiji-sgwb/data/download.json").read_text())["orbit"]
    check("verified_official_orbit",file_hash(ROOT/orbit_record["path"])==orbit_record["sha256"])
    bt,bf=config["block_time"],config["block_frequency"]
    assert bt>0 and bf>0
    controls_f=np.unique(np.linspace(0,len(frequency)-1,32,dtype=int))
    controls_t=np.array([0,26,51])
    ff,tt=frequency[controls_f],times[controls_t]
    source=ROOT/"external/taiji-sgwb/demos"/entries[0]
    noise_start=time.perf_counter()
    ns,nodes,record=initialize_original_response(source,frequency,previous[0]["settings"],ROOT/"runs/taiji-sgwb/workspace")
    noise_seconds=time.perf_counter()-noise_start
    check("original_full_noise_shapes",ns["acc_corr_factor"].shape==(3,3,6,52,4426) and ns["ro_corr_factor"].shape==(3,3,6,52,4426))
    check("original_times_match_preprocessing",np.array_equal(ns["t_seg"],times))
    probe_start=time.perf_counter()
    ordinary,ordinary_record=original_orf_block(source,nodes,ns,ff,tt,reuse=False)
    ordinary_seconds=time.perf_counter()-probe_start
    probe_start=time.perf_counter()
    memoized,memo_record=original_orf_block(source,nodes,ns,ff,tt,reuse=True)
    memo_seconds=time.perf_counter()-probe_start
    check("reuse_matches_original_calc_orf",relative(memoized,ordinary)<config["relative_tolerance"],
          {"relative_L2":relative(memoized,ordinary),"original_seconds":ordinary_seconds,"reuse_seconds":memo_seconds,"calls":memo_record})
    check("three_original_channel_calls_per_block",memo_record["original_GW_response_calls"]==3 and memo_record["identical_input_reuses"]==6)
    blocked_probe=np.empty_like(ordinary)
    for ts in range(0,len(tt),2):
        for fs in range(0,len(ff),7):
            value,_=original_orf_block(source,nodes,ns,ff[fs:fs+7],tt[ts:ts+2],reuse=True)
            blocked_probe[:,:,ts:ts+2,fs:fs+7]=value
    check("ORF_time_frequency_blocking_matches_unblocked",relative(blocked_probe,ordinary)<config["relative_tolerance"],
          {"relative_L2":relative(blocked_probe,ordinary),"probe_times":controls_t.tolist(),"probe_frequencies":controls_f.tolist(),"probe_block_time":2,"probe_block_frequency":7})
    second_source=ROOT/"external/taiji-sgwb/demos"/entries[1]
    control_settings=dict(previous[1]["settings"])
    control_settings.update(nseg=len(tt))
    secondary,secondary_nodes,second_record=initialize_original_response(second_source,ff,control_settings,ROOT/"runs/taiji-sgwb/workspace",control_times=tt)
    from taijisgwb.detector.tdi import tdi_X2,tdi_aet_from_tdi_x
    methods=tdi_aet_from_tdi_x(tdi_X2)
    control_noise={"acc":np.empty((3,3,6,3,len(ff)),complex),"ro":np.empty((3,3,6,3,len(ff)),complex)}
    for i in range(3):
        for j in range(i,3):
            for key,method in [("acc",secondary["taiji"].calc_noise_acc_corr_factor),("ro",secondary["taiji"].calc_noise_ro_corr_factor)]:
                control_noise[key][i,j]=method(ff,tt,methods[i],None if i==j else methods[j]).to_array
                if i!=j:control_noise[key][j,i]=control_noise[key][i,j].conj()
    for key,array in [("acc",ns["acc_corr_factor"]),("ro",ns["ro_corr_factor"])]:
        ref=array[:,:,:,controls_t,:][:,:,:,:,controls_f]
        check(key+"_direct_original_noise_controls",relative(control_noise[key],ref)<config["relative_tolerance"],{"relative_L2":relative(control_noise[key],ref)})
        original_secondary = secondary["acc_corr_factor" if key=="acc" else "ro_corr_factor"]
        check(key+"_both_original_noise_sections_match",relative(original_secondary,ref)<config["relative_tolerance"],{"relative_L2":relative(original_secondary,ref)})
    second_orf,_=original_orf_block(second_source,secondary_nodes,secondary,ff,tt,reuse=False)
    check("both_original_ORF_control_sections_match",relative(second_orf,ordinary)<config["relative_tolerance"],{"relative_L2":relative(second_orf,ordinary)})
    check("both_original_response_node_texts_identical",[r["source"] for r in record["noise_nodes"]+record["orf_nodes"]]==[r["source"] for r in second_record["noise_nodes"]+second_record["orf_nodes"]])
    for e,r in zip(entries,[record,second_record]):
        folder=OUT/Path(e).stem;folder.mkdir(parents=True,exist_ok=True)
        (folder/"source-execution.json").write_text(json.dumps(r,indent=2)+"\n")
        work=ROOT/"runs/taiji-sgwb/response"/Path(e).stem/"demos";work.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/"external/taiji-sgwb/demos"/e,work/e)
    np.savez_compressed(OUT/"unblocked-controls.npz",frequency=ff,time=tt,ordinary_orf=ordinary,memoized_orf=memoized,
        blocked_orf=blocked_probe,rj_original_orf=second_orf,acc=control_noise["acc"],ro=control_noise["ro"])
    del secondary,control_noise
    orf=np.empty((3,3,len(times),len(frequency)),complex)
    blocks=[];total=((len(times)+bt-1)//bt)*((len(frequency)+bf-1)//bf)
    full_start=time.perf_counter()
    for ts in range(0,len(times),bt):
        for fs in range(0,len(frequency),bf):
            before=time.perf_counter()
            value,counts=original_orf_block(source,nodes,ns,frequency[fs:fs+bf],times[ts:ts+bt],reuse=True)
            assert np.isfinite(value).all()
            orf[:,:,ts:ts+bt,fs:fs+bf]=value
            blocks.append({"time_start":ts,"time_stop":min(ts+bt,len(times)),"frequency_start":fs,
                "frequency_stop":min(fs+bf,len(frequency)),"seconds":time.perf_counter()-before,
                "original_GW_response_calls":counts["original_GW_response_calls"],"identical_input_reuses":counts["identical_input_reuses"]})
            if len(blocks)%20==0 or len(blocks)==total:
                print(f"ORF blocks {len(blocks)}/{total}; elapsed {time.perf_counter()-full_start:.1f}s",flush=True)
    orf_seconds=time.perf_counter()-full_start
    check("full_ORF_grid_finite",orf.shape==(3,3,52,4426) and np.isfinite(orf).all())
    check("full_ORF_matches_unblocked_control_points",relative(orf[:,:,controls_t,:][:,:,:,controls_f],ordinary)<config["relative_tolerance"],
          {"relative_L2":relative(orf[:,:,controls_t,:][:,:,:,controls_f],ordinary)})
    check("block_coverage_complete",len(blocks)==total and sum((b["time_stop"]-b["time_start"])*(b["frequency_stop"]-b["frequency_start"]) for b in blocks)==52*4426,
          {"blocks":total,"time_frequency_points":52*4426})
    for name,array in [("acc_corr_factor",ns["acc_corr_factor"]),("ro_corr_factor",ns["ro_corr_factor"]),("orf",orf)]:
        check(name+"_finite",np.isfinite(array).all())
        check(name+"_Hermitian",relative(array,np.swapaxes(array.conj(),0,1))<1e-14)
        diagonal=np.asarray([array[i,i].real for i in range(3)])
        check(name+"_nonnegative_diagonal",np.all(diagonal>=0))
        # Scale each channel covariance to compare eigenvalues independent of power units.
        den=np.sqrt(diagonal[:,None]*diagonal[None,:])
        assert np.all(den>0)
        normalized=np.moveaxis(array/den,[0,1],[-2,-1])
        eig=np.linalg.eigvalsh(normalized)
        check(name+"_normalized_PSD",eig.min()>=-128*np.finfo(float).eps,
              {"minimum_eigenvalue":float(eig.min()),"relative_limit":float(128*np.finfo(float).eps)})
    check("unit_amplitude_noise_spectra_positive_finite",all(np.isfinite(ns[k]).all() and np.all(ns[k]>0) for k in ["spectrum_acc","spectrum_ro"]))
    cache=ROOT/"data/processed/taiji-sgwb/response/response.h5";cache.parent.mkdir(parents=True,exist_ok=True)
    from taijisgwb.detector.constants import MOSA_LABELS
    arrays={"f_est":frequency,"t_seg":times,"acc_corr_factor":ns["acc_corr_factor"],"ro_corr_factor":ns["ro_corr_factor"],
            "spectrum_acc":ns["spectrum_acc"],"spectrum_ro":ns["spectrum_ro"],"orf":orf}
    with h5py.File(cache,"w") as h:
        for name,array in arrays.items():h.create_dataset(name,data=array)
        h.attrs.update({"upstream_commit":"4afaad4044b08721e7f1ce29cba3b0d912636dce","orbit_sha256":orbit_record["sha256"],
            "frequency_sha256":digest_array(frequency),"time_sha256":digest_array(times),"nside":14,"sky_pixels":2352,
            "block_time":bt,"block_frequency":bf,"link_order":json.dumps(MOSA_LABELS),"channel_order":"A,E,T",
            "noise_axes":"channel_i,channel_j,link,week,frequency","orf_axes":"channel_i,channel_j,week,frequency",
            "response_convention":"response_i * conjugate(response_j); original calc_orf",
            "noise_spectra":"unit-amplitude original spectra; apply six individual amplitudes squared in Stage 7",
            "compatible_entries":json.dumps(entries),"cache_reuse":"only identical-input original calc_gw_response outputs within each block"})
    read=load_response_cache(cache)
    check("cache_reader_exact_original_named_arrays",all(np.array_equal(read[k],v) for k,v in arrays.items()))
    del read
    (OUT/"block-timings.json").write_text(json.dumps({"blocks":blocks,"total_seconds":orf_seconds},indent=2)+"\n")
    mean=np.mean(orf,axis=2)
    np.savez_compressed(OUT/"response-summary.npz",frequency=frequency,time=times,mean_orf=mean,
        orf_control=orf[:,:,controls_t,:][:,:,:,controls_f],spectrum_acc=ns["spectrum_acc"],spectrum_ro=ns["spectrum_ro"])
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots()
    for i,label in enumerate(["A","E","T"]):ax.loglog(frequency,mean[i,i].real,label=label)
    ax.set(xlabel="Frequency (Hz)",ylabel="Mean auto ORF",title="Original nside=14 response: 52 weekly segments")
    ax.grid(True,which="both",alpha=.3);ax.legend();fig.tight_layout();fig.savefig(OUT/"orf-auto.png",dpi=180);plt.close(fig)
    source_manifest=json.loads((ROOT/"results/taiji-sgwb/source/manifest.json").read_text())
    check("all_original_source_files_unchanged",all(file_hash(ROOT/f["repository_path"])==f["sha256"] for f in source_manifest["files"]))
    result={"schema_version":1,"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope":"Full original noise transfer arrays and blocked original ORF; no parameter likelihood or posterior sampling.",
        "checks":checks,"details":details,"all_checks_pass":all(checks.values()),"config":config,
        "original_sky_nside":14,"original_sky_pixels":2352,"channels":["A","E","T"],"link_order":MOSA_LABELS,
        "array_shapes":{k:list(v.shape) for k,v in arrays.items()},"array_hashes":{k:digest_array(v) for k,v in arrays.items()},
        "cache":{"path":str(cache.relative_to(ROOT)),"bytes":cache.stat().st_size,"sha256":file_hash(cache)},
        "shared_cache_basis":"Original response nodes and preprocessing settings identical; both original sections verified on the actual unblocked control grid.",
        "timing":{"full_original_noise_seconds":noise_seconds,"full_blocked_ORF_seconds":orf_seconds,"worker_seconds":time.perf_counter()-started},
        "memory_estimate":{"unblocked_single_sky_array_bytes":52*4426*2352*16,"blocked_single_sky_array_bytes":bt*bf*2352*16},
        "remaining":"Stage 7 physical spectral-model and likelihood verification; sky-resolution convergence is not assessed here."}
    (OUT/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"Response checks: {sum(checks.values())}/{len(checks)} passed",flush=True)


if __name__=="__main__":main()
