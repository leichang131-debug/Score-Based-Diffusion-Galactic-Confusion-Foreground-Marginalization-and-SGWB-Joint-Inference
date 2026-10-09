"""Optional ranged download from the official server, with TFDS SHA-256 verification."""
from pathlib import Path
import urllib.request
import hashlib
import concurrent.futures
import time
ROOT = Path(__file__).resolve().parents[2]
URL = 'https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz'
SIZE = 170052171
SHA256 = 'c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd'
DIRECTORY = ROOT / 'data/raw/tensorflow_datasets/downloads/manual'
DIRECTORY.mkdir(parents=True, exist_ok=True)
TARGET = DIRECTORY / 'cifar-10-binary.tar.gz'
PARTS = DIRECTORY / 'cifar10-range-parts'
PARTS.mkdir(exist_ok=True)
CHUNK = 4 * 1024 * 1024

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def fetch(i):
    start = i*CHUNK
    end = min(SIZE-1,start+CHUNK-1)
    part = PARTS / f'{i:04d}.part'
    if part.exists() and part.stat().st_size==end-start+1: return part
    for attempt in range(3):
        try:
            request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
            with urllib.request.urlopen(request,timeout=90) as response:
                assert response.status==206
                assert response.headers.get('Content-Range')==f'bytes {start}-{end}/{SIZE}'
                content=response.read(end-start+2)
            assert len(content)==end-start+1
            part.write_bytes(content)
            return part
        except Exception:
            if attempt==2: raise
            time.sleep(attempt+1)

if TARGET.exists() and TARGET.stat().st_size==SIZE and digest(TARGET)==SHA256:
    print('Verified existing official archive',flush=True)
else:
    count=(SIZE+CHUNK-1)//CHUNK
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(fetch,i) for i in range(count)]
        for done,future in enumerate(concurrent.futures.as_completed(futures),1):
            future.result();print(f'Completed archive ranges: {done}/{count}',flush=True)
    temporary=TARGET.with_suffix('.assembling')
    with temporary.open('wb') as f:
        for i in range(count): f.write((PARTS/f'{i:04d}.part').read_bytes())
    assert temporary.stat().st_size==SIZE and digest(temporary)==SHA256
    temporary.replace(TARGET)
    for p in PARTS.glob('*.part'): p.unlink()
    PARTS.rmdir()
print('Official archive SHA-256 verified:',SHA256,flush=True)
