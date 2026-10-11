# Environments

Keep independently validated environment specifications for Score-SDE, TDC, Triangle-GB, and TaijiSGWB. Maintain platform-specific locks for macOS CPU and the laboratory Linux cluster as needed.

Score-SDE and Triangle-Simulator now have separate validated macOS CPU environments; see their component READMEs and validation evidence. TaijiSGWB and Linux cluster environments remain pending. Record the Python architecture, package versions, JAX devices, driver/runtime information, and successful verification commands before marking an environment reproducible.

Triangle-GB has an [installed dedicated macOS ARM64 CPU environment](triangle-gb/README.md). See its validation record for checks and remaining data/Fisher dependencies.
