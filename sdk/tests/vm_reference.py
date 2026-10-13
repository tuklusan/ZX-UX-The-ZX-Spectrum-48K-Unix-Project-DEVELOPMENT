#!/usr/bin/env python3
"""Check the v1 C48 compiler and VM independently of historical binaries.

  vm_reference.py [--native|--bytecode] [--only NAMES] [--png DIR]
  vm_reference.py --reference-sdk DIR [other options]  # optional historical comparison

The default runner uses the local C48 source collection and known output
checks. An explicitly supplied historical reference VM may also compare
displays; it is not part of v1 code generation or program loading.
"""
import json
import os
import sys
import time
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SDKDIR = os.path.dirname(HERE)
sys.path.insert(0, SDKDIR)

import rvm                    # noqa: E402
from rcc import driver        # noqa: E402

# per-program scripted runs: args, keys, rvm frame budget
RUNS = json.load(open(os.path.join(HERE, 'runs.json')))
V1_SCREENS = json.load(open(os.path.join(HERE, 'v1-screens.json')))


class StopRun(Exception):
    pass


def sdk_run(sdk, src, args, keys, ticks, steps=3000000):
    sys.path.insert(0, os.path.join(sdk, 'compiler'))
    from pathlib import Path
    from c48.compiler import compile_file
    from c48.screen import Font4x8, ZXScreen
    from c48.romvm import RomMathVM
    from c48 import errors
    prog = compile_file(Path(src))
    screen = ZXScreen(Font4x8.load(Path(sdk) / 'compiler' / 'assets' / 'SANYALnet-Labs-4x8-font-FINAL.bin'))
    kq = list(keys)

    def inp():
        if not kq:
            raise StopRun()
        return kq.pop(0)
    vm = RomMathVM(prog, screen, argv=['prog'] + list(args),
                   approximate_rom_math=True, input_provider=inp, tick_provider=lambda: ticks,
                   heap_size=1024, max_steps=steps)
    try:
        st = vm.run()
        why = 'exit %s' % st
    except StopRun:
        why = 'input'
    except errors.RuntimeC48Error as e:
        why = 'error %s' % e
    except Exception as e:      # step limit etc.
        why = 'stop %s' % type(e).__name__
    return screen.bytes(), why


RCCFLAGS = []


def rcc_run(src, args, keys, ticks, frames):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'p.ssx')
        rc = driver.main([src, '-o', out] + RCCFLAGS)
        if rc:
            return None, 'compile failed', 0
        data = open(out, 'rb').read()
        vm = rvm.VM(data, args, keys, None, ticks)
        why = vm.run(frames)
        return vm.screen(), '%s %s' % (why, vm.status if why == 'exit' else ''), len(data)


def diff(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def main(argv):
    sdk = None
    RCCFLAGS.clear()
    only = None
    pngdir = None
    i = 0
    while i < len(argv):
        if argv[i] == '--reference-sdk':
            sdk = argv[i + 1]
            i += 2
        elif argv[i] == '--only':
            only = set(argv[i + 1].split(','))
            i += 2
        elif argv[i] == '--png':
            pngdir = argv[i + 1]
            i += 2
        elif argv[i] in ('--bytecode', '--native'):
            RCCFLAGS.append(argv[i])
            i += 1
        else:
            raise SystemExit('unknown option: ' + argv[i])
    if set(RUNS) != set(V1_SCREENS):
        raise SystemExit('Missing or unexpected v1 screen baselines')
    src = os.path.normpath(os.path.join(SDKDIR, '..', 'programs', 'c48'))
    total = ok = 0
    for name, run in RUNS.items():
        if only and name not in only and name.split(':')[0] not in only:
            continue
        path = os.path.join(src, run['dir'], run.get('src', name) + '.c')
        keys = run.get('keys', '').encode().decode('unicode_escape').encode('latin-1')
        args = run.get('args', [])
        ticks = run.get('ticks', 1234)
        t0 = time.time()
        frames = run.get('frames', 6000) * (8 if '--bytecode' in RCCFLAGS else 1)
        b, why_b, size = rcc_run(path, args, keys, ticks, frames)
        t1 = time.time()
        total += 1
        if b is None:
            print('%-14s FAIL %s' % (name, why_b))
            continue
        expected = V1_SCREENS.get(name)
        checks = [('screen', len(b) == 6912),
                  ('baseline', expected is not None)]
        if expected is not None:
            import hashlib
            checks.append(('screen-sha', hashlib.sha256(b).hexdigest() == expected['sha256']))
            checks.append(('state', why_b.strip() == expected['state']))
        if 'sha' in run:
            import hashlib
            checks.append(('sha', hashlib.sha256(b).hexdigest() == run['sha']))
        if 'expect_text' in run:
            checks.append(('text', run['expect_text'] in rvm.screen_text(b)))
        if 'expect_status' in run:
            checks.append(('status', why_b.strip() == 'exit %d' % run['expect_status']))
        sdkinfo = ''
        if sdk is not None and not run.get('nosdk'):
            a, why_a = sdk_run(sdk, path, args, keys, ticks, run.get('steps', 6000000))
            d = diff(a, b)
            checks.append(('sdk-screen', d <= run.get('tolerance', 0)))
            sdkinfo = 'sdk: %-12s %4d bytes differ' % (why_a[:12], d)
            if pngdir:
                os.makedirs(pngdir, exist_ok=True)
                rvm.write_png(a, os.path.join(pngdir, name.replace(':', '_') + '.sdk.png'))
        t2 = time.time()
        good = all(c for _, c in checks)
        ok += good
        print('%-14s %s rvm: %-9s ssx %5d  %s [%s] (%.1fs/%.1fs) %s'
              % (name, 'PASS' if good else 'FAIL', why_b.strip(), size, sdkinfo,
                 ','.join(k + ('' if c else '!') for k, c in checks), t1 - t0, t2 - t1, run.get('note', '')))
        if pngdir:
            os.makedirs(pngdir, exist_ok=True)
            rvm.write_png(b, os.path.join(pngdir, name.replace(':', '_') + '.png'))
    print('%d/%d v1 sessions pass' % (ok, total))
    return 0 if ok == total else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
