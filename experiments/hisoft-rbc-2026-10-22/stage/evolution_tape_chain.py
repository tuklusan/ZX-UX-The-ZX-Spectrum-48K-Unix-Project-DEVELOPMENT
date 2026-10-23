"""Compile the Evolution trilogy's next-tape LOAD through native cassette exec.

The original menu instructs the player to supply the next tape. On ZX-UX,
exec('/dev/cassette/NAME') invokes the kernel's resident tape loader; it
only succeeds with the appropriate tape actually supplied. It does not
fabricate the next game or swallow missing-media errors. Other LOAD, SAVE,
VERIFY and MERGE syntax remains blocked by the normal memory scanner.

The previous program must relinquish its screen before exec, following the
frozen SDK's documented syscall 11 wrapper. A failed exec regains the screen
and stops rather than pretending to have continued into the next stage.
"""
from __future__ import annotations

# The ZX-UX TZX loader searches 10-character internal tape names. These are
# the compiler-produced names of 45 and 46, not filesystem aliases.
_LOAD = 0xEF
_REM = 0xEA
_EXPECTED = {
    8060: {
        'step': '44-evolution-1', 'selection': b'4', 'next': '45-evoluti',
        'menu': 8010, 'menu_fragment': b'"4....Load stages 4&5."',
        'exit': 8070, 'exit_key': b'5',
    },
    1860: {
        'step': '45-evolution-2', 'selection': b'3', 'next': '46-evoluti',
        'menu': 1820, 'menu_fragment': b'"3...Load the 6th stage."',
        'exit': 1870, 'exit_key': b'4',
    },
}


def _code_tokens(body):
    quoted = False
    i = 0
    while i < len(body):
        c = body[i]
        if c == 14 and not quoted and i + 5 < len(body):
            i += 6
            continue
        if c == 34:
            quoted = not quoted
        elif not quoted and c == _REM:
            return
        elif not quoted:
            yield c
        i += 1


def stage_shape(lines):
    """Match the archived menu and the sole quoted-empty LOAD exactly."""
    lines = list(lines)
    rows = dict(lines)
    if len(rows) != len(lines):
        return None
    load_lines = [n for n, b in lines if _LOAD in _code_tokens(b)]
    if len(load_lines) != 1:
        return None
    line = load_lines[0]
    spec = _EXPECTED.get(line)
    if spec is None:
        return None
    expected_load = b'\xfa\xa6="' + spec['selection'] + b'"\xcb\xef""\r'
    expected_exit = b'\xfa\xa6="' + spec['exit_key'] + b'"\xcb\xe2\r'
    if rows[line] != expected_load or rows.get(spec['exit']) != expected_exit:
        return None
    if spec['menu_fragment'] not in rows.get(spec['menu'], b''):
        return None
    # Other tape operations remain blocked by the independent memory scanner.
    return {'line': line, 'next': spec['next'], 'stage': spec['step'],
            'cassette_path': '/dev/cassette/' + spec['next']}


def allow_native_evolution_load(lines, findings):
    match = stage_shape(lines)
    if match is None:
        return 0
    selected = [f for f in findings if f.operation == 'LOAD' and
                f.line == match['line'] and
                f.classification == 'tape_or_external_io' and
                f.severity == 'block']
    if len(selected) != 1 or any(f.operation == 'LOAD' and f not in selected for f in findings):
        return 0
    for f in selected:
        f.severity = 'info'
        f.classification = 'native_next_cassette_exec'
    return 1


def install(compiler):
    cls = compiler.Compiler
    if getattr(cls, '_zxux_evolution_load_installed', False):
        return
    old_reset = cls.reset
    old_layout = cls.layout_vars
    old_dispatch = cls.dispatch.fget

    def reset(self, program):
        old_reset(self, program)
        self._zxux_evolution_load = stage_shape(self.lines)
        self._zxux_evolution_path = 0

    def layout_vars(self):
        old_layout(self)
        if self._zxux_evolution_load:
            self._zxux_evolution_path = self.pc
            self.pc = (self.pc + len(self._zxux_evolution_load['cassette_path']) + 1) & 0xFFFF

    def st_load(self):
        match = self._zxux_evolution_load
        if match is None or self.line_no != match['line']:
            self.not_supported('LOAD outside Evolution stage transition')
        if self.get_char() != ord('"'):
            self.not_supported('LOAD filename or expression')
        self.next_char()
        if self.get_char() != ord('"'):
            self.not_supported('LOAD nonempty filename')
        self.next_char()
        if not self.at_end():
            self.not_supported('LOAD parameters')
        # The path belongs to this program's BSS; no protected-memory poke.
        self.ld_hl(self._zxux_evolution_path)
        for value in match['cassette_path'].encode('ascii') + b'\0':
            self.emit('ld (hl),{}; inc hl', value)
        # The previous program must release its screen before exec. On a
        # genuine kernel success this call does not return. No tape provided
        # -> the kernel loader handles its normal load error; syscall errors
        # restore the screen and end the failed transition.
        self.emit('ld hl,0; ld a,39; call $6003')
        self.ld_hl(self._zxux_evolution_path)
        self.emit('ld de,0; ld a,11; call $6003')
        self.emit('ld hl,1; ld a,39; call $6003')
        self.st_stop()

    def dispatch(self):
        table = old_dispatch(self)
        table[_LOAD] = self.st_load
        return table

    cls.reset = reset
    cls.layout_vars = layout_vars
    cls.st_load = st_load
    cls.dispatch = property(dispatch)
    cls._zxux_evolution_load_installed = True