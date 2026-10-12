#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export MPLCONFIGDIR="$REPO_ROOT/runs/taiji-sgwb/matplotlib"
export MPLBACKEND="${MPLBACKEND:-Agg}"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-1}"
mkdir -p "$MPLCONFIGDIR"
exec "$REPO_ROOT/environments/taiji-sgwb/.venv/bin/python" -B "$@"
