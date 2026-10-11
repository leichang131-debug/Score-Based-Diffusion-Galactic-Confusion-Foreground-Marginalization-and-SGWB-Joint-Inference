#!/usr/bin/env python3
"""Resumable, ranged download of official LDC Sangria; no scientific execution."""
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/triangle-gb/sangria'
DATA = ROOT / 'data/raw/triangle-gb'
NAME = 'LDC2_sangria_training_v2.h5'
SIZE = 3082321484
MD5 = 'b8369cb5c06bcf984ef8057198683250'
API = 'https://zenodo.org/api/records/7132178'


def digest(path):
    a,b=hashlib.md5(),hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(4*1024*1024): a.update(chunk);b.update(chunk)
    return a.hexdigest(),b.hexdigest()


def main():
    started=time.perf_counter()
    OUT.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(API,timeout=60) as f:record=json.load(f)
    item=next(x for x in record['files'] if x['key']==NAME)
    assert item['size']==SIZE and item['checksum']=='md5:'+MD5
    url=item['links']['self'];target=DATA/NAME;reused=target.exists()
    if not reused:
        # Zenodo supports HTTP byte ranges. Six disjoint local segments support resume.
        count=6
        width=(SIZE+count-1)//count
        def segment(i):
            start=i*width;end=min(SIZE,(i+1)*width)-1;expected=end-start+1
            part=DATA/(NAME+f'.segment-{i}')
            for attempt in range(6):
                done=part.stat().st_size if part.exists() else 0
                assert done<=expected
                if done==expected:return part
                try:
                    req=urllib.request.Request(url,headers={'Range':f'bytes={start+done}-{end}'})
                    with urllib.request.urlopen(req,timeout=90) as response:
                        assert response.status==206
                        assert response.headers['Content-Range']==f'bytes {start+done}-{end}/{SIZE}'
                        with part.open('ab') as f:
                            milestone=done//(64*1024*1024)
                            while chunk:=response.read(1024*1024):
                                f.write(chunk);done+=len(chunk)
                                assert done<=expected
                                current=done//(64*1024*1024)
                                if current>milestone:
                                    print(f'Segment {i}: {done}/{expected} bytes',flush=True);milestone=current
                    assert done==expected
                    return part
                except Exception as exc:
                    print(f'Segment {i} retry {attempt+1}: {type(exc).__name__}: {exc}',flush=True)
                    if attempt==5:raise
                    time.sleep(min(30,2**attempt))
        print('Downloading official Sangria using six resumable byte ranges.',flush=True)
        with ThreadPoolExecutor(max_workers=count) as pool:parts=list(pool.map(segment,range(count)))
        assembled=DATA/(NAME+'.part')
        with assembled.open('wb') as out:
            for part in parts:
                with part.open('rb') as f:
                    while chunk:=f.read(4*1024*1024):out.write(chunk)
        assert assembled.stat().st_size==SIZE
        md5,sha=digest(assembled);assert md5==MD5
        assembled.replace(target)
        for part in parts:part.unlink()
    md5,sha=digest(target);assert target.stat().st_size==SIZE and md5==MD5
    report={'record_url':'https://zenodo.org/records/7132178','metadata_url':API,
            'download_url':url,'filename':NAME,'local_path':target.relative_to(ROOT).as_posix(),
            'official_bytes':SIZE,'local_bytes':target.stat().st_size,'official_md5':MD5,
            'local_md5':md5,'local_sha256':sha,'reused_verified_file':reused,
            'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'seconds':time.perf_counter()-started,'bulk_data_committed':False}
    (OUT/'download-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print('VERIFIED',NAME,'SHA256',sha,flush=True)


if __name__=='__main__':main()
