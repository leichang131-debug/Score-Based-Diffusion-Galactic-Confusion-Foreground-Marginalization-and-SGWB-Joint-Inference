# TaijiSGWB Stage 3: official data and orbit preparation

Completed locally: **24/24 data/interface checks passed** for the official TDC II 2.8 realistic-orbit training set and its published orbit. Both original demo read/AET/trim interfaces executed against the actual downloaded dataset. No full STFT/CSD preprocessing, response-grid computation or inference was performed.

## Official provenance and preserved filenames

The official [TDC II links index](https://github.com/TriangleDataCenter/Taiji-Data-Challenge-II-Docs-Links) points to [Zenodo training-set record 17538642](https://zenodo.org/records/17538642). The latest-version endpoint resolved to the same record during this run; complete metadata snapshots are retained. This is the training file with component truth, not the blind-data or verification-binary datasets used in earlier work.

| Input | Preserved local path | Bytes | Verification |
| --- | --- | ---: | --- |
| Official training set | `data/raw/taiji-sgwb/TDCII2.8.h5` | 658310880 | Official MD5 and local SHA-256 |
| Official orbit | `data/raw/taiji-sgwb/MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5` | 54400 | Pinned official Git blob and local hashes |

Data official MD5: `a1975be6d933fae5fbf26da86a67049e`.

Data SHA-256: `7bcf2d3df221667677628e96492c6bd9591419980c6d2a214914a0084bb5f7d5`.

Orbit SHA-256: `eaf3491df20a0eb55dfcee7559048f483e06018286062733ab032626a2ba0946`.

The orbit is downloaded from the official Triangle-Simulator repository at `ab796358e9a36c8987f6bb53a97230d603bfdfd5`, with Git blob `a33227ec744cdddaee0fd0fb2be224e0354a6998`. No separate official MD5 is published for this GitHub file; the locally calculated MD5 is explicitly identified as local. The pinned official training-generation notebooks reference this same orbit directory. The raw downloaded orbit is used directly by the original InterpolationOrbit; no format conversion or extrapolation is needed at the analysis times. This confirms published input compatibility, not an independently verified copy of the author's private data files.

## Original filename difference

Both original TaijiSGWB demos expect `data/TDCII2-8.h5`; the official download is named `TDCII2.8.h5`. The official file is retained under its original name. Only an ignored relative symlink provides the author's expected filename:

```text
runs/taiji-sgwb/workspace/data/
├── TDCII2-8.h5 -> official TDCII2.8.h5
└── MicroSateOrbitEclipticTCB/
    └── MicroSateOrbit.hdf5 -> official downloaded orbit
```

`path-map.json` records exact link targets. `configs/reproduction/taiji-sgwb/data-paths.json` records the mapping for later callers. The original author's absolute PROJ_DIR remains unchanged in upstream code; the subsequent execution launcher must explicitly provide the local root. Stage 3 does not claim the unadapted full script can resolve the author's home directory.

## Actual input structure and complete scan

The downloaded data has 40 datasets and the orbit has 10 datasets. All numeric values in every dataset were scanned in bounded blocks, including structured orbit fields and spectra. Dataset shapes, dtypes, finite-value counts and ranges are recorded in `hdf5-inventory.json`. No NaN or Inf was found.

| Required data field | Actual shape | Meaning |
| --- | --- | --- |
| `/data/time` | `(6311629,)` | Shared sample times |
| `/data/XYZ` | `(3, 6311629)` | Total X/Y/Z observations |
| `/data/foreground` | `(3, 6311629)` | Provided foreground truth |
| `/data/noise` | `(3, 6311629)` | Provided instrument-noise realization |
| `/data/sgwb` | `(3, 6311629)` | Provided SGWB realization |

Channel row order and the component-sum convention are corroborated by the official `Scripts/TDCII2.8/Combination.ipynb`. Source-only reference extracts from Combination, Noise and SGWB are preserved under `official-reference/`, with their commit `6d5a0a273dafdc4212526be6c9b3189783be59bf`, hashes and original GPL license. Their saved upstream outputs are excluded and they were not executed locally.

Data times are uniformly spaced from 0 to 31,558,140 seconds, dt=5 seconds, sample rate=0.2 Hz and Nyquist=0.1 Hz. No waveform/unit rescaling is applied to XYZ. Interpretation follows the original generation and inference conventions. Parameters are stored as length-one HDF5 arrays; summaries export their single values while retaining original shape evidence. Injected SGWB omega0=1e-12 and n=2/3 match the template baseline. All six ACC and six OMS truth amplitudes are within the original priors.

Across the full time series:

- `XYZ = sgwb + noise + foreground` is exactly reproduced in floating-point arithmetic with the original summation order.
- `XYZ - foreground = noise + sgwb` has relative L2 error `5.268191e-17`, below the declared 1e-12 threshold.

Both demos' exact import/read/transform/trim AST nodes were executed, with only the input filename provided by the caller. The resulting full AET arrays are finite with shape `(3, 6310829)`. This is execution of the data interface, not execution of either full inference program. The report contains the executed original code text, original file hashes and line numbers.

## Orbit coverage and original analysis geometry

The official orbit contains 374 samples from 0 to 32,227,200 seconds. It covers the full and trimmed data range and all original weekly segment midpoints. The original cubic InterpolationOrbit reads `/tcb/t`, six `/tcb/l_ij` light-time datasets (structured `tt` field) and three `/tcb/sc_i` structured x/y/z datasets. Actual positions, light times and arm vectors at all 52 midpoints are finite; light times are positive.

| Original setting | Actual value |
| --- | ---: |
| Crop at each end | 400 points / 2000 seconds |
| Samples per week | 120960 |
| Full week segments | 52 |
| Tail outside complete segments | 20909 samples |
| Raw frequency bins per merged bin | 6 |
| Actual merged-bin spacing | 9.92063492063492e-6 Hz |
| Bins retained after original frequency mask and notches | 4426 |

The spacing is slightly below the nominal `f_res=1e-5` because the original code chooses an integer number of raw bins. The analysis-grid calculation reproduces this geometry without performing the full Fourier transform. `analysis-grid.npz` contains the frequencies, segment centers, orbit times and interpolated light times.

## Download and validation history

The first single transfer was deliberately stopped after slow progress, retaining its partial file. Four bounded official range transfers then verified each Content-Range; an interrupted connection required a retry, reusing completed verified ranges. The final assembled 658,310,880-byte file passed the official MD5 before acceptance. Logs for all transfer attempts are retained. `download-ranges.json` records the preserved prefix and verified ranges.

`download.json` records 122.065 seconds for the final resume/verification attempt only, excluding earlier attempts. It is not the total initial download duration. The finalized validation wrapper took 1.498 seconds on cached local files; this measures scanning/read checks, not simulations or sampling.

Two local checker issues were corrected with their logs retained: the initial prior-bound check assumed scalar parameter storage instead of length-one arrays; a subsequent export needed NumPy boolean values converted to JSON booleans. Neither required changing official files or upstream code. The final complete run passed all 24 checks.

## Reusable commands

From the research repository root:

```bash
python3 scripts/reproduction/download-taiji-sgwb-data.py
python3 scripts/reproduction/run-taiji-sgwb-data-check.py
python3 scripts/reproduction/audit-taiji-sgwb-data.py
```

Or include download in the validation wrapper:

```bash
python3 scripts/reproduction/run-taiji-sgwb-data-check.py --download
python3 scripts/reproduction/audit-taiji-sgwb-data.py
```

Download is resumable and verifies original byte counts/MD5. Existing accepted files are rechecked. The wrapper records aliases, actual command return codes and timings. The audit rehashes both raw inputs, verifies links/source preservation and exports the evidence manifest without running either full demo.

## Git and remaining scope

Raw HDF5 inputs, range chunks and runtime links are ignored by Git. Scripts, path configuration, official metadata, compact previews/grids, full-scan diagnostics and execution logs are tracked under `results/taiji-sgwb/data/`. Clone users obtain the original filenames by rerunning the downloader.

This stage prepares 2.8, shared by the two published TaijiSGWB demos. The 2.8_EQ, 2.9 and 2.9_EQ datasets are not downloaded or validated in this stage. Subsequent stages have completed full STFT/CSD preprocessing, response caching and the original 2.8 template schedule. Convergence is unconfirmed and EQ/RJ sampling remain incomplete; see [current status](status-and-cluster-handoff.md).
