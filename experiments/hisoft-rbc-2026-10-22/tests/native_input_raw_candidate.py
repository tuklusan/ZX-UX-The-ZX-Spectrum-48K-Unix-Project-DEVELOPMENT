"""Test-only raw tty source INPUT witness. NOT the published RBC runtime.

All changes are made to independently witnessed pre-link assembler source.
The existing published SSX, sources, kernel and ROM are never edited.
The low-kernel ROM edit workspace is bounded and excess input is discarded.
Full Sinclair ROM INPUT equivalence is not established; do not release.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import ras
import rld

ROM_EDITOR_CALL = '    call 0x0f2c\n'
ROM_EDIT_SPACE_END = 0x5d98

# ZX-UX dev.asm _gtty=32, _stty=31; three-word tty buffer, mode at +4.
# Protect ROM editor workspace below LOWK=0x5d98, leaving two bytes spare.
# Overflow drops excess printable keys and *continues* until ENTER.
# Original ROM $1652 inserts one character into its own workspace.
EDITOR = '''rbc_raw_test_input:
    ld hl,($5c61)
    push hl
    ld hl,($5c5b)
    ld (rbc_raw_start),hl
    ld hl,0
    ld de,rbc_raw_tty
    ld a,32
    call $6003
    jp c,rbc_raw_abort
    ld a,(rbc_raw_tty+4)
    ld (rbc_raw_oldmode),a
    ld a,32
    ld (rbc_raw_tty+4),a
    ld hl,0
    ld de,rbc_raw_tty
    ld a,31
    call $6003
    jp c,rbc_raw_abort
rbc_raw_poll:
    ld hl,0
    ld de,($5c5b)
    ld bc,1
    ld a,3
    call $6003
    jp c,rbc_raw_restore_abort
    ld a,h
    or l
    jp z,rbc_raw_restore_abort
    ld hl,($5c5b)
    ld a,(hl)
    cp 13
    jp z,rbc_raw_done
    cp 12
    jp z,rbc_raw_delete
    cp 7
    jp z,rbc_raw_restore_abort
    cp 8
    jp c,rbc_raw_poll
    cp 128
    jp nc,rbc_raw_restore_abort
    push af
    ld hl,($5c65)
    ld bc,$5d96
    or a
    sbc hl,bc
    jp nc,rbc_raw_full
    ld hl,($5c5b)
    ld (hl),13
    call $1652
    pop af
    ld (de),a
    inc de
    ld ($5c5b),de
    jp rbc_raw_poll
rbc_raw_full:
    pop af
    jp rbc_raw_poll
rbc_raw_delete:
    ld hl,($5c5b)
    ld de,(rbc_raw_start)
    or a
    sbc hl,de
    jp z,rbc_raw_poll
    add hl,de
    dec hl
    ld (hl),13
    ld ($5c5b),hl
    jp rbc_raw_poll
rbc_raw_done:
    ld hl,($5c5b)
    ld (hl),13
    ld a,(rbc_raw_oldmode)
    ld (rbc_raw_tty+4),a
    ld hl,0
    ld de,rbc_raw_tty
    ld a,31
    call $6003
    jp c,rbc_raw_abort
    pop hl
    ld ($5c61),hl
    ret
rbc_raw_restore_abort:
    ld a,(rbc_raw_oldmode)
    ld (rbc_raw_tty+4),a
    ld hl,0
    ld de,rbc_raw_tty
    ld a,31
    call $6003
rbc_raw_abort:
    ld de,1
    jp rbc_wrapper_exit
'''
DATA = '''rbc_raw_tty:
    db 0,0,0,0,0,0
rbc_raw_oldmode:
    db 0
rbc_raw_start:
    dw 0
'''


def assemble_candidate(source: str, *, stack: int = 384):
    if (source.count(ROM_EDITOR_CALL) != 1 or
            source.count('    section data\n') != 1 or
            'rbc_wrapper_exit:' not in source or
            not any(line.startswith('original_rt_') and line.endswith(':')
                    for line in source.splitlines())):
        raise ValueError('source-owned ROM editor witness unavailable')
    amended = source.replace(ROM_EDITOR_CALL,
                             '    call rbc_raw_test_input\n', 1)
    amended = amended.replace('    section data\n',
                              EDITOR + '    section data\n' + DATA, 1)
    obj = ras.assemble_text(amended, 'raw-test-input-source.s')
    linked, bss, entry, labels, _ = rld.link(
        [rld.Obj(obj, 'raw-test-input-source.sso')], [],
        entry='start', stack=stack)
    parsed = rld.parse_ssx(linked)
    if (entry != 0 or parsed['entry'] != 0 or
            max(len(linked), len(parsed['image']) + bss + stack) > 14000 or
            not parsed['relocs']):
        raise ValueError('candidate fails relocation/loader bounds')
    for org in (0x8100, 0x9100, 0xa000):
        moved, moved_bss, moved_entry, _, _ = rld.link(
            [rld.Obj(obj, 'raw-test-input-source.sso')], [],
            entry='start', stack=stack, org=org)
        if (moved_bss != bss or moved_entry != entry or
                moved != rld.relocate(parsed['image'], parsed['relocs'], org)):
            raise ValueError('three-base relocations differ')
    return linked
