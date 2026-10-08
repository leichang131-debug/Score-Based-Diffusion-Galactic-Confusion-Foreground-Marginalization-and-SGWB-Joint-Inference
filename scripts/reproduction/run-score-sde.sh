#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="$ROOT/environments/score-sde/.venv/bin/python"
UPSTREAM="$ROOT/external/score-sde-reproduction"
export JAX_PLATFORMS=cpu
export MPLCONFIGDIR="$ROOT/runs/score-sde/matplotlib"
export TFDS_DATA_DIR="$ROOT/data/raw/tensorflow_datasets"
mkdir -p "$MPLCONFIGDIR" "$TFDS_DATA_DIR"
cd "$UPSTREAM"
exec "$PYTHON" "$ROOT/scripts/reproduction/score_sde_bootstrap.py" "$@"
