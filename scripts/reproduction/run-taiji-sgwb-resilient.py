#!/usr/bin/env python3
"""Detached-session, bounded recovery of the unchanged full-data sampler."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'runs/taiji-sgwb/template-formal'
OUT = ROOT / 'results/taiji-sgwb/template-formal'


def write(value):
    value['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    target = WORK / 'resilience.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(target)


def active_sampler_processes():
    rows = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
    return [row for row in rows.splitlines() if 'python' in row.lower() and
            ('run-taiji-sgwb-template-formal.py' in row or
             'run-taiji-sgwb-template-formal-worker.py' in row)]


def main():
    attempts = []
    for attempt in range(1, 5):
        if (WORK / 'stop-requested').exists():
            write({'status': 'STOPPED_BY_USER', 'attempts': attempts})
            return
        progress = json.loads((WORK / 'progress.json').read_text())
        if progress['status'] == 'SAMPLING_COMPLETE':
            write({'status': 'SAMPLING_ALREADY_COMPLETE', 'attempts': attempts,
                   'note': 'Never restart completed sampling; inspect analysis/sync separately.'})
            return
        active = active_sampler_processes()
        if active:
            write({'status': 'REFUSED_DUPLICATE_START', 'processes': active, 'attempts': attempts})
            raise RuntimeError('Existing sampler family; no duplicate launch or automatic killing')
        lock = WORK / 'supervisor.lock'
        if lock.exists():
            # Check process existence as well as the command inventory. PID reuse
            # causes a conservative refusal rather than removing an active lock.
            pid = int(lock.read_text())
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                archived = WORK / f'stale-supervisor-{time.time_ns()}.lock'
                lock.replace(archived)
            else:
                raise RuntimeError(f'Lock PID {pid} is alive; manual inspection needed')
        command = ['bash', 'scripts/reproduction/run-taiji-sgwb-python.sh',
                   'scripts/reproduction/run-taiji-sgwb-template-formal.py']
        pointer=json.loads((WORK/'latest-checkpoint.json').read_text())
        checkpoint=json.loads((WORK/pointer['directory']/'state.json').read_text())
        cfg=json.loads((ROOT/'configs/reproduction/taiji-sgwb/template-formal.json').read_text())
        restored_done=checkpoint['burn_done']+checkpoint['production_done']*cfg['thin_by']
        entry = {'attempt': attempt, 'start_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'progress_before': restored_done, 'progress_file_before': progress['transitions_done'], 'command': command}
        attempts.append(entry)
        write({'status': 'RUNNING', 'pid': os.getpid(), 'attempts': attempts,
               'maximum_automatic_retries': 3})
        with (WORK / 'supervisor-execution.log').open('a') as log:
            proc = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT)
            entry['supervisor_pid'] = proc.pid
            write({'status': 'RUNNING', 'pid': os.getpid(), 'attempts': attempts,
                   'maximum_automatic_retries': 3})
            entry['returncode'] = proc.wait()
        entry['end_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        progress = json.loads((WORK / 'progress.json').read_text())
        entry['progress_after'] = progress['transitions_done']
        if progress['status'] in ['SAMPLING_COMPLETE', 'STOPPED_AT_CHECKPOINT'] or (WORK / 'stop-requested').exists():
            final = {'status': progress['status'], 'attempts': attempts,
                     'note': 'See formal status.json for posterior analysis and synchronization outcome.'}
            write(final)
            (OUT / 'resilience-outcome.json').write_text(json.dumps(final, indent=2) + '\n')
            return
        write({'status': 'WAITING_BEFORE_RETRY', 'attempts': attempts,
               'note': 'Resume only verified immutable checkpoint; no source/config change.'})
        if attempt < 4:
            time.sleep(30)
    write({'status': 'RETRY_LIMIT_REACHED', 'attempts': attempts})
    raise RuntimeError('Three retries exhausted; inspect failure evidence')


if __name__ == '__main__':
    main()
