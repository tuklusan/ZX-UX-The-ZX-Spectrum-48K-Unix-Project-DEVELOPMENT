"""Bounded ZX-UX tty INPUT source emission from a witnessed ROM EDITOR call.

This bridge is limited to line input and deliberately refuses unsupported
source layouts. It does not claim the full 48K ROM editor control-key behavior.
All relocation witnesses are made on the real, pre-link Z80 object.
"""
from __future__ import annotations

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

import ras
import rld


def assemble_input_source(original: str, *, stack: int, maximum: int):
    """Replace a known original source call, never linked machine-code bytes."""
    if (not isinstance(original, str) or not original.isascii() or
            original.count(ROM_EDITOR_CALL) != 1 or
            original.count('    section data\n') != 1 or
            'rbc_wrapper_exit:' not in original or
            not any(s.startswith('original_rt_') and s.endswith(':')
                    for s in original.splitlines()) or
            'rbc_raw_test_input:' in original or 'rbc_raw_tty:' in original):
        raise ValueError('ZX-UX INPUT source call not independently witnessed')
    if not (isinstance(stack, int) and 0 < stack <= 65535 and
            isinstance(maximum, int) and maximum >= 0):
        raise ValueError('invalid INPUT source memory bounds')
    text = original.replace(ROM_EDITOR_CALL, '    call rbc_raw_test_input\n', 1)
    text = text.replace('    section data\n', EDITOR + '    section data\n' + DATA, 1)
    obj = ras.assemble_text(text, 'rbc-zxux-input.s')
    linked, bss, entry, _, _ = rld.link(
        [rld.Obj(obj, 'rbc-zxux-input.sso')], [], entry='start', stack=stack)
    image = rld.parse_ssx(linked)
    total = len(image['image']) + image['bss'] + image['stack']
    if entry or image['entry'] or image['bss'] != bss or image['stack'] != stack:
        raise ValueError('ZX-UX INPUT entry/BSS/stack mismatch')
    if maximum and max(total, len(linked)) > maximum:
        raise ValueError('ZX-UX INPUT memory limit exceeded: '
                         f'file={len(linked)}, image={len(image["image"])}, '
                         f'bss={bss}, stack={stack}, total={total}, max={maximum}')
    # Even --max overrides cannot force an image past the unchanged loader.
    if max(total, len(linked)) > 14000:
        raise ValueError('ZX-UX INPUT cannot fit the 14,000-byte loader')
    if not image['relocs']:
        raise ValueError('ZX-UX INPUT has no verified native relocations')
    for org in (0x8100, 0x9100, 0xa000):
        moved, moved_bss, moved_entry, _, _ = rld.link(
            [rld.Obj(obj, 'rbc-zxux-input.sso')], [], entry='start',
            stack=stack, org=org)
        if (moved_bss != bss or moved_entry != entry or
                moved != rld.relocate(image['image'], image['relocs'], org)):
            raise ValueError(f'ZX-UX INPUT three-base relocation failed at {org:#06x}')
    return text, obj, linked
