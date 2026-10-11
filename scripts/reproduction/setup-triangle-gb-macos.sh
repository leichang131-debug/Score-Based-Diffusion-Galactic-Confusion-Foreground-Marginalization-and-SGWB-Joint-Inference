#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_DIR="$REPO_ROOT/environments/triangle-gb"
export UV_CACHE_DIR="$REPO_ROOT/runs/triangle-gb-setup/uv-cache"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$REPO_ROOT/../.python-runtimes}"
mkdir -p "$UV_CACHE_DIR"
[[ "$(uname -m)" == arm64 && "$(uname -s)" == Darwin ]]
python3 "$REPO_ROOT/scripts/reproduction/audit-triangle-gb-source.py"
uv python install 3.11.14
if [[ ! -x "$ENV_DIR/.venv/bin/python" ]]; then
  uv venv --python "$UV_PYTHON_INSTALL_DIR/cpython-3.11.14-macos-aarch64-none/bin/python3.11" "$ENV_DIR/.venv"
fi
"$ENV_DIR/.venv/bin/python" -c 'import platform; assert platform.python_version() == "3.11.14"; assert platform.machine() == "arm64"'
uv pip sync --python "$ENV_DIR/.venv/bin/python" --require-hashes "$ENV_DIR/requirements-macos-arm64-py311.txt" --index-url https://pypi.org/simple
# Triangle must precede Triangle_GB. Editable installation preserves pinned source.
uv pip install --python "$ENV_DIR/.venv/bin/python" --no-deps --no-build-isolation --editable "$REPO_ROOT/external/triangle-simulator"
uv pip install --python "$ENV_DIR/.venv/bin/python" --no-deps --no-build-isolation --editable "$REPO_ROOT/external/triangle-gb"
uv pip check --python "$ENV_DIR/.venv/bin/python"
"$ENV_DIR/.venv/bin/python" -m ipykernel install --prefix "$ENV_DIR/.venv" --name triangle-gb --display-name 'Triangle-GB — Python 3.11.14 (CPU)'
"$ENV_DIR/.venv/bin/python" "$REPO_ROOT/scripts/reproduction/prepare-triangle-gb-paths.py"
