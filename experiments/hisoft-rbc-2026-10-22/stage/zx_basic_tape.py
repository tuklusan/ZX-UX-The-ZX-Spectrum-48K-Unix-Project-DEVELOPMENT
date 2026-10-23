#!/usr/bin/env python3
"""Portable, standard-library ZX Spectrum 48K BASIC and tape tools.

Independent implementation of the Sinclair tape and BASIC formats.
Design/reference: BAS2TAP 2.6, Martijn van der Heide (1998-2013),
https://github.com/tuklusan/bas2tap (GPL-2.0-or-later upstream).
Does not copy BAS2TAP's source, and does not implement its full syntax checker.
Original tape byte streams must remain primary when exact runtime fidelity matters.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import struct
from pathlib import Path

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
    result=bytearray();i=0;in_string=False;in_rem=False;in_data=False
    while i < len(text):
        c=text[i]
        if c=='{':
            expansion=expand_braces(text,i)
            if expansion:
                part,i=expansion;result.extend(part);continue
        if c=='"':
            in_string=not in_string;result.append(34);i+=1;continue
        if not in_string and not in_rem and c==':': in_data=False
        if not in_string and not in_rem and not in_data:
            matched=None
            for word, code in KEYS:
                fragment=text[i:i+len(word)]
                if (fragment.upper() if case_insensitive else fragment)!=word: continue
                if word[0].isalpha() and i and (text[i-1].isalnum() or text[i-1] in '_$'):
                    continue
                # End-of-token digits are permitted (PRINT10), letters aren't (PRINTABLE).
                if word[-1].isalpha() and i+len(word)<len(text):
                    nxt=text[i+len(word)]
                    if nxt.isalpha() or nxt in '_$': continue
                matched=(word,code);break
            if matched:
                word, code=matched
                result.append(code);i+=len(word)
                if code==234:in_rem=True
                if code==228:in_data=True
                continue
            nm=NUMBER.match(text,i)
            if nm:
                literal=nm.group()
                result.extend(literal.encode('ascii'))
                result.append(14);result.extend(spectrum_float(float(literal)))
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


def parse_tap(data: bytes):
    blocks=[];i=0
    while i<len(data):
        if len(data)-i<2:raise ValueError(f'TAP truncated before block length at {i}')
        length=int.from_bytes(data[i:i+2],'little');i+=2
        if length<2 or i+length>len(data): raise ValueError(f'Bad TAP length at {i-2}: {length}')
        raw=data[i:i+length];i+=length
        if xor_checksum(raw):raise ValueError(f'Bad TAP block checksum at {i-length}')
        blocks.append(raw)
    return blocks


def tap_to_tzx(tap: bytes, pause_ms=1000) -> bytes:
    if not 0<=pause_ms<=65535:raise ValueError('pause must fit 16 bits')
    out=bytearray(b'ZXTape!\x1a\x01\x14')
    for raw in parse_tap(tap):
        out.extend(b'\x10'+struct.pack('<HH',pause_ms,len(raw))+raw)
    return bytes(out)


def parse_standard_tzx(data: bytes):
    """Read common TZX tape blocks; preserve metadata but do not treat it as tape data.

    Turbo blocks carry waveform metadata which is *not* reproduced by TAP -> TZX.
    Use the unmodified source TZX for runtime tests of those tapes.
    """
    if not data.startswith(b'ZXTape!\x1a') or len(data)<10:
        raise ValueError('Not a TZX file')
    result=[];at=10
    def take(n):
        nonlocal at
        if at+n>len(data):raise ValueError('Truncated TZX block at %s'%at)
        value=data[at:at+n];at+=n
        return value
    while at<len(data):
        block_id=take(1)[0]
        if block_id==0x10:
            head=take(4);length=int.from_bytes(head[2:4],'little')
            block=take(length)
        elif block_id==0x11:
            # Turbo-speed data block: 15 timing/flag bytes, three size bytes.
            head=take(18);length=int.from_bytes(head[-3:],'little')
            block=take(length)
        elif block_id==0x20:take(2);continue
        elif block_id==0x30:
            length=take(1)[0];take(length);continue
        elif block_id==0x32:
            length=int.from_bytes(take(2),'little');take(length);continue
        elif block_id==0x31:
            head=take(2);take(head[1]);continue
        elif block_id==0x33:
            count=take(1)[0];take(3*count);continue
        elif block_id==0x35:
            take(10);take(int.from_bytes(take(4),'little'));continue
        else:
            raise ValueError(f'TZX block 0x{block_id:02X}: unsupported, preserve original TZX')
        if xor_checksum(block):raise ValueError('TZX tape block checksum failure')
        result.append(block)
    return result


def decode_basic(raw: bytes):
    """Strict, length-based decoder; preserves escaped bytes (no variable-area guessing)."""
    lines=[];at=0
    while at<len(raw):
        if at+4>len(raw):raise ValueError(f'Truncated BASIC header at {at}')
        number=int.from_bytes(raw[at:at+2],'big');length=int.from_bytes(raw[at+2:at+4],'little')
        if not 0<=number<=9999:raise ValueError(f'Nonstandard BASIC line {number} at {at}')
        if length==0 or at+4+length>len(raw):raise ValueError(f'Bad BASIC line length {length} at {at}')
        body=raw[at+4:at+4+length]
        if body[-1]!=13:raise ValueError(f'No BASIC CR terminator on {number}')
        out=[];i=0;in_string=False;in_rem=False
        while i<len(body)-1:
            b=body[i]
            if b==14 and not in_string and not in_rem and i+6<=len(body)-1:
                # Five-byte hidden numeric form already has a preceding displayed literal.
                i+=6;continue
            if b>=165:
                if in_rem:out.append(f'{{{b:02X}}}')
                else:out.append(TOKENS[b]+' ')
            elif b==34:
                out.append('"');in_string=not in_string
            elif b in (94,96,127):out.append({94:'↑',96:'£',127:'©'}[b])
            elif 32<=b<127:out.append(chr(b))
            else:out.append(f'{{{b:02X}}}')
            if b==234 and not in_string:in_rem=True
            i+=1
        lines.append(f'{number} '+''.join(out).rstrip())
        at+=4+length
    return '\n'.join(lines)+'\n'


def find_basic(tape_blocks):
    found=[]
    for i,block in enumerate(tape_blocks[:-1]):
        if len(block)!=19 or block[0:2]!=b'\x00\x00':continue
        if block[-1] != xor_checksum(block[:-1]): continue
        name=block[2:12].decode('latin1').rstrip()
        length=int.from_bytes(block[12:14],'little')
        var_offset=int.from_bytes(block[16:18],'little')
        payload=tape_blocks[i+1]
        if not payload or payload[0]!=255:continue
        if len(payload)-2!=length:continue
        found.append((name,payload[1:1+min(var_offset,length)]))
    return found


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('compile',help='ASCII numbered listing -> ROM-loadable TAP/TZX')
    p.add_argument('listing',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--name');p.add_argument('--autostart',type=int)
    p.add_argument('--ignore-case',action='store_true')
    p=sub.add_parser('convert',help='Lossless standard TAP -> standard-speed TZX')
    p.add_argument('tap',type=Path);p.add_argument('tzx',type=Path)
    p=sub.add_parser('inspect',help='Check blocks and decode standard BASIC in TAP/TZX')
    p.add_argument('tape',type=Path);p.add_argument('--listing-dir',type=Path)
    args=parser.parse_args(argv)
    if args.action=='compile':
        src=args.listing.read_text(encoding='utf-8-sig')
        tape=listing_tap(compile_listing(src,args.ignore_case), args.name or args.listing.stem,
                         args.autostart if args.autostart is not None else 0x8000)
        result=tap_to_tzx(tape) if args.output.suffix.lower()=='.tzx' else tape
        if args.output.suffix.lower() not in ('.tap','.tzx'):parser.error('Output suffix must be .tap or .tzx')
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(result)
        print('Created',args.output,'bytes',len(result),'TAP blocks',len(parse_tap(tape)))
    elif args.action=='convert':
        tzx=tap_to_tzx(args.tap.read_bytes());args.tzx.parent.mkdir(parents=True,exist_ok=True)
        args.tzx.write_bytes(tzx);print('Created',args.tzx)
    else:
        buf=args.tape.read_bytes()
        blocks=parse_tap(buf) if args.tape.suffix.lower()=='.tap' else parse_standard_tzx(buf)
        entries=[]
        for i,(name,raw) in enumerate(find_basic(blocks)):
            item=dict(name=name,bytes=len(raw));
            try:
                text=decode_basic(raw)
                item['status']='decoded';item['lines']=len(text.splitlines())
                if args.listing_dir:
                    args.listing_dir.mkdir(parents=True,exist_ok=True)
                    dest=args.listing_dir/f'{i+1:03d}-{re.sub(r"[^a-zA-Z0-9_-]", "_", name)}.bas'
                    dest.write_text(text,encoding='utf8');item['listing']=str(dest)
            except ValueError as exc:item['status']='nonstandard';item['reason']=str(exc)
            entries.append(item)
        print(json.dumps(dict(tape=str(args.tape),blocks=len(blocks),basic=entries),indent=2))
if __name__=='__main__': main()
