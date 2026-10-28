"""Real-ZX-UX tests for bounded raw INPUT, separate from published runtime."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/tests')]
import rvm
import rld
from native_rbc_cli import compile_native
from native_input_raw_candidate import assemble_candidate
from test_native_oxo_complete_round import text_row

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAME = ROOT / 'src/bonus/60-programs/39-flying-geese'
READY = all(p.is_file() for p in (CHECKPOINT / 'rbc.py',
    CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN, GAME / 'BASIC/39-flying-geese.bas',
    GAME / 'BASIC/39-flying-geese.tzx', GAME / 'bin/39-flying-geese.ssx'))


@unittest.skipUnless(READY, 'original compiler, ROM and frozen ZX-UX required')
class NativeRawSourceInput(unittest.TestCase):
    def setUp(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())

    def make(self, bas: Path, out: Path):
        asm, obj, legacy, proof = compile_native(
            bas, CHECKPOINT, FRONTEND, TAPE, ROM)
        self.assertTrue(obj.startswith(b'SSO1'))
        self.assertTrue(proof['native_three_base_source_verified'])
        self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
        self.assertFalse(proof['optimizer_used'])
        amended = assemble_candidate(asm)
        self.assertNotEqual(legacy, amended)
        self.assertEqual(rld.parse_ssx(amended)['entry'], 0)
        out.write_bytes(amended)
        return amended

    def test_string_numeric_delete_and_bounded_overlong_line(self):
        fixtures = [
            ('10 REM : OPEN #\n20 INPUT A$\n'
             '30 POKE 22528,LEN A$+20\n40 STOP\n',
             [('abc', 23), ('z'*80, 100), ('z'*110, None),
              ('abc{DELETE}d', 23), ('', 20)]),
            ('10 REM : OPEN #\n20 INPUT A\n'
             '30 IF A=1234 THEN POKE 22528,55\n40 STOP\n',
             [('1234', 55), ('123x{DELETE}4', 55),
              ('abc{ENTER}{WAIT 100}1234', 55)]),
        ]
        with tempfile.TemporaryDirectory(prefix='raw-input-test-') as tmp:
            for i, (basic, cases) in enumerate(fixtures):
                bas, ssx = Path(tmp) / f'input-{i}.bas', Path(tmp) / f'input-{i}.ssx'
                bas.write_text(basic, encoding='ascii')
                self.make(bas, ssx)
                for script, want in cases:
                    with self.subTest(fixture=i, script=script[:15]):
                        run = rvm.run_kernel(ssx,
                            keys='{WAIT 200}'+script+'{ENTER}',
                            frames=2000, system=SYSTEM)
                        self.assertEqual(run.why, 'exit', run.summary())
                        self.assertEqual(run.fg.status, 0)
                        cell = run.fg.exit_picture[0][6144]
                        if want is None:
                            self.assertGreater(cell, 90)
                            self.assertLess(cell, 125)
                        else:
                            self.assertEqual(cell, want)
                        run.session.wait_prompt(1500)
                        self.assertEqual(run.session.last_line(), '#')
                        self.assertFalse(run.session.owns_screen(run.fg.pid))

    def test_original_flying_geese_raw_input_replay_is_not_published(self):
        bas = GAME / 'BASIC/39-flying-geese.bas'
        tzx = GAME / 'BASIC/39-flying-geese.tzx'
        published = GAME / 'bin/39-flying-geese.ssx'
        original_bytes = tuple(f.read_bytes() for f in (bas, tzx, published))
        font = (CHECKPOINT / 'font32.bin').read_bytes()
        self.assertEqual(len(font), 768)
        with tempfile.TemporaryDirectory(prefix='raw-geese-test-') as tmp:
            ssx = Path(tmp) / 'geese-experimental.ssx'
            image = self.make(bas, ssx)
            self.assertLessEqual(len(image), 14000)
            shots = '{WAIT 100}' + 'a'*130
            opts = rvm.Options()
            opts.prog = str(ssx)
            opts.keys = shots+'{WAIT 150}{ENTER}'
            opts.frames = 5200
            opts.system = SYSTEM
            replay = rvm.Runner(opts)
            replay.start()
            recorded = []
            for _ in range(8200):
                replay.frame()
                if (replay.fg.started is not None and replay.fg.ended is None and
                        (replay.session.m.frame - replay.fg.started) % 25 == 0 and
                        not recorded):
                    pic, border = replay.picture()
                    if text_row(pic, 9, font).strip() == 'GAME OVER':
                        recorded.append((pic, border))
                why = replay.check(5200)
                if why:
                    replay.why = why
                    break
            self.assertEqual(len(recorded), 1, 'GAME OVER was never observed')
            overpic, overborder = recorded[0]
            self.assertIn('IN 100 SHOTS', text_row(overpic, 11, font))
            self.assertEqual(replay.why, 'frames', replay.summary())
            self.assertIsNone(replay.fg.ended)
            newpic, newborder = replay.picture()
            self.assertNotEqual(hashlib.sha256(overpic).digest(),
                                hashlib.sha256(newpic).digest())
            self.assertTrue(text_row(newpic, 0, font).strip().startswith('SHOTS:'))
            self.assertNotIn('GAME OVER', text_row(newpic, 9, font))
            if os.environ.get('RBC_RAW_GEESE_CAPTURE_DIR'):
                folder = Path(os.environ['RBC_RAW_GEESE_CAPTURE_DIR'])
                folder.mkdir(parents=True, exist_ok=True)
                rvm.write_png(overpic, str(folder / 'flying-geese-raw-gameover.png'), overborder)
                rvm.write_png(newpic, str(folder / 'flying-geese-raw-replay.png'), newborder)
        self.assertEqual(tuple(f.read_bytes() for f in (bas, tzx, published)),
                         original_bytes)

    def test_overlong_raw_input_never_enters_low_kernel(self):
        with tempfile.TemporaryDirectory(prefix='raw-input-space-') as folder:
            bas = Path(folder) / 'bounds.bas'
            ssx = Path(folder) / 'bounds.ssx'
            bas.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                           '30 POKE 22528,LEN A$+20\n40 STOP\n',
                           encoding='ascii')
            self.make(bas, ssx)
            opt = rvm.Options()
            opt.prog = str(ssx)
            opt.system = SYSTEM
            opt.keys = '{WAIT 200}' + 'z'*120 + '{ENTER}'
            opt.frames = 2400
            run = rvm.Runner(opt)
            run.start()
            observed = []

            def sample(_frame):
                if run.fg.started is not None and run.fg.ended is None:
                    observed.append(run.session.word(0x5c65))

            run.session.frame_hooks.append(sample)
            for _ in range(5400):
                run.frame()
                why = run.check(2400)
                if why:
                    run.why = why
                    break
            self.assertEqual(run.why, 'exit', run.summary())
            self.assertEqual(run.fg.status, 0)
            self.assertTrue(observed)
            self.assertGreater(min(observed), 0x5d00)
            self.assertLess(max(observed), 0x5d98)
            run.session.wait_prompt(1500)
            self.assertEqual(run.session.last_line(), '#')

    def test_sequential_raw_input_processes_restore_shell_and_rom_state(self):
        protected = (0x5c36, 0x5c37, 0x5c7b, 0x5c7c,
                     0x5c6a, 0x5c39, 0x5c8d, 0x5c8e, 0x5c8f, 0x5c90)
        with tempfile.TemporaryDirectory(prefix='raw-input-isolation-') as folder:
            bas = Path(folder) / 'session.bas'
            ssx = Path(folder) / 'session.ssx'
            bas.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                           '30 POKE 22528,LEN A$+30\n40 STOP\n',
                           encoding='ascii')
            data = self.make(bas, ssx)
            first = rvm.run_kernel(ssx, keys='{WAIT 200}alpha{ENTER}',
                                   frames=1100, system=SYSTEM)
            self.assertEqual(first.why, 'exit', first.summary())
            self.assertEqual(first.fg.status, 0)
            self.assertEqual(first.fg.exit_picture[0][6144], 35)
            session = first.session
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertFalse(session.owns_screen(first.fg.pid))
            snapshot = bytes(session.m.mem[x] for x in protected)
            second = session.launch(data, 'raw-input2')
            session.kb.type('xyz\n')
            for _ in range(1500):
                session.step()
                if second.ended is not None:
                    break
            self.assertIsNotNone(second.ended, 'second native process stalled')
            self.assertEqual(second.status, 0)
            self.assertEqual(second.exit_picture[0][6144], 33)
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertFalse(session.owns_screen(second.pid))
            self.assertEqual(bytes(session.m.mem[x] for x in protected), snapshot)
            calls = session.syscalls
            session.kb.type('\n')
            session.wait_prompt(1500)
            self.assertGreater(session.syscalls, calls)

    def test_two_original_input_games_advance_with_raw_editor(self):
        font = (CHECKPOINT / 'font32.bin').read_bytes()
        cases = (
            ('01-minelay', '{WAIT 250}{ENTER}{WAIT 100}{ENTER}'
             '{WAIT 150}2{WAIT 100}q', 1800, 0, 'Score 0'),
            ('30-space-traffic', '{WAIT 250}{ENTER}{WAIT 100}{ENTER}',
             1500, 5, 'You scored 0 points.'),
        )
        with tempfile.TemporaryDirectory(prefix='raw-input-games-') as folder:
            for name, keys, frames, line, expected in cases:
                with self.subTest(game=name):
                    game = ROOT / 'src/bonus/60-programs' / name
                    bas = game / 'BASIC' / (name+'.bas')
                    tzx = game / 'BASIC' / (name+'.tzx')
                    pub = game / 'bin' / (name+'.ssx')
                    unchanged = tuple(x.read_bytes() for x in (bas, tzx, pub))
                    ssx = Path(folder) / (name+'.ssx')
                    self.make(bas, ssx)
                    test = rvm.run_kernel(ssx, keys=keys, frames=frames,
                                          system=SYSTEM)
                    self.assertEqual(test.why, 'frames', test.summary())
                    self.assertIsNone(test.fg.ended)
                    self.assertTrue(test.session.owns_screen(test.fg.pid))
                    pic, _ = test.picture()
                    self.assertIn(expected, text_row(pic, line, font))
                    self.assertEqual(tuple(x.read_bytes() for x in (bas, tzx, pub)),
                                     unchanged)

    def test_suspect_original_rom_editor_not_silently_rewritten(self):
        with self.assertRaisesRegex(ValueError, 'witness unavailable'):
            assemble_candidate('    call 0x0f2c\n    section data\n')


if __name__ == '__main__':
    unittest.main()
