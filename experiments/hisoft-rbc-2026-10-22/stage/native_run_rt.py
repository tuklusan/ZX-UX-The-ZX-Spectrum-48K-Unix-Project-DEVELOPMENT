"""Compile a bare Sinclair RUN as a native restart in the same process.

The restart restores the starting stack, clears numeric and string variable
storage, resets DATA/READ and jumps to the first original BASIC line. A
separate two-byte stack slot survives clearing. This changes generated code
only when a RUN token occurs outside quoted text and comments.
"""

_RUN = 0xF7
_REM = 0xEA


def _uses_run(lines):
    for _, body in lines:
        quoted = False
        pos = 0
        while pos < len(body):
            char = body[pos]
            if char == 14 and not quoted and pos + 5 < len(body):
                pos += 6
                continue
            if char == 34:
                quoted = not quoted
            elif not quoted and char == _REM:
                break
            elif not quoted and char == _RUN:
                return True
            pos += 1
    return False

def _run_entry(lines, requested):
    """Sinclair's next-existing-line behavior for a constant RUN target."""
    if not isinstance(requested, int) or requested < 0 or requested >= 0x4000:
        return None
    return next((number for number, _ in lines if number > 0 and number >= requested), None)


def install(compiler):
    cls = compiler.Compiler
    if getattr(cls, '_zxux_has_native_run', False):
        return
    initial_reset = cls.reset
    initial_layout = cls.layout_vars
    initial_entry = cls.entry_point_line
    initial_dispatch = cls.dispatch.fget

    def reset(self, program):
        initial_reset(self, program)
        self._zxux_run_present = _uses_run(self.lines)
        self._zxux_run_first = next((n for n, _ in self.lines if n > 0), 0)
        self._zxux_run_sp = 0
        self._zxux_run_clear_bytes = 1

    def layout_vars(self):
        initial_layout(self)
        if not self._zxux_run_present:
            return
        # Preserve system-variable BSS when RUN clears BASIC variables.
        # The sysvar helper allocates its own process region after user vars.
        sysvar_base = getattr(self, '_zxux_sysvar_base', 0)
        user_end = sysvar_base if sysvar_base and sysvar_base >= self.vars_start else self.pc
        user_size = (user_end - self.vars_start) & 0xffff
        if not user_size:
            # MEM_FILL uses BC=size-1, so keep a single-byte scratch area.
            self.pc = (self.pc + 1) & 0xffff
            user_size = 1
        self._zxux_run_clear_bytes = user_size
        self._zxux_run_sp = self.pc
        self.pc = (self.pc + 2) & 0xffff

    def entry_point_line(self):
        if (self._zxux_run_present and not self.pass0
                and self.line_no == self._zxux_run_first):
            # Z80 ED73 stores SP without disturbing flags or registers.
            self.emit_op_reloc('ld (nn),sp', self._zxux_run_sp)
        return initial_entry(self)

    def st_run(self):
        if not self._zxux_run_present or not self._zxux_run_first:
            self.not_supported('RUN entry')
        if self.at_end():
            requested = self._zxux_run_first
        else:
            # The existing HiSoft parser reads the hidden numeric constant.
            computed, requested = self.goto_target()
            if computed:
                self.not_supported('computed RUN line')
        target = _run_entry(self.lines, requested)
        if target is None:
            self.not_supported('RUN line outside listing')
        # Z80 ED7B restores the caller's stack even after nested GO SUB.
        self.emit_op_reloc('ld sp,(nn)', self._zxux_run_sp)
        self.ld_hl(self.vars_start)
        self.ld_bc_abs((self._zxux_run_clear_bytes - 1) & 0xffff)
        self.emit('ld a,0')
        self.call_rt(compiler.RT.MEM_FILL)
        self.emit_restore()
        self.emit_goto('jp nn', target)

    def dispatch(self):
        result = initial_dispatch(self)
        result[_RUN] = self.st_run
        return result

    cls.reset = reset
    cls.layout_vars = layout_vars
    cls.entry_point_line = entry_point_line
    cls.st_run = st_run
    cls.dispatch = property(dispatch)
    cls._zxux_has_native_run = True
