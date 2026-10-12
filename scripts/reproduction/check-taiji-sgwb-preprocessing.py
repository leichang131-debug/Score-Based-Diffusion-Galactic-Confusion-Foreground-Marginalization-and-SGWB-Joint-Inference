#!/usr/bin/env python3
"""Execute unchanged full preprocessing and independent numerical checks."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "runs/taiji-sgwb/matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ.setdefault(key, "1")
import h5py
import numpy as np
from taiji_sgwb_preprocessing import execute_original_preprocessing, digest_array, load_preprocessing_cache


def relative_l2(actual, expected):
    return float(np.linalg.norm(actual-expected) / np.linalg.norm(expected))


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8*1024*1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True, choices=["template_nofg_28t.py", "rj_nofg_28t.py"])
    args = parser.parse_args()
    start = time.perf_counter()
    case = Path(args.entry).stem
    out = ROOT / "results/taiji-sgwb/preprocessing" / case
    work = ROOT / "runs/taiji-sgwb/preprocessing" / case / "demos"
    cache_dir = ROOT / "data/processed/taiji-sgwb/preprocessing" / case
    for folder in [out, work, cache_dir]:
        folder.mkdir(parents=True, exist_ok=True)
    source = ROOT / "external/taiji-sgwb/demos" / args.entry
    working = work / args.entry
    shutil.copyfile(source, working)
    download = json.loads((ROOT / "results/taiji-sgwb/data/download.json").read_text())
    data = ROOT / download["data"]["path"]
    assert file_hash(data) == download["data"]["sha256"]
    t0 = time.perf_counter()
    ns, snapshots, execution = execute_original_preprocessing(source, working, ROOT / "runs/taiji-sgwb/workspace")
    original_seconds = time.perf_counter() - t0
    (out / "source-execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    print("Original preprocessing completed", args.entry, f"{original_seconds:.3f}s", flush=True)
    z, csd, freq = ns["strain_segs"], ns["csd_est"], ns["f_est"]
    n, weeks = ns["nperseg"], ns["nseg"]
    fs, nperbin = ns["fsample"], ns["nperbin"]
    w = ns["win_array"]
    checks, details = {}, {}
    def check(name, passed, detail=None):
        checks[name] = bool(passed)
        if detail is not None:
            details[name] = detail
        print("PASS" if passed else "FAIL", name, flush=True)
    check("original_scientific_configuration", weeks == 52 and n == 120960 and nperbin == 6 and fs == .2 and ns["nf_est"] == 4426)
    check("full_STFT_shape", z.shape == (3, 52, 60481), list(z.shape))
    check("final_CSD_shape", csd.shape == (3, 3, 52, 4426), list(csd.shape))
    check("finite_full_STFT_and_CSD", np.isfinite(z).all() and np.isfinite(csd).all())
    check("frequency_sorted_and_in_band", np.all(np.diff(freq) > 0) and np.all((freq >= 1e-4) & (freq < .05)))
    check("notched_intervals_excluded", not np.any(((freq >= .0235) & (freq < .0265)) | ((freq >= .047) & (freq < .052))))
    stage3_grid = np.load(ROOT / "results/taiji-sgwb/data/analysis-grid.npz")
    check("frequency_matches_stage3_geometry", np.array_equal(freq, stage3_grid["frequency"]))
    window_normalizer = np.sqrt(fs * np.sum(w*w))
    check("window_PSD_normalization", np.allclose(ns["SFT"].win, w/window_normalizer, rtol=1e-14, atol=0),
          {"factor": float(window_normalizer), "equivalent_noise_bandwidth_bins": float(ns["win_bw"]), "fft_mode": ns["SFT"].fft_mode, "phase_shift": ns["SFT"].phase_shift})

    # Independent full-grid reference: direct NumPy FFT of contiguous weeks.
    # SciPy's default phase_shift=0 centers the Fourier phase via a half-window roll.
    # This common phase cancels in cross products but is retained for complex FFT parity.
    errors, parseval_errors = [], []
    manual_csd = np.empty_like(csd)
    raw_freq = np.fft.rfftfreq(n, d=ns["dt"])
    merged_freq = raw_freq[:ns["nbin"]*nperbin].reshape(-1, nperbin).mean(axis=1)
    band = (merged_freq >= 1e-4) & (merged_freq < .05)
    notch = ~(((merged_freq >= .0235) & (merged_freq < .0265)) | ((merged_freq >= .047) & (merged_freq < .052)))
    retained = band & notch
    check("independent_frequency_merge_and_mask", np.allclose(freq, merged_freq[retained], rtol=1e-14, atol=1e-18))
    fft_start = time.perf_counter()
    for week in range(weeks):
        transformed = []
        for channel in range(3):
            chunk = ns["strain_AET2"][channel][week*n:(week+1)*n]
            centered = chunk - chunk.mean()
            weighted = centered*w
            fft = np.fft.rfft(np.roll(weighted/window_normalizer, -n//2))
            transformed.append(fft)
            errors.append(relative_l2(z[channel, week], fft))
            powers = np.abs(z[channel, week])**2
            integral = (powers[0] + powers[-1] + 2*powers[1:-1].sum()) * fs/n
            reference = np.sum(weighted*weighted)/np.sum(w*w)
            parseval_errors.append(abs(float(integral/reference)-1))
        transformed = np.asarray(transformed)
        for i in range(3):
            for j in range(3):
                cross = transformed[i].conj() * transformed[j]
                combined = 2*cross[:ns["nbin"]*nperbin].reshape(-1,nperbin).mean(axis=1)
                manual_csd[i,j,week] = combined[retained]
    independent_seconds = time.perf_counter() - fft_start
    check("independent_full_complex_FFT", max(errors) < 1e-12, {"max_week_channel_relative_L2": max(errors), "weeks_checked": 52, "channels_checked": 3})
    check("one_sided_PSD_Parseval", max(parseval_errors) < 1e-12, {"max_relative_error": max(parseval_errors),
          "DC_Nyquist_weight": 1, "interior_weight": 2, "note": "Original CSD doubles all raw bins, but neither DC nor Nyquist belongs to the retained inference frequency grid."})
    csd_error = relative_l2(csd, manual_csd)
    check("independent_full_CSD_merge_and_masks", csd_error < 1e-12, {"relative_L2": csd_error})
    hermitian_error = relative_l2(csd, np.swapaxes(csd.conj(),0,1))
    check("CSD_Hermitian", hermitian_error < 1e-14, {"relative_L2": hermitian_error})
    diagonal = np.asarray([csd[i,i].real for i in range(3)])
    diagonal_imaginary_ratio = max(float(np.max(np.abs(csd[i,i].imag)/diagonal[i])) for i in range(3))
    roundoff_limit = 8*np.finfo(np.float64).eps
    check("diagonal_positive_and_real_to_roundoff", np.all(diagonal > 0) and diagonal_imaginary_ratio <= roundoff_limit,
          {"max_relative_imaginary": diagonal_imaginary_ratio, "relative_limit": float(roundoff_limit),
           "criterion": "8 * float64 machine epsilon; original arrays are not projected to real or symmetrized."})
    scales = np.sqrt(diagonal[:,None]*diagonal[None,:])
    correlation = np.moveaxis(csd/scales, [0,1], [-2,-1])
    eigenvalues = np.linalg.eigvalsh(correlation)
    check("all_spectral_matrices_positive_semidefinite", eigenvalues.min() >= -1e-10,
          {"matrices_checked": int(np.prod(correlation.shape[:-2])), "minimum_normalized_eigenvalue": float(eigenvalues.min())})
    max_coherence = float(np.max(np.abs(csd/scales)**2))
    check("coherence_bounded", max_coherence <= 1+1e-12, {"maximum_including_autos": max_coherence})
    check("final_FFT_bins_exclude_DC_and_Nyquist", freq[0] > 0 and freq[-1] < fs/2)
    merged = snapshots["merged_frequency"]
    after_band = snapshots["band_frequency"]
    counts = {"raw_rfft_bins": z.shape[-1], "raw_bins_used_for_merging": ns["nbin"]*nperbin,
              "discarded_raw_tail_bins": z.shape[-1]-ns["nbin"]*nperbin,
              "merged_bins": len(merged), "in_band_bins_before_notch": len(after_band),
              "removed_by_notch": len(after_band)-len(freq), "retained_bins": len(freq)}
    check("filter_counts_consistent", counts["merged_bins"] == 10080 and counts["retained_bins"] == 4426, counts)

    artifact_start = time.perf_counter()
    cache = cache_dir / "preprocessing.h5"
    centers = (np.arange(weeks)+.5)*ns["tperseg"] + ns["ndrop_points"]*ns["dt"]
    with h5py.File(cache, "w") as h5:
        for name, array in [("frequency", freq), ("csd_est", csd), ("strain_segs", z),
                            ("frequency_before_notch", after_band), ("csd_before_notch", snapshots["band_CSD"]),
                            ("segment_center", centers), ("window", w)]:
            h5.create_dataset(name, data=array)
        h5.attrs.update({"entry": args.entry, "upstream_commit": "4afaad4044b08721e7f1ce29cba3b0d912636dce",
            "source_sha256": execution["source_sha256"], "input_sha256": download["data"]["sha256"],
            "dt": ns["dt"], "tperseg": ns["tperseg"], "nperseg": n, "nseg": weeks,
            "nperbin": nperbin, "win_bw": ns["win_bw"], "window": "Kaiser(beta=14)",
            "STFT_axes": "channel,week,raw_frequency", "CSD_axes": "channel_i,channel_j,week,merged_frequency",
            "CSD_convention": "2*mean(conj(STFT_i)*STFT_j); same as original; not STFT_i*conj(STFT_j)",
            "normalization": "ShortTimeFFT onesided scale_to=psd; six-bin CSD mean times two",
            "weekly_matrices_preserved": True, "foreground": "provided truth subtracted"})
    loaded = load_preprocessing_cache(cache)
    check("cache_load_interface_exact", np.array_equal(loaded["frequency"], freq) and np.array_equal(loaded["csd_est"], csd) and np.array_equal(loaded["segment_center"], centers) and loaded["nperbin"] == nperbin and loaded["win_bw"] == ns["win_bw"])
    original_plot = work / "asd_AET_nofg.png"
    check("original_named_plot_generated", original_plot.is_file() and original_plot.stat().st_size > 0)
    shutil.copyfile(original_plot, out / original_plot.name)
    # Portable summaries retain full final frequency grid and all time-averaged complex CSDs.
    np.savez_compressed(out / "spectral-summary.npz", frequency=freq, mean_csd=csd.mean(axis=2),
        frequency_before_notch=after_band, mean_csd_before_notch=snapshots["band_CSD"].mean(axis=2),
        segment_center=centers, normalized_eigenvalue_min=eigenvalues.min(axis=-1))
    sample_frequencies = np.array([0, len(freq)//2, len(freq)-1])
    np.savez_compressed(out / "matrix-preview.npz", frequency=freq[sample_frequencies],
        csd=csd[:,:,[0,weeks//2,weeks-1],:][:,:,:,sample_frequencies])
    report = {"schema_version": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "entry": args.entry, "scope": "Original full-year preprocessing only; response and inference not executed.",
        "source_sha256": execution["source_sha256"], "input_sha256": download["data"]["sha256"],
        "checks": checks, "details": details, "all_checks_pass": all(checks.values()),
        "settings": {name: ns[name] for name in ["f_analow", "f_anaupp", "f_res", "dt", "fsample", "nperseg", "nseg", "tperseg", "nperbin", "win_bw", "nf_est", "ndrop_points", "npool"]},
        "settings_note": "npool=62 is preserved but unused; no multiprocessing sampler or response computation executed.",
        "shapes": {k:v for k,v in snapshots.items() if k.endswith("shape") or k.startswith("masked_CSD_shape")},
        "counts": counts, "timing": {"original_prefix_seconds": original_seconds,
            "independent_full_reference_seconds": independent_seconds, "cache_and_exports_seconds": time.perf_counter()-artifact_start,
            "worker_seconds": time.perf_counter()-start},
        "arrays": {"frequency": digest_array(freq), "CSD": digest_array(csd), "STFT": digest_array(z)},
        "cache": {"path": str(cache.relative_to(ROOT)), "bytes": cache.stat().st_size, "sha256": file_hash(cache)},
        "CSD_index_convention": "conj(channel_i)*channel_j; original contraction convention retained",
        "remaining": "Original response construction and physical likelihood/sampling remain pending."}
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Preprocessing checks: {sum(checks.values())}/{len(checks)} passed", flush=True)
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
