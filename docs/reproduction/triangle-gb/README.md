# Triangle-GB reproduction

Source integration is complete. Independent environment and path setup is documented in [environment setup](environment-setup.md); consult its validation evidence for readiness. See [source integration and scope](source-integration.md).

Next milestones:

1. Download/verify public TDC II verification data and inspect the HDF5 schema.
2. Reproduce Example 0 at original settings; audit TD/FD response comparison and mismatch.
3. Reproduce Example 1 search and Example 2 posterior inference with runtime budgeting.
4. Prepare LDC reconstruction and the network example as separate documented milestones.

Running examples validates the core `Triangle_GB/` methods they call. It does not establish all auxiliary methods, arbitrary configurations or GPU paths. Keep source and executed evidence separate.
