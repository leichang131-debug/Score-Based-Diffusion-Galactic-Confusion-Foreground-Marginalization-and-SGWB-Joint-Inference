#!/usr/bin/env python3
"""Summarize validated prerequisites and unchanged working copies; never claim full reproduction."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/triangle-gb/prerequisites'
WORK=ROOT/'runs/triangle-gb/workspace/Triangle-GB'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    def read(path):return json.loads((ROOT/path).read_text())
    env=read('results/triangle-gb/environment/validation.json')
    fisher=read('results/triangle-gb/fisher/validation.json')
    sangria=read('results/triangle-gb/sangria/validation.json')
    vgb=read('results/triangle-gb/data/validation.json')
    assert env['all_environment_checks_pass'] and env['all_five_example_input_files_available']
    assert fisher['all_checks_pass'] and sangria['all_preparation_checks_pass'] and vgb['input_preparation_checks_pass']
    notebooks=[]
    for source in sorted((ROOT/'external/triangle-gb/Examples').glob('*.ipynb')):
        target=WORK/'Examples'/source.name;a=json.loads(source.read_text());b=json.loads(target.read_text())
        assert len(a['cells'])==len(b['cells'])
        assert all(x['source']==y['source'] and x['cell_type']==y['cell_type'] and x.get('attachments')==y.get('attachments') for x,y in zip(a['cells'],b['cells']))
        assert all(not c.get('outputs') and c.get('execution_count') is None for c in b['cells'] if c['cell_type']=='code')
        notebooks.append({'filename':source.name,'same_source_and_markdown_and_attachments':True,'historical_outputs_cleared':True,'working_path':str(target.relative_to(ROOT)),'source_file_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    assert len(notebooks)==5 and (WORK/'Triangle_GB').resolve()==(ROOT/'external/triangle-gb/Triangle_GB').resolve()
    for name in ['LDC2_sangria_training_v2.h5','0_1_VGB_TDIXYZ.h5','0_1_VGB_parameters.h5']:
        p=ROOT/'data/raw/triangle-gb'/name;assert p.is_file();subprocess.run(['git','-C',str(ROOT),'check-ignore','--quiet',str(p)],check=True)
    cache=ROOT/sangria['cache']['local_ignored_path'];assert cache.is_file() and cache.stat().st_size==sangria['cache']['bytes']
    summary={'all_five_input_and_import_prerequisites_available':True,'full_five_notebook_reproduction_completed':False,
        'environment_checks_passed':len(env['checks']),'fisher_checks_passed':len(fisher['checks']),
        'Sangria_preparation_checks_passed':len(sangria['checks']),'working_notebooks':notebooks,
        'scope':'Full original inputs/cache and interfaces prepared; original source/Markdown preserved. No search/sampler completion claim.',
        'scientific_issues_to_retain':['Examples 1/2 strict original orbit coverage fails; inherited boundary extrapolation remains explicitly documented.', 'Sangria delayed starting boundary uses approximately 25 seconds of extrapolation; full scientific waveform accuracy is not established by finiteness checks.', 'Original network Fisher raw-unit conditioning warning is retained; posterior convergence is a separate validation.'],
        'next_step':'Run each same-name working notebook freshly, save outputs/logs/timing and audit scientific results; plan sampling multiprocessing memory before long runs.'}
    (OUT/'readiness.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('All five example input/import prerequisites available; 5/5 working copies preserve source/Markdown. Full notebook reproduction remains pending.')

if __name__=='__main__':main()
