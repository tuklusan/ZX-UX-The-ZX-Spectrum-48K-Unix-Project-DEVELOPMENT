"""Enable the upstream HiSoft computed-line lookup on demand."""


def compiler_with_computed_lines(base):
    """Use the same flags set by HiSoft's REM : GOSUB : directive.

    Some original listings begin at line 1, leaving no room for two
    separate directives before the first statement. Keep every original
    line and delegate line search, code emission and line-table layout
    entirely to the upstream compiler.
    """
    class ComputedLines(base):
        def reset(self, program):
            super().reset(program)
            self.goto_directive = 1
            self.gosub_all = 1

    return ComputedLines
