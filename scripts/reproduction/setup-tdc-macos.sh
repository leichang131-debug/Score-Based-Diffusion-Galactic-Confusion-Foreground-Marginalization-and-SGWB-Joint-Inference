#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$REPO_ROOT/external/triangle-simulator"
ENV_DIR="$REPO_ROOT/environments/tdc"
export UV_CACHE_DIR="$REPO_ROOT/runs/tdc-setup/uv-cache"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$REPO_ROOT/../.python-runtimes}"
mkdir -p "$UV_CACHE_DIR"
git -C "$REPO_ROOT" submodule update --init external/triangle-simulator
test "$(git -C "$SRC" rev-parse HEAD)" = ab796358e9a36c8987f6bb53a97230d603bfdfd5
uv python install 3.9.19
if [[ ! -x "$ENV_DIR/.venv/bin/python" ]]; then
  uv venv --python "$UV_PYTHON_INSTALL_DIR/cpython-3.9.19-macos-aarch64-none/bin/python3.9" "$ENV_DIR/.venv"
fi
"$ENV_DIR/.venv/bin/python" -c 'import platform; assert platform.python_version() == "3.9.19"; assert platform.machine() == "arm64"'
uv export --project "$SRC" --locked --no-dev --no-emit-project --format requirements.txt --output-file "$ENV_DIR/requirements-upstream.txt"
uv pip sync --python "$ENV_DIR/.venv/bin/python" "$ENV_DIR/requirements-upstream.txt"
uv pip install --python "$ENV_DIR/.venv/bin/python" --no-deps --editable "$SRC"
uv pip check --python "$ENV_DIR/.venv/bin/python"
"$ENV_DIR/.venv/bin/python" -m ipykernel install --prefix "$ENV_DIR/.venv" --name triangle-tdc --display-name "Triangle TDC — Python 3.9.19"
