#!/usr/bin/env python3
"""Recover Spectrum BASIC from previously downloaded snapshots and compile TAP/TZX.

Requires SkoolKit for reading Z80 snapshots and the zmakebas-plus CLI for
compiling text. No original media is changed and no runtime checks are claimed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from skoolkit.snapshot import get_snapshot
from skoolkit.basic import BasicLister

BASIC_LINE = re.compile(r'^\s*(\d{1,4})(?:\s+|$)(.*)$')
DISPLAY_ESCAPE = re.compile(r'\{(UDG-[A-U]|0x[0-9A-Fa-f]{2,6})\}')


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_listing(text):
    """Translate SkoolKit's graphic display into zmakebas+ text notation.

    The original BASIC dump is retained separately. This rewrite does NOT make
    binary/REM-packed programs roundtrip-equivalent to their source snapshots.
    """
    text = text.replace('\\', '\\\\')
    text = text.replace('©', r'\*').replace('↑', r'\{0x5E}').replace('£', r'\{0x60}')

    def replace_escape(match):
        value = match.group(1)
        if value.startswith('UDG-'):
            return '\\' + value[-1]
        body = value[2:]
        if len(body) % 2:
            return match.group(0)
        return ''.join(r'\{0x' + body[i:i+2] + '}' for i in range(0, len(body), 2))

    text = DISPLAY_ESCAPE.sub(replace_escape, text)
    return text


def validate_line_numbers(text):
    nums = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = BASIC_LINE.match(line)
        if not m:
            return {'error':'Missing numbered BASIC line', 'text':line[:160]}
        nums.append(int(m.group(1)))
    if not nums:
        return {'error':'Empty BASIC listing'}
    if len(nums) != len(set(nums)):
        dups = [n for n,c in Counter(nums).items() if c>1]
        return {'error':'Duplicate line numbers in captured snapshot', 'duplicates':dups}
    if nums != sorted(nums):
        return {'error':'Program lines out of order'}
    return {'line_count':len(nums), 'first_line':nums[0], 'last_line':nums[-1]}


def verify_tap(tap):
    pos=0; blocks=[]
    while pos<len(tap):
        if pos+2>len(tap):raise ValueError('Partial TAP block length')
        n=int.from_bytes(tap[pos:pos+2],'little'); pos+=2
        if n<2 or pos+n>len(tap):raise ValueError('Invalid TAP block size')
        b=tap[pos:pos+n];pos+=n
        xor=0
        for v in b:xor^=v
        if xor:raise ValueError('TAP checksum mismatch')
        blocks.append(b)
    if not blocks:raise ValueError('No TAP blocks')
    if len(blocks)<2 or not any(len(b)==19 and b[0]==0 and b[1]==0 for b in blocks):
        raise ValueError('TAP lacks expected BASIC header')
    return blocks


def build_tzx(blocks):
    tzx=bytearray(b'ZXTape!\x1a\x01\x14')
    for block in blocks:
        tzx.extend(b'\x10')
        tzx.extend((1000).to_bytes(2,'little'))
        tzx.extend(len(block).to_bytes(2,'little'))
        tzx.extend(block)
    return bytes(tzx)


KNOWN_REPAIRS = {
    '13-firefoxcomplete--FireFoxComplete.bas': 'aae1e57b0376d1f4acf795e70320cb87e26a0580cd7b3123fc3f75cc69a059fd',
    '14-outlander--Outlander.bas': '5ba9be2d78e46bf030a62cd2079434be4767af5e39e7ef6e5d5ad7aefc9ef870',
    '31-galactoids--Galactoids.bas': '3124a9a3b3e1ca3f7dd8e3914a40f6130f0e0e306e91c79f847c69212ae45d50',
}


def prepare_listing(name, raw):
    """Apply three explicit, logged repairs to unchanged SkoolKit source dumps."""
    if name not in KNOWN_REPAIRS:
        return raw, []
    actual=hashlib.sha256(raw.encode('utf-8')).hexdigest()
    if actual != KNOWN_REPAIRS[name]:
        raise ValueError(f'Snapshot text changed: {name}, expected {KNOWN_REPAIRS[name]}, found {actual}')
    if name.startswith('13-firefox'):
        before='3000 RESTORE : INPUT ("You scored ";s;" Another game ?");a$'
        after='3000 RESTORE : INPUT "You scored ";s;" Another game ?";a$'
        if raw.count(before)!=1:raise ValueError('Cannot locate INPUT line')
        return raw.replace(before,after), ['Replaced parenthesized INPUT prompt with equivalent ungrouped INPUT form for the strict compiler']
    if name.startswith('14-outlander'):
        lines=raw.splitlines()
        if len(lines)<4 or not all(x.lstrip().startswith('0 REM ') for x in lines[:4]):
            raise ValueError('Expected four duplicate zero-numbered comment lines')
        one='   0 REM '+' | '.join(x.split('REM ',1)[1].strip() for x in lines[:4])
        return '\n'.join([one]+lines[4:])+'\n',['Combined four zero-numbered REM comment lines; BASIC commands unchanged']
    if name.startswith('31-galactoids'):
        lines=raw.splitlines()
        if len(lines)<2 or not lines[-2].lstrip().startswith('660 DATA 62,254,219,254') or not lines[-1].startswith('15874 '):
            raise ValueError('Expected damaged final snapshot BASIC line')
        return '\n'.join(lines[:-2]+[' 660 DATA 62,254,219,254'])+'\n', ['Damaged line 660 and unparseable remainder replaced by its readable DATA prefix; program is incomplete']
    raise ValueError('Unexpected listed repair')


def write_source(out, name, text, build_text):
    path = out/'basic-original'/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text, encoding='utf-8')
    normalized=out/'basic-for-zmakebas'/name
    normalized.parent.mkdir(parents=True,exist_ok=True)
    normalized.write_text(normalize_listing(build_text), encoding='utf-8')
    return path,normalized


def record_issue(rec,kind,description):
    rec['status']=kind
    rec['error']=description


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cli',type=Path,required=True)
    ap.add_argument('--tool-sha',required=True)
    ns=ap.parse_args()
    src,out=ns.source,ns.output
    out.mkdir(parents=True,exist_ok=True)
    records=[]; known=set()
    origs=sorted((src/'extracted').rglob('*.z80'),key=lambda p:str(p).lower())
    originals=sorted((src/'bas').glob('*.bas'),key=lambda p:str(p).lower())
    print(f'Input: {len(origs)} Z80 snapshots, {len(originals)} tape BASIC files',flush=True)
    inputs=[]
    for path in origs:
        name=path.parent.name+'--'+path.stem+'.bas'
        rec={'source_file':str(path.relative_to(src)), 'source_sha256':hash_file(path),
             'filename':name, 'origin':'snapshot', 'status':'pending'}
        try:
            mem=get_snapshot(str(path))
            prog=mem[23635]+256*mem[23636]
            vars=mem[23627]+256*mem[23628]
            if not 23296<=prog<vars<=65535:
                raise ValueError(f'Bad BASIC memory span PROG={prog} VARS={vars}')
            text=BasicLister().list_basic(mem)+'\n'
            if not text.strip():raise ValueError('BASIC listing is empty')
            rec.update({'start_address':prog,'end_address':vars,'snapshot_listing_lines':len(text.splitlines())})
            inputs.append((rec,text))
        except Exception as e:
            record_issue(rec,'extract_failed',str(e))
            records.append(rec)
    for path in originals:
        name=path.name
        rec={'source_file':str(path.relative_to(src)),'source_sha256':hash_file(path),
             'filename':name,'origin':'source_tape','status':'pending'}
        try:
            text=path.read_text(encoding='utf-8')
            inputs.append((rec,text))
        except Exception as e:
            record_issue(rec,'extract_failed',str(e))
            records.append(rec)

    for rec,text in inputs:
        name=rec['filename']
        if name in known:
            record_issue(rec,'name_collision','Duplicate output filename: '+name)
            records.append(rec);continue
        known.add(name)
        try:
            build_text,adjustments=prepare_listing(name,text)
        except Exception as e:
            record_issue(rec,'repair_failed',str(e))
            records.append(rec);print('REPAIR FAIL',name,rec['error'],flush=True);continue
        rec['adjustments']=adjustments
        raw,normalized=write_source(out,name,text,build_text)
        check=validate_line_numbers(build_text)
        rec.update({'raw_bas_sha256':hash_file(raw),'normalized_bas_sha256':hash_file(normalized),
                    'line_check':check})
        if 'error' in check:
            record_issue(rec,'line_failure',check['error']+' '+str(check.get('duplicates','')))
            records.append(rec);print('LINE FAIL',name,rec['error'],flush=True);continue
        tap=out/'tap'/Path(name).with_suffix('.tap')
        tap.parent.mkdir(parents=True,exist_ok=True)
        command=['node',str(ns.cli.resolve()),'-n',Path(name).stem[:10],'-o',str(tap.resolve()),str(normalized.resolve())]
        try:
            proc=subprocess.run(command,capture_output=True,text=True,timeout=60)
            rec.update({'cli_exit':proc.returncode,'cli_stdout':proc.stdout[-2000:],'cli_stderr':proc.stderr[-10000:]})
            if proc.returncode != 0:
                record_issue(rec,'compile_failed',proc.stderr.strip() or f'zmakebas exited {proc.returncode}')
            elif not tap.exists():
                record_issue(rec,'compile_failed','zmakebas returned success without TAP file')
            else:
                blocks=verify_tap(tap.read_bytes())
                tzx=out/'tzx'/Path(name).with_suffix('.tzx')
                tzx.parent.mkdir(parents=True,exist_ok=True)
                tzx.write_bytes(build_tzx(blocks))
                result_status = ('compiled_partial' if name.startswith('31-galactoids') else
                                 'compiled_with_adjustments' if adjustments else 'compiled_not_run')
                rec.update({'status':result_status,'tap_sha256':hash_file(tap),
                            'tzx_sha256':hash_file(tzx),'tap_blocks':len(blocks),
                            'tap_file':str(tap.relative_to(out)),'tzx_file':str(tzx.relative_to(out))})
        except Exception as e:
            record_issue(rec,'compile_failed',str(e))
        print(rec['status'].upper(),name,rec.get('error','')[:250],flush=True)
        records.append(rec)

    statuses=Counter(r['status'] for r in records)
    total_tapes=sum(1 for r in records if r['status'].startswith('compiled_'))
    report={'source_url':'https://www.thespectrumshow.net/type-in-games.html',
            'generation_utc':datetime.now(timezone.utc).isoformat(),
            'zmakebas_repo':'https://github.com/tuklusan/zmakebas-plus',
            'zmakebas_commit':ns.tool_sha,
            'source_run':'GitHub Actions run 39986062137',
            'snapshot_count':len(origs),'source_tape_listings':len(originals),
            'records':records,'status_counts':dict(statuses), 'tape_count':total_tapes,
            'note':'Generated TAP/TZX has BASIC content only. No Spectrum Fuse run or complete game check was performed. Snapshot machine code, variables and runtime state are not restored by BASIC-only tapes. ZX81 .z81 game snapshot is separate from the Spectrum set.'}
    (out/'build-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'README.txt').write_text(
        f'Spectrum Show BASIC tape exports using zmakebas-plus\n\n'
        f'Original Z80 snapshot programs: {len(origs)}\n'
        f'Existing tape-extracted BASIC programs: {len(originals)}\n'
        f'Total candidate listings: {len(inputs)}\n'
        f'TAP and TZX converted: {total_tapes}\n'
        f'Untouched listings compiled: {statuses["compiled_not_run"]}\n'
        f'Listings needing repair: {statuses["compiled_with_adjustments"]}\n'
        f'Damaged snapshot partial tape: {statuses["compiled_partial"]}\n'
        f'Failures: {len(records)-total_tapes}\n\n'
        'basic-original/       Raw SkoolKit text listings or original tape BASIC dumps\n'
        'basic-for-zmakebas/  Plain text, with graphic and byte notation adjusted\n'
        'tap/                  TAP files built using zmakebas-plus\n'
        'tzx/                  TZX standard-speed tape wrappers of TAP output\n'
        'build-report.json     Individual input hashes, results, and errors\n\n'
        'IMPORTANT: TAP/TZX checksums checked, but no end-to-end Fuse test.\n'
        'Machine code stored outside the BASIC listing in snapshots is missing.\n'
        'No changes to the 60 preserved ZX-UX BASIC programs or release tree.\n', encoding='utf-8')
    bundle=out.parent/'spectrum-show-all-tapes.zip'
    with ZipFile(bundle,'w',compression=ZIP_DEFLATED,compresslevel=8) as z:
        for file in sorted(out.rglob('*')):
            if file.is_file():z.write(file,file.relative_to(out))
    print('SUMMARY',dict(statuses),'tapes',total_tapes,'bundle',bundle,'bytes',bundle.stat().st_size,flush=True)
    return 0

if __name__=='__main__':sys.exit(main())