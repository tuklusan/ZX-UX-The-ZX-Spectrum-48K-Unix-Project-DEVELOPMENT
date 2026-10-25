"""Run real ZX-UX kernel process-isolation checks for the SSX exit wrapper.

These native fixtures test the packer and shell return path; the separate
BASIC compiler and original-game probes still require the HiSoft frontend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from native_error_exit import error_exit_bytes
import rld
import rvm


def linked_fixtures(rbc, work):
    # Change the actual system variables and user-defined graphics, then exit.
    mutation = bytes.fromhex('2a7b5c364921444422365c3e88326a5c3e9932395c')
    # A long-running process allows a live UDG sample in the real kernel.
    pause = bytes.fromhex('01ffff0b78b120fbc9')
    programs = {
        'stop': mutation + b'\xc9',
        'error': mutation + error_exit_bytes(11),
        'val-error': mutation + error_exit_bytes(10),
        'after-error': pause,
    }
    result = {}
    for name, code in programs.items():
        bases = (0x5000, 0x6000, 0x7000)
        builds = [rbc.HiSoftBuild(code, base, base, 0) for base in bases]
        data, meta = rbc.build_ssx(builds, bytes(768), rld, 384,
                                   use_rom_font=True)
        parsed = rld.parse_ssx(data)
        size = len(parsed['image']) + parsed['bss'] + parsed['stack']
        if max(len(data),size) > 12000:
            raise RuntimeError(name + ': exceeds default memory admission')
        target = work / (name + '.ssx')
        target.write_bytes(data)
        result[name] = {'path':target, 'file':len(data), 'image':len(parsed['image']),
                        'bss':parsed['bss'], 'stack':parsed['stack'], 'total':size,
                        'sha256':hashlib.sha256(data).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler',type=Path,
                        default=ROOT/'build/tmp/rbc-round2/current/rbc')
    parser.add_argument('--system',type=Path,default=ROOT/'build/out/ZX-UX.tzx')
    parser.add_argument('--work',type=Path,default=ROOT/'build/tmp/rbc-gate7-wrapper')
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    if not (compiler/'rbc.py').is_file():
        raise RuntimeError('missing prepared compiler checkpoint')
    if not args.system.with_name('kernel.json').is_file():
        raise RuntimeError('missing native kernel metadata')
    if args.system.read_bytes() != (ROOT/'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native kernel differs from frozen release')
    args.work.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(compiler))
    import rbc
    programs = linked_fixtures(rbc,args.work)
    fresh = rvm.run_kernel(programs['after-error']['path'],frames=15,
                           system=args.system,cache=True)
    if fresh.why != 'frames':
        raise RuntimeError('fresh graphics baseline was not running')
    initial = fresh.session.m.mem[fresh.session.word(0x5c7b)]
    options = rvm.Options()
    options.prog = str(programs['stop']['path'])
    options.system = str(args.system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    shell_chars = session.word(0x5c36)
    shell_udg = session.word(0x5c7b)
    rows = []
    for index,(name,expected) in enumerate((('stop',0),('error',11),
                                            ('after-error',0),('val-error',10),
                                            ('after-error',0))):
        binary = programs[name]['path']
        job = runner.fg if index == 0 else session.launch(
            binary.read_bytes(),rvm.zxux.program_name(str(binary)))
        observed = None
        for _ in range(4200):
            runner.frame()
            if name == 'after-error' and job.started is not None and job.ended is None:
                if session.m.frame-job.started >= 15 and observed is None:
                    ptr = session.word(0x5c7b)
                    observed = session.m.mem[ptr]
            if job.ended is not None:
                break
        row = {'name':name,'status':job.status,'started':job.started,
               'ended':job.ended,'active_glyph':observed,
               'chars':session.word(0x5c36),'udg':session.word(0x5c7b),
               'screen_released':not session.owns_screen(job.pid)}
        rows.append(row)
        if job.started is None or job.ended is None or job.status != expected:
            raise RuntimeError(name + ': real kernel process exit failed: '+str(row))
        if row['chars'] != shell_chars or row['udg'] != shell_udg or not row['screen_released']:
            raise RuntimeError(name + ': shell graphics state leaked: '+str(row))
        if name == 'after-error' and observed != initial:
            raise RuntimeError(name + ': prior process UDG data leaked: '+str(row))
    print('GATE7_NATIVE_WRAPPER',json.dumps({
        'baseline_chars':shell_chars,'baseline_udg':shell_udg,
        'fresh_glyph':initial,'runs':rows,
        'files':{k:{j:v for j,v in obj.items() if j!='path'}
                 for k,obj in programs.items()}},sort_keys=True))


if __name__ == '__main__':
    main()
