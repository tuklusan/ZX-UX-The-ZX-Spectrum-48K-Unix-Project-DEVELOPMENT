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
        # Use register-only no-ops: PUSH/POP writes observable stack bytes.
        whole = self.source().replace('    push hl\n    pop hl\n',
                                      '    ld a,a\n    ld a,a\n')
        obj = ras.assemble_text(whole, 'register-before.s')
        before = rld.link([rld.Obj(obj, 'register-before.sso')], [],
                          entry='start', stack=384)[0]
        seen = []
        def optimize(source):
            seen.append(source)
            return source.replace('    ld a,a\n    ld a,a\n', '')
        result = verify_whole_optimizer_candidate(whole, before, optimize)
        self.assertEqual(seen, [whole])
        self.assertTrue(result['native_candidate_link_verified'])
        self.assertTrue(result['source_cfg_liveness']['source_liveness_converged'])
        self.assertFalse(result['candidate_cfg_liveness']['rewrite_safe_to_admit'])
        self.assertTrue(result['protected_source_lines_preserved'])
        self.assertFalse(result['candidate_byte_identical'])
        self.assertGreaterEqual(result['candidate_file_bytes_saved'], 0)
        self.assertGreater(result['native_baseline_image_bytes'],
                           result['native_candidate_image_bytes'])
        self.assertGreater(result['candidate_total_bytes_saved'], 0)
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(result['native_behavior_verified'])
        self.assertFalse(result['full_program_optimized'])

    def test_runtime_witness_checked_on_changed_native_candidate(self):
        original = self.source().replace('    push hl\n    pop hl\n',
                                         '    ld a,a\n    ld a,a\n')
        obj = ras.assemble_text(original, 'runtime-witness-before.s')
        before = rld.link([rld.Obj(obj, 'runtime-witness-before.sso')], [],
                          entry='start', stack=384)[0]
        def optimize(source):
            return source.replace('    ld a,a\n    ld a,a\n', '')
        resource = bytes((195, 0, 118, 255, 24))
        result = verify_whole_optimizer_candidate(
            original, before, optimize, expected_runtime_bytes=resource)
        self.assertFalse(result['candidate_byte_identical'])
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])
        attempts = []
        def traced(source):
            attempts.append(source)
            return optimize(source)
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'runtime resource differs from baseline'):
            verify_whole_optimizer_candidate(
                original, before, traced, expected_runtime_bytes=b'not present')
        self.assertEqual(attempts, [])  # Reject the baseline before optimizing.
        # Data pointers are source-owned relocation words. They can move as
        # code shrinks; an exact-byte resource witness must not silently pass.
        before_image = rld.parse_ssx(before)['image']
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'runtime resource differs from candidate'):
            verify_whole_optimizer_candidate(
                original, before, optimize, expected_runtime_bytes=before_image[-7:])

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

    def test_unverified_control_transfer_rewrite_is_rejected(self):
        original = self.source()
        baseline = self.baseline()
        for transformed in (
                original.replace('    call worker\n', '    call start\n'),
                original.replace('    call worker\n', '    jp worker\n'),
                original.replace('    ret\n', '    reti\n', 1),
                original.replace('    ret\n', '    di\n    ret\n', 1),
        ):
            with self.subTest(transformed=transformed):
                with self.assertRaisesRegex(WholeOptimizerError, 'control-flow or interrupt'):
                    verify_whole_optimizer_candidate(original, baseline,
                                                     lambda _: transformed)

    def test_tail_call_return_to_jump_rejected_due_to_stack_write(self):
        original = self.source()
        changed = original.replace('    call worker\n    ret\n', '    jp worker\n')
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'control-flow or interrupt'):
            verify_whole_optimizer_candidate(original, self.baseline(),
                                             lambda _: changed)

    def test_control_source_comments_and_operand_spacing_are_harmless(self):
        original = self.source()
        modified = original.replace('    call worker\n',
                                    '    call  worker ; preserve branch\n')
        result = verify_whole_optimizer_candidate(original, self.baseline(),
                                                  lambda _: modified)
        self.assertTrue(result['candidate_byte_identical'])
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])

    def test_removed_label_anchored_noops_are_reported_and_rejected(self):
        # Two adjacent bytes are instructions, not disposable label storage.
        source = self.source().replace(
            'worker:\n    ld hl',
            'worker:\n    ld a, a\nsecond:\n    ld a, a\nlast:\n    ld hl')
        obj = ras.assemble_text(source, 'label-noops-before.s')
        baseline = rld.link([rld.Obj(obj, 'label-noops-before.sso')], [],
                            entry='start', stack=384)[0]
        def drop_labeled_instructions(text):
            return text.replace('    ld a, a\n', '')
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'protected resource boundary; first change after worker:'):
            verify_whole_optimizer_candidate(
                source, baseline, drop_labeled_instructions)

    def test_original_biorhythms_protected_resource_failure_is_precise(self):
        env = tuple(os.environ.get(name) for name in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(env):
            self.skipTest('requires exact original compiler and optimizer')
        from gate8_full_source_audit import run
        game = '23-biorhythms'
        source = ROOT / 'src/bonus/60-programs' / game / 'BASIC' / (game + '.bas')
        report = run(source, Path(env[0]), Path(env[1]), Path(env[2]),
                     ROOT / 'src/zx-ux-sdk/rom/48.rom')
        baseline = report['native_whole_source_baseline']
        candidate = baseline['native_whole_optimizer_candidate']
        self.assertTrue(baseline['native_whole_source_baseline_linked'])
        self.assertTrue(baseline['native_image_byte_exact'])
        self.assertFalse(candidate['native_candidate_link_verified'])
        self.assertIn('original_rt_150b:', candidate['blocker'])
        self.assertIn('protected resource boundary', candidate['blocker'])
        self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(report['gate8_complete'])

    def test_memory_reads_and_stack_effects_cannot_be_silently_deleted(self):
        original = ('    section text\n    global start\nstart:\n'
                    '    ld a,(23692)\n    push af\n    ld a,255\n'
                    '    ld (23692),a\n    pop af\n'
                    '    ld (23692),a\n    ret\n')
        obj = ras.assemble_text(original, 'memory-before.s')
        baseline = rld.link([rld.Obj(obj, 'memory-before.sso')], [],
                            entry='start', stack=384)[0]
        for changed in (
                original.replace('    ld a,(23692)\n', ''),
                original.replace('    ld a,(23692)', '    ld a,12'),
                original.replace('    push af\n', ''),
                original.replace('    pop af\n', ''),
                original.replace('    ld (23692),a\n', '', 1)):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(WholeOptimizerError,
                                            'memory, I/O or stack effects'):
                    verify_whole_optimizer_candidate(original, baseline,
                                                     lambda _: changed)
        harmless = original.replace('    ld a,(23692)',
                                    '    ld  a, (23692) ; still reads memory')
        candidate = verify_whole_optimizer_candidate(original, baseline,
                                                      lambda _: harmless)
        self.assertTrue(candidate['candidate_byte_identical'])
        self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])

    def test_pointer_register_rewrite_must_not_sneak_past_memory_guard(self):
        # Both programs contain precisely the same memory operation mnemonics;
        # their HL values direct the read to different source addresses.
        source = ('    section text\n    global start\nstart:\n'
                  '    ld hl,23692\n    ld a,(hl)\n'
                  '    ld (23693),a\n    ret\n')
        other = source.replace('ld hl,23692', 'ld hl,23694')
        plain = rld.link([rld.Obj(ras.assemble_text(source, 'hl-before.s'),
                                  'hl-before.sso')], [], entry='start', stack=384)[0]
        changed = rld.link([rld.Obj(ras.assemble_text(other, 'hl-after.s'),
                                    'hl-after.sso')], [], entry='start', stack=384)[0]
        from gate8_native_whole_optimizer import _observable_accesses
        self.assertEqual(_observable_accesses(source), _observable_accesses(other))
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'register, flag or address state'):
            verify_whole_optimizer_candidate(source, plain, lambda _: other)

        from z80_python.cpu import Z80CPU
        for base in (0x7000, 0x8000, 0x9000):
            def execute(ssx):
                parsed = rld.parse_ssx(ssx)
                memory = bytearray([0]) * 65536
                memory[base:base + len(parsed['image'])] = rld.relocate(
                    parsed['image'], parsed['relocs'], base)
                memory[23692], memory[23694] = 0x12, 0xe7
                memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                cpu.pc = base + parsed['entry']
                cpu.sp = 0xd000
                for _ in range(8):
                    if cpu.pc == 0xb000:
                        break
                    cpu.step()
                else:
                    self.fail('native pointer test did not return')
                return memory[23693]
            with self.subTest(base=base):
                self.assertEqual(execute(plain), 0x12)
                self.assertEqual(execute(changed), 0xe7)

    def test_register_and_flag_changes_before_unmodified_output_rejected(self):
        source = ('    section text\n    global start\nstart:\n'
                  '    ld a,7\n    ld (23692),a\n    ret\n')
        plain = rld.link([rld.Obj(ras.assemble_text(source, 'register-before.s'),
                                  'register-before.sso')], [], entry='start', stack=384)[0]
        changes = (source.replace('ld a,7', 'ld a,8'),
                   source.replace('ld a,7', 'xor a'),
                   source.replace('ld a,7\n', ''))
        for changed in changes:
            with self.subTest(candidate=changed):
                with self.assertRaisesRegex(WholeOptimizerError,
                                            'register, flag or address state'):
                    verify_whole_optimizer_candidate(source, plain,
                                                     lambda _: changed)

    def test_native_conditional_branch_shortening_changes_clock(self):
        # Source-level JP -> JR can leave flags/registers unchanged but alters
        # elapsed Z80 T-states, affecting clock-dependent native behavior.
        source = ('    section text\n    global start\nstart:\n'
                  '    jp z,finish\n    nop\nfinish:\n    ret\n')
        other = source.replace('jp z,finish', 'jr z,finish')
        def linked(text):
            obj = ras.assemble_text(text, 'branch-clock.s')
            return rld.link([rld.Obj(obj, 'branch-clock.sso')], [],
                            entry='start', stack=384)[0]
        before, after = linked(source), linked(other)
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'control-flow or interrupt instruction'):
            verify_whole_optimizer_candidate(source, before, lambda _: other)
        from z80_python.cpu import Z80CPU
        def measure(ssx, base, flags):
            info = rld.parse_ssx(ssx)
            memory = bytearray(65536)
            memory[base:base + len(info['image'])] = rld.relocate(
                info['image'], info['relocs'], base)
            memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
            cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
            cpu.pc = base + info['entry']
            cpu.sp = 0xd000
            cpu.f = flags
            cycles = 0
            for _ in range(6):
                if cpu.pc == 0xb000:
                    break
                cycles += cpu.step()
            else:
                self.fail('native timed branch did not return')
            return (cpu.pc, cpu.sp, int(cpu.f), cpu.a), cycles
        for base in (0x7000, 0x8000, 0x9000):
            for flags, delta in ((0x40, 2), (0, -3)):
                with self.subTest(base=base, flags=flags):
                    old_state, old_t = measure(before, base, flags)
                    new_state, new_t = measure(after, base, flags)
                    self.assertEqual(old_state, new_state)
                    self.assertEqual(new_t - old_t, delta)

    def test_wrong_optimizer_output_rejected(self):
        with self.assertRaisesRegex(WholeOptimizerError, 'text'):
            verify_whole_optimizer_candidate(self.source(), self.baseline(),
                                             lambda _: b'bad')

    def test_locked_real_upstream_identity(self):
        path = os.environ.get('RBC_G8_OPTIMIZER')
        if not path:
            self.skipTest('locked optimizer source path required')
        optimizer = load_locked_optimizer(Path(path))
        # Native probing shows an observable stack-memory difference for the
        # proposed tail-transfer shortening, even with equal registers.
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'control-flow or interrupt'):
            verify_whole_optimizer_candidate(
                self.source(), self.baseline(), optimizer.optimize)
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
                if candidate.get('native_candidate_link_verified'):
                    self.assertTrue(candidate['optimizer_full_program_source_presented'])
                    self.assertTrue(candidate['protected_source_lines_preserved'])
                else:
                    self.assertIn('blocker', candidate)
                    self.assertIn('optimizer', candidate['blocker'])
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(candidate['native_behavior_verified'])
                self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
