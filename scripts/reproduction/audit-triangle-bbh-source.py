#!/usr/bin/env python3
"""Check the entire unmodified Triangle-BBH git tree, including bundled WF4Py."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'external/triangle-bbh';OUT=ROOT/'results/triangle-gb/fisher'
PIN='f99b0a34ea8d085aff67220bdc165a746ba5ceda'
def git(*a):return subprocess.check_output(['git','-C',str(SRC),*a])
assert git('rev-parse','HEAD').decode().strip()==PIN
assert not git('status','--porcelain').strip()
files=git('ls-tree','-r','--name-only',PIN).decode().splitlines();entries=[]
for name in files:
 b=(SRC/name).read_bytes();assert b==git('show',PIN+':'+name),name
 entries.append({'path':'external/triangle-bbh/'+name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
assert 'Triangle_BBH/Fisher.py' in files and 'WF4Py/setup.py' in files
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'source-audit.json').write_text(json.dumps({'pinned_commit':PIN,'source_url':'https://github.com/TriangleDataCenter/Triangle-BBH','all_tracked_files_match_git_blobs':True,'source_clean':True,'files':entries},indent=2)+'\n')
print('Triangle-BBH source audit:',len(entries),'files unchanged.')
