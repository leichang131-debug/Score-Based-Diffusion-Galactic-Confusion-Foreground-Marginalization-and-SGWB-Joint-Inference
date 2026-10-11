# Triangle-GB: pinned source and directory preparation

## Completed scope

The full upstream file tree is integrated as an unmodified Git submodule at `external/triangle-gb`.

- Upstream: https://github.com/TriangleDataCenter/Triangle-GB
- Pinned commit: `cbc0a1b0cbf4ec05ec969fa39405394168c3e06c`.
- Upstream commit date: 2026-09-16 (UTC).
- Preparation date: 2026-10-11 (Asia/Shanghai).
- License: original GPL-3.0 retained; the research repository's MIT license does not relicense this submodule.
- Checkout is shallow and detached at the pinned commit. All tracked files are present; historical commits are not fully downloaded.

The former source-slot README was replaced by the actual upstream submodule. Project-specific integration documentation lives outside it. No upstream module, notebook, embedded output, orbit file or packaging file was changed. No dependencies were installed, no public data downloaded, and no Triangle-GB examples executed in this milestone.

## Source inventory and planned coverage

The package has `Triangle_GB/__init__.py` and `Triangle_GB/TDIFly.py`, exporting `TDIFly`, `TDIFlyGB` and `TDIFlyGBNetwork`. The complete `Examples/` folder contains:

| Original filename | Planned validation |
| --- | --- |
| `0_TDIFlyGB_Compare_TD_FD_Waveforms(CPU).ipynb` | Original-scale time/frequency response comparison, channel conversion, frequency fill and mismatch |
| `1_TDIFlyGB_Rapid_Search(CPU).ipynb` | F-statistic, intrinsic/extrinsic parameter conversion and search/reconstruction |
| `2_TDIFlyGB_Parameter_Estimation(CPU).ipynb` | Likelihood wrapper, Bilby/Nessai sampling and posterior diagnostics |
| `3_LDC2a_GB_Reconstruction.ipynb` | LDC input conventions, multi-source response and summed reconstruction |
| `GB_network_PE_example_for_2609.16477.ipynb` | Multi-detector network response and inference |

All six `Examples/LDCEqualArmOrbit/*.dat` files are retained. The pinned Triangle-Simulator submodule remains at `ab796358e9a36c8987f6bb53a97230d603bfdfd5`. Interface compatibility will be checked before environment readiness is declared.

## Prepared project-owned directories

- `environments/triangle-gb/`: future isolated environment and dependency locks.
- `notebooks/reproduction/triangle-gb/Examples/`: future same-name executed notebooks; currently README only.
- `scripts/reproduction/audit-triangle-gb-source.py`: source-only audit, not a scientific runner.
- `results/triangle-gb/source/`: source audit and complete file manifest.
- `docs/reproduction/triangle-gb/`: stage reports and scope.
- `data/triangle-gb/`: curated data provenance; bulk files will go to ignored `data/raw/triangle-gb/`.

## Source checks and fresh checkout

From the research repository root:

```bash
git submodule update --init --recursive
python3 scripts/reproduction/audit-triangle-gb-source.py
```

The script compares every working-tree file with the pinned Git blob, verifies clean source, checks the five original notebooks and required core classes, and hashes all tracked files. It parses Python/JSON as data without importing or executing upstream code. This establishes complete source preservation, not waveform accuracy or posterior convergence.

The original notebooks contain sibling `Triangle-Simulator` relative paths and author-specific data paths. Resolve and document these interfaces before execution; do not imply the README-only execution directories are runnable notebooks. Example 1/2 download links are present in their first Markdown cells; see [data provenance](../../../data/triangle-gb/README.md).
