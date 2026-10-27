"""Independent full-program optimizer source identity and native pair gates."""
from pathlib import Path
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_whole_optimizer import (
    WholeOptimizerError, load_locked_optimizer, verify_whole_optimizer_candidate)


class WholeOptimizerTests(unittest.TestCase):
    def source(self):
        return ('    section text\n    global start\nstart:\n'
                '    push hl\n    pop hl\n    call worker\n    ret\n'
                'worker:\n    ld hl,bytes_resource\n    ret\n'
                '    section data\nbytes_resource:\n'
                '    db 195,0,118,255,24\n'
                '    dw worker\n'
                '    section bss\n    ds 7\n')

    def baseline(self):
        obj = ras.assemble_text(self.source(), 'whole-opt-before.s')
        return rld.link([rld.Obj(obj, 'whole-opt-before.sso')], [],
                        entry='start', stack=384)[0]

    def test_full_program_optimizer_relinks_and_preserves_resource(self):
        whole = self.source()
        before = self.baseline()
        seen = []
        def optimize(source):
            seen.append(source)
            return source.replace('    push hl\n    pop hl\n', '')
        result = verify_whole_optimizer_candidate(whole, before, optimize)
        self.assertEqual(seen, [whole])
        self.assertTrue(result['native_candidate_link_verified'])
        self.assertTrue(result['protected_source_lines_preserved'])
        self.assertFalse(result['candidate_byte_identical'])
        self.assertGreaterEqual(result['candidate_file_bytes_saved'], 0)
        self.assertGreater(result['native_baseline_image_bytes'],
                           result['native_candidate_image_bytes'])
        self.assertGreater(result['candidate_total_bytes_saved'], 0)
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(result['native_behavior_verified'])
        self.assertFalse(result['full_program_optimized'])

    def test_reject_forged_or_stale_native_baseline_before_optimizing(self):
        genuine = self.baseline()
        original = self.source()
        calls = []
        def spy(text):
            calls.append(text)
            return text
        changed = original.replace('    push hl\n    pop hl\n', '')
        # Neither an alternate linked image nor altered bytes match this source.
        for bad in (
                rld.link([rld.Obj(ras.assemble_text(changed, 'other.s'),
                                  'other.sso')], [], entry='start', stack=384)[0],
                genuine[:-1] + bytes([genuine[-1] ^ 1])):
            with self.subTest(baseline_bytes=len(bad)):
                with self.assertRaises(WholeOptimizerError):
                    verify_whole_optimizer_candidate(original, bad, spy)
        self.assertEqual(calls, [])
        result = verify_whole_optimizer_candidate(original, genuine, spy)
        self.assertTrue(result['native_baseline_source_reassembled'])
        self.assertEqual(calls, [original])

    def test_protect_binary_resource(self):
        with self.assertRaisesRegex(WholeOptimizerError, 'protected'):
            verify_whole_optimizer_candidate(
                self.source(), self.baseline(),
                lambda source: source.replace('db 195,0,118,255,24',
                                              'db 195,0,118,255,23'))

    def test_protect_pointer_and_labels(self):
        for transformer in (
                lambda s: s.replace('dw worker', 'dw start'),
                lambda s: s.replace('worker:\n', 'different:\n'),
                lambda s: s.replace('section bss', 'section data'),
                lambda s: s + '    org 1234\n'):
            with self.subTest(transformer=transformer):
                with self.assertRaises(WholeOptimizerError):
                    verify_whole_optimizer_candidate(self.source(),
                                                     self.baseline(), transformer)

    def test_wrong_optimizer_output_rejected(self):
        with self.assertRaisesRegex(WholeOptimizerError, 'text'):
            verify_whole_optimizer_candidate(self.source(), self.baseline(),
                                             lambda _: b'bad')

    def test_locked_real_upstream_identity(self):
        path = os.environ.get('RBC_G8_OPTIMIZER')
        if not path:
            self.skipTest('locked optimizer source path required')
        optimizer = load_locked_optimizer(Path(path))
        candidate = verify_whole_optimizer_candidate(
            self.source(), self.baseline(), optimizer.optimize)
        self.assertTrue(candidate['native_candidate_link_verified'])
        self.assertFalse(candidate['native_behavior_verified'])
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / 'upeepz80'
            fake.mkdir()
            (fake / 'peephole.py').write_text('unsafe')
            with self.assertRaisesRegex(WholeOptimizerError, 'source'):
                load_locked_optimizer(Path(temp))

    def test_original_games_full_source_candidate_no_false_admission(self):
        compiler = os.environ.get('RBC_G8_CHECKPOINT')
        frontend = os.environ.get('RBC_G8_FRONTEND')
        tape = os.environ.get('RBC_G8_TAPE')
        optimizer = os.environ.get('RBC_G8_OPTIMIZER')
        if not all((compiler, frontend, tape, optimizer)):
            self.skipTest('requires locked original compiler and upeepz80 source')
        from gate8_full_source_audit import run
        for game in ('42-bricklayer', '28-dam-busters', '56-roots'):
            with self.subTest(game=game):
                report = run(ROOT / f'src/bonus/60-programs/{game}/BASIC/{game}.bas',
                             Path(compiler), Path(frontend), Path(tape),
                             ROOT / 'src/zx-ux-sdk/rom/48.rom')
                base = report['native_whole_source_baseline']
                self.assertTrue(base['native_whole_source_baseline_linked'])
                candidate = base['native_whole_optimizer_candidate']
                self.assertTrue(candidate['optimizer_full_program_source_presented'])
                self.assertTrue(candidate['native_candidate_link_verified'])
                self.assertTrue(candidate['protected_source_lines_preserved'])
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(candidate['native_behavior_verified'])
                self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
