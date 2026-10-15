# Environments

Keep independently validated environment specifications for Score-SDE, TDC, Triangle-GB, and TaijiSGWB. Maintain platform-specific locks for macOS CPU and the laboratory Linux cluster as needed.

Score-SDE and Triangle-Simulator now have separate validated macOS CPU environments; see their component READMEs and validation evidence. TaijiSGWB also has a validated independent macOS ARM64 Python 3.11 environment; see [its setup](taiji-sgwb/README.md). Linux cluster environments remain pending. Record the Python architecture, package versions, JAX devices, driver/runtime information, and successful verification commands before marking an environment reproducible.

Triangle-GB has an [installed dedicated macOS ARM64 CPU environment](triangle-gb/README.md). Sangria and Fisher dependencies are prepared and all five examples have executed; see [current reports and core-check limitations](../docs/reproduction/triangle-gb/README.md).
