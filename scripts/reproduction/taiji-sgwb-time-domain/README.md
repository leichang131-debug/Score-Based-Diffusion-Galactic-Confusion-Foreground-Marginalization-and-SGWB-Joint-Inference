# Reproduction entry points

- `replay-figure-8.sh` runs the unchanged upstream archive download and `reproduce.py all --latex` workflow. It writes logs and output to a new run directory.
- `audit-figure-8.py` verifies the PNG against the upstream report and independently reads the six archived HDF5 files to check the ten-parameter traces and recompute the three Bayes factors.

- `summarize-formal-sampling.py` checks the extracted formal archives against the Bilby/Dynesty outputs and writes the timing CSV.

- `plot-fresh-figure-8.py` renders the three fresh posteriors and Figure 8 spectrum with the upstream LaTeX style and configuration-only legends.

See the [reference replay](../../../results/taiji-sgwb-time-domain/reference-replay/README.md) for the exact commands and evidence. Production run and resume tools remain pending.
