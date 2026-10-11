#!/usr/bin/env python3
"""Prepare local ignored workspace paths without editing upstream notebooks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'runs/triangle-gb/workspace'
EXAMPLES = WORK / 'Triangle-GB/Examples'
EXAMPLES.mkdir(parents=True, exist_ok=True)
(WORK / 'Triangle-GB/Test').mkdir(parents=True, exist_ok=True)
(ROOT / 'data/raw/triangle-gb').mkdir(parents=True, exist_ok=True)


def link(path, target):
    if path.is_symlink():
        if path.resolve() != target.resolve():
            raise RuntimeError(f'Existing link points elsewhere: {path}')
    elif path.exists():
        raise RuntimeError(f'Refusing to replace an existing path: {path}')
    else:
        path.symlink_to(target, target_is_directory=True)


link(WORK / 'Triangle-GB/Triangle_GB', ROOT / 'external/triangle-gb/Triangle_GB')
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
print('Prepared ignored Triangle-GB workspace; no notebook executed.')

# Dedicated-kernel startup hook; do not edit any upstream notebook cell.
startup = ROOT / 'runs/triangle-gb/ipython/profile_default/startup'
startup.mkdir(parents=True, exist_ok=True)
hook = ROOT / 'scripts/reproduction/triangle_gb_path_adapter.py'
(startup / '00-triangle-gb-paths.py').write_text(
    'import runpy\nrunpy.run_path(' + repr(str(hook)) + ')["install_adapter"]()\n')

# Prepare only missing same-name working copies; never overwrite user edits.
source_examples = ROOT / 'external/triangle-gb/Examples'
for source in sorted(source_examples.glob('*.ipynb')):
    target = EXAMPLES / source.name
    if not target.exists():
        notebook = json.loads(source.read_text())
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
        notebook['metadata']['kernelspec'] = {
            'display_name': 'Triangle-GB — Python 3.11.14 (CPU)',
            'language': 'python', 'name': 'triangle-gb'}
        target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n')
    original = json.loads(source.read_text())
    current = json.loads(target.read_text())
    if len(original['cells']) != len(current['cells']) or any(
        a['cell_type'] != b['cell_type'] or a['source'] != b['source']
        for a, b in zip(original['cells'], current['cells'])):
        raise RuntimeError(f'Working copy source/Markdown changed: {target}')
print('Five same-name working notebooks retain all source/Markdown; no upstream outputs copied.')
