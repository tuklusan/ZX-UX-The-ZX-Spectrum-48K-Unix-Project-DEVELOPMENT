"""Non-mutating audit of HiSoft's byte-producing paths.

Capture is diagnostic, not a symbolic backend. It records original assembly
and every numeric emission in the final compiler pass. Direct RAM patches,
rewinds and appended runtime routines are detected as unresolved boundaries;
they may not be silently presented to a whole-program optimizer as code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps


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
        for event in self.events:
            for offset, value in enumerate(event.data):
                pos = event.position + offset
                if pos >= len(image):
                    continue
                if pos in last_writer:
                    overlaps.add(pos)
                last_writer[pos] = (value, event.kind)
        uncovered = [i for i in range(len(image)) if i not in last_writer]
        patched = [i for i, actual in enumerate(image)
                   if i in last_writer and last_writer[i][0] != actual]
        categories = {}
        for _, kind in last_writer.values():
            categories[kind] = categories.get(kind, 0) + 1
        return {'image_bytes': len(image), 'captured_bytes': len(last_writer),
                'uncovered_bytes': len(uncovered), 'uncovered_first': uncovered[:16],
                'changed_after_emit': len(patched), 'patch_first': patched[:16],
                'rewritten_bytes': len(overlaps),
                'byte_categories': categories,
                'safe_to_optimize': False,  # numeric addresses still need symbolization
                'complete_byte_trace': not uncovered and not patched}


def install(compiler_module):
    """Instrument the class without changing emission semantics or output."""
    cls = compiler_module.Compiler
    if getattr(cls, '_zxux_symbolic_capture_installed', False):
        return

    original_reset = cls.reset
    @wraps(original_reset)
    def reset(self, *args, **kwargs):
        self._zxux_capture = Capture()
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
                          if method_name == 'emit' and args else str(args[:1]))
                capture.record(self, start, category, source, symbol)
                return value
            return call
        setattr(cls, method, wrapping(original, kind, method))
    cls._zxux_symbolic_capture_installed = True


def audit_result(compiler, result):
    """Read an actual linked compilation's HiSoft code, not a guessed image."""
    capture = getattr(compiler, '_zxux_capture', None)
    if capture is None or not result.ok:
        raise ValueError('capture missing or compilation failed')
    if result.mode != 'C':
        raise ValueError('the full compiled mode C image is required')
    return capture.audit(result.code)
