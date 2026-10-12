#!/usr/bin/env python3
"""Preserve official filenames and provide original demo names via symlinks."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    raw = ROOT / "data/raw/taiji-sgwb"
    data = raw / "TDCII2.8.h5"
    orbit = raw / "MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5"
    assert data.is_file() and orbit.is_file()
    base = ROOT / "runs/taiji-sgwb/workspace/data"
    links = [(base / "TDCII2-8.h5", data),
             (base / "MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5", orbit)]
    mapping = []
    for link, target in links:
        link.parent.mkdir(parents=True, exist_ok=True)
        if not link.is_symlink() and link.exists():
            raise RuntimeError(f"Refusing to replace an existing regular file: {link}")
        if link.is_symlink():
            assert link.resolve() == target.resolve(), f"Existing link differs: {link}"
        else:
            link.symlink_to(os.path.relpath(target, link.parent))
        assert link.resolve() == target.resolve()
        mapping.append({"link": str(link.relative_to(ROOT)), "target": str(target.relative_to(ROOT)),
                        "relative_symlink": os.readlink(link), "verified": True})
    result = {"scope": "Ignored runtime path aliases only; original input names and upstream programs unchanged.",
              "original_project_root": "/home/yang/WorkSpace/taiji_data_challenge_sgwb",
              "local_project_root": "runs/taiji-sgwb/workspace", "links": mapping,
              "note": "The original PROJ_DIR is not changed; a future launcher must explicitly supply the local project root."}
    out = ROOT / "results/taiji-sgwb/data/path-map.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
