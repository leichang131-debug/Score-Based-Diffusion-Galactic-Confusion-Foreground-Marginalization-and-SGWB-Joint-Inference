#!/usr/bin/env python3
"""Prepare local ignored workspace paths without editing upstream notebooks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'runs/triangle-gb/workspace'
EXAMPLES = WORK / 'Triangle-GB/Examples'
EXAMPLES.mkdir(parents=True, exist_ok=True)
(ROOT / 'data/raw/triangle-gb').mkdir(parents=True, exist_ok=True)


def link(path, target):
    if path.is_symlink():
        if path.resolve() != target.resolve():
            raise RuntimeError(f'Existing link points elsewhere: {path}')
    elif path.exists():
        raise RuntimeError(f'Refusing to replace an existing path: {path}')
    else:
        path.symlink_to(target, target_is_directory=True)


link(WORK / 'Triangle-Simulator', ROOT / 'external/triangle-simulator')
link(EXAMPLES / 'LDCEqualArmOrbit', ROOT / 'external/triangle-gb/Examples/LDCEqualArmOrbit')
paths = {
    'repository_root': str(ROOT),
    'working_examples': str(EXAMPLES),
    'source_examples': str(ROOT / 'external/triangle-gb/Examples'),
    'tdc_orbit': str(ROOT / 'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB'),
    'ldc_orbit': str(ROOT / 'external/triangle-gb/Examples/LDCEqualArmOrbit'),
    'vgb_data': str(ROOT / 'data/raw/triangle-gb/0_1_VGB_TDIXYZ.h5'),
    'vgb_parameters': str(ROOT / 'data/raw/triangle-gb/0_1_VGB_parameters.h5'),
    'ldc_sangria': str(ROOT / 'data/raw/triangle-gb/LDC2_sangria_training_v2.h5'),
}
(WORK / 'paths.local.json').write_text(json.dumps(paths, indent=2) + '\n')
print('Prepared ignored Triangle-GB workspace; no notebooks copied or executed.')
