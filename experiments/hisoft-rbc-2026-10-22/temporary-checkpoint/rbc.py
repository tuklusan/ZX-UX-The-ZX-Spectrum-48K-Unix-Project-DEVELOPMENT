#!/usr/bin/env python3
# adapted from hisoft compiler
"""rbc experimental Python BASIC -> ZX-UX SSX1 compiler.

The BASIC front end is Melissa O'Neill's MIT-licensed pyhsb (HiSoft BASIC
v1.1 compatible), loaded as Python modules. The output stage is ZX-UX-specific:
three-base address analysis, a relocatable SSX1 image, an 8x8 VGA font, and a
process start/exit shim. This file does not embed original HiSoft compiler code.

An isolated experiment. A successful compile does NOT establish that Spectrum
ROM routines and RAM system variables are safe under ZX-UX. Test each binary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import tempfile
from dataclasses import dataclass
from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYS = 0x6003
CHARS = 0x5C36
UDG = 0x5C7B    # Sinclair BASIC user-defined graphics base (21*8 bytes)
HEADER_BYTES = 20


def _sdk_modules(sdk: Path):
    """Load frozen ZX-UX packer, not a replacement executable format."""
    sys.path.insert(0, str(sdk))
    import rld  # type: ignore
    import rtap  # type: ignore
    return rld, rtap


def _hisoft_modules(frontend: Path):
    if not (frontend / 'pyhsb.py').is_file() or not (frontend / 'compiler.py').is_file():
        raise ValueError('pyhsb source checkout required via --frontend; '
                         'see https://github.com/imneme/pyhsb')
    sys.path.insert(0, str(frontend))
    import compiler  # type: ignore
    import hbcimage  # type: ignore
    import source  # type: ignore
    return compiler, hbcimage, source


def _tap_from_tzx(p: Path) -> bytes:
    """Convert standard-speed Sinclair TZX data blocks to TAP for pyhsb.

    Unsupported TZX block kinds are rejected, never skipped by guesswork.
    Exact data blocks are preserved, headers and data remain in sequence.
    """
    b = p.read_bytes()
    if not b.startswith(b'ZXTape!\x1a') or len(b) < 10:
        raise ValueError(f'{p}: not TZX')
    out = bytearray()
    i = 10
    while i < len(b):
        k = b[i]; i += 1
        if k == 0x10:
            if i+4 > len(b): raise ValueError('truncated TZX standard header')
            pause, size = struct.unpack_from('<HH', b, i); i += 4
            if i+size > len(b): raise ValueError('truncated TZX standard data')
            block = b[i:i+size]; i += size
            if len(block) < 2 or _xor(block):
                raise ValueError('bad Sinclair tape checksum')
            out.extend(struct.pack('<H', size)); out.extend(block)
        elif k == 0x30:
            if i >= len(b):raise ValueError('truncated TZX text')
            n = b[i]; i += 1+n
            if i > len(b):raise ValueError('truncated TZX text')
        elif k == 0x32:
            if i+2 > len(b): raise ValueError('truncated TZX archive information')
            n = struct.unpack_from('<H',b,i)[0];i+=2+n
            if i>len(b): raise ValueError('truncated TZX archive information')
        else:
            raise ValueError(f'unhandled TZX block {k:#04x} at {i-1}: use a TAP copy')
    return bytes(out)


def _xor(a):
    v=0
    for x in a:v^=x
    return v


@dataclass
class HiSoftBuild:
    code: bytes
    base: int
    entry: int
    bss: int
    label: str = ''


def _source_program(src: Path, source, kw, fp):
    """Read numbered archival .bas listings, preserving Spectrum byte escapes.

    Historical text uses {90} for a single byte in the Spectrum character
    set. The generic plain-text reader treats those four characters literally.
    It also misses AND/OR/TO/THEN immediately following a decimal digit.
    Original .tap inputs are still handled by the upstream token reader.
    """
    if src.suffix.lower() != '.bas':
        return source.read_program(src, kw, fp)
    import tap as spectrum_tap
    rows=[]
    for file_line, raw in enumerate(src.read_text(encoding='latin-1').splitlines(),1):
        raw=raw.strip()
        if not raw:continue
        match=re.match(r'^(\d+)\s+(.*)$',raw)
        if not match:
            raise ValueError(f'{src.name}: invalid BASIC text line {file_line}')
        number=int(match.group(1)); body=match.group(2)
        # Preserve quoted text and REMs verbatim. Only adjust digit-adjacent
        # language words where the plain-text lexer lacks a word boundary.
        chunks=[];i=0;quoted=False;comment=False
        while i < len(body):
            c=body[i]
            if not quoted and not comment and c=='"': quoted=True
            elif quoted and c=='"': quoted=False
            if not quoted and not comment and body[i:i+3].upper()=='REM':
                left=(i==0 or not body[i-1].isalnum())
                right=(i+3==len(body) or not body[i+3].isalnum())
                if left and right: comment=True
            if not quoted and not comment and c.isdigit():
                for word in ('THEN','STEP','AND','OR','TO'):
                    if body.startswith(word,i+1):
                        chunks.append(c+' '+word+' ');i+=1+len(word);break
                else:
                    chunks.append(c);i+=1
                continue
            chunks.append(c);i+=1
        encoded=source.tokenize_line(''.join(chunks),kw)
        # Replace archival {HH} byte notation, including UDG character codes
        # inside quoted strings and control bytes kept in REM comments.
        encoded=re.sub(rb'\{([0-9A-Fa-f]{2})\}',
                       lambda m: bytes((int(m.group(1),16),)),encoded)
        rows.append((number,source.hide_numbers(encoded,fp)+b'\x0d'))
    if not rows:raise ValueError(f'{src.name}: empty BASIC listing')
    numbers=[n for n,_ in rows]
    if len(set(numbers))!=len(numbers):
        raise ValueError(f'{src.name}: duplicate BASIC line numbers')
    return src.stem[:10],spectrum_tap.join_lines(sorted(rows))


def _compile_three(src:Path, frontend:Path, tape:Path, romfile:Path,
                   ramtop:int, directives: list[str], memory_policy:str) -> tuple[list[HiSoftBuild], dict]:
    compiler, hbcimage, source = _hisoft_modules(frontend)
    rom = romfile.read_bytes()
    if len(rom) != 16384:raise ValueError('48K ROM must be 16384 bytes')
    with tempfile.TemporaryDirectory(prefix='rbc-tap-') as tmp:
        if tape.suffix.lower() == '.tzx':
            temp = Path(tmp)/'hisoft.tap';temp.write_bytes(_tap_from_tzx(tape))
            tape = temp
        img = hbcimage.Image.from_tape(tape)
        if not getattr(img,'v11', False):
            raise ValueError('rbc requires HiSoft BASIC v1.1, 48K tape (Side A)')
        kw = source.Keywords(rom)
        initial = compiler.Compiler(img,rom,ramtop=ramtop)
        name, program = _source_program(src,source,kw,initial.fp)
        if not source.open_lines(program):
            program = source.add_directives(program, directives, True, [], kw, initial.fp)
        else:
            program = source.add_directives(program, directives, False, [], kw, initial.fp)
        program = source.tokenize_directives(program,kw)
        import tap as spectrum_tap
        checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)
        memory_report = summarize(checks)
        enforce(checks, memory_policy)
        builds=[]
        for n,top in enumerate((ramtop,ramtop-389,ramtop-617)):
            if top < 32768:raise ValueError('too little compilation space')
            c=compiler.Compiler(img,rom,ramtop=top)
            res=c.compile_whole(program)
            if not res.ok:
                raise ValueError(f'{src.name}: HiSoft v1.1 compile failed: {res.error}'
                                 f' line {res.error_line}: {res.detail}')
            entry=res.entries[0][1] if res.entries else res.code_base
            builds.append(HiSoftBuild(bytes(res.code),res.load,entry,res.var_bytes,f'ramtop {top}'))
        return builds, {'program':name,'source_bytes':len(program),
                        'compiler':'pyhsb HiSoft v1.1, 48K','frontend':str(frontend),
                        'tape':tape.name if tape.suffix.lower()=='.tap' else str(tape),
                        'memory_policy':memory_policy, 'memory_check':memory_report}


def _reloc_sites(builds: list[HiSoftBuild]) -> list[int]:
    """Find 16-bit absolute references through controlled compile-time shifts.

    Each changed word must be a pointer into the generated image or BSS and
    track both shifts exactly. This does not independently prove safe ROM use.
    """
    if len(builds) < 2:raise ValueError('need at least two compiler passes')
    first=builds[0];length=len(first.code)
    for other in builds[1:]:
        if len(other.code)!=length or first.bss!=other.bss:
            raise ValueError('compiles differ in code/BSS size; relocation unresolved')
        if (other.entry-other.base) != (first.entry-first.base):
            raise ValueError('entry offset changed between compiles')
    changes={i for i in range(length) if any(b.code[i]!=first.code[i] for b in builds[1:])}
    sites=[]
    covered=set()
    for i in range(length-1):
        if i in covered or i+1 in covered:continue
        if i not in changes and i+1 not in changes:continue
        v=int.from_bytes(first.code[i:i+2],'little')
        if not first.base <= v <= first.base+length+first.bss:continue
        if all(int.from_bytes(b.code[i:i+2],'little') == (v+b.base-first.base)&0xFFFF for b in builds[1:]):
            sites.append(i); covered.update((i,i+1))
    unknown=changes-covered
    if unknown:
        raise ValueError(f'changes not explained by relocations: {len(unknown)} byte(s), '
                         f'first offsets {sorted(unknown)[:12]}; refusing output')
    return sites


class Emitter:
    def __init__(self):
        self.code=bytearray()
        self.fixups=[]
    def emit(self,*values):self.code.extend(values)
    def word(self,v):self.code.extend(struct.pack('<H',v&0xFFFF))
    def relative(self,v):self.fixups.append(len(self.code));self.word(v)
    def ldhl(self,v,rel=False):self.emit(0x21);(self.relative if rel else self.word)(v)
    def ldhl_ind(self,v,rel=False):self.emit(0x2A);(self.relative if rel else self.word)(v)
    def sthl(self,v,rel=False):self.emit(0x22);(self.relative if rel else self.word)(v)
    def call(self,v,rel=False):self.emit(0xCD);(self.relative if rel else self.word)(v)
    def lda(self,v):self.emit(0x3E,v)
    def fix(self,site,v):self.code[site:site+2]=struct.pack('<H',v&0xFFFF)


def build_ssx(builds: list[HiSoftBuild], font:bytes, rld,
              stack:int=384) -> tuple[bytes,dict]:
    if len(font)!=768:raise ValueError('font32 must contain 768 bytes (ASCII 32..127)')
    p=builds[0];sites=_reloc_sites(builds)
    if p.entry < p.base or p.entry >= p.base+len(p.code):
        raise ValueError('entry point not within program image')
    e=Emitter()
    # The ROM remains mapped under ZX-UX. Claim the display, then set
    # the ROM's CHARS pointer to the embedded 8x8 font for printable chars.
    e.ldhl(1);e.lda(39);e.call(SYS)
    e.ldhl_ind(CHARS)
    store_chars=len(e.code)+1;e.sthl(0,rel=True)
    e.ldhl_ind(UDG)
    store_udg=len(e.code)+1;e.sthl(0,rel=True)
    fontptr=len(e.code)+1;e.ldhl(0,rel=True)
    e.sthl(CHARS)
    udgptr=len(e.code)+1;e.ldhl(0,rel=True)
    e.sthl(UDG)
    call=len(e.code)+1;e.call(0,rel=True)
    restore_udg=len(e.code)+1;e.ldhl_ind(0,rel=True)
    e.sthl(UDG)
    restore_chars=len(e.code)+1;e.ldhl_ind(0,rel=True)
    e.sthl(CHARS)
    e.ldhl(0);e.lda(39);e.call(SYS)
    e.ldhl(0);e.lda(1);e.call(SYS)
    e.emit(0x76)
    entry_image=len(e.code)
    e.code.extend(p.code)
    saved_chars=len(e.code);e.word(0)
    saved_udg=len(e.code);e.word(0)
    font_start=len(e.code);e.code.extend(font)
    udg_start=len(e.code);e.code.extend(bytes(21*8))
    for offset,value in ((store_chars,saved_chars),(store_udg,saved_udg),
                         (fontptr,font_start-256),(udgptr,udg_start),
                         (call,entry_image+p.entry-p.base),
                         (restore_udg,saved_udg),(restore_chars,saved_chars)):
        e.fix(offset,value)
    for site in sites:
        orig=int.from_bytes(p.code[site:site+2],'little')
        target=entry_image+(orig-p.base)
        e.fix(entry_image+site,target)
        e.fixups.append(entry_image+site)
    reloc=sorted(e.fixups)
    if len(set(reloc))!=len(reloc) or any(x+2>len(e.code) for x in reloc):
        raise ValueError('overlapping or invalid relocations')
    if len(e.code)+p.bss+stack>65535:
        raise ValueError('image, variables and stack cannot fit in 48K address space')
    rs=rld.reloc_stream(reloc)
    hdr=b'SSX1'+struct.pack('<BBHHHHHH',0,HEADER_BYTES,len(e.code),p.bss,stack,0,0,len(reloc))
    ssx=hdr+struct.pack('<H',rld.fletcher16(hdr+e.code+rs))+e.code+rs
    check=rld.parse_ssx(ssx)
    if check['relocs']!=reloc or check['image']!=bytes(e.code):
        raise ValueError('SSX1 round-trip validation failed')
    return ssx, {'machine_code':len(p.code),'image':len(e.code),'bss':p.bss,
                 'entry_offset':entry_image+p.entry-p.base,'relocations':len(reloc),
                 'font_bytes':len(font),'udg_bytes':21*8,
                 'rom_and_system_variable_compatibility':'unverified',
                 'visual_and_gameplay_compatibility':'unverified'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path,help='original .bas or .tap; untouched')
    ap.add_argument('-o','--output',type=Path,required=True,help='target SSX1 executable')
    ap.add_argument('--frontend',type=Path,default=Path(os.getenv('PYHSB_PATH','pyhsb')))
    ap.add_argument('--sdk',type=Path,default=HERE.parent.parent/'work'/'dist_sdk')
    ap.add_argument('--tape',type=Path,default=HERE.parent.parent/'..'/'Hisoft BASIC Compiler v1.1 - Side A.tzx')
    ap.add_argument('--rom',type=Path,default=HERE.parent.parent/'inputs'/'48.rom')
    ap.add_argument('--font32',type=Path,default=HERE/'font32.bin')
    ap.add_argument('--ramtop',type=int,default=65367)
    ap.add_argument('--stack',type=int,default=384)
    ap.add_argument('--directive',action='append',default=[],help='HiSoft compiler directive')
    ap.add_argument('--memory-policy',choices=('strict','review'),default='strict',
                    help='strict refuses unsafe memory operations; review compiles for isolated tests')
    ap.add_argument('--tzx',type=Path)
    ap.add_argument('--report',type=Path)
    # Replay existing genuine HiSoft compilations without re-interpreting .bas.
    # This is a regression mode, never a substitute for pyhsb-source mode.
    ap.add_argument('--pair-second',type=Path,help='second HiSoft code binary')
    ap.add_argument('--pair-third',type=Path,help='third HiSoft code binary')
    ap.add_argument('--base',type=int,help='first build load address (pair regression mode)')
    ap.add_argument('--second-base',type=int)
    ap.add_argument('--third-base',type=int)
    ap.add_argument('--var-bytes',type=int)
    ap.add_argument('--entry',type=int,help='absolute HiSoft entry (pair regression mode)')
    args=ap.parse_args(argv)
    try:
        rld,rtap=_sdk_modules(args.sdk)
        font=args.font32.read_bytes()
        if args.pair_second:
            if None in (args.base,args.second_base,args.var_bytes):
                raise ValueError('pair mode needs --base, --second-base and --var-bytes')
            entry=args.entry if args.entry is not None else args.base
            builds=[HiSoftBuild(args.source.read_bytes(),args.base,entry,args.var_bytes,'first'),
                    HiSoftBuild(args.pair_second.read_bytes(),args.second_base,
                                entry+args.second_base-args.base,args.var_bytes,'second')]
            if args.pair_third:
                if args.third_base is None:raise ValueError('third build needs --third-base')
                builds.append(HiSoftBuild(args.pair_third.read_bytes(),args.third_base,
                    entry+args.third_base-args.base,args.var_bytes,'third'))
            meta={'source_mode':'replay existing HiSoft binaries'}
        else:
            builds,meta=_compile_three(args.source,args.frontend,args.tape,args.rom,
                                       args.ramtop,args.directive,args.memory_policy)
            meta['source_mode']='pyhsb HiSoft v1.1 (48K) source compile'
        ssx,diagnostics=build_ssx(builds,font,rld,args.stack)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(ssx)
        if args.tzx:
            hdr,block=rtap.records(ssx,args.output.stem[:10])
            title=b'ZX-UX RBC experimental'
            tzx_head=b'ZXTape!\x1a\x01\x14'+bytes((0x30,len(title)))+title
            rtap.write(str(args.tzx),tzx_head,[(1000,hdr),(2000,block)])
        meta.update(diagnostics)
        if args.report:
            args.report.write_text(json.dumps(meta,indent=2)+'\n')
        print(f'{args.source.name}: {len(builds[0].code)} bytes of HiSoft code -> '
              f'{len(ssx)} byte SSX1 ({diagnostics["relocations"]} relocations) '
              f'at {args.output}')
        return 0
    except MemoryBlocked as exc:
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({'compile':'blocked',
                        'memory_policy':args.memory_policy,
                        'memory_check':summarize(exc.findings)},indent=2)+'\n')
        print('rbc: '+str(exc),file=sys.stderr)
        return 1
    except (ValueError,OSError) as exc:
        print('rbc: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())