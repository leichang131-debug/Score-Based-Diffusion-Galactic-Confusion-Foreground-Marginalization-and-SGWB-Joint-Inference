# Triangle-GB reproduction

Source integration is complete. Independent environment and path setup is documented in [environment setup](environment-setup.md); consult its validation evidence for readiness. See [source integration and scope](source-integration.md).

All public input/dependency prerequisites are now prepared, including Sangria and the complete dgb cache, pinned Triangle-BBH/WF4Py, and original network Fisher/prior interfaces. See [prerequisite completion](prerequisites-completion.md). The VGB strict orbit-coverage gap remains explicitly documented.

[Example 0](example-0.md) has completed a fresh full-scale local execution (10 nonempty code cells, two figures, reference mismatch agreement). [Example 1](example-1.md) has also completed the unchanged full-data rapid-search tutorial (17 nonempty cells, four figures, successful original DE search). [Example 2](example-2.md) has completed the original 500-live-point posterior-sampling workflow, with sampler diagnostics explicitly recorded. [Example 3](example-3.md) has completed full unchanged Sangria band reconstruction (16 nonempty cells, four figures, all 26 million catalog rows loaded, 39 sources reconstructed). The [network example](network.md) has also completed full original-default local execution (13 nonempty cells, three figures, 1000-live-point sampling). All five example notebooks are now executed; sampler reliability limitations remain explicit in each report. Input-preparation checks alone are not complete notebook reproductions.

Running examples validates the core `Triangle_GB/` methods they call. It does not establish all auxiliary methods, arbitrary configurations or GPU paths. Keep source and executed evidence separate.

## Core CPU verification and unresolved issues

[Core verification](core-validation.md) completed: 22 of 28 checks passed, six failed checks cover three original interface defects and two unmet time/frequency precision criteria. Default time output with drop_points=0 is zero; partial-band vectorized fill overwrites edge bins; loop fill fails in a tested wide-band case. Example 2 injection has a measured boundary effect; the original network injection support lies inside its band. Source is unchanged. Tutorial completion remains established, but package-wide acceptance and posterior calibration do not.
