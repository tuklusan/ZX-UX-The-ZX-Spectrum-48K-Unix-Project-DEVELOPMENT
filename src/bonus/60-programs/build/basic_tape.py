#!/usr/bin/env python3
"""Portable, standard-library ZX Spectrum 48K BASIC and tape tools.

Independent implementation of the Sinclair tape and BASIC formats.
Design/reference: BAS2TAP 2.6, Martijn van der Heide (1998-2013),
https://github.com/tuklusan/bas2tap (GPL-2.0-or-later upstream).
Does not copy BAS2TAP's source, and does not implement its full syntax checker.
Original tape byte streams must remain primary when exact runtime fidelity matters.
"""
from __future__ import annotations
import math
import re
import struct

# 48K ROM token byte values. 128K-only SPECTRUM/PLAY are deliberately excluded.
WORDS = '''RND|INKEY$|PI|FN|POINT|SCREEN$|ATTR|AT|TAB|VAL$|CODE|VAL|LEN|SIN|COS|TAN|ASN|ACS|ATN|LN|EXP|INT|SQR|SGN|ABS|PEEK|IN|USR|STR$|CHR$|NOT|BIN|OR|AND|<=|>=|<>|LINE|THEN|TO|STEP|DEF FN|CAT|FORMAT|MOVE|ERASE|OPEN #|CLOSE #|MERGE|VERIFY|BEEP|CIRCLE|INK|PAPER|FLASH|BRIGHT|INVERSE|OVER|OUT|LPRINT|LLIST|STOP|READ|DATA|RESTORE|NEW|BORDER|CONTINUE|DIM|REM|FOR|GO TO|GO SUB|INPUT|LOAD|LIST|LET|PAUSE|NEXT|POKE|PRINT|PLOT|RUN|SAVE|RANDOMIZE|IF|CLS|DRAW|CLEAR|RETURN|COPY'''.split('|')
TOKENS = dict(enumerate(WORDS, 165))
assert TOKENS[234] == 'REM' and TOKENS[245] == 'PRINT' and TOKENS[247] == 'RUN'
KEYS = sorted(((v, k) for k, v in TOKENS.items()), key=lambda kv: -len(kv[0]))
NUMBER = re.compile(r'(?<![A-Za-z_$])(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?')
LINE = re.compile(r'^\s*(\d{1,4})(?:\s+|(?=[A-Z]))(.*)$')
GRAPHICS = re.compile(r'^\{([^{}]+)\}')
CONTROL = {'INK':16, 'PAPER':17, 'FLASH':18, 'BRIGHT':19, 'INVERSE':20,
           'OVER':21, 'AT':22, 'TAB':23}


def spectrum_float(value: float) -> bytes:
    """5-byte Spectrum number; prefer its exact small signed-integer form."""
    if not math.isfinite(value):
        raise ValueError('Non-finite numbers are not representable')
    if value.is_integer() and -65535 <= value <= 65535:
        n = int(abs(value))
        return bytes((0, 255 if value < 0 else 0, n & 255, n >> 8, 0))
    if value == 0:
        return bytes(5)
    fraction, exp = math.frexp(abs(value))
    eb = exp + 128
    if not 1 <= eb <= 255:
        raise ValueError(f'Numeric literal out of ZX Spectrum range: {value}')
    mantissa = int(round((fraction * 2 - 1) * (1 << 31)))
    if mantissa >= 1 << 31:
        eb += 1; mantissa = 0
    if eb > 255:
        raise ValueError(f'Numeric literal out of ZX Spectrum range: {value}')
    return bytes((eb, ((mantissa >> 24) & 127) | (128 if value < 0 else 0),
                  (mantissa >> 16) & 255, (mantissa >> 8) & 255, mantissa & 255))


def expand_braces(s: str, pos: int):
    m = GRAPHICS.match(s[pos:])
    if not m: return None
    name = m.group(1)
    cap = name.upper()
    if re.fullmatch(r'[0-9A-Fa-f]{2}', name): return bytes([int(name, 16)]), pos+m.end()
    if re.fullmatch(r'0x[0-9A-Fa-f]{2}', name): return bytes([int(name[2:], 16)]), pos+m.end()
    if cap == '(C)': return b'\x7f',pos+m.end()
    if cap == 'CODE': return b'\xaf',pos+m.end()
    if cap == 'CAT': return b'\xcf',pos+m.end()
    if re.fullmatch('[A-U]',name): return bytes([144 + ord(name)-65]),pos+m.end()
    if re.fullmatch(r'[+-][1-8]',name): return bytes([128 + (8 if name[0]=='+' else 0) + int(name[1])-1]),pos+m.end()
    cm = re.fullmatch(r'(INK|PAPER|FLASH|BRIGHT|INVERSE|OVER|AT|TAB)\s+(\d+)(?:\s*,\s*(\d+))?',cap)
    if cm:
        code = CONTROL[cm[1]]; args = [int(cm[2])] + ([int(cm[3])] if cm[3] else [])
        if len(args) != (2 if code==22 else 1) or any(n>255 for n in args):
            raise ValueError('Invalid control expansion '+m.group())
        return bytes([code]+args),pos+m.end()
    raise ValueError('Unknown Spectrum escape '+m.group())


