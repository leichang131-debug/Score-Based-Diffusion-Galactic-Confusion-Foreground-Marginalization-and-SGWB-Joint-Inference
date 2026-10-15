# TaijiSGWB Stage 1: complete pinned source preservation

Upstream: https://github.com/DrizzleatDusk/TaijiSGWB

Pinned commit: `4afaad4044b08721e7f1ce29cba3b0d912636dce` (`initial commit`).

Source snapshot: `external/taiji-sgwb/`, directly tracked as ordinary files in the research repository since 2026-10-15. All 19 files retain the upstream names, directory hierarchy, contents, file modes and original GPL license. GitHub and ordinary clones now expose `demos/` and `src/taijisgwb/` directly, without initializing a TaijiSGWB submodule. Other external components remain submodules. The fixed upstream URL, commit, Git tree and per-file blob/SHA-256 identities are recorded in `configs/upstream/taiji-sgwb.json`. No second execution copy is maintained.

## Scope and status

Stage 1 preserves the entire 19-file upstream tree, including 15 Python files, two demo entry points, the build configuration, README, ignore rules and original license. Names, directory hierarchy, byte contents and Git file modes are audited against the pinned blob identities; the original Git tree hash is reconstructed from the snapshot without needing cached upstream Git history. No upstream Python is imported or executed by the audit. This source-preservation stage is distinct from later deployment and completed template inference; see the current handoff record for their status. Source preservation checks do not validate scientific correctness.

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
python3 scripts/reproduction/audit-taiji-sgwb-source.py
```

For a local audit without a network check:

```bash
python3 scripts/reproduction/audit-taiji-sgwb-source.py --offline
```

TaijiSGWB files arrive with an ordinary clone; the other upstream components still require their own submodule initialization. The offline audit verifies all 19 directly indexed files and reconstructs tree `2e8b119ce0cd93f426b0b32081cd8347d2bb8e02` using only the snapshot and committed lock metadata. Finder `.DS_Store` metadata is ignored and never tracked. The online audit additionally verifies upstream HEAD and main against the pin. A future upstream update will cause those checks to fail without silently updating the checkout; local source preservation can still be checked offline.

## Evidence

- [File list](../../../results/taiji-sgwb/source/file-list.txt): all original relative paths.
- [Manifest](../../../results/taiji-sgwb/source/manifest.json): byte sizes, SHA-256, Git blob IDs, file modes and per-file comparison results.
- [Audit](../../../results/taiji-sgwb/source/audit.json): version, upstream verification, source checks and explicit scope.
- [Audit script](../../../scripts/reproduction/audit-taiji-sgwb-source.py): reproducible standard-library inspection.

Future launch/configuration adapters and evidence exporters belong in project-owned directories. Original demo names, package paths, comments and contents are retained. Any necessary runtime adaptation must be separately documented and checked against the original implementation.

## License

Upstream declares `GPL-3.0-or-later` and retains its original `LICENSE`. The project root MIT license covers project-owned material and does not relicense TaijiSGWB.


## Conversion record

The previous submodule registration and gitlink were removed without editing any upstream file. The old Git pointer is backed up in ignored runs/taiji-sgwb/source-snapshot-conversion/; local cached Git objects remain recoverable. Historical source evidence is preserved under results/taiji-sgwb/source/submodule-before-conversion/. The reference 19-file manifest remains byte-identical. A shared project-owned taiji_sgwb_source.py now supplies source-pin and pristine-tree checks to dependent audits, instead of mistakenly reading the parent repository HEAD after conversion.

The environment path is unchanged, including existing editable imports. Sampling input/configuration, frozen execution adapters, HDF chains and final checkpoints are unchanged; no new MCMC run is part of conversion. The full source remains GPL-3.0-or-later and is not relicensed by the project's MIT license.

## Snapshot conversion verification (2026-10-15)

The conversion report is `results/taiji-sgwb/source/snapshot-conversion.json`. The online source audit passes 18/18 checks. An independent export without upstream Git objects or submodule metadata passes all 16 offline checks; its evidence is `clean-export-audit.json` and `clean-export-check.log` in the same evidence directory. Existing environment imports resolve to the unchanged local package path.

The original source manifest remains byte-identical. SHA-256 checks confirm that the formal sampling backend, final state JSON/NPZ and cold-chain samples are unchanged. The other four submodules retain their original pins. No sampling was launched or advanced for this conversion.

Upstream trailing whitespace is retained intentionally to preserve exact source bytes; whitespace checks for newly maintained project files exclude `external/taiji-sgwb/`. The original submodule audit and manifest are archived under `source/submodule-before-conversion/`.
