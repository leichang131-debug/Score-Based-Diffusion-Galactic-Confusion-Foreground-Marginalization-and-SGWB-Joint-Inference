# Triangle-GB data provenance

Examples 1 and 2 share two public TDC II verification files linked in their original first Markdown cells. Both have been downloaded locally with their original filenames under ignored `data/raw/triangle-gb/`, checked against official sizes and MD5 values, and assigned local SHA-256 hashes. No bulk data are committed.

- [0_1_VGB_TDIXYZ.h5](https://zenodo.org/records/15469724/files/0_1_VGB_TDIXYZ.h5?download=1): 100,707,680 bytes; published MD5 `01b91a77eef8ae14b12473fa11b9f5ce`.
- [0_1_VGB_parameters.h5](https://zenodo.org/records/15532090/files/0_1_VGB_parameters.h5?download=1): 7,904 bytes; published MD5 `53ac143f8537996bf73c2dcd2419f4f4`.

See [download/check evidence](../../results/triangle-gb/data/README.md) and [data preparation report](../../docs/reproduction/triangle-gb/data-preparation.md). HDF5 schema, full numerical finiteness and tutorial preprocessing checks pass. **Strict orbit coverage does not pass**: the data tail extends 22,140 seconds beyond the bundled default orbit table, and the zero-padded sparse template grid also queries negative delayed boundary times. This is recorded separately from data integrity; default spline extrapolation is finite but its accuracy has not been established.

Example 0 generates its own signal. Example 3 now has the separate official `LDC2_sangria_training_v2.h5` input and full original dgb parameter cache prepared; see [prerequisite completion](../../docs/reproduction/triangle-gb/prerequisites-completion.md). The network Fisher dependency is installed from pinned Triangle-BBH and bundled WF4Py. Earlier statements about missing Sangria/Fisher describe prior milestones, not current prerequisites.
