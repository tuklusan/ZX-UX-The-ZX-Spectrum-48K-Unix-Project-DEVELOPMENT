#!/usr/bin/env python3
"""Run approved-rcc C48 ENV1/ARG1 native integration; fail closed.

Designed to run on a clean current ZX-UX checkout with reviewed crt0 BSS patch
applied. Requires fresh build/test.z80 (boot from checked current tape),
checked native SDK, and installed SkoolKit/48K ROM. Records actual test
executions, never source-only claims. No private checker (local-only gate).

  python3 -B tests/c48/native_env1_v1.py --report /private/native-env1-v1.json
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/c48/native_env1_storage_lifetime.c'
CRT = ROOT / 'release/src/zx-ux-sdk/lib/crt0.asm'
SDK_SOURCE = ROOT / 'release/src/zx-ux-sdk'
SDK_STAGE = ROOT / 'release/build/sdk'
TMP_BUILD = ROOT / 'release/build/build'
BOOT_TZX = ROOT / 'release/dist/zx-ux/ZX-UX.tzx'
SSX_NAME = 'env48'
ROM_HASH = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'
MAX_NATIVE_RAM = 14000
TAP2SNA_SHA256 = 'c754087b68897780211e60d062da4831f04e83a72dc15d88a6dab436e2150e8d'
ARG = '/dev/cassette/' + SSX_NAME


class GateFailure(RuntimeError):
    pass


def ensure(ok, why):
    if not ok:
        raise GateFailure(why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(cmd):
    p = subprocess.run([str(x) for x in cmd], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, check=False)
    ensure(p.returncode == 0, 'command failed (exit %d): %s\n%s' %
           (p.returncode, ' '.join(map(str, cmd)), p.stdout[-3000:]))
    return p.stdout


def assess_sources():
    paths = [FIXTURE, CRT, SDK_SOURCE/'bin/rcc', SDK_SOURCE/'lib/build.py',
             SDK_SOURCE/'rld.py', SDK_SOURCE/'rtap.py',
             SDK_SOURCE/'rcc/driver.py', BOOT_TZX,
             ROOT/'tests/c48/native_env1_v1.py']
    ensure(all(p.is_file() and not p.is_symlink() for p in paths),
           'SDK, fixture or v1 boot inputs missing; no native proof')
    candidate = CRT.read_text()
    ensure(candidate.count('__c48_env1: ds 1') == 1 and
           'ld (@env1),a' in candidate and
           '        section bss\n        global __c48_env1\n@env1:\n__c48_env1: ds 1' in candidate,
           'current process-owned ENV1 bootstrap or exact diagnostic alias absent')
    before = subprocess.check_output(['git', 'show', 'HEAD:release/src/zx-ux-sdk/lib/crt0.asm'], cwd=ROOT)
    ensure(before == CRT.read_bytes(),
           'unexpected source base; inspect before testing')
    ensure(b'_c48_env1' in FIXTURE.read_bytes(), 'expected C48 fixture missing')
    return {'source_commit': subprocess.check_output(
                ['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            'source_tree': subprocess.check_output(
                ['git','rev-parse','HEAD^{tree}'], cwd=ROOT, text=True).strip(),
            'files': {str(p.relative_to(ROOT)): sha(p) for p in paths}}


def archive_env1_symbol(src, output):
    """Check the real rcc native linker selected the separate ENV1 BSS byte."""
    sys.path.insert(0, str(SDK_STAGE))
    import rld
    from rcc import driver
    # This recompiles independently of the CLI and inspects actual link symbols.
    source, program, gen = driver.compile_to_asm(str(src), {'lib': False, 'heap': 1024, 'stack': None, 'udgs': None})
    obj = rld.Obj(__import__('ras').assemble_text(source, src.name + '.s'), src.name)
    libpath = SDK_STAGE/'lib/libc48.ssa'
    lib = rld.read_archive(libpath.read_bytes(), str(libpath))
    native, bss, ent, gaddr, members = rld.link([obj], [lib], 'start',
                                                 driver.stack_estimate(gen), 0)
    actual = output.read_bytes()
    ensure(actual == native, 'CLI build and independent SDK link differ')
    h = rld.parse_ssx(actual)
    ensure('start' in gaddr and '__c48_env1' in gaddr and '@env1' in gaddr,
           'ENV1 bootstrap or diagnostic symbol unresolved in native image')
    ensure(gaddr['@env1'] == gaddr['__c48_env1'],
           'diagnostic ENV1 symbol does not alias the bootstrap byte')
    offset, reloc = gaddr['__c48_env1']
    ensure(reloc and len(h['image']) <= offset < len(h['image']) + h['bss'],
           'ENV1 not in separately zero-initialized BSS')
    ensure(h['flags'] == 0 and h['bss'] >= 1 and h['entry'] == gaddr['start'][0],
           'invalid native SSX1 format / bootstrap')
    need = __import__('rtap').need(actual)
    ensure(need <= MAX_NATIVE_RAM, 'native code exceeds checked 48K allowance')
    ensure(all(m.name for m in members), 'linker selected an object entry without a name')
    return {'env1_bss_offset': offset, 'code': len(h['image']),
            'bss': h['bss'], 'stack': h['stack'], 'heap': h['heap'],
            'ssx_bytes': len(actual), 'native_required_bytes': need,
            'selected_archive_members': [m.name for m in members],
            'ssx_sha256': sha(output), 'archive_sha256': sha(libpath)}


def inject_cassette(session, blocks, argument):
    import zxrun
    session.zx.type(ARG + ' ' + argument + '\n')
    session.zx.tr.edges = zxrun.tape_pulses(blocks,
                                             session.zx.sim.registers[25] + 350000)


def df_free(session):
    import suite
    return suite.df_free(session)


def validate_output(screen, expected):
    ensure('C48-ENV1-FAIL' not in screen, 'runtime printed ENV1 failure')
    ensure(expected in screen, 'missing expected C48 native text '+expected)


def save_capture(session, name):
    """Save only pixels actually reached during current native execution."""
    import rvm
    d = TMP_BUILD / 'c48-env1/proof'
    ensure(not d.is_symlink(), 'capture directory cannot be a symbolic link')
    d.mkdir(parents=True, exist_ok=True)
    scr = d / (name + '.scr')
    png = d / (name + '.png')
    ensure(not scr.is_symlink() and not png.is_symlink(),
           'capture paths cannot be symbolic links')
    pixels = bytes(session.zx.mem[0x4000:0x5b00])
    ensure(len(pixels) == 6912, 'bad Spectrum screen length')
    scr.write_bytes(pixels)
    rvm.write_png(pixels, str(png), session.zx.tr.border)
    ensure(png.stat().st_size > 0, 'PNG capture missing')
    return {'scr_path': str(scr.relative_to(ROOT)),
            'scr_sha256': sha(scr), 'png_path': str(png.relative_to(ROOT)),
            'png_sha256': sha(png)}


def wait_native_marker(session, expected, frames=6000):
    """Observe the C48 marker before process exit reclaims its screen."""
    for _ in range(frames):
        session.zx.run(1)
        screen = session.screen()
        ensure('C48-ENV1-FAIL' not in screen, 'native C48 execution failed')
        if expected in screen:
            return screen
    raise GateFailure('native marker not observed while process ran: ' + expected)


def consecutive_processes(snapshot, blocks):
    import suite
    s = suite.Session(str(snapshot))
    s.login()
    free = df_free(s)
    records = []
    for i in range(2):
        inject_cassette(s, blocks, 'e48')
        screen = wait_native_marker(s, 'C48-ENV1-OK')
        validate_output(screen, 'C48-ENV1-OK')
        capture = save_capture(s, 'sequential-' + str(i+1))
        s.wait_prompt(6000)
        after = df_free(s)
        ensure(after >= free - 8, 'process allocation not released')
        records.append({'run': i+1, 'outcome':'PASS', 'free_bytes':after,
                        'screen_sha256': hashlib.sha256(screen.encode()).hexdigest(),
                        'capture': capture})
    return records


def ssx_images(memory, bss_offset):
    """Kernel process slot IMAGE pointers point at independent native instances."""
    table = 0x5B00 + 68   # src/kvars.inc: p_img, word[NPROC=4]
    images = []
    for slot in range(4):
        ptr = memory[table+2*slot] | (memory[table+2*slot+1] << 8)
        if ptr and 0x6000 <= ptr and ptr + bss_offset < 0xFFB7:
            images.append((slot, ptr, memory[ptr + bss_offset]))
    return images


def simultaneous_processes(snapshot, blocks, env_offset):
    import suite
    s = suite.Session(str(snapshot))
    s.login()
    original = df_free(s)
    inject_cassette(s, blocks, 'hold &')
    s.until('C48-ENV1-HOLD-START', 6000)
    hold_snapshot = s.screen()
    validate_output(hold_snapshot, 'C48-ENV1-HOLD-START')
    inject_cassette(s, blocks, 'check')
    observed = None
    seen_check = False
    seen_hold = False
    for _ in range(6000):
        images = ssx_images(s.zx.mem, env_offset)
        marked = [(slot, ptr, val) for slot, ptr, val in images if val in (65, 90)]
        if any(x[2] == 65 for x in marked) and any(x[2] == 90 for x in marked):
            check = next(x for x in marked if x[2] == 65)
            hold = next(x for x in marked if x[2] == 90)
            if check[0] != hold[0] and check[1] != hold[1]:
                observed = {'hold': hold, 'check': check}
        s.zx.run(1)
        if _ % 8 == 0:
            screen = s.screen()
            ensure('C48-ENV1-FAIL' not in screen, 'native concurrent failure')
            seen_check |= 'C48-ENV1-CHECK-OK' in screen
            seen_hold |= 'C48-ENV1-HOLD-OK' in screen
        if observed and seen_check and seen_hold:
            break
    ensure(observed is not None, 'no simultaneous distinct process IMAGE+ENV1 storage proof')
    ensure(seen_check and seen_hold, 'not both native execution paths completed')
    s.wait_prompt(6000)
    ensure(df_free(s) >= original - 8, 'process memory not released after concurrency')
    return {'result':'PASS','simultaneous_image_slots':observed,
            'checked_program_pass':seen_check,'holding_program_pass':seen_hold,
            'capture': save_capture(s, 'concurrent')}


def fresh_snapshot(tap2sna):
    """Always create a new 48K ROM tape-load snapshot, not a cached .z80."""
    from skoolkit import ROM48
    ensure(sha(ROM48) == ROM_HASH, '48K ROM checksum differs')
    p = Path(tap2sna).resolve()
    ensure(p.is_file() and not p.is_symlink() and ROOT not in p.parents,
           'checked tap2sna must be a real tool outside Git')
    ensure(sha(p) == TAP2SNA_SHA256,
           'tape loader must match the owner-supplied checked toolbox')
    out = TMP_BUILD / 'c48-env1/native-current-tape.z80'
    ensure(not out.is_symlink() and not out.parent.is_symlink(),
           'cannot write snapshot through a link')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    command = run([sys.executable, '-B', p, BOOT_TZX, out])
    ensure(out.is_file() and out.stat().st_size >= 1000,
           'new tape-driven native snapshot not produced')
    return out, {'tap2sna_sha256':sha(p), 'snapshot_sha256':sha(out),
                 'rom_sha256':sha(ROM48),
                 'tape_boot_sha256':sha(BOOT_TZX),
                 'command_log_sha256':hashlib.sha256(command.encode()).hexdigest()}


def full_run(report, tap2sna):
    source_hashes = assess_sources()
    libpath = SDK_STAGE / 'lib/libc48.ssa'
    ensure(not libpath.is_symlink(), 'SDK runtime archive cannot be a symbolic link')
    buildlog = run([sys.executable, '-B', SDK_STAGE/'lib/build.py'])
    out = TMP_BUILD/'c48-env1/env48.ssx'
    ensure(not out.parent.is_symlink() and not out.is_symlink(),
           'native output path cannot be a symbolic link')
    out.parent.mkdir(parents=True, exist_ok=True)
    compilelog = run([sys.executable, '-B', SDK_STAGE/'bin/rcc', '--native',
                      '-o', out, FIXTURE])
    link = archive_env1_symbol(FIXTURE, out)
    sys.path.insert(0, str(SDK_STAGE))
    sys.path.insert(0, str(ROOT/'tests'))
    import rtap, suite
    snap, snapshot_proof = fresh_snapshot(tap2sna)
    ssx = out.read_bytes()
    blocks = rtap.records(ssx, SSX_NAME)
    sequential = consecutive_processes(snap, blocks)
    concurrent = simultaneous_processes(snap, blocks, link['env1_bss_offset'])
    return {'result':'PASS', 'case_id': 'native_env1_storage_lifetime',
            'source': source_hashes, 'link': link,
            'sequential': sequential, 'concurrent': concurrent,
            'native_snapshot': snapshot_proof,
            'compiler': 'release/build/sdk/bin/rcc --native', 'target':'ZX-UX v1 native',
            'runtime_build_log_sha256':hashlib.sha256(buildlog.encode()).hexdigest(),
            'compiler_log_sha256':hashlib.sha256(compilelog.encode()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--tap2sna', required=True, type=Path,
                        help='checked SkoolKit 10.1 toolbox tap2sna.py, outside Git')
    args = parser.parse_args(argv)
    report = args.report.resolve()
    ensure(ROOT not in report.parents and report.suffix == '.json',
           'report must remain outside the checkout and release')
    ensure(report != FIXTURE.resolve() and report != CRT.resolve(),
           'report must not overwrite source')
    result = {'result':'INCONCLUSIVE', 'source_sha': 'unknown'}
    try:
        result = full_run(report, args.tap2sna)
        code = 0
    except (GateFailure, OSError, subprocess.SubprocessError, ValueError) as e:
        result = {'result':'FAIL','reason': str(e)}
        code = 1
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(result['result'])
    return code


if __name__ == '__main__':
    raise SystemExit(main())
