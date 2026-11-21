#!/usr/bin/env python3
"""Verify and describe the archived inputs and output of a Figure 8 replay."""
import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
from PIL import Image


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs", type=Path, help="Output directory from the upstream replay")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3] / "external/taiji-sgwb-time-domain"
    verification = json.loads((args.outputs / "verification.json").read_text())
    if (verification["unexpected_differences"] or verification["production_inference_rerun"]
            or verification["posterior_source"] != "archived production chains"):
        raise ValueError("Expected a verified archived replay")
    cases = json.loads((root / "data/cases.json").read_text())["sw_benchmark"]
    fits = {
        "fd_equal": ("fit_079", "fit_078", 10.65),
        "td_equal": ("fit_081", "fit_080", 9.96),
        "td_unequal": ("fit_083", "fit_082", 5.81),
    }
    provenance = []
    for config, (full_id, null_id, reference) in fits.items():
        full, null = (root / cases[config][key] for key in ("posterior", "null"))
        with h5py.File(full) as h5, h5py.File(null) as h0:
            trace = h5["pe/trace"][:]
            if trace.ndim != 2 or trace.shape[1] != 10 or not trace.shape[0] or not np.isfinite(trace).all():
                raise ValueError(f"Invalid archived posterior for {config}")
            log_z = float(h5["pe/evidence"][()])
            log_z_null = float(h0["pe/evidence"][()])
        log_bf = log_z - log_z_null
        if not np.isfinite(log_bf) or round(log_bf, 2) != reference:
            raise ValueError(f"Paper Figure 8 Bayes factor mismatch for {config}: {log_bf}")
        provenance.append({
            "configuration": config, "full_fit": full_id, "null_fit": null_id,
            "full_input": full.relative_to(root).as_posix(), "full_sha256": digest(full),
            "null_input": null.relative_to(root).as_posix(), "null_sha256": digest(null),
            "posterior_shape": list(trace.shape), "log_z_full": log_z,
            "log_z_null": log_z_null, "log_bayes_factor": log_bf,
            "paper_log_bayes_factor": reference,
        })
    figure = "figure/10para_corner.png"
    path = args.outputs / figure
    sha256 = digest(path)
    expected = next(item for item in verification["figures"] if item["file"] == figure)
    if sha256 != expected["sha256"]:
        raise ValueError("Figure 8 does not match the upstream verification record")
    with Image.open(path) as png:
        width, height = png.size
        png.verify()
    print(json.dumps({
        "status": verification["status"],
        "posterior_source": verification["posterior_source"],
        "production_inference_rerun": False,
        "replay_seconds": verification["seconds"],
        "input_files_verified": verification["input_files_verified"],
        "figure": {"file": path.name, "sha256": sha256, "width": width, "height": height},
        "configurations": provenance,
    }, indent=2))


if __name__ == "__main__":
    main()
