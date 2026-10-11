# Triangle-GB data provenance

Status: no example data have been downloaded at this stage. Store bulk input files under ignored `data/raw/triangle-gb/`; record their provenance and checksums in curated evidence before execution.

Examples 1 and 2 use the same publicly linked TDC II verification files:

- [0_1_VGB_TDIXYZ.h5](https://zenodo.org/records/15469724/files/0_1_VGB_TDIXYZ.h5?download=1): 100,707,680 bytes; published MD5 `01b91a77eef8ae14b12473fa11b9f5ce`.
- [0_1_VGB_parameters.h5](https://zenodo.org/records/15532090/files/0_1_VGB_parameters.h5?download=1): 7,904 bytes; published MD5 `53ac143f8537996bf73c2dcd2419f4f4`.

These metadata were checked through Zenodo; downloading and checking the actual local files remain pending. Example 0 generates its own source signal using the existing Triangle-Simulator orbit. Example 3 requires the separate `LDC2_sangria_training_v2.h5` dataset, not supplied by this repository. The network example generates its own synthetic data.
