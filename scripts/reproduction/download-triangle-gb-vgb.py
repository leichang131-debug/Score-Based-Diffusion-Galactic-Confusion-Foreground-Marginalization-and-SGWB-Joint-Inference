#!/usr/bin/env python3
"""Download only the two public files linked in Examples 1/2, verify and record provenance."""
import datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/raw/triangle-gb'
OUT = ROOT / 'results/triangle-gb/data'
FILES = [
    ('15469724', '0_1_VGB_TDIXYZ.h5', 100707680, '01b91a77eef8ae14b12473fa11b9f5ce'),
    ('15532090', '0_1_VGB_parameters.h5', 7904, '53ac143f8537996bf73c2dcd2419f4f4'),
]


def hashes(path):
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with path.open('rb') as file:
        while chunk := file.read(1024 * 1024):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for record_id, name, expected_bytes, expected_md5 in FILES:
        started = time.perf_counter()
        api_url = f'https://zenodo.org/api/records/{record_id}'
        with urllib.request.urlopen(api_url, timeout=60) as response:
            metadata = json.load(response)
        item = next(f for f in metadata['files'] if f['key'] == name)
        assert item['size'] == expected_bytes, 'Official size changed; review required.'
        assert item['checksum'] == 'md5:' + expected_md5, 'Official checksum changed; review required.'
        target = DATA / name
        reused = target.exists()
        if not reused:
            partial = target.with_suffix(target.suffix + '.part')
            print('Downloading', name, flush=True)
            # A failed partial download stays local; the next attempt restarts it.
            with urllib.request.urlopen(item['links']['self'], timeout=60) as response, partial.open('wb') as file:
                received = 0
                while chunk := response.read(1024 * 1024):
                    file.write(chunk)
                    received += len(chunk)
                    if received % (20 * 1024 * 1024) == 0:
                        print(f'{name}: {received}/{expected_bytes} bytes', flush=True)
            assert partial.stat().st_size == expected_bytes
            md5, sha = hashes(partial)
            assert md5 == expected_md5
            partial.replace(target)
        md5, sha = hashes(target)
        assert target.stat().st_size == expected_bytes
        assert md5 == expected_md5, 'Existing local file does not match official MD5.'
        records.append({'record_url': f'https://zenodo.org/records/{record_id}',
                        'metadata_url': api_url, 'download_url': item['links']['self'],
                        'notebook_download_url': f'https://zenodo.org/records/{record_id}/files/{name}?download=1',
                        'path': target.relative_to(ROOT).as_posix(), 'filename': name,
                        'official_bytes': expected_bytes, 'local_bytes': target.stat().st_size,
                        'official_md5': expected_md5, 'local_md5': md5, 'local_sha256': sha,
                        'reused_existing_verified_file': reused,
                        'seconds': time.perf_counter() - started,
                        'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print('VERIFIED', name, 'MD5', md5, 'SHA256', sha, flush=True)
    (OUT / 'download-provenance.json').write_text(json.dumps({'scope': 'Public input-file download and checksum verification only.', 'files': records}, indent=2) + '\n')


if __name__ == '__main__':
    main()
