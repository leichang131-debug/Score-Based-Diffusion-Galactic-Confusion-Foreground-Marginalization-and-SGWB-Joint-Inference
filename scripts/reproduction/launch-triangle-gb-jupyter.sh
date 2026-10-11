#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_DIR="$REPO_ROOT/environments/triangle-gb"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export MPLCONFIGDIR="$REPO_ROOT/runs/triangle-gb/matplotlib"
export JUPYTER_CONFIG_DIR="$REPO_ROOT/runs/triangle-gb/jupyter-config"
export JUPYTER_RUNTIME_DIR="$REPO_ROOT/runs/triangle-gb/jupyter-runtime"
mkdir -p "$MPLCONFIGDIR" "$JUPYTER_CONFIG_DIR" "$JUPYTER_RUNTIME_DIR"
"$ENV_DIR/.venv/bin/python" "$REPO_ROOT/scripts/reproduction/prepare-triangle-gb-paths.py"
cd "$REPO_ROOT"
exec "$ENV_DIR/.venv/bin/jupyter" lab --ServerApp.root_dir="$REPO_ROOT" "$REPO_ROOT/runs/triangle-gb/workspace/Triangle-GB/Examples"
