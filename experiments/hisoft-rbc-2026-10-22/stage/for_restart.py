"""Allow BASIC FOR to replace the previous frame for the same control letter.

Sinclair BASIC replaces the control state for a repeated FOR name. HiSoft
rejects such a reuse while the earlier FOR still appears active to its
source-order analyzer. The compiler already has one descriptor per letter,
so clearing the compile-only active bit lets the replacement FOR overwrite
that descriptor, including its limit, step, and restart address. It never
changes the generated code for the earlier FOR statement.
"""


def install(compiler):
    base = compiler.Compiler
    original = base.st_for
    if getattr(original, '_zxux_restart_for', False):
        return

    def st_for(self):
        char = self.get_char()
        entry = self.fors[compiler.letter(char)]
        if entry['flags'] & 0x80:
            entry['flags'] &= 0x7F
        return original(self)

    st_for._zxux_restart_for = True
    base.st_for = st_for