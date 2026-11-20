# Full-covariance Taiji environment

The local environment uses CPython 3.12.14 on macOS ARM64 with the CPU backend. Its dependencies are installed from the [upstream inference requirements](../../external/taiji-sgwb-time-domain/requirements-inference.txt), including the replay requirements and upstream constraints. See the [installed package lock](requirements-macos-arm64-cpu.lock.txt) and the [validation record](../../results/taiji-sgwb-time-domain/environment/macos-arm64-cpu.json).

From the research repository root, recreate the local environment with an ARM64 Python 3.12 interpreter and uv:

```sh
env_dir="$PWD/environments/taiji-sgwb-time-domain/.venv"
uv venv --python python3.12 "$env_dir"
uv pip sync --python "$env_dir/bin/python" environments/taiji-sgwb-time-domain/requirements-macos-arm64-cpu.lock.txt
uv pip check --python "$env_dir/bin/python"
cd external/taiji-sgwb-time-domain
JAX_PLATFORMS=cpu "$env_dir/bin/python" infer.py list
JAX_PLATFORMS=cpu "$env_dir/bin/python" scripts/astro/ch33_sw10_fullxyz_20260531.py --help
```

For a new Linux environment, install the upstream inference requirements and record a separate verified lock. The macOS check covers package imports, the vendored Triangle-Simulator import, the Figure 8 fit registry, and synthetic NumPy/JAX likelihood agreement. Linux, CUDA, official data replay, production input validation, and sampling are pending for this baseline.
