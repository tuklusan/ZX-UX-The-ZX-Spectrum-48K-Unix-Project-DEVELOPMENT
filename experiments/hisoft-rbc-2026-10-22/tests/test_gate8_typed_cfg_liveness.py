"""Typed whole-Z80 CFG and conservative register liveness checks."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_typed_cfg_liveness import (inspect_typed_cfg_liveness, TypedCFGError,
                                      _effects)


class TypedWholeCFGTests(unittest.TestCase):
    def test_reachable_internal_branch_and_unreachable_instruction(self):
        source = ('    section text\n    global start\nstart:\n'
                  '    ld a,1\n    jp done\n    nop\n'
                  'done:\n    ld a,2\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['instruction_count'], 5)
        self.assertEqual(report['reachable_instructions'], 4)
        self.assertEqual(report['unreached_instructions'], 1)
        self.assertEqual(report['unresolved_control_edges'], 0)
        self.assertTrue(report['source_liveness_converged'])
        self.assertFalse(report['rewrite_safe_to_admit'])

    def test_opaque_indirect_and_protected_data_do_not_become_edges(self):
        source = ('    section text\n    global start\nstart:\n'
                  '    jp (hl)\n    db 195,0,118,255\n'
                  'entry:\n    call datum\n    ret\n'
                  'section data\ndatum:\n    dw entry\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertGreater(report['unresolved_control_edges'], 0)
        self.assertEqual(report['direct_cfg_reachable_instructions'], 1)
        self.assertEqual(report['reachable_instructions'], report['instruction_count'])
        self.assertTrue(report['unknown_entry_reachability'])
        self.assertGreater(report['register_effects_unknown'], 0)
        self.assertFalse(report['native_behavior_verified'])

    def test_address_table_is_a_possible_entry_without_direct_branch(self):
        source = ('section text\nstart:\n    ret\n'
                  'handler:\n    ld a,42\n    ret\n'
                  'section data\ntable:\n    dw handler\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['direct_cfg_reachable_instructions'], 1)
        self.assertEqual(report['symbolic_table_entry_instructions'], 1)
        self.assertEqual(report['reachable_instructions'], 3)
        self.assertFalse(report['unknown_entry_reachability'])
        self.assertFalse(report['rewrite_safe_to_admit'])

    def test_native_indirect_table_dispatch_cannot_be_called_dead(self):
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        source = ('    section text\n    global start\nstart:\n'
                  '    ld hl,(dispatch)\n    jp (hl)\n'
                  'unused:\n    ld a,0\n    ret\n'
                  'handler:\n    ld a,42\n    ret\n'
                  '    section data\ndispatch:\n    dw handler\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['direct_cfg_reachable_instructions'], 2)
        self.assertEqual(report['symbolic_table_entry_instructions'], 1)
        self.assertTrue(report['unknown_entry_reachability'])
        self.assertEqual(report['reachable_instructions'], report['instruction_count'])
        self.assertGreater(report['unresolved_exit_sites'], 0)
        self.assertFalse(report['rewrite_safe_to_admit'])
        obj = ras.assemble_text(source, 'indirect-table.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'indirect-table.sso')], [],
                           entry='start', stack=384)
        info = rld.parse_ssx(ssx)
        self.assertGreaterEqual(len(info['relocs']), 2)
        for base in (0x7000, 0x8000, 0x9000):
            with self.subTest(base=base):
                memory = bytearray(65536)
                image = rld.relocate(info['image'], info['relocs'], base)
                memory[base:base + len(image)] = image
                memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                cpu.pc = base + info['entry']
                cpu.sp = 0xd000
                for _ in range(12):
                    if cpu.pc == 0xb000:
                        break
                    cpu.step()
                else:
                    self.fail('indirect handler did not return')
                self.assertEqual(cpu.a, 42)

    def test_address_taken_without_word_table_is_an_entry(self):
        # RET is an indirect transfer when the return address was pushed.
        source = ('section text\nstart:\n'
                  '    ld hl,handler\n    push hl\n    ret\n'
                  'unused:\n    xor a\n    ret\n'
                  'handler:\n    ld a,42\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['direct_cfg_reachable_instructions'], 3)
        self.assertEqual(report['symbolic_address_entry_instructions'], 1)
        self.assertEqual(report['symbolic_table_entry_instructions'], 0)
        self.assertEqual(report['reachable_instructions'], 5)
        self.assertEqual(report['unreached_instructions'], 2)
        self.assertFalse(report['unknown_entry_reachability'])
        self.assertFalse(report['rewrite_safe_to_admit'])

    def test_native_return_stack_dispatch_at_three_process_bases(self):
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        source = ('    section text\n    global start\nstart:\n'
                  '    ld hl,handler\n    push hl\n    ret\n'
                  'unused:\n    xor a\n    ret\n'
                  'handler:\n    ld a,42\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['symbolic_address_entry_instructions'], 1)
        obj = ras.assemble_text(source, 'return-stack-dispatch.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'return-stack-dispatch.sso')], [],
                           entry='start', stack=384)
        info = rld.parse_ssx(ssx)
        self.assertGreaterEqual(len(info['relocs']), 1)
        for base in (0x7000, 0x8000, 0x9000):
            with self.subTest(base=base):
                memory = bytearray(65536)
                image = rld.relocate(info['image'], info['relocs'], base)
                memory[base:base+len(image)] = image
                memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                cpu.pc, cpu.sp = base + info['entry'], 0xd000
                for _ in range(12):
                    if cpu.pc == 0xb000:
                        break
                    cpu.step()
                else:
                    self.fail('return-stack handler did not return')
                self.assertEqual(cpu.a, 42)
                self.assertEqual(cpu.sp, 0xd002)

    def test_arithmetic_on_code_pointer_is_unresolved(self):
        for source in (
                'section text\nstart:\n ret\nhandler:\n ret\n'
                'section data\n    dw handler+1\n',
                'section text\nstart:\n ret\nhandler:\n ret\n'
                'section data\n    db handler & 255,handler >> 8\n',
                'section text\nstart:\n ld hl,handler+1\n ret\n'
                'handler:\n nop\n ret\n'):
            with self.subTest(source=source):
                report = inspect_typed_cfg_liveness(source)
                self.assertTrue(report['unknown_entry_reachability'])
                self.assertEqual(report['reachable_instructions'],
                                 report['instruction_count'])
                self.assertGreater(report['unresolved_pointer_expressions'], 0)
                self.assertFalse(report['rewrite_safe_to_admit'])

    def test_zero_prefixed_decimal_rom_control_targets(self):
        # ras accepts leading zeros as decimal, not Python's base-0 syntax.
        # The CFG must classify the exact number used by the native linker.
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        spellings = ('0100', '000100', '100', '$64', '0x64')
        for spelling in spellings:
            source = ('    section text\n    global start\nstart:\n'
                      f'    jp {spelling}\n')
            with self.subTest(spelling=spelling):
                report = inspect_typed_cfg_liveness(source)
                self.assertEqual(report['rom_transfer_edges'], 1)
                self.assertEqual(report['unresolved_control_edges'], 0)
                self.assertEqual(report['direct_cfg_reachable_instructions'], 1)
                self.assertFalse(report['rewrite_safe_to_admit'])
                obj = ras.assemble_text(source, 'leading-zero-jp.s')
                ssx, *_ = rld.link([rld.Obj(obj, 'leading-zero-jp.sso')], [],
                                  entry='start', stack=384)
                info = rld.parse_ssx(ssx)
                self.assertEqual(info['image'], b'\xc3\x64\x00')
                for base in (0x7000, 0x8000, 0x9000):
                    memory = bytearray(65536)
                    code = rld.relocate(info['image'], info['relocs'], base)
                    memory[base:base+len(code)] = code
                    # A small ROM-address test stub, independent of the
                    # actual Spectrum ROM, returns through the process stack.
                    memory[0x64:0x67] = b'\x3e\x2a\xc9'
                    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                    cpu.pc, cpu.sp = base + info['entry'], 0xd000
                    for _ in range(8):
                        if cpu.pc == 0xb000:
                            break
                        cpu.step()
                    else:
                        self.fail('native decimal ROM jump did not return')
                    self.assertEqual(cpu.a, 42)

    def test_leading_zero_decimal_above_rom_not_called_a_rom_edge(self):
        for literal in ('016384', '16384', '$4000', '0x4000'):
            with self.subTest(literal=literal):
                report = inspect_typed_cfg_liveness(
                    '    section text\nstart:\n    jp ' + literal + '\n')
                self.assertEqual(report['rom_transfer_edges'], 0)
                self.assertTrue(report['unknown_entry_reachability'])
                self.assertEqual(report['unresolved_control_edges'], 1)
                self.assertFalse(report['rewrite_safe_to_admit'])

    def test_conditional_returns_and_rom_jumps_have_external_live_exits(self):
        # The taken path is visible to a caller, even when the fallthrough
        # overwrites all the registers. It must not be treated as only a
        # single in-program edge.
        for transfer in ('ret c', 'ret z', 'jp c,0100', 'jp nz,$64'):
            source = ('section text\nstart:\n    ld a,11\n    '
                      + transfer + '\n    ld a,22\n    ret\n')
            with self.subTest(transfer=transfer):
                report = inspect_typed_cfg_liveness(source)
                self.assertEqual(report['conditional_external_exit_sites'], 1)
                self.assertFalse(report['unknown_entry_reachability'])
                self.assertFalse(report['rewrite_safe_to_admit'])
        # Unconditional RET already has no source successor and all-live exit.
        report = inspect_typed_cfg_liveness(
            'section text\nstart:\n    ret\n')
        self.assertEqual(report['conditional_external_exit_sites'], 0)

    def test_native_conditional_return_exposes_state_at_three_bases(self):
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        for flag_code, expected in (('scf', 11), ('or a', 22)):
            source = ('    section text\n    global start\nstart:\n'
                      '    ld a,11\n    ' + flag_code + '\n'
                      '    ret c\n    ld a,22\n    ret\n')
            report = inspect_typed_cfg_liveness(source)
            self.assertEqual(report['conditional_external_exit_sites'], 1)
            obj = ras.assemble_text(source, 'conditional-ret.s')
            ssx, *_ = rld.link([rld.Obj(obj, 'conditional-ret.sso')], [],
                              entry='start', stack=384)
            info = rld.parse_ssx(ssx)
            for base in (0x7000, 0x8000, 0x9000):
                with self.subTest(flag_code=flag_code, base=base):
                    memory = bytearray(65536)
                    code = rld.relocate(info['image'], info['relocs'], base)
                    memory[base:base+len(code)] = code
                    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                    cpu.pc, cpu.sp = base + info['entry'], 0xd000
                    for _ in range(10):
                        if cpu.pc == 0xb000:
                            break
                        cpu.step()
                    else:
                        self.fail('conditional return did not exit')
                    self.assertEqual(cpu.a, expected)
                    self.assertEqual(cpu.sp, 0xd002)

    def test_no_labels_for_opaque_bytes_or_unknown_entry(self):
        for source in (
                'section text\nstart:\n db 0\n',
                'section text\nstart:\n nop\nstart:\n ret\n',
                'section text\nstart:\n nop\nsection data\n ret\n'):
            with self.subTest(source=source):
                with self.assertRaises(TypedCFGError):
                    inspect_typed_cfg_liveness(source)

    def test_byte_inc_dec_keep_input_carry_live(self):
        # INC and DEC preserve the incoming carry flag on a real Z80.
        # Treating F as write-only would erase a live condition dependency.
        for opcode in ('inc', 'dec'):
            for register in ('a', 'b', 'c', 'd', 'e', 'h', 'l'):
                with self.subTest(opcode=opcode, register=register):
                    read, written, modelled = _effects(opcode, register)
                    self.assertTrue(modelled)
                    self.assertEqual(read, frozenset((register, 'f', 'r')))
                    self.assertEqual(written, frozenset((register, 'f', 'r')))
        # 16-bit forms do not have the same flag behavior: keep them unknown.
        for opcode in ('inc', 'dec'):
            reads, writes, modelled = _effects(opcode, 'hl')
            self.assertFalse(modelled)
            self.assertIn('f', reads)
            self.assertIn('f', writes)

    def test_native_carry_survives_inc_dec_and_controls_a_branch(self):
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        for opcode, value, expected in (('inc', 255, 0), ('dec', 0, 255)):
            source = ('    section text\n    global start\nstart:\n'
                      '    scf\n'
                      f'    ld b,{value}\n'
                      f'    {opcode} b\n'
                      '    jr c,was_carried\n'
                      '    ld a,0\n'
                      '    ret\n'
                      'was_carried:\n'
                      '    ld a,1\n'
                      '    ret\n')
            obj = ras.assemble_text(source, 'carry-liveness.s')
            ssx, *_ = rld.link([rld.Obj(obj, 'carry-liveness.sso')], [],
                               entry='start', stack=384)
            info = rld.parse_ssx(ssx)
            audit = inspect_typed_cfg_liveness(source)
            self.assertTrue(audit['source_liveness_converged'])
            self.assertFalse(audit['rewrite_safe_to_admit'])
            for base in (0x7000, 0x8000, 0x9000):
                with self.subTest(opcode=opcode, base=base):
                    memory = bytearray(65536)
                    image = rld.relocate(info['image'], info['relocs'], base)
                    memory[base:base + len(image)] = image
                    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                    cpu.pc = base + info['entry']
                    cpu.sp = 0xd000
                    for _ in range(15):
                        if cpu.pc == 0xb000:
                            break
                        cpu.step()
                    else:
                        self.fail('native carry probe did not return')
                    self.assertEqual(cpu.a, 1)
                    self.assertEqual(cpu.b, expected)
                    self.assertEqual(int(cpu.f) & 1, 1)

    def test_fetch_refresh_is_live_even_for_nop_and_register_loads(self):
        # Every M1 fetch changes low R bits, observable via LD A,R. A purely
        # dataflow-driven NOP removal would otherwise lose this dependency.
        for opcode, operand, uses, writes in (
                ('nop', '', ('r',), ('r',)),
                ('ld', 'a,b', ('b', 'r'), ('a', 'r')),
                ('ld', 'a,7', ('r',), ('a', 'r')),
                ('inc', 'b', ('b', 'f', 'r'), ('b', 'f', 'r')),
                ('dec', 'b', ('b', 'f', 'r'), ('b', 'f', 'r'))):
            with self.subTest(opcode=opcode, operand=operand):
                use, define, known = _effects(opcode, operand)
                self.assertTrue(known)
                self.assertEqual(use, frozenset(uses))
                self.assertEqual(define, frozenset(writes))

    def test_native_refresh_read_detects_deleted_nop_at_three_bases(self):
        import ras
        import rld
        from z80_python.cpu import Z80CPU
        original = ('    section text\n    global start\nstart:\n'
                    '    nop\n    ld a,r\n    ret\n')
        changed = original.replace('    nop\n', '')
        def link(source):
            obj = ras.assemble_text(source, 'refresh-register.s')
            return rld.link([rld.Obj(obj, 'refresh-register.sso')], [],
                            entry='start', stack=384)[0]
        before, after = link(original), link(changed)
        self.assertNotEqual(before, after)
        audit = inspect_typed_cfg_liveness(original)
        self.assertTrue(audit['source_liveness_converged'])
        self.assertFalse(audit['rewrite_safe_to_admit'])
        for base in (0x7000, 0x8000, 0x9000):
            for initial_r in (0, 0x7e, 0xff):
                def execute(ssx):
                    info = rld.parse_ssx(ssx)
                    memory = bytearray(65536)
                    code = rld.relocate(info['image'], info['relocs'], base)
                    memory[base:base + len(code)] = code
                    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                    cpu.pc, cpu.sp, cpu.r = base + info['entry'], 0xd000, initial_r
                    for _ in range(8):
                        if cpu.pc == 0xb000:
                            break
                        cpu.step()
                    else:
                        self.fail('native refresh probe did not return')
                    return cpu.a, cpu.r
                with self.subTest(base=base, initial_r=initial_r):
                    original_a, original_r = execute(before)
                    changed_a, changed_r = execute(after)
                    self.assertEqual((original_a - changed_a) & 127, 1)
                    self.assertEqual((original_r - changed_r) & 127, 1)

    def test_backward_register_liveness_is_conservative(self):
        source = ('section text\nstart:\n'
                  '    ld a,2\n    ld a,3\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['register_effects_modelled'], 2)
        self.assertFalse(report['rewrite_safe_to_admit'])


if __name__ == '__main__':
    unittest.main()
