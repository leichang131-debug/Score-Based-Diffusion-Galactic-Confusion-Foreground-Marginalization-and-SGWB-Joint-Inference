#!/usr/bin/env python3
"""Verify trusted, extracted server run products and write a runtime summary."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import dill
import h5py
import numpy as np


CASES = {
    "fit_079": ("static_equal_arm_fd", "fd-campaign.json", "check"),
    "fit_081": ("equal_arm_td", "fit_081-campaign.json", "td-check/fit_081"),
    "fit_083": ("unequal_arm_td", "fit_083-campaign.json", "td-check/fit_083"),
}
PAPER_SETTINGS = {"nlive": 1000, "walks": 64, "dlogz": 0.1, "seed": 20261017}
CHINA_TIME = timezone(timedelta(hours=8))


def load_json(path):
    return json.loads(path.read_text())


def require(condition, case, message):
    if not condition:
        raise ValueError(f"{case}: {message}")


def summarize(root, case, configuration, campaign_file, checks_dir):
    logs = root / "logs"
    run = root / "production" / case
    campaign = load_json(logs / campaign_file)
    attempt = campaign.get("production", campaign)
    metrics = campaign["production_result"] if case == "fit_079" else campaign["result"]
    require(campaign["case"] == case and campaign["status"] == "complete"
            and attempt["returncode"] == 0, case, "campaign did not finish successfully")
    wall = float(campaign.get("production_wall_seconds_total", attempt["wall_seconds"]))
    require(np.isfinite(wall) and wall > 0, case, "invalid wall time")
    check = load_json(root / checks_dir / "likelihood_verification.json")
    checks = [row for row in check["checks"] if row["id"] == case and row["pass"]]
    require(check["status"] == "PASS" and len(checks) == 1, case, "input validation failed")
    cpu = load_json(logs / f"benchmark-{case}-cpu.json")
    gpu = load_json(logs / f"benchmark-{case}-cuda.json")
    require(cpu["fit_id"] == gpu["fit_id"] == case, case, "benchmark case mismatch")

    bilby = load_json(run / f"{case}_result.json")
    with (run / f"{case}_dynesty.pickle").open("rb") as stream:
        nested = dill.load(stream)
    calls = int(np.sum(nested.ncall))
    iterations = int(nested.niter)
    weights = np.asarray(nested.importance_weights())
    require(bilby["label"] == case and bilby["sampler"] == "dynesty"
            and calls == bilby["num_likelihood_evaluations"] == metrics["likelihood_calls"]
            and iterations == metrics["nested_iterations"], case, "sampler count mismatch")
    require(nested.samples.ndim == 2 and nested.samples.shape[1] == 10
            and len(weights) == len(nested.samples) and np.isfinite(nested.samples).all()
            and np.isfinite(weights).all() and np.all(weights >= 0)
            and np.isclose(weights.sum(), 1), case, "invalid weighted nested samples")
    require((run / f"{case}_resume.pickle").stat().st_size > 0, case, "empty checkpoint")
    with h5py.File(run / "posterior.h5") as h5:
        pe = h5["pe"]
        trace = pe["trace"][:]
        names = [name.decode() for name in pe["fit_parameter_names"][:]]
        logz = float(pe["evidence"][()])
        logz_error = float(pe["evidence_err"][()])
        target = h5.get("tables", getlink=True)
        require(names == bilby["search_parameter_keys"] and len(names) == 10
                and trace.shape == (metrics["samples"], 10) and np.isfinite(trace).all(),
                case, "posterior shape or parameter names differ")
        require(all(pe.attrs[key] == value for key, value in PAPER_SETTINGS.items()),
                case, "sampler settings differ")
        require(np.isfinite(logz) and np.isfinite(logz_error)
                and np.isclose(logz, nested.logz[-1], rtol=0, atol=1e-8)
                and logz == metrics["log_evidence"] == bilby["log_evidence"]
                and logz_error == metrics["log_evidence_error"] == bilby["log_evidence_err"],
                case, "evidence mismatch")
        require(isinstance(target, h5py.ExternalLink), case, "missing input bundle link")

    start = datetime.fromtimestamp(attempt["started_utc_epoch"], CHINA_TIME)
    end = start + timedelta(seconds=float(attempt["wall_seconds"]))
    return {
        "case": case, "configuration": configuration, "status": campaign["status"],
        "device": gpu["device"], "started_cst": start.isoformat(timespec="seconds"),
        "finished_cst": end.isoformat(timespec="seconds"), "wall_seconds": wall,
        "bilby_sampling_seconds": bilby["sampling_time"], "likelihood_calls": calls,
        "nested_iterations": iterations, "weighted_nested_samples": len(weights),
        "posterior_samples": len(trace), "dimensions": len(names),
        "log_evidence": logz, "log_evidence_error": logz_error,
        "cpu_warm_median_ms": 1000 * cpu["warm_median_seconds"],
        "cuda_warm_median_ms": 1000 * gpu["warm_median_seconds"],
        "cuda_benchmark_startup_seconds": gpu["startup_seconds"],
        "truth_loglike_abs_error": checks[0]["absolute_error"],
        "input_bundle_sha256": campaign["input_sha256"],
        "input_bundle_link_target": target.filename,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted_root", type=Path, help="Extract only the trusted campaign archives here")
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    rows = [summarize(args.extracted_root, case, *data) for case, data in CASES.items()]
    with args.output_csv.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row["case"], row["wall_seconds"], row["likelihood_calls"], row["posterior_samples"])


if __name__ == "__main__":
    main()
