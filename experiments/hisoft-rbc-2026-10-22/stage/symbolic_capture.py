"""Non-mutating audit of HiSoft's byte-producing paths.

Capture is diagnostic, not a symbolic backend. It records original assembly
and every numeric emission in the final compiler pass. Direct RAM patches,
rewinds and appended runtime routines are detected as unresolved boundaries;
they may not be silently presented to a whole-program optimizer as code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
import sys


@dataclass(frozen=True)
class Emission:
    position: int
    kind: str
    source: str
    data: bytes
    symbol_offset: int | None = None


@dataclass
class Capture:
    events: list[Emission] = field(default_factory=list)

    def record(self, compiler, position, kind, source, symbol_offset=None):
        if not compiler.storing:
            return
        if compiler.pc < position:
            raise ValueError('emitter wrapped 16-bit code address')
        self.events.append(Emission(position, kind, source,
                                    bytes(compiler.far[position:compiler.pc]), symbol_offset))

    def audit(self, image: bytes) -> dict:
        """Compare captured pre-encoding sites to actual image bytes.

        Holes are code not seen through the six documented emit methods;
        patched bytes are locations changed after their recorded emission.
        Neither category is safe to optimize without a symbolic producer.
        """
        last_writer = {}
        overlaps = set()
        out_of_image = []
        for event in self.events:
            for offset, value in enumerate(event.data):
                pos = event.position + offset
                if pos < 0 or pos >= len(image):
                    out_of_image.append(pos)
                    continue
                if pos in last_writer:
                    overlaps.add(pos)
                last_writer[pos] = (value, event.kind)
        uncovered = [i for i in range(len(image)) if i not in last_writer]
        patched = [i for i, actual in enumerate(image)
                   if i in last_writer and last_writer[i][0] != actual]
        direct_sites = {event.position + offset
                        for event in self.events if event.kind == 'direct-write'
                        for offset in range(len(event.data))
                        if event.position + offset < len(image)}
        categories = {}
        for _, kind in last_writer.values():
            categories[kind] = categories.get(kind, 0) + 1
        return {'image_bytes': len(image), 'captured_bytes': len(last_writer),
                'uncovered_bytes': len(uncovered), 'uncovered_first': uncovered[:16],
                'changed_after_emit': len(patched), 'patch_first': patched[:16],
                'rewritten_bytes': len(overlaps),
                'unresolved_direct_write_bytes': len(direct_sites),
                'out_of_image_emission_bytes': len(out_of_image),
                'out_of_image_first': out_of_image[:16],
                'byte_categories': categories,
                'safe_to_optimize': False,  # numeric addresses still need symbolization
                'complete_byte_trace': not uncovered and not patched and not out_of_image}



class TracedRAM(bytearray):
    """Observe HiSoft's direct stores at emission time, with exact byte offsets.

    The byte buffer still behaves as ordinary bytearray. Only 48K's staging
    machine can be wrapped: the 128K far-memory callback retains a separate
    closure pointer and must never be redirected here.
    """

    def __init__(self, initial, owner):
        super().__init__(initial)
        self._owner = owner

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        owner = self._owner
        if (getattr(owner, 'counting', True) or
                getattr(owner, 'de_flags', 0) & 1 or
                getattr(owner, '_zxux_capture_active', False) or
                getattr(owner, '_zxux_runtime_emitting', False) or
                getattr(owner, '_zxux_in_data', False)):
            return
        trace = getattr(owner, '_zxux_capture', None)
        if trace is None:
            return
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step != 1 or stop - start > 4096:
                raise ValueError('unresolved direct Z80 write slice')
            indices = list(range(start, stop))
        else:
            indices = [key if key >= 0 else len(self) + key]
        if not indices:
            return
        method = sys._getframe(1).f_code.co_name
        if indices != list(range(indices[0], indices[0] + len(indices))):
            raise ValueError('unresolved noncontiguous Z80 direct write')
        begin = indices[0]
        trace.events.append(Emission(begin, 'direct-write', method,
                                     bytes(self[begin:begin + len(indices)])))


def install(compiler_module):
    """Instrument the class without changing emission semantics or output."""
    cls = compiler_module.Compiler
    if getattr(cls, '_zxux_symbolic_capture_installed', False):
        return

    original_init = cls.__init__
    @wraps(original_init)
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        machine = getattr(self, 'm', None)
        if machine is not None and getattr(machine, 'p', {}).get('direct', False):
            # Replace BOTH aliases. The 48K runtime copies from its staging
            # buffer to m.far, and the HiSoft compiler uses self.far.
            traced = TracedRAM(self.far, self)
            machine.far = self.far = traced
    cls.__init__ = __init__

    original_reset = cls.reset
    @wraps(original_reset)
    def reset(self, *args, **kwargs):
        self._zxux_capture = Capture()
        if hasattr(self, 'm'):
            self.m._zxux_capture_owner = self
        return original_reset(self, *args, **kwargs)
    cls.reset = reset

    for method, kind in (
        ('emit', 'instruction'), ('emit_opcode', 'opcode'),
        ('emit_word_reloc', 'relocation'), ('emit_word', 'word'),
        ('emit_byte', 'byte'), ('emit_bytes', 'binary'),
    ):
        original = getattr(cls, method)
        def wrapping(fn, category, method_name):
            @wraps(fn)
            def call(self, *args, **kwargs):
                active = getattr(self, '_zxux_capture_active', 0)
                if active or not getattr(self, 'storing', False):
                    return fn(self, *args, **kwargs)
                start = self.pc
                self._zxux_capture_active = active + 1
                try:
                    value = fn(self, *args, **kwargs)
                finally:
                    self._zxux_capture_active = active
                capture = getattr(self, '_zxux_capture', None)
                if capture is None:
                    capture = Capture()
                    self._zxux_capture = capture
                symbol = args[0] if method_name == 'emit_word_reloc' else None
                source = (str(args[0]).format(*args[1:])
                          if method_name == 'emit' and args else
                          str(args[0]) if method_name == 'emit_opcode' and args
                          else str(args[:1]))
                capture.record(self, start, category, source, symbol)
                return value
            return call
        setattr(cls, method, wrapping(original, kind, method))
    # HiSoft stores DATA directly into its reserved data section, outside
    # emit_byte/emit_bytes. Capture the typed source DATA record at its actual
    # destination while the statement is being compiled, not by sweeping the
    # finished linked binary for bytes that happen to resemble instructions.
    if hasattr(cls, 'st_data'):
        original_data = cls.st_data
        @wraps(original_data)
        def st_data(self, *args, **kwargs):
            active = getattr(self, 'storing_data', False)
            start = getattr(self, 'data_size', 0)
            result = original_data(self, *args, **kwargs)
            end = getattr(self, 'data_size', 0)
            if active and end > start:
                begin = self.data_start + start
                finish = self.data_start + end
                capture = getattr(self, '_zxux_capture', None)
                if capture is None:
                    raise ValueError('DATA was emitted without a capture')
                capture.events.append(Emission(
                    begin, 'data-source', f'BASIC line {self.line_no} DATA',
                    bytes(self.far[begin:finish])))
            return result
        cls.st_data = st_data
    cls._zxux_symbolic_capture_installed = True

    # HiSoft runtime emitters execute in the Z80 model and copy bytes into
    # Machine.far without passing Compiler.emit(). Treat those bytes as an
    # opaque runtime section until their source becomes symbolic too.
    runtime = getattr(compiler_module, 'rtlib', None)
    machine_cls = getattr(runtime, 'Machine', None)
    if machine_cls is not None and not getattr(machine_cls, '_zxux_runtime_capture_installed', False):
        original_runtime = machine_cls.run_emitter
        @wraps(original_runtime)
        def run_emitter(self, n, pc, counting, code_base):
            owner = getattr(self, '_zxux_capture_owner', None)
            if owner is not None:
                owner._zxux_runtime_emitting = True
            try:
                end = original_runtime(self, n, pc, counting, code_base)
            finally:
                if owner is not None:
                    owner._zxux_runtime_emitting = False
            if owner is not None and not counting and not self.de_flags & 1:
                trace = getattr(owner, '_zxux_capture', None)
                if trace is not None:
                    trace.events.append(Emission(pc, 'runtime-opaque', f'RT{n}',
                                                 bytes(self.far[pc:end])))
            return end
        machine_cls.run_emitter = run_emitter
        machine_cls._zxux_runtime_capture_installed = True


def audit_result(compiler, result):
    """Read an actual linked compilation's HiSoft code, not a guessed image."""
    capture = getattr(compiler, '_zxux_capture', None)
    if capture is None or not result.ok:
        raise ValueError('capture missing or compilation failed')
    if result.mode != 'C':
        raise ValueError('the full compiled mode C image is required')
    return capture.audit(result.code)
