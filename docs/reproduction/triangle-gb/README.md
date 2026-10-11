# Triangle-GB reproduction

Current milestone: full source integration and directory preparation only. See [source integration and scope](source-integration.md).

Next milestones:

1. Resolve and validate a dedicated environment and original-path handling.
2. Download/verify public TDC II verification data and inspect the HDF5 schema.
3. Reproduce Example 0 at original settings; audit TD/FD response comparison and mismatch.
4. Reproduce Example 1 search and Example 2 posterior inference with runtime budgeting.
5. Prepare LDC reconstruction and the network example as separate documented milestones.

Running examples validates the core `Triangle_GB/` methods they call. It does not establish all auxiliary methods, arbitrary configurations or GPU paths. Keep source and executed evidence separate.
