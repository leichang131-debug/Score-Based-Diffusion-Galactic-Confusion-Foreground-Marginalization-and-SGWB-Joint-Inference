#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIMES="$ROOT/../.python-runtimes"
CACHE="$ROOT/runs/score-sde/uv-cache"
PYTHON="$RUNTIMES/cpython-3.12.14-macos-aarch64-none/bin/python3.12"
mkdir -p "$CACHE"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo "This setup is validated for macOS ARM64 CPU only." >&2; exit 1
fi
uv --cache-dir "$CACHE" python install 3.12.14 --no-bin --install-dir "$RUNTIMES"
if [[ ! -x "$ROOT/environments/score-sde/.venv/bin/python" ]]; then
  uv --cache-dir "$CACHE" venv --python "$PYTHON" "$ROOT/environments/score-sde/.venv"
fi
uv --cache-dir "$CACHE" pip sync --python "$ROOT/environments/score-sde/.venv/bin/python" "$ROOT/environments/score-sde/requirements-lock.txt"
uv --cache-dir "$CACHE" pip check --python "$ROOT/environments/score-sde/.venv/bin/python"
