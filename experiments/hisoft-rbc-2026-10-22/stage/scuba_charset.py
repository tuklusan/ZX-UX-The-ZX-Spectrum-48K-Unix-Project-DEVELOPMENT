"""Map Scuba's verified custom font onto the RBC process-owned character area.

The original game copies 768 bytes from the 48K ROM, paints 13 characters,
and switches CHARS between ROM and its RAM copy. It executes no loaded code.
Only the exact archived program layout is accepted. Direct writes to global
system variables or the 60000-range are never admitted unchanged.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

# All entries are compared after token-aware decoding and space removal.
_ORIGINAL = {
    5: 'POKE23658,255',
    632: '''POKE23606,0:POKE23607,60:PRINTAT0,0;INVERSE1;"NOFISH!YOU'RETHESUPPER!"''',
    3000: 'POKE23606,0:POKE23607,60:',
    3270: 'POKE23606,96:POKE23607,235:RETURN',
    5000: 'RESTORE:FORK=0TO12:FORJ=0TO7:',
    5008: 'READA:POKE60256+(K+33)*8+J,A:NEXTJ:NEXTK',
    9000: 'BORDER0:PAPER0:CLS:INK4:IFPEEK60256=255THENGOTO9060',
    9020: 'FORX=256TO1023:POKE60000+X,PEEK(15104+X)',
    9040: 'NEXTX',
    5020: 'DATA0,0,221,63,220,7,0,0',
    5120: 'DATA0,0,29,255,4,4,4,0',
    5220: 'DATA0,0,187,252,59,224,0,0',
    5320: 'DATA0,0,184,255,32,32,32,0',
    5420: 'DATA0,0,76,126,124,64,0,0',
    5520: 'DATA0,0,50,126,62,2,0,0',
    5620: 'DATA0,140,190,255,190,128,0,0',
    5720: 'DATA0,140,191,254,191,128,0,0',
    5820: 'DATA0,49,125,255,125,1,0,0',
    5920: 'DATA0,49,253,127,253,1,0,0',
    6020: 'DATA88,88,124,60,60,40,40,40',
    6120: 'DATA26,26,62,60,60,20,20,20',
    6140: 'DATA60,124,60,60,255,255,60,60',
}
_ADAPTED = dict(_ORIGINAL)
_ADAPTED.update({
    632: '''PRINTAT0,0;INVERSE1;"NOFISH!YOU'RETHESUPPER!"''',
    3000: '',
    3270: 'RETURN',
    5008: 'READA:POKEUSR"A"-1024+(K+33)*8+J,A:NEXTJ:NEXTK',
    9000: 'BORDER0:PAPER0:CLS:INK4:IFPEEK(USR"A"-768)=255THENGOTO9060',
    9020: 'FORX=256TO1023:POKEUSR"A"-1024+X,PEEK(15104+X)',
})



def _visible(rows, tokens):
    return {n: re.sub(r'\s+', '', _line_text(body, tokens)).upper()
            for n, body in rows}


def _shape(rows, tokens, adapted):
    if len(dict(rows)) != len(rows):
        return False
    visible = _visible(rows, tokens)
    want = _ADAPTED if adapted else _ORIGINAL
    if any(visible.get(line) != text for line, text in want.items()):
        return False
    # Only the archived font and keyboard operations are accepted. The
    # 5000 loop writes 104 consecutive bytes; 9020 writes 768 font bytes.
    valid_pokes = {5, 632, 3000, 3270, 5008, 9020}
    if adapted:
        valid_pokes = {5, 5008, 9020}
    if {n for n, txt in visible.items() if 'POKE' in txt} != valid_pokes:
        return False
    if {n for n, txt in visible.items() if 'PEEK' in txt} != {9000, 9020}:
        return False
    if any(re.search(r'(?:GOTO|GOSUB)(?:5008|9020)\b', txt)
           for txt in visible.values()):
        return False
    if any(re.search(r'\b(?:LET|INPUT|READ)\s*[KJX]\s*=', txt)
           for n, txt in visible.items() if n not in (5000, 9020)):
        # No external address changes inside the verified loop bodies.
        return False
    return True


def adapt_scuba_charset(program, kw, fp, source, tap):
    rows = list(tap.split_lines(program))
    if not _shape(rows, kw.TOKEN, False):
        return program, []
    originals = dict(rows)
    def make(body):
        return source.hide_numbers(source.tokenize_line(body, kw), fp) + b'\r'
    changes = {
        632: originals[632].split(b':', 2)[2],
        3000: bytes((kw.CODE_FOR['REM'], 13)),
        3270: bytes((kw.CODE_FOR['RETURN'], 13)),
        5008: make('READ A:POKE USR "a"-1024+(K+33)*8+J,A:NEXT J:NEXT K'),
        9000: make('BORDER 0:PAPER 0:CLS:INK 4:IF PEEK (USR "a"-768)=255 THEN GO TO 9060'),
        9020: make('FOR X=256 TO 1023:POKE USR "a"-1024+X,PEEK (15104+X)'),
    }
    updated = [(n, changes.get(n, body)) for n, body in rows]
    if not _shape(updated, kw.TOKEN, True):
        return program, []
    return tap.join_lines(updated), [{'private_rom_font': True,
        'switch_lines': [632, 3000, 3270],
        'private_character_writes': [5008, 9020],
        'original_basic_unchanged': True}]


def allow_scuba_font_access(lines, tokens, findings):
    """Approve only the three remaining bounded reads/writes, together."""
    if not _shape(list(lines), tokens, True):
        return 0
    eligible = [f for f in findings if f.severity == 'block'
                and ((f.operation == 'POKE' and f.line in (5008, 9020))
                     or (f.operation == 'PEEK' and f.line == 9000))]
    if len(eligible) != 3 or {f.line for f in eligible} != {5008, 9000, 9020}:
        return 0
    expected = {
        5008: ('POKE', r'USR\s*"a"\s*-\s*1024\s*\+\s*\(\s*K\s*\+\s*33\s*\)\s*\*\s*8\s*\+\s*J\s*,\s*A'),
        9000: ('PEEK', r'\(\s*USR\s*"a"\s*-\s*768\s*\)'),
        9020: ('POKE', r'USR\s*"a"\s*-\s*1024\s*\+\s*X\s*,'),
    }
    if any(f.operation != expected[f.line][0]
           or not re.match(expected[f.line][1], f.expression, re.I)
           for f in eligible):
        return 0
    for f in eligible:
        f.severity = 'info'
        f.classification = 'bounded_private_charset_access'
    return 3


def install(compiler):
    cls = compiler.Compiler
    if getattr(cls, '_zxux_scuba_font_installed', False):
        return
    original_reset = cls.reset
    original_entry = cls.entry_point_line
    def reset(self, program):
        original_reset(self, program)
        import source
        self._zxux_scuba_charset = _shape(self.lines, source.Keywords(self.rom).TOKEN, True)
    def entry_point_line(self):
        original_entry(self)
        if not getattr(self, '_zxux_scuba_charset', False) or self.pass0:
            return
        if self.line_no in (632, 3000):
            # Restore ROM CHARS for headings and the shark end screen.
            self.emit('ld hl,$3C00; ld ($5C36),hl')
        elif self.line_no == 3270:
            # The RBC-owned font precedes RBC's process UDG by 768 bytes.
            # CHARS points 256 bytes before the first printable bitmap.
            self.emit('ld hl,($5C7B); ld de,1024; or a; sbc hl,de; ld ($5C36),hl')
    cls.reset = reset
    cls.entry_point_line = entry_point_line
    cls._zxux_scuba_font_installed = True


def rom_font(rom):
    """Return the genuine 48K printable font for this verified Scuba build."""
    if len(rom) != 16384:
        raise ValueError('expected a 16 KB Spectrum ROM')
    return rom[0x3D00:0x4000]
