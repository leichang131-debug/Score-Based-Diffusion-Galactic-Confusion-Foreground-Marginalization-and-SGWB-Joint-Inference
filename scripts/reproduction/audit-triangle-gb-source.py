#!/usr/bin/env python3
"""Audit pinned source preservation only; never import or run upstream code."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'external/triangle-gb'
OUTPUT = ROOT / 'results/triangle-gb/source'
PIN = 'cbc0a1b0cbf4ec05ec969fa39405394168c3e06c'
SIM_PIN = 'ab796358e9a36c8987f6bb53a97230d603bfdfd5'
URL = 'https://github.com/TriangleDataCenter/Triangle-GB.git'
NOTEBOOKS = [
    '0_TDIFlyGB_Compare_TD_FD_Waveforms(CPU).ipynb',
    '1_TDIFlyGB_Rapid_Search(CPU).ipynb',
    '2_TDIFlyGB_Parameter_Estimation(CPU).ipynb',
    '3_LDC2a_GB_Reconstruction.ipynb',
    'GB_network_PE_example_for_2609.16477.ipynb',
]
ORBITS = [f'Examples/LDCEqualArmOrbit/SC{k}{i}.dat'
          for k in ('P', 'V') for i in range(1, 4)]
EXPECTED = sorted(['.gitignore', 'README.md', 'LICENSE', 'pyproject.toml',
                   'Triangle_GB/__init__.py', 'Triangle_GB/TDIFly.py']
                  + ['Examples/' + name for name in NOTEBOOKS] + ORBITS)


def git(*args, cwd=SOURCE):
    return subprocess.check_output(['git', '-C', str(cwd), *args])


def audit():
    checks = {}
    checks['pinned_commit'] = git('rev-parse', 'HEAD').decode().strip() == PIN
    checks['clean_source'] = not git('status', '--porcelain').strip()
    paths = sorted(git('ls-tree', '-r', '--name-only', PIN).decode().splitlines())
    checks['complete_expected_tree'] = paths == EXPECTED
    manifest = []
    matches = True
    for name in paths:
        path = SOURCE / name
        actual = path.read_bytes()
        original = git('show', f'{PIN}:{name}')
        matches = matches and actual == original
        manifest.append({'path': 'external/triangle-gb/' + name,
                         'bytes': len(actual),
                         'sha256': hashlib.sha256(actual).hexdigest()})
    checks['all_files_match_pinned_git_blobs'] = matches
    notebooks = []
    for name in NOTEBOOKS:
        nb = json.loads((SOURCE / 'Examples' / name).read_text())
        checks['notebook_json_' + name] = nb['nbformat'] == 4
        notebooks.append({'filename': name, 'cells': len(nb['cells']),
                          'code_cells': sum(c['cell_type'] == 'code' for c in nb['cells']),
                          'outputs_origin': 'upstream reference outputs; not locally executed'})
    required_classes = {'TDIFly', 'TDIFlyGB', 'TDIFlyGBNetwork'}
    tree = ast.parse((SOURCE / 'Triangle_GB/TDIFly.py').read_text())
    checks['required_core_classes'] = required_classes <= {
        node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    init_tree = ast.parse((SOURCE / 'Triangle_GB/__init__.py').read_text())
    exports = {item.name for node in init_tree.body if isinstance(node, ast.ImportFrom)
               and node.module == 'TDIFly' for item in node.names}
    checks['public_class_imports'] = required_classes <= exports
    checks['six_orbit_files'] = all((SOURCE / name).is_file() for name in ORBITS)
    checks['original_gpl3_license'] = 'Version 3, 29 June 2007' in (SOURCE / 'LICENSE').read_text()
    checks['declared_python_minimum'] = 'requires-python = ">=3.9"' in (SOURCE / 'pyproject.toml').read_text()
    checks['registered_submodule_url'] = git('config', '-f', '.gitmodules', '--get',
        'submodule.external/triangle-gb.url', cwd=ROOT).decode().strip() == URL
    simulator = ROOT / 'external/triangle-simulator'
    checks['simulator_pin_preserved'] = git('rev-parse', 'HEAD', cwd=simulator).decode().strip() == SIM_PIN
    checks['simulator_source_clean'] = not git('status', '--porcelain', cwd=simulator).strip()
    report = {'scope': 'Source preservation only; no environment installation, data download or example execution.',
              'upstream_url': URL, 'pinned_commit': PIN,
              'upstream_commit_date': git('show', '-s', '--format=%cI', PIN).decode().strip(),
              'shallow_checkout': git('rev-parse', '--is-shallow-repository').decode().strip() == 'true',
              'tracked_files': len(paths), 'notebooks': notebooks,
              'checks': checks, 'all_checks_pass': all(checks.values())}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'manifest.json').write_text(json.dumps({'pinned_commit': PIN, 'files': manifest}, indent=2) + '\n')
    (OUTPUT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Triangle-GB source audit: {sum(checks.values())}/{len(checks)} checks passed; {len(paths)} files, {len(notebooks)} notebooks.")
    if not report['all_checks_pass']:
        raise SystemExit('FAILED: ' + ', '.join(k for k, passed in checks.items() if not passed))


if __name__ == '__main__':
    audit()
