#!/bin/bash
# Run through Terminal.app, not the coding tool's process tree.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
mkdir -p runs/taiji-sgwb/template-formal
if /usr/bin/screen -ls 2>/dev/null | /usr/bin/grep -q '\.taiji-sgwb-formal'; then
    echo 'An existing TaijiSGWB screen session must be inspected before starting another.'
    exit 1
fi
echo "Starting original full-data chain from its verified latest checkpoint."
echo "Keep AC connected and the lid open. Force sleep/logout/shutdown can stop the job."
/usr/bin/screen -dmS taiji-sgwb-formal /bin/bash \
    "$REPO_ROOT/scripts/reproduction/run-taiji-sgwb-python.sh" \
    "$REPO_ROOT/scripts/reproduction/run-taiji-sgwb-resilient.py"
/usr/bin/screen -ls
echo "Detached session started. Actual progress is recorded in runs/taiji-sgwb/template-formal/progress.json."
