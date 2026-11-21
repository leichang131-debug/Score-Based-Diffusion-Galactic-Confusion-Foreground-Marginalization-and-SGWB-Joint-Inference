#!/usr/bin/env bash
# Replay the upstream paper figures with its LaTeX rendering option.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
upstream="$repo/external/taiji-sgwb-time-domain"
python="${TAIJI_PYTHON:-$repo/environments/taiji-sgwb-time-domain/.venv/bin/python}"
runs="$repo/runs/taiji-sgwb-time-domain"
mkdir -p "$runs"
if [[ $# -gt 1 ]]; then
    echo "Usage: $0 [run-directory]" >&2
    exit 2
fi
if [[ $# -eq 1 ]]; then
    mkdir -p "$1"
    run="$(cd "$1" && pwd)"
else
    run="$(mktemp -d "$runs/figure-8.XXXXXXXX")"
fi
if [[ -e "$run/replay.txt" || -e "$run/outputs" ]]; then
    echo "Choose a fresh replay directory: $run" >&2
    exit 2
fi

command -v latex >/dev/null
command -v dvipng >/dev/null
export MPLBACKEND=Agg
export MPLCONFIGDIR="$run/matplotlib"

cd "$upstream"
"$python" -u get_data.py 2>&1 | tee "$run/replay-data.txt"
"$python" -u reproduce.py all --latex --output "$run/outputs" 2>&1 | tee "$run/replay.txt"
echo "Figure 8: $run/outputs/figure/10para_corner.png"
