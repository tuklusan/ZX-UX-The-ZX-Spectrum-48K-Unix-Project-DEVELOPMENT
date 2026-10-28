"""Non-mutating audit of HiSoft's byte-producing paths.

Capture is diagnostic, not a symbolic backend. It records original assembly
and every numeric emission in the final compiler pass. Direct RAM patches,
rewinds and appended runtime routines are detected as unresolved boundaries;
they may not be silently presented to a whole-program optimizer as code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
from runtime_emitter_trace import RuntimeEmitterTrace
import sys


@dataclass(frozen=True)
class Emission:
    position: int
    kind: str
    source: str
    data: bytes
    symbol_offset: int | None = None
    source_site: str | None = None
    producer_pcs: tuple[int, ...] | None = None


@dataclass
class Capture:
    events: list[Emission] = field(default_factory=list)
    runtime_traces: list[dict] = field(default_factory=list)

    def record(self, compiler, position, kind, source, symbol_offset=None, source_site=None):
        if not compiler.storing:
            return
        if compiler.pc < position:
            raise ValueError('emitter wrapped 16-bit code address')
        self.events.append(Emission(position, kind, source,
                                    bytes(compiler.far[position:compiler.pc]), symbol_offset, source_site))

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
                'runtime_emitter_traces': len(self.runtime_traces),
                'runtime_trace_covered_bytes': sum(r['covered_bytes'] for r in self.runtime_traces),
                'runtime_trace_uncovered_bytes': sum(r['uncovered_bytes'] for r in self.runtime_traces),
                'runtime_trace_untraced_pc_writes': sum(r['untraced_pc_writes'] for r in self.runtime_traces),
                'runtime_trace_changed_bytes': sum(r['changed_after_write'] for r in self.runtime_traces),
                'runtime_trace_outside_bytes': sum(r['outside_emitter_bytes'] for r in self.runtime_traces),
                'runtime_trace_source_pc_count': sum(r['source_pc_count'] for r in self.runtime_traces),
                'runtime_traces_complete': all(r['fully_observed'] for r in self.runtime_traces),
                'runtime_typed_calculated_bytes': sum(
                    r.get('typed_calculated_bytes', 0) for r in self.runtime_traces),
                'runtime_untyped_calculated_bytes': sum(
                    r.get('untyped_calculated_bytes', 0) for r in self.runtime_traces),
                'runtime_typed_source_events': sum(r.get('typed_source_events', 0) for r in self.runtime_traces),
                'safe_to_optimize': False,  # numeric addresses still need symbolization
                'complete_byte_trace': (not uncovered and not patched and not out_of_image and
                                        all(r['fully_observed'] for r in self.runtime_traces))}



class TracedRAM(bytearray):
    """Observe HiSoft's direct stores at emission time, with exact byte offsets.

    The byte buffer still behaves as ordinary bytearray. Only 48K's staging
    machine can be wrapped: the 128K far-memory callback retains a separate
    closure pointer and must never be redirected here.
    """

    def __init__(self, initial, owner):
        super().__init__(initial)
        self._owner = owner

    def _reject_untraced_mutation(self):
        """No bytearray mutator may bypass typed emission in the storing pass."""
        owner = self._owner
        if (not (getattr(owner, 'counting', True) or
                 getattr(owner, 'de_flags', 0) & 1 or
                 getattr(owner, '_zxux_capture_active', False) or
                 getattr(owner, '_zxux_runtime_emitting', False)) and
                getattr(owner, '_zxux_capture', None) is not None):
            raise ValueError('unresolved untraced Z80 RAM mutation')

    def __delitem__(self, key):
        self._reject_untraced_mutation()
        return super().__delitem__(key)

    def append(self, value):
        self._reject_untraced_mutation()
        return super().append(value)

    def extend(self, values):
        self._reject_untraced_mutation()
        return super().extend(values)

    def insert(self, index, value):
        self._reject_untraced_mutation()
        return super().insert(index, value)

    def pop(self, index=-1):
        self._reject_untraced_mutation()
        return super().pop(index)

    def remove(self, value):
        self._reject_untraced_mutation()
        return super().remove(value)

    def clear(self):
        self._reject_untraced_mutation()
        return super().clear()

    def reverse(self):
        self._reject_untraced_mutation()
        return super().reverse()

    def __iadd__(self, values):
        self._reject_untraced_mutation()
        return super().__iadd__(values)

    def __imul__(self, times):
        self._reject_untraced_mutation()
        return super().__imul__(times)

    def __setitem__(self, key, value):
        owner = self._owner
        tracing = (not (getattr(owner, 'counting', True) or
                        getattr(owner, 'de_flags', 0) & 1 or
                        getattr(owner, '_zxux_capture_active', False) or
                        getattr(owner, '_zxux_runtime_emitting', False)) and
                   getattr(owner, '_zxux_capture', None) is not None)
        if tracing and isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            # A reversed, unit-step slice denotes an empty insertion point.
            # Replacing it with empty bytes is not a resize or a write.
            width = max(0, stop - start)
            if step != 1 or width > 4096:
                raise ValueError('unresolved direct Z80 write slice')
            if not hasattr(value, '__len__') or len(value) != width:
                raise ValueError('unresolved resizing Z80 direct write')
        super().__setitem__(key, value)
        if (getattr(owner, 'counting', True) or
                getattr(owner, 'de_flags', 0) & 1 or
                getattr(owner, '_zxux_capture_active', False) or
                getattr(owner, '_zxux_runtime_emitting', False)):
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
        # Only HiSoft's DATA producers own the current forward-growing field.
        # A nested patch or a write to an earlier field is a separate event
        # even while the enclosing DATA statement is active. A DATA-source
        # event may not hide writes made by other compiler paths.
        if (method in ('st_data', 'data_string') and
                getattr(owner, '_zxux_in_data', False)):
            lo = getattr(owner, 'data_start', None)
            hi = getattr(owner, 'vars_start', None)
            cursor = getattr(owner, 'data_size', None)
            if (getattr(owner, 'storing_data', False) and
                    type(lo) is int and type(hi) is int and
                    type(cursor) is int and 0 <= cursor <= hi - lo and
                    all(lo + cursor <= index < hi for index in indices)):
                return
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
                caller = sys._getframe(1)
                source_site = f'{caller.f_code.co_name}:{caller.f_lineno}'
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
                capture.record(self, start, category, source, symbol, source_site)
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
            old_in_data = getattr(self, '_zxux_in_data', False)
            self._zxux_in_data = True
            try:
                result = original_data(self, *args, **kwargs)
            finally:
                self._zxux_in_data = old_in_data
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
    # The original DEF FN compiler advances PC over private parameter slots
    # without invoking any byte emitter. The original `unwritten` producer
    # identifies exact spans; capture their existing contents at that source
    # call, rather than inferring holes from a linked binary. These remain
    # protected data, never code eligible for optimizer rewrites.
    if hasattr(cls, 'st_deffn'):
        original_deffn = cls.st_deffn
        @wraps(original_deffn)
        def st_deffn(self, *args, **kwargs):
            old = tuple(getattr(self, 'unwritten', ()))
            result = original_deffn(self, *args, **kwargs)
            if getattr(self, 'storing', False):
                new = tuple(getattr(self, 'unwritten', ()))
                if new[:len(old)] != old:
                    raise ValueError('DEF FN reservation history changed')
                for pos, size in new[len(old):]:
                    if (type(pos) is not int or type(size) is not int or
                            size not in (2, 5) or pos < 0 or
                            pos + size > len(self.far)):
                        raise ValueError('DEF FN reservation has untyped bounds')
                    data = bytes(self.far[pos:pos + size])
                    self._zxux_capture.events.append(Emission(
                        pos, 'inline-data', 'protected:def-fn-param', data,
                        source_site='st_deffn:unwritten'))
            return result
        cls.st_deffn = st_deffn
    cls._zxux_symbolic_capture_installed = True

    # Source declarations are provided separately from runtime output. An
    # emitter without a source provider stays opaque; matching bytes alone
    # never make it a typed instruction stream.
    runtime = getattr(compiler_module, 'rtlib', None)
    machine_cls = getattr(runtime, 'Machine', None)
    if machine_cls is not None and not getattr(machine_cls, '_zxux_runtime_capture_installed', False):
        original_runtime = machine_cls.run_emitter
        @wraps(original_runtime)
        def run_emitter(self, n, pc, counting, code_base):
            owner = getattr(self, '_zxux_capture_owner', None)
            tracing = (owner is not None and not counting and not self.de_flags & 1
                       and getattr(self, 'p', {}).get('direct', False))
            if owner is not None:
                owner._zxux_runtime_emitting = True
            try:
                if tracing:
                    with RuntimeEmitterTrace(self, code_base=code_base) as source_trace:
                        end = original_runtime(self, n, pc, counting, code_base)
                else:
                    end = original_runtime(self, n, pc, counting, code_base)
            finally:
                if owner is not None:
                    owner._zxux_runtime_emitting = False
            if owner is not None and not counting and not self.de_flags & 1:
                trace = getattr(owner, '_zxux_capture', None)
                if trace is not None:
                    source_events = None
                    if tracing:
                        report = source_trace.inspect(pc, end, bytes(self.far[pc:end]))
                        report['routine'] = n
                        provider = getattr(self, '_zxux_typed_runtime_source', None)
                        if provider is not None:
                            if not report['fully_observed']:
                                raise ValueError('typed runtime needs complete original writer trace')
                            if not callable(provider):
                                raise ValueError('runtime source provider must be callable')
                            # The provider supplies independently reviewed original
                            # statements and an assembler, not a decoded result.
                            statements, assembler = provider(n, pc, end, code_base)
                            from runtime_typed_source import typed_runtime_events
                            source_events = typed_runtime_events(
                                source_trace.writes, statements,
                                bytes(self.far[pc:end]), pc, end, code_base,
                                assembler)
                            report['typed_instructions'] = True
                            report['typed_source_events'] = len(source_events)
                        trace.runtime_traces.append(report)
                    elif getattr(self, '_zxux_typed_runtime_source', None) is not None:
                        raise ValueError('typed runtime source requires 48K write tracing')
                    if source_events is None:
                        trace.events.append(Emission(pc, 'runtime-opaque', f'RT{n}',
                                                     bytes(self.far[pc:end])))
                    else:
                        trace.events.extend(source_events)
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
