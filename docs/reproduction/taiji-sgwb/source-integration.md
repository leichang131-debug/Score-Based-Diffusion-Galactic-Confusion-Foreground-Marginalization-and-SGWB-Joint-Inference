# TaijiSGWB Stage 1: complete pinned source preservation

Upstream: https://github.com/DrizzleatDusk/TaijiSGWB

Pinned commit: `4afaad4044b08721e7f1ce29cba3b0d912636dce` (`initial commit`).

Source checkout: `external/taiji-sgwb/`, integrated as a Git submodule, consistent with the other upstream components. The earlier project-owned placeholder README was replaced with the original upstream README. A gitlink records the exact commit; the parent repository does not duplicate or relicense upstream files. GitHub opens the submodule at the pinned upstream revision.

## Scope and status

Stage 1 preserves the entire 19-file upstream tree, including 15 Python files, two demo entry points, the build configuration, README, ignore rules and original license. Names, directory hierarchy, byte contents and Git file modes are audited against the pinned Git objects. No upstream Python is imported or executed by the audit. Environment installation, dataset acquisition, response calculation and inference reproduction are pending. Source preservation checks do not validate scientific correctness.

## Original structure

```text
external/taiji-sgwb/
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── demos/
│   ├── rj_nofg_28t.py
│   └── template_nofg_28t.py
└── src/taijisgwb/
    ├── __init__.py
    ├── analyorf.py
    ├── constants.py
    ├── plotlib.py
    ├── utils.py
    ├── waveform.py
    └── detector/
        ├── __init__.py
        ├── constants.py
        ├── data.py
        ├── interferometer.py
        ├── noise.py
        ├── orbit.py
        └── tdi.py
```

Both demos are original source, not locally reproduced outputs. The repository includes no input datasets, orbit files, notebook tutorials or completed sampling backends. These will be prepared separately without adding files to the upstream checkout.

## Retrieve and audit

From the research repository root:

```bash
git submodule update --init --recursive
python3 scripts/reproduction/audit-taiji-sgwb-source.py
```

For a local audit without a network check:

```bash
python3 scripts/reproduction/audit-taiji-sgwb-source.py --offline
```

The online audit verifies upstream HEAD and main against the pin. A future upstream update will cause those checks to fail without silently updating the checkout; local source preservation can still be checked offline.

## Evidence

- [File list](../../../results/taiji-sgwb/source/file-list.txt): all original relative paths.
- [Manifest](../../../results/taiji-sgwb/source/manifest.json): byte sizes, SHA-256, Git blob IDs, file modes and per-file comparison results.
- [Audit](../../../results/taiji-sgwb/source/audit.json): version, upstream verification, source checks and explicit scope.
- [Audit script](../../../scripts/reproduction/audit-taiji-sgwb-source.py): reproducible standard-library inspection.

Future launch/configuration adapters and evidence exporters belong in project-owned directories. Original demo names, package paths, comments and contents are retained. Any necessary runtime adaptation must be separately documented and checked against the original implementation.

## License

Upstream declares `GPL-3.0-or-later` and retains its original `LICENSE`. The project root MIT license covers project-owned material and does not relicense TaijiSGWB.
