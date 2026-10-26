"""Test consecutive RBC programs within one native ZX-UX boot session."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

PROGRAMS = {
    'stop-and-font': '10 POKE USR "a",73\n20 POKE 23606,0\n30 POKE 23607,60\n40 STOP\n',
    'after-stop': '10 LET Q=PEEK USR "a"\n20 POKE USR "b",Q\n30 PAUSE 150\n40 STOP\n',
    'normal-end': '10 LET A=2\n20 PRINT "COMPLETE"\n',
    'handled-error': '10 POKE USR "a",88\n20 LET P=24576\n30 POKE P,77\n',
    'after-error': '10 LET Q=PEEK USR "a"\n20 POKE USR "b",Q\n30 PAUSE 150\n40 STOP\n',
}


def compile_all(work, compiler, frontend, tape, rom):
    compiled = {}
    for name, listing in PROGRAMS.items():
        path = work / (name + '.bas')
        target = work / (name + '.ssx')
        path.write_text(listing, encoding='ascii')
        args = [sys.executable, str(compiler), str(path),
                '--frontend', str(frontend),
                '--sdk', str(ROOT / 'src/zx-ux-sdk'),
                '--rom', str(rom),
                '--tape', str(tape),
                '--max', '12000', '-o', str(target)]
        run = subprocess.run(args, text=True, capture_output=True, timeout=120)
        if run.returncode or not target.is_file():
            raise RuntimeError(name + ': native link failed: ' + run.stderr)
        data = target.read_bytes()
        image = rld.parse_ssx(data)
        total = len(image['image']) + image['bss'] + image['stack']
        if max(total, len(data)) > 12000:
            raise RuntimeError(name + ': default memory admission failed')
        compiled[name] = {'path': target, 'file': len(data), 'image': len(image['image']),
                          'bss': image['bss'], 'stack': image['stack'], 'total': total,
                          'sha256': hashlib.sha256(data).hexdigest()}
    return compiled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7')
    ap.add_argument('--compiler', type=Path, required=True,
                    help='recovered current RBC rbc.py')
    ap.add_argument('--frontend', type=Path, required=True,
                    help='verified canonical HiSoft frontend directory')
    ap.add_argument('--tape', type=Path, required=True,
                    help='original HiSoft 48K compiler TZX')
    ap.add_argument('--rom', type=Path, default=ROOT / 'src/zx-ux-sdk/rom/48.rom')
    ap.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    args = ap.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    system = args.system.resolve()
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('Native kernel symbols missing')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('Native kernel tape differs from frozen version')
    if not args.compiler.resolve().is_file() or not args.frontend.resolve().is_dir():
        raise RuntimeError('prepared RBC and canonical frontend required')
    compiled = compile_all(work, args.compiler.resolve(), args.frontend.resolve(),
                           args.tape.resolve(), args.rom.resolve())
    # Use a separately booted copy of the same SSX to establish its actual
    # initial graphic bytes. ZX Spectrum UDG data need not start at zero.
    reference = rvm.run_kernel(compiled['after-stop']['path'],
                               frames=45, system=system, cache=True)
    if reference.why != 'frames':
        raise RuntimeError('The independent graphic reference did not run')
    base = reference.session.word(0x5c7b)
    initial_glyph = reference.session.m.mem[base + 8]
    initial_a = reference.session.m.mem[base]
    print('GATE7_REFERENCE', json.dumps({'udg_pointer': base, 'glyph_a':initial_a, 'glyph_b':initial_glyph}), flush=True)
    options = rvm.Options()
    options.prog = str(compiled['stop-and-font']['path'])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    baseline_chars = session.word(0x5c36)
    results = {'shell_chars_baseline': baseline_chars,
               'initial_graphic_byte': initial_glyph, 'initial_glyph_a': initial_a,
               'reference_udg_pointer':base, 'processes': {}}

    def execute(name, first=False, probe=False):
        if first:
            job = runner.fg
        else:
            file = compiled[name]['path']
            job = session.launch(file.read_bytes(), rvm.zxux.program_name(str(file)))
        observation = None
        at_start = None
        at_fifteen = None
        for _ in range(4200):
            runner.frame()
            if job.started is not None and job.ended is None:
                elapsed = session.m.frame - job.started
                if at_start is None:
                    udg = session.word(0x5c7b)
                    at_start = {'udg_pointer':udg, 'glyph_a':session.m.mem[udg],
                                'glyph_b':session.m.mem[udg+8], 'elapsed':elapsed}
                if elapsed >= 15 and at_fifteen is None:
                    udg = session.word(0x5c7b)
                    at_fifteen = {'udg_pointer':udg, 'glyph_a':session.m.mem[udg],
                                  'glyph_b':session.m.mem[udg+8], 'elapsed':elapsed}
                if (probe and elapsed >= 15 and observation is None
                        and at_start is not None
                        and session.word(0x5c7b) == at_start['udg_pointer']):
                    # The SSX wrapper restores UDG before the kernel marks
                    # the job ended. Only sample its private bank while selected.
                    observation = session.m.mem[at_start['udg_pointer'] + 8]
            if job.ended is not None:
                break
        if job.started is None or job.ended is None:
            raise RuntimeError(name + ': process did not execute and return to shell')
        row = dict(compiled[name])
        row['path'] = str(row['path'].relative_to(ROOT))
        row.update(pid=job.pid, status=job.status, frames=job.ended - job.started,
                   shell_chars=session.word(0x5c36), screen_released=not session.owns_screen(job.pid))
        row['at_start'] = at_start
        row['at_fifteen'] = at_fifteen
        if probe:
            row['other_process_udg_byte'] = observation
        results['processes'][name] = row
        print('GATE7_SESSION', name, json.dumps(row), flush=True)
        if not row['screen_released']:
            raise RuntimeError(name + ': process did not release screen')
        if row['shell_chars'] != baseline_chars:
            raise RuntimeError(name + ': screen character pointer was not restored')
        if probe and observation != initial_glyph:
            raise RuntimeError(name + ': other process graphics data leaked')
        return row

    try:
        stop = execute('stop-and-font', first=True)
        again = execute('after-stop', probe=True)
        natural = execute('normal-end')
        error = execute('handled-error')
        later = execute('after-error', probe=True)
        if stop['status'] not in (0, 9) or again['status'] not in (0, 9):
            raise RuntimeError('STOP returned an unexpected native status')
        if natural['status'] not in (0, 9):
            raise RuntimeError('Normal program completion returned an unexpected status')
        if error['status'] != 11:
            raise RuntimeError('Protected memory error did not exit with native status 11')
        if later['status'] not in (0, 9):
            raise RuntimeError('Second process did not complete')
    finally:
        (work / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
