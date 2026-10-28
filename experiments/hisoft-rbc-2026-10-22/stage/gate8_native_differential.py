"""Bounded native comparison for linked Z80 programs.

A completed probe checks full CPU state, T-states, process memory writes and
port output at independently relocated process bases. ROM, device input,
interrupts and nonterminating code require separate native execution gates.
"""
from __future__ import annotations

import rld
from z80_python.cpu import Z80CPU


class NativeProbeBlocked(ValueError):
    """The finite native probe cannot establish a comparable exit."""


def _run(payload: bytes, base: int, flags: int, limit: int) -> tuple:
    try:
        parsed = rld.parse_ssx(payload)
    except (rld.LinkError, ValueError, TypeError, KeyError) as exc:
        raise NativeProbeBlocked('invalid native input') from exc
    first, last = base, base + len(parsed['image'])
    # The loader reserves the image, zero-initialized BSS and stack together.
    # Checking only executable bytes admits impossible process layouts.
    process_end = last + parsed['bss'] + parsed['stack']
    if first < 0x6000 or process_end > 0xa000 or not parsed['image']:
        raise NativeProbeBlocked('native image/BSS/stack outside bounded process area')
    try:
        image = rld.relocate(parsed['image'], parsed['relocs'], base)
    except (rld.LinkError, ValueError, OverflowError) as exc:
        raise NativeProbeBlocked('invalid native relocation') from exc
    memory = bytearray(65536)
    memory[first:last] = image
    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
    writes = []
    ports = []

    def read_byte(address: int) -> int:
        # A zero-filled probe buffer is not the original 48K ROM. Refuse
        # ROM reads rather than claiming equivalence for invented contents.
        if not 0x4000 <= address <= 0xffff:
            raise NativeProbeBlocked('native execution read unmodelled ROM')
        return memory[address]

    def write_byte(address: int, value: int) -> None:
        if not 0x4000 <= address <= 0xffff:
            raise NativeProbeBlocked('native execution attempted ROM write')
        writes.append((address, value))
        memory[address] = value

    def read_port(_address: int) -> int:
        raise NativeProbeBlocked('external device input is not modelled')

    def write_port(address: int, value: int) -> None:
        ports.append((address, value))

    cpu = Z80CPU(read_byte, write_byte, read_port=read_port,
                 write_port=write_port)
    cpu.pc = first + parsed['entry']
    cpu.sp = 0xd000
    cpu.f = flags
    cycles = 0
    returned = False
    for _ in range(limit):
        if cpu.pc == 0xb000:
            if cpu.sp != 0xd002 or not returned:
                raise NativeProbeBlocked('process did not return through caller stack')
            return cpu.capture_state(), cycles, tuple(writes), tuple(ports)
        if not first <= cpu.pc < last:
            raise NativeProbeBlocked('execution escaped the native code image')
        # An arbitrary JP with SP set to its final value is not a return.
        # Observe the opcode and original stack word before stepping so a
        # forged jump to the caller address cannot pass the exit gate.
        opcode = memory[cpu.pc]
        stack = cpu.sp
        return_word = memory[stack] | memory[(stack + 1) & 0xffff] << 8
        is_return = opcode == 0xc9 or opcode & 0xc7 == 0xc0
        if opcode == 0xed and memory[(cpu.pc + 1) & 0xffff] in (0x45, 0x4d):
            is_return = True
        try:
            cycles += cpu.step()
        except (NotImplementedError, IndexError) as exc:
            raise NativeProbeBlocked('native instruction not supported by probe') from exc
        # The probe uses a separate caller sentinel at 0xD000. The SSX
        # declared stack is the maximum space below that sentinel; a program
        # cannot borrow extra bytes and then hide an overflow by popping.
        # RET through the caller sentinel may advance SP by two bytes.
        if not 0xd000 - parsed['stack'] <= cpu.sp <= 0xd002:
            raise NativeProbeBlocked('native execution exceeded declared stack')
        returned = (cpu.pc == 0xb000 and is_return and
                    stack == 0xd000 and return_word == 0xb000 and
                    cpu.sp == 0xd002)
    if returned:
        return cpu.capture_state(), cycles, tuple(writes), tuple(ports)
    raise NativeProbeBlocked('bounded native execution did not return')


def compare_native_probes(plain: bytes, candidate: bytes, *,
                          bases=(0x6000, 0x7000, 0x8000),
                          flags=(0, 1, 0x40, 0xff),
                          limit=512) -> dict:
    """Contrast bounded deterministic exits without approving publication."""
    if (not isinstance(plain, bytes) or not isinstance(candidate, bytes)
            or type(limit) is not int or not 1 <= limit <= 100000
            # One-shot iterators can be empty or silently exhaust after the
            # first base, reporting a match without a complete probe matrix.
            or type(bases) not in (tuple, list)
            or type(flags) not in (tuple, list)
            or not bases or not flags):
        raise NativeProbeBlocked('invalid bounded native probe parameters')
    checked = 0
    mismatches = []
    for base in bases:
        if type(base) is not int:
            raise NativeProbeBlocked('invalid native process base')
        for initial_flags in flags:
            if type(initial_flags) is not int or not 0 <= initial_flags <= 255:
                raise NativeProbeBlocked('invalid initial Z80 flags')
            before = _run(plain, base, initial_flags, limit)
            after = _run(candidate, base, initial_flags, limit)
            checked += 1
            if before != after:
                changed = tuple(name for name, a, b in zip(
                    ('processor_state', 't_states', 'memory_writes', 'port_writes'),
                    before, after) if a != b)
                mismatches.append({'base': base, 'flags': initial_flags,
                                   'changed': changed})
    return {'checked_exits': checked,
            'bounded_exit_states_match': not mismatches,
            'first_mismatches': mismatches[:5],
            'native_behavior_verified': False,
            'whole_program_optimized': False}
