#!/usr/bin/env python3
"""Build the standalone plan with XeLaTeX; keep intermediates outside Git."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'route-b-research-and-server-implementation-plan.pdf'

def main():
    engine = shutil.which('xelatex')
    if engine is None:
        raise SystemExit('XeLaTeX is required, with ctex, xeCJK, TikZ, tcolorbox and CJK fonts.')
    with tempfile.TemporaryDirectory(prefix='route-b-plan-') as temporary:
        for _ in range(3):
            subprocess.run([engine, '-interaction=nonstopmode', '-halt-on-error',
                            '-file-line-error', f'-output-directory={temporary}',
                            'main.tex'], cwd=ROOT, check=True)
        log = (Path(temporary) / 'main.log').read_text(errors='replace')
        forbidden = ('Overfull \\hbox', 'Overfull \\vbox', 'Missing character:',
                     'There were undefined references')
        if any(pattern in log for pattern in forbidden):
            raise SystemExit('Layout or reference diagnostics require review before publication.')
        shutil.copy2(Path(temporary) / 'main.pdf', OUTPUT)
    print(OUTPUT)
    print('Re-render and visually review the PDF after rebuilding; update manifest hashes.')

if __name__ == '__main__':
    main()
