"""Read-only provenance checks for the vendored, unmodified TaijiSGWB tree."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'external/taiji-sgwb'
LOCK = ROOT / 'configs/upstream/taiji-sgwb.json'
PIN = '4afaad4044b08721e7f1ce29cba3b0d912636dce'
URL = 'https://github.com/DrizzleatDusk/TaijiSGWB.git'


def source_lock():
    lock = json.loads(LOCK.read_text())
    assert lock['pinned_commit'] == PIN and lock['upstream_url'] == URL
    assert lock['integration'] == 'fixed-source-snapshot'
    return lock


def source_pin():
    return source_lock()['pinned_commit']


def git_object(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def file_records():
    records = []
    for entry in source_lock()['files']:
        p = SOURCE / entry['path']
        data = p.read_bytes()
        mode = '100755' if p.stat().st_mode & 0o111 else '100644'
        oid = git_object('blob', data)
        records.append({**entry, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                        'matches_pinned_blob': oid == entry['git_blob'],
                        'matches_git_mode': mode == entry['git_mode']})
    return records


def actual_tree_oid():
    tree = {}
    for entry in source_lock()['files']:
        parts = Path(entry['path']).parts
        branch = tree
        for part in parts[:-1]:
            branch = branch.setdefault(part, {})
        p = SOURCE / entry['path']
        branch[parts[-1]] = ('100755' if p.stat().st_mode & 0o111 else '100644',
                            git_object('blob', p.read_bytes()))

    def digest(branch):
        entries = []
        for name, value in branch.items():
            directory = isinstance(value, dict)
            mode, oid = ('40000', digest(value)) if directory else value
            entries.append(((name + ('/' if directory else '')).encode(),
                            mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(oid)))
        return git_object('tree', b''.join(value for _, value in sorted(entries)))
    return digest(tree)


def source_is_pristine():
    try:
        lock = source_lock()
        records = file_records()
        return (not (SOURCE / '.git').exists() and
                all(f['matches_pinned_blob'] and f['matches_git_mode'] for f in records) and
                all(f['sha256'] == expected['sha256'] for f, expected in zip(records, lock['files'])) and
                actual_tree_oid() == lock['tree_oid'])
    except (OSError, KeyError, AssertionError, ValueError):
        return False
