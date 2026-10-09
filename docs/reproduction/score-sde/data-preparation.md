# CIFAR-10 preparation for the original Score-SDE pipeline

Scope: environment, source-state, disk and real-data input validation. No model initialization, optimization, or training is performed by this preparation stage.

From the repository root:

```bash
# Optional: use eight byte-range requests if the original server is slow.
environments/score-sde/.venv/bin/python scripts/reproduction/download-cifar10-archive.py
# Prepare TFDS records and verify all raw examples plus the original pipeline.
environments/score-sde/.venv/bin/python scripts/reproduction/prepare-cifar10.py
```

Data are from the original CIFAR-10 binary archive at https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz. Expected size: 170052171 bytes. SHA-256 from the installed TFDS checksum registry: `c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd`.
The optional downloader validates HTTP byte ranges and the assembled file's size and SHA-256. TFDS performs forced checksum validation again. HTTPS certificate validation remains enabled.

Prepared data reside under `data/raw/tensorflow_datasets/cifar10/3.0.2/`; the manually downloaded archive is under `data/raw/tensorflow_datasets/downloads/manual/`. TFDS reuses the prepared data on subsequent runs. Data and temporary downloads are ignored by Git.

The preparation script disables optional GCS metadata probing using TFDS 4.9.4's runtime flag, avoiding a stalled cloud request. It does not edit TFDS or either upstream repository. Dataset generation and preprocessing use the real TFDS builder and original `datasets.get_dataset` implementation.

Checks:

- Scan all 50000 training examples and 10000 test examples.
- Verify uint8 32x32x3 raw images, integer labels 0–9, and balanced per-class counts.
- Read both streams through upstream `datasets.get_dataset` in training mode.
- Use batch size 1 and one update per compiled scan, on one CPU device.
- Verify loader shape `[device, scan_step, batch, height, width, channels] = [1, 1, 1, 32, 32, 3]` and float32 pixels in `[0, 1]`.
- Apply the original centered scaler and verify finite values in `[-1, 1]`.
- Verify that removing device and scan-step axes leaves network input `[1, 32, 32, 3]`.
- Record prepared-file hashes, package versions and pinned upstream commits.

The upstream training-mode evaluation stream uses the CIFAR-10 **test** split and retains its original random-flip preprocessing. It should not also be described as an untouched independent final test set.

The machine-readable validation record is `cifar10-validation.json`. It documents data readiness, not model convergence or generation quality. Full local logs remain under `runs/score-sde/`.
