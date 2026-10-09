"""Verify every tracked upstream file and nested Git link without editing source.

Online by default: verify that the teacher's remote HEAD matches the pinned
wrapper. --offline verifies local files only and explicitly skips remote status.
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/reproduction/score-sde'
WRAPPER='8c399ccd8079e5fe7e264f8a72ec97a598b33be1'
ORIGINAL='0acb9e0ea3b8cccd935068cd9c657318fbc6ce4c'
URL='https://github.com/iphysresearch/score-sde-reproduction.git'
parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()

def git(path,*argv):
    return subprocess.check_output(['git','-C',str(path),*argv])

files=[];links=[];repos=[]
def audit(relative,expected):
    base=ROOT/relative
    head=git(base,'rev-parse','HEAD').decode().strip()
    assert head==expected,(relative,head,expected)
    status=git(base,'status','--porcelain','--untracked-files=all').decode()
    assert not status,(relative,status)
    entries=git(base,'ls-tree','-rz',head).split(b'\0')
    count=0
    for entry in entries:
        if not entry:continue
        header,name=entry.split(b'\t',1)
        mode,kind,oid=header.decode().split()
        name=os.fsdecode(name);target=base/name
        if kind=='commit':
            nested=git(target,'rev-parse','HEAD').decode().strip()
            assert nested==oid
            links.append({'parent':relative,'path':name,'pinned_commit':oid,'local_commit':nested})
            audit(str(Path(relative)/name),oid)
        else:
            assert kind=='blob'
            raw=os.fsencode(os.readlink(target)) if mode=='120000' else target.read_bytes()
            actual=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
            assert actual==oid,(str(target),'content differs from Git blob')
            if mode=='100755':assert os.access(target,os.X_OK)
            files.append({'upstream_repository':relative,'upstream_path':name,
                'local_repository_path':str(target.relative_to(ROOT)), 'mode':mode,
                'git_blob_sha1':oid,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'status':'exact_match'})
            count+=1
    repos.append({'path':relative,'commit':head,'tracked_file_count':count,'worktree_clean':True})

# Parent repository must track the correct source URL and Git link.
assert git(ROOT,'config','-f','.gitmodules','--get','submodule.external/score-sde-reproduction.url').decode().strip()==URL
assert git(ROOT/'external/score-sde-reproduction','config','-f','.gitmodules','--get','submodule.score_sde.url').decode().strip()=='https://github.com/yang-song/score_sde.git'
# Parent repository must actually track the wrapper as a Git link.
parent=git(ROOT,'ls-tree','HEAD','external/score-sde-reproduction').decode().split()
assert parent[:3]==['160000','commit',WRAPPER]
audit('external/score-sde-reproduction',WRAPPER)
assert len(links)==1 and links[0]['pinned_commit']==ORIGINAL
remote={'status':'skipped_offline'}
if not args.offline:
    head=subprocess.check_output(['git','ls-remote',URL,'HEAD'],text=True).split()[0]
    remote={'status':'checked','head':head,'matches_pinned_wrapper':head==WRAPPER}
    assert head==WRAPPER,'Remote changed: audit the new commit before claiming current-source parity.'
report={'status':'passed','date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    'scope':'All tracked teacher-wrapper files and the entire pinned original submodule; content and executable-mode checks. Source presence does not imply all entry points were executed.',
    'remote':remote,'repositories':repos,'parent_gitlink_matches_wrapper':True,'nested_gitlinks':links,
    'matched_files':len(files),'missing_or_modified_files':0,
    'files':sorted(files,key=lambda x:x['local_repository_path'])}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
with (OUT/'source-file-map.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(files[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(report['files'])
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
