# Triangle-GB Examples 1/2: data download and input preparation

## Outcome and scope

Preparation date: 2026-10-11. Both official public files were downloaded on this Mac with unchanged filenames and verified against official sizes and MD5. All numeric values in all 12 HDF5 datasets are finite. Seven input-preparation checks pass; **strict orbit coverage fails** and remains an explicit issue.

No upstream files were edited. The canonical `external/triangle-gb/` tree retains `Examples/`, `Triangle_GB/`, all original subdirectories, filenames, explanatory Markdown and code. Future executed copies must preserve these divisions, filenames and source/Markdown cells. Project-owned download/check/adaptation scripts are separate from the canonical tree. Notebook outputs cannot be treated as local evidence until cleared and freshly executed.

The checker executes unchanged zero-based source cells 5, 6, 9 and 17 from Example 1 after assigning local path variables in its external namespace; those cells are verified identical in Example 2. It separately executes each notebook's original cells 12, 13 and 14, preserving their distinct selected source. It does not run plot cells, optimization, waveform generation or nested sampling. Source-cell SHA-256 values are recorded in `validation.json`.

## Verified inputs

| Original filename | Bytes | Local SHA-256 |
| --- | --- | --- |
| `0_1_VGB_TDIXYZ.h5` | 100,707,680 | `766b50adaabe7dfca1a7cff853845a920f5467b2ffb7ef6e064231ba1ed6bdb3` |
| `0_1_VGB_parameters.h5` | 7,904 | `484862f47179b295f8750a5733ee93d912b9a717faef88cecc7d011ad439ce9e` |

Official MD5 values and record URLs are in `download-provenance.json`. Files live in ignored `data/raw/triangle-gb/`. `git check-ignore` confirms both are excluded; filenames are unchanged. Download time recorded by the script includes network transfer, metadata retrieval and checksum reads: 116.114 seconds in total for the successful first download. This timing depends on network/cache state and is not an example runtime.

## Structure and tutorial conventions

The data file contains `/time` and `/XYZ/X2`, `/XYZ/Y2`, `/XYZ/Z2`, each `float64` with **3,146,975** entries. The parameter file contains `A`, `f0`, `fdot0`, `inclination`, `latitude`, `longitude`, `phase0` and `psi`, each with **55** `float64` entries. All fields have matching source-array lengths. The data are the combined XYZ channels, not separate per-source waveforms. Shared parameter index ordering is used exactly as in the notebooks; integrity checks alone do not independently recover or prove the physical association of all 55 sources.

Original `read_dict_from_h5`, `AETfromXYZ`, `XYZfromAET` and `FFT_window` implementations were used. The original A/E conversion and the round trip agree to a maximum relative error of 2.900e-16 relative to the largest input channel amplitude. Sampling interval is **10 s**, strictly increasing and uniform. The observed range is **2,000 to 31,471,740 s**. Original zero padding adds **200** samples, giving **3,147,175** samples and `Tobs = 31471750 s`. Padding values are checked to be zero.

FFT preparation uses the original Tukey `alpha = 10000/Tobs`, normalization and DC exclusion. Both full A/E spectra are finite, and frequency spacing matches `1/Tobs`. Example 1 selects source index **4** (`f0 = 0.0032247077105 Hz`); Example 2 selects index **1** (`f0 = 0.0048216991071 Hz`). Each original 5e-6 Hz band contains **157** bins, with positive finite `PSDlevel`. The check verifies input/band availability; it is not an optimizer recovery or posterior-quality result.

The final complete input check took **0.686 s**, excluding Python startup/imports and the prior download. It scans the full files and performs actual full-size channel conversion and FFT; it does not claim the full tutorials execute in this time.

## Orbit coverage issue: retain and resolve explicitly

The pinned default `MicroSateOrbitEclipticTCB` position/velocity files have **365** rows at the original daily cadence. Default `Orbit` constructs its grid from **0 to 31,449,600 s**. The observed data end **22,140 s (6.15 hours)** later; **2,214** observed samples (0.07035%) lie outside the table. The padded grid has the same tail issue. The original `Nsparse=512` constructor includes an endpoint at **31,471,750 s**, **22,150 s** past the orbit end.

Actual cumulative TDI delay queries extend down to **-69.944357 s** near the zero-padded start. The maximum observed cumulative delay is **70.156669 s**; raw data starting at 2,000 s are safely inside the lower bound after this delay. The artificial zero-padded template boundary still extrapolates. Default orbit position and light-travel-time functions return finite values on the required sparse queries, and the original constructor runs. **Finite extrapolation does not establish waveform accuracy or strict coverage.**

No data were cropped, no extra orbit samples synthesized, no `dt`/`tstart` changed and no upstream code patched. The final report intentionally has `all_checks_pass=false`, `input_preparation_checks_pass=true`, `strict_orbit_coverage_confirmed=false`; checker exit status 2 records this diagnosed gap.

For a faithful original-method reproduction, retain original settings and disclose the inherited extrapolation explicitly. Before asserting scientific accuracy, confirm the intended orbit file/coverage with the teachers or obtain a matching orbit table covering the padded interval and delayed boundary. A later sensitivity comparison with a coverage-complete orbit can quantify the effect. Cropping or changing cadence would change the original experiment and must be treated as a separate, documented variation. The current milestone does not decide that extrapolation is accurate.

## Commands and evidence

From the research repository root:

```bash
python3 scripts/reproduction/download-triangle-gb-vgb.py
environments/triangle-gb/.venv/bin/python scripts/reproduction/check-triangle-gb-vgb-data.py
```

The downloader reuses only verified complete files, writes new downloads to `.part`, and renames after size/MD5 checks. Re-running with existing files reports verification/reuse timing rather than the first download time. The checker intentionally exits 2 for the current coverage gap; inspect the structured report rather than relabeling it as a passing scientific test.

Curated evidence is in `results/triangle-gb/data/`; source preservation is separately audited by `audit-triangle-gb-source.py`. Local absolute paths are namespace adapters only. The bulk data are not in GitHub, but scripts, metadata, checksums and actual checks are reproducible from the public links. No Example 3 data or network Fisher package was downloaded.
