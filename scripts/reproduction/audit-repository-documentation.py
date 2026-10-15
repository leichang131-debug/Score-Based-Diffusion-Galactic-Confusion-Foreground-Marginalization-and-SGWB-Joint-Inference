#!/usr/bin/env python3
"""Read-only tracked-file syntax, local-link and artifact-hash verification."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    paths = [p for p in paths if p and (ROOT/p).is_file()]
    issues = []
    counts = {'json_files': 0, 'python_files': 0, 'markdown_files': 0,
              'local_links': 0, 'manifest_files': 0, 'hash_entries': 0, 'root_layout_paths': 0}
    per_manifest = {}
    for name in paths:
        p = ROOT/name
        if p.suffix == '.py':
            counts['python_files'] += 1
            try:
                ast.parse(p.read_text(), filename=name)
            except (SyntaxError, UnicodeError) as exc:
                issues.append({'file': name, 'problem': 'python_syntax', 'detail': str(exc)})
        if p.suffix == '.json':
            counts['json_files'] += 1
            try:
                doc = json.loads(p.read_text())
            except (ValueError, UnicodeError) as exc:
                issues.append({'file': name, 'problem': 'json_syntax', 'detail': str(exc)})
                continue
            if 'manifest' not in p.name:
                continue
            entries = doc if isinstance(doc, list) else doc.get('files', []) if isinstance(doc, dict) else []
            if not isinstance(entries, list) or not entries:
                continue
            counts['manifest_files'] += 1
            checked = 0
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get('sha256'):
                    continue
                rel = entry.get('repository_path', entry.get('path', entry.get('file')))
                if not rel:
                    continue
                target = ROOT/rel
                if not target.exists() and (p.parent/rel).exists():
                    target = p.parent/rel
                checked += 1
                counts['hash_entries'] += 1
                if not target.is_file():
                    issues.append({'file': name, 'path': rel, 'problem': 'missing_hash_target'})
                elif hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
                    issues.append({'file': name, 'path': rel, 'problem': 'hash_mismatch'})
            per_manifest[name] = checked
        # Original vendored Markdown is preserved; project local links are audited.
        if p.suffix == '.md' and not name.startswith('external/taiji-sgwb/'):
            counts['markdown_files'] += 1
            for match in re.finditer(r'!?\[[^\]\n]*\]\((?:<([^>]+)>|([^\s)]+))\)', p.read_text()):
                link = match.group(1) or match.group(2)
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:|^#', link):
                    continue
                target = unquote(link.split('#')[0])
                if target:
                    counts['local_links'] += 1
                    if not (p.parent/target).exists():
                        issues.append({'file': name, 'target': link, 'problem': 'broken_local_link'})
    layout = re.search(r'```text\n(.*?)```', (ROOT/'README.md').read_text(), re.S)
    if layout:
        parents = []
        for line in layout.group(1).splitlines():
            item = re.match(r'([│ ]*)(?:├── |└── )([^ #]+)', line)
            if not item:
                continue
            level = len(item.group(1))//4
            label = item.group(2).rstrip('/')
            relative = Path(*parents[:level], label)
            counts['root_layout_paths'] += 1
            if not (ROOT/relative).exists():
                issues.append({'file': 'README.md', 'path': str(relative), 'problem': 'missing_layout_path'})
            if item.group(2).endswith('/'):
                parents = parents[:level]+[label]
    report = {'scope': 'Current tracked files, including staged additions. No scientific execution; no remote URL or anchor checks. Supported manifest.files/list path+SHA256 records only; templates without file hashes are not scientific evidence.',
              'counts': counts, 'per_manifest': per_manifest, 'issues': issues,
              'all_checks_pass': not issues}
    destination = args.output if args.output.is_absolute() else ROOT/args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'counts': counts, 'issues': issues, 'all_checks_pass': not issues}, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
