#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_DIR="$REPO_ROOT/environments/taiji-sgwb"
export UV_CACHE_DIR="$REPO_ROOT/runs/taiji-sgwb-setup/uv-cache"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$REPO_ROOT/../.python-runtimes}"
mkdir -p "$UV_CACHE_DIR"
[[ "$(uname -m)" == arm64 && "$(uname -s)" == Darwin ]]
python3 "$REPO_ROOT/scripts/reproduction/audit-taiji-sgwb-source.py" --offline --output-dir "$REPO_ROOT/runs/taiji-sgwb-setup/source-audit"
if [[ ! -x "$UV_PYTHON_INSTALL_DIR/cpython-3.11.14-macos-aarch64-none/bin/python3.11" ]]; then
  uv python install --no-bin 3.11.14
fi
if [[ ! -x "$ENV_DIR/.venv/bin/python" ]]; then
  uv venv --python "$UV_PYTHON_INSTALL_DIR/cpython-3.11.14-macos-aarch64-none/bin/python3.11" "$ENV_DIR/.venv"
fi
"$ENV_DIR/.venv/bin/python" -c 'import platform; assert platform.python_version() == "3.11.14"; assert platform.machine() == "arm64"'
uv pip sync --python "$ENV_DIR/.venv/bin/python" --require-hashes "$ENV_DIR/requirements-macos-arm64-py311.txt" --index-url https://pypi.org/simple
# Hatchling is in the lock; install the pinned source without dependency resolution.
uv pip install --python "$ENV_DIR/.venv/bin/python" --no-deps --no-build-isolation --editable "$REPO_ROOT/external/taiji-sgwb"
uv pip check --python "$ENV_DIR/.venv/bin/python"
