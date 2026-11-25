#!/usr/bin/env python3
"""Render Figure 8 style posteriors from the three fresh full-model runs."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

UPSTREAM = Path(__file__).resolve().parents[3] / "external/taiji-sgwb-time-domain"
CASES = [
    ("fit_079", "FD PE", "red"),
    ("fit_081", "TD equal PE", "green"),
    ("fit_083", "TD unequal PE", "purple"),
]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def section(source, start, end=None):
    first = source.index(start)
    return source[first:source.index(end, first) if end else len(source)]


def run(source, name, scope):
    exec(compile(source, name, "exec"), scope)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production", type=Path, help="Extracted production/ directory")
    parser.add_argument("output", type=Path, help="Directory for plots and provenance")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(UPSTREAM))

    cases, inputs = [], {}
    truth, names = None, None
    for fit, label, color in CASES:
        path = args.production / fit / "posterior.h5"
        with h5py.File(path) as h5:
            samples = h5["pe/trace"][:]
            this_truth = h5["pe/truth_fit"][:]
            this_names = h5["pe/fit_parameter_names"][:]
            if (str(h5.attrs.get("source_fit")) != fit or samples.ndim != 2
                    or samples.shape[1] != 10 or not len(samples)
                    or not np.isfinite(samples).all()):
                raise ValueError(f"Invalid full posterior: {path}")
        if truth is None:
            truth, names = this_truth, this_names
        elif not np.array_equal(truth, this_truth) or not np.array_equal(names, this_names):
            raise ValueError(f"Parameter order or injected values differ: {path}")
        cases.append({"label": label, "color": color, "samples": samples})
        inputs[fit] = {"file": f"production/{fit}/posterior.h5", "sha256": digest(path),
                       "samples": len(samples), "outside_paper_fixed_ranges": {
                           "log_Omega_0": int(np.count_nonzero((samples[:, 8] < -12.1) | (samples[:, 8] > -11.1))),
                           "log_fp": int(np.count_nonzero((samples[:, 9] < -2.35) | (samples[:, 9] > -2.12))),
                       }}

    cells = UPSTREAM / "paper_cells"
    style = (cells / "cell_03.py").read_text()
    loader = (cells / "cell_41.py").read_text()
    original_plot = (cells / "cell_43.py").read_text()
    archived_rel = json.loads((UPSTREAM / "data/cases.json").read_text())["sw_benchmark"]["td_equal"]["posterior"]
    archived = UPSTREAM / archived_rel
    with h5py.File(archived) as h5:
        if not np.array_equal(h5["parameters_true"][:10], truth):
            raise ValueError("Spectrum reference and fresh runs have different injection parameters")

    scope = {
        "USE_TEX": True, "sw10_truth": truth, "h5py": h5py,
        "sw10_products": {"TD equal PE": {"path": archived}},
        "resolve_result_path": lambda path: path,
        "display": lambda *_args: None,
    }
    run(style, "cell_03.py", scope)
    run(section(loader, "# Spectrum curves for the upper-right inset"), "cell_41_spectrum", scope)
    spectrum = scope["sw10_spectrum_context"]
    keys = ("frequency", "dwd", "astro", "sw", "noise")
    arrays = [np.asarray(spectrum[k]) for k in keys]
    if not all(a.shape == arrays[0].shape and np.isfinite(a).all() and (a > 0).all() for a in arrays):
        raise ValueError("Invalid spectrum from the reference tables")
    np.savetxt(output / "component_spectra.csv", np.column_stack(arrays), delimiter=",",
               header="frequency_hz,omega_dwd,omega_ast,omega_sw,omega_taiji_xx_equivalent_noise", comments="")

    # Execute upstream rendering with only the input list, output routing and legend adapted.
    head = original_plot[:original_plot.index("fig7_output = ")]
    body = section(original_plot, "fig7_param_labels =")
    legend = next(line for line in body.splitlines() if "label=rf" in line and "Line2D" in line)
    body = body.replace(legend, '    mlines.Line2D([], [], color=case["color"], linewidth=3.0, label=case["label"])')
    # Give every configuration the same upstream comparison ranges, including the base layer.
    body = body.replace("all_fig7_samples = np.vstack([case[\"samples\"] for case in fig7_sample_defs])",
                        "all_fig7_samples = np.vstack([case[\"samples\"] for case in range_cases])")
    body = body.replace('    labelpad=corner_labelpad,\n)\n\nfor case',
                        '    range=fig7_ranges,\n    labelpad=corner_labelpad,\n)\n\nfor case', 1)
    if "ln_bf" in body or body.count("range=fig7_ranges") != 2:
        raise ValueError("The pinned upstream cell no longer matches the plotting adapter")
    scope["range_cases"] = cases
    for label, selection in [("10para_corner", cases), *[(f"{case}_corner", [s]) for (case, _, _), s in zip(CASES, cases)]]:
        print(f"Rendering {label}", flush=True)
        scope.update(fig7_sample_defs=selection, fig7_output=output / f"{label}.png")
        np.random.seed(20260520)
        run(head + body, "cell_43_adapted", scope)
        legend_labels = [text.get_text() for text in scope["fig7_fig"].legends[0].get_texts()]
        if legend_labels != [case["label"] for case in selection]:
            raise ValueError("Configuration-only legend check failed")

    fig, ax = plt.subplots(figsize=(7.4, 6.6), layout="constrained")
    scope["fig7_inset"] = ax
    run(section(body, "fig7_inset.loglog(", "fig7_output.parent.mkdir"), "cell_43_spectrum", scope)
    fig.savefig(output / "component_spectra.png", dpi=scope["output_dpi"], bbox_inches="tight", pad_inches=.05)
    plt.close(fig)
    paths = ["10para_corner.png", *(f"{case}_corner.png" for case, _, _ in CASES),
             "component_spectra.png", "component_spectra.csv"]
    report = {
        "upstream": "https://github.com/Eric-Friedman-666/taiji-sgwb-time-domain",
        "upstream_commit": "e5ebd75639c3433717ff2cafe52e7f2f5a3f34bb",
        "upstream_cell_sha256": {f"cell_{i:02d}.py": digest(cells / f"cell_{i:02d}.py") for i in (3, 41, 43)},
        "text_usetex": bool(plt.rcParams["text.usetex"]),
        "contour_probability": [0.393, 0.865],
        "display_ranges": [list(map(float, r)) for r in scope["fig7_ranges"]],
        "bayes_factor_annotated": False,
        "posterior_inputs": inputs,
        "spectrum_source": {"file": archived_rel, "sha256": digest(archived),
                            "shared": "Injected spectra and equivalent Taiji XX noise from the archived TD equal response tables"},
        "outputs": {name: digest(output / name) for name in paths},
    }
    (output / "provenance.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
