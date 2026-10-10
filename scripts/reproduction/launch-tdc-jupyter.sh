#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-1}"
export JUPYTER_CONFIG_DIR="$REPO_ROOT/runs/tdc-jupyter/config"
export JUPYTER_DATA_DIR="$REPO_ROOT/environments/tdc/.venv/share/jupyter"
export JUPYTER_RUNTIME_DIR="$REPO_ROOT/runs/tdc-jupyter/runtime"
export IPYTHONDIR="$REPO_ROOT/runs/tdc-jupyter/ipython"
export MPLCONFIGDIR="$REPO_ROOT/runs/tdc-jupyter/matplotlib"
mkdir -p "$JUPYTER_CONFIG_DIR" "$JUPYTER_RUNTIME_DIR" "$IPYTHONDIR" "$MPLCONFIGDIR"
cd "$REPO_ROOT/external/triangle-simulator/Tutorials"
exec "$REPO_ROOT/environments/tdc/.venv/bin/jupyter" lab \
  --ServerApp.root_dir="$REPO_ROOT" \
  --LabApp.default_url=/lab/tree/external/triangle-simulator/Tutorials "$@"