def encode_body(text: str, case_insensitive=False) -> bytes:
    """Tokenize ordinary Sinclair BASIC source. Unrecognized constructs fail closed."""
    result=bytearray();i=0;in_string=False;in_rem=False;in_data=False;bin_next=False
    while i < len(text):
        c=text[i]
        if c=='{':
            expansion=expand_braces(text,i)
            if expansion:
                part,i=expansion;result.extend(part);continue
        if c=='"':
            in_string=not in_string;result.append(34);i+=1;continue
        if not in_string and not in_rem and c==':': in_data=False
        if not in_string and not in_rem:
            matched=None
            for word, code in KEYS:
                if in_data and word != 'BIN': continue
                fragment=text[i:i+len(word)]
                if (fragment.upper() if case_insensitive else fragment)!=word: continue
                if word not in ('TO', 'THEN') and word[0].isalpha() and i and (text[i-1].isalpha() or text[i-1] in '_$'):
                    continue
                # End-of-token digits are permitted (PRINT10), letters aren't (PRINTABLE).
                if word[-1].isalpha() and i+len(word)<len(text):
                    nxt=text[i+len(word)]
                    if (nxt.isalpha() or nxt in '_$') and word not in ('TO', 'THEN'): continue
                matched=(word,code);break
            if matched:
                word, code=matched
                result.append(code);i+=len(word)
                if code==234:in_rem=True
                if code==228:in_data=True
                if word=='BIN':bin_next=True
                continue
            nm=NUMBER.match(text,i)
            if nm:
                literal=nm.group()
                result.extend(literal.encode('ascii'))
                result.append(14);result.extend(spectrum_float(float(int(literal, 2)) if bin_next else float(literal)))
                bin_next=False
                i=nm.end();continue
        # No token expansion inside string/REM/DATA, but preserve original bytes.
        if c in '↑£©': result.append({'↑':94,'£':96,'©':127}[c])
        elif ord(c)<=127: result.append(ord(c))
        else:
            raise ValueError(f'Unsupported non-Spectrum character U+{ord(c):04X} (use {{XX}} escape)')
        i+=1
    if in_string and not in_rem: raise ValueError('Unclosed BASIC string')
    return bytes(result)


def compile_listing(source: str, case_insensitive=False) -> bytes:
    blocks=[];previous=-1
    for input_number,text in enumerate(source.splitlines(),1):
        if not text.strip():continue
        m=LINE.match(text)
        if not m:raise ValueError(f'Input line {input_number}: missing BASIC line number: {text[:65]!r}')
        number=int(m[1]); body=m[2]
        if number>9999 or number<=previous:
            raise ValueError(f'Input line {input_number}: line numbers must increase and be <=9999')
        encoded=encode_body(body,case_insensitive)+b'\x0d'
        if len(encoded)>65535:raise ValueError('BASIC line exceeds tape limit')
        blocks.append(number.to_bytes(2,'big')+len(encoded).to_bytes(2,'little')+encoded)
        previous=number
    if not blocks:raise ValueError('No numbered BASIC lines found')
    all_data=b''.join(blocks)
    if len(all_data)>65535:raise ValueError('BASIC program exceeds 65535 bytes')
    return all_data


def xor_checksum(data: bytes) -> int:
    v=0
    for x in data:v^=x
    return v


def tap_block(flag: int, payload: bytes) -> bytes:
    content=bytes([flag])+payload
    if len(content)+1 >65535:raise ValueError('Block too large for TAP')
    return struct.pack('<H',len(content)+1)+content+bytes([xor_checksum(content)])


def listing_tap(raw: bytes, name: str, autostart=0x8000) -> bytes:
    if not 0<=autostart<=9999 and autostart!=0x8000:
        raise ValueError('Invalid autostart line')
    if len(raw)>65533:raise ValueError('BASIC tape payload too large')
    header=bytes([0])+name.encode('ascii','replace')[:10].ljust(10,b' ')+struct.pack('<HHH',len(raw),autostart,len(raw))
    return tap_block(0,header)+tap_block(255,raw)


def tzx_from_listing(source: str, name: str) -> bytes:
    """Make a standard-speed non-autostart TZX from a decoded BASIC listing."""
    return _to_tzx(listing_tap(compile_listing(source), name, 0x8000))


def _to_tzx(tap: bytes) -> bytes:
    import struct
    out = bytearray(b'ZXTape!\x1a\x01\x14')
    pos = 0
    while pos < len(tap):
        length = int.from_bytes(tap[pos:pos+2], 'little')
        pos += 2
        block = tap[pos:pos+length]
        if len(block) != length or not length or xor_checksum(block):
            raise ValueError('Invalid generated TAP block')
        out.extend(b'\x10' + struct.pack('<HH', 1000, length) + block)
        pos += length
    return bytes(out)
