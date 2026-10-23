#!/usr/bin/env python3
"""Fetch Spectrum Show type-ins, preserve tapes, and make inspected BASIC text.

Usage: python3 spectrum_show_runner.py --output typeins_output
This is acquisition/conversion, NOT proof of end-to-end execution.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

SITE = 'https://www.thespectrumshow.net/type-in-games.html'
UA = 'Mozilla/5.0 (compatible; ZX-Spectrum-preservation-downloader/1.0)'
MAX_ZIP = 50_000_000
MAX_MEMBER = 20_000_000
MAX_TOTAL = 100_000_000
TOKENS = ('RND','INKEY$','PI','FN','POINT','SCREEN$','ATTR','AT','TAB','VAL$','CODE',
          'VAL','LEN','SIN','COS','TAN','ASN','ACS','ATN','LN','EXP','INT','SQR','SGN',
          'ABS','PEEK','IN','USR','STR$','CHR$','NOT','BIN','OR','AND','<=','>=','<>',
          'LINE','THEN','TO','STEP','DEF FN','CAT','FORMAT','MOVE','ERASE','OPEN #',
          'CLOSE #','MERGE','VERIFY','BEEP','CIRCLE','INK','PAPER','FLASH','BRIGHT',
          'INVERSE','OVER','OUT','LPRINT','LLIST','STOP','READ','DATA','RESTORE',
          'NEW','BORDER','CONTINUE','DIM','REM','FOR','GO TO','GO SUB','INPUT',
          'LOAD','LIST','LET','PAUSE','NEXT','POKE','PRINT','PLOT','RUN','SAVE',
          'RANDOMIZE','IF','CLS','DRAW','CLEAR','RETURN','COPY')
assert len(TOKENS) == 91

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if re.search(r'\.zip(?:\?|$)', href, re.I):
                self.urls.append(urljoin(SITE, href))

def sha256(b): return hashlib.sha256(b).hexdigest()

def fetch(url):
    last = None
    for n in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent':UA}), timeout=45) as r:
                size = r.headers.get('Content-Length')
                if size and int(size) > MAX_ZIP: raise ValueError('zip too large')
                body = r.read(MAX_ZIP + 1)
                if len(body) > MAX_ZIP: raise ValueError('download too large')
                return body
        except (HTTPError, URLError, TimeoutError) as e:
            last = e
            if n < 3: time.sleep(2 ** n)
    raise RuntimeError(f'Download failed: {url}: {last}')

def tap_blocks(data):
    off = 0
    blocks = []
    while off < len(data):
        if off+2 > len(data): raise ValueError(f'TAP truncated length at {off}')
        size = struct.unpack_from('<H', data, off)[0]
        off += 2
        if size < 2 or off + size > len(data): raise ValueError(f'TAP truncated block at {off}')
        block = data[off:off+size]
        if 0 != xor_bytes(block): raise ValueError(f'TAP checksum failure at {off}')
        blocks.append(block); off += size
    return blocks

def xor_bytes(block):
    x=0
    for b in block: x ^= b
    return x

def tap_to_tzx(data):
    blocks = tap_blocks(data)
    # TZX v1.20 standard speed (0x10) tape blocks; exact TAP payload preserved.
    tzx = bytearray(b'ZXTape!\x1a\x01\x14')
    for block in blocks:
        tzx += b'\x10' + struct.pack('<HH', 1000, len(block)) + block
    return bytes(tzx)

def tzx_standard_blocks(data):
    if not data.startswith(b'ZXTape!\x1a') or len(data)<10: raise ValueError('Invalid TZX header')
    blocks=[]; p=10
    while p<len(data):
        op=data[p]; p+=1
        if op==0x10:
            if p+4>len(data): raise ValueError('Short TZX standard block header')
            size=int.from_bytes(data[p+2:p+4], 'little'); p+=4
            if p+size>len(data): raise ValueError('Short TZX standard block')
            block=data[p:p+size]; p+=size
            if xor_bytes(block): raise ValueError('TZX standard block checksum failure')
            blocks.append(block)
        elif op==0x11:
            if p+18>len(data): raise ValueError('Short TZX turbo header')
            size=int.from_bytes(data[p+15:p+18], 'little'); p+=18
            if p+size>len(data): raise ValueError('Short TZX turbo payload')
            block=data[p:p+size]; p+=size
            if xor_bytes(block): raise ValueError('TZX turbo checksum failure')
            blocks.append(block)
        elif op==0x20: p+=2
        elif op==0x21 or op==0x30:
            if p>=len(data): raise ValueError('Short TZX text/group block')
            n=data[p]; p+=1+n
        elif op==0x22 or op==0x25 or op==0x27: pass
        elif op==0x24: p+=2
        elif op==0x26:
            if p+2>len(data): raise ValueError('Short TZX call block')
            n=int.from_bytes(data[p:p+2],'little'); p+=2+2*n
        elif op==0x28:
            if p+2>len(data): raise ValueError('Short TZX selection block')
            n=int.from_bytes(data[p:p+2],'little'); p+=2+n
        elif op==0x2a: p+=4
        elif op==0x2b: p+=5
        elif op==0x31:
            if p+2>len(data): raise ValueError('Short TZX message')
            n=data[p+1]; p+=2+n
        elif op==0x32:
            if p+2>len(data): raise ValueError('Short TZX archive')
            n=int.from_bytes(data[p:p+2],'little'); p+=2+n
        elif op==0x33:
            if p>=len(data): raise ValueError('Short TZX hardware block')
            n=data[p]; p+=1+3*n
        elif op==0x35:
            if p+20>len(data): raise ValueError('Short TZX custom block')
            n=int.from_bytes(data[p+16:p+20], 'little'); p+=20+n
        elif op in (0x15, 0x18, 0x19):
            # Retain the original TZX unchanged; do not claim BASIC was extracted.
            raise ValueError(f'TZX block 0x{op:02x} requires a separate decoder')
        else:
            raise ValueError(f'Unsupported TZX block 0x{op:02x}')
        if p>len(data): raise ValueError('Truncated TZX block')
    return blocks

def listing_from_program(buf):
    lines=[]; pos=0
    while pos<len(buf):
        if pos+4>len(buf): raise ValueError(f'Truncated BASIC line header at {pos}')
        number=int.from_bytes(buf[pos:pos+2], 'big')
        length=int.from_bytes(buf[pos+2:pos+4], 'little'); pos+=4
        if number>9999 or length==0 or pos+length>len(buf):
            raise ValueError(f'Invalid BASIC line {number} (length {length})')
        row=buf[pos:pos+length]; pos+=length
        if row[-1]!=13: raise ValueError(f'BASIC line {number} missing newline')
        parts=[]; i=0; spaced=False
        while i<len(row)-1:
            c=row[i]
            if c==14 and i+5<len(row)-1:  # stored numeric value after text
                i+=6; continue
            if 16<=c<=21 and i+1<len(row)-1:
                parts.append('{0x%02X%02X}'%(c,row[i+1])); i+=2; spaced=False; continue
            if 22<=c<=23 and i+2<len(row)-1:
                parts.append('{0x%02X%02X%02X}'%(c,row[i+1],row[i+2])); i+=3; spaced=False; continue
            if c>=165:
                token=TOKENS[c-165]
                if spaced and c>=197 and token[0]>='A': parts.append(' ')
                parts.append(token)
                if c<168 or c==203 or token[-1] in '#=>': spaced=True
                else: parts.append(' '); spaced=False
            elif c in (94,96,127):
                parts.append({94:'↑',96:'£',127:'©'}[c]);spaced=True
            elif 32<=c<=126:
                parts.append(chr(c));spaced=c>32
            elif 144<=c<=164:
                parts.append('{UDG-'+chr(c-79)+'}');spaced=True
            else:
                parts.append('{0x%02X}'%c);spaced=False
            i+=1
        lines.append(f'{number:4} '+''.join(parts).rstrip())
    return '\n'.join(lines)+'\n', len(lines)

def extract_basic(blocks):
    entries=[]
    for i,block in enumerate(blocks[:-1]):
        if len(block)!=19 or block[0]!=0 or block[1]!=0: continue
        body=blocks[i+1]; expected=int.from_bytes(block[12:14],'little')
        if not body or body[0]!=255 or len(body)!=expected+2: continue
        name=block[2:12].decode('latin-1').strip() or 'program'
        basic_length=int.from_bytes(block[16:18],'little')
        if basic_length>expected: continue
        # When variables offset is 0xFFFF, dump whole data with strict line validation.
        basic=body[1:1+(basic_length if basic_length != 0xFFFF else expected)]
        listing,count=listing_from_program(basic)
        entries.append({'name':name,'listing':listing,'lines':count})
    return entries

def safe_slug(s):
    s=re.sub('[^A-Za-z0-9._-]+','-',s).strip('._-')
    return s[:100] or 'file'

def archive_members(zip_path, target):
    result=[]; used=0
    with ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            parts=PurePosixPath(info.filename.replace('\\','/')).parts
            if (not parts or any(x in ('..','') for x in parts) or info.filename.startswith('/')
                    or info.file_size>MAX_MEMBER):
                raise ValueError('Unsafe archive member '+info.filename)
            used+=info.file_size
            if used>MAX_TOTAL: raise ValueError('Archive too large when extracted')
            dest=target.joinpath(*parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src, dest.open('wb') as dst: shutil.copyfileobj(src,dst)
            result.append(dest)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path('typeins_output'))
    ap.add_argument('--catalog-only', action='store_true')
    ap.add_argument('--limit',type=int,default=0,help='For controlled tests only')
    ns=ap.parse_args(); out=ns.output
    out.mkdir(parents=True,exist_ok=True)
    index={'source':SITE,'generated_utc':datetime.now(timezone.utc).isoformat(),
           'scope':'download + tape conversion + BASIC listing; Fuse end-to-end NOT verified',
           'entries':[],'errors':[]}
    try:
        page=fetch(SITE).decode('utf-8',errors='replace')
        parser=Links();parser.feed(page)
        urls=list(dict.fromkeys(parser.urls))
        if not urls: raise ValueError('No ZIP download links found; site markup may have changed')
        if ns.limit: urls=urls[:ns.limit]
        index['discovered_zip_links']=len(parser.urls)
        (out/'source-links.txt').write_text('\n'.join(urls)+'\n',encoding='utf-8')
    except Exception as e:
        index['errors'].append({'stage':'catalog','error':str(e)})
        (out/'index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
        print('Cannot reach catalog: '+str(e))
        return 2
    if not ns.catalog_only:
        for j,url in enumerate(urls,1):
            name=safe_slug(unquote(Path(urlsplit(url).path).stem))
            item={'number':j,'name':name,'url':url,'files':[],'errors':[]}
            print(f'[{j}/{len(urls)}] {name}',flush=True)
            try:
                blob=fetch(url)
                if blob[:4]!=b'PK\x03\x04': raise ValueError('Response was not a ZIP')
                archive=out/'original-zips'/f'{j:02}-{name}.zip';archive.parent.mkdir(exist_ok=True)
                archive.write_bytes(blob)
                item.update({'zip_sha256':sha256(blob),'zip_bytes':len(blob)})
                files=archive_members(archive,out/'extracted'/f'{j:02}-{name}')
                for src in files:
                    rel=str(src.relative_to(out)); ext=src.suffix.lower()
                    f={'file':rel,'type':ext,'sha256':sha256(src.read_bytes()),'listings':[]}
                    try:
                        if ext=='.tap':
                            content=src.read_bytes()
                            blocks=tap_blocks(content)
                            d=out/'tzx'/f'{j:02}-{name}-{safe_slug(src.stem)}.tzx'
                            d.parent.mkdir(exist_ok=True);d.write_bytes(tap_to_tzx(content))
                            f['tzx']=str(d.relative_to(out));f['tap_blocks']=len(blocks)
                        elif ext=='.tzx':
                            blocks=tzx_standard_blocks(src.read_bytes())
                            d=out/'tzx'/f'{j:02}-{name}-{safe_slug(src.stem)}.tzx'
                            d.parent.mkdir(exist_ok=True);shutil.copyfile(src,d)
                            f['tzx']=str(d.relative_to(out));f['standard_blocks']=len(blocks)
                        elif ext in ('.bas','.txt'):
                            if ext=='.bas':
                                raw=src.read_bytes()
                                # Preserve provided BAS files exactly; never alter unknown source encoding.
                                d=out/'bas-original'/f'{j:02}-{name}-{safe_slug(src.name)}'
                                d.parent.mkdir(exist_ok=True);d.write_bytes(raw)
                                f['bas_original']=str(d.relative_to(out))
                            blocks=[]
                        else:
                            blocks=[]
                        if blocks:
                            for k,prog in enumerate(extract_basic(blocks),1):
                                d=out/'bas'/f'{j:02}-{name}-{safe_slug(src.stem)}-{k:02}.bas'
                                d.parent.mkdir(exist_ok=True);d.write_text(prog['listing'],encoding='utf-8')
                                f['listings'].append({'path':str(d.relative_to(out)),
                                                      'program_name':prog['name'],'line_count':prog['lines']})
                    except Exception as e:
                        f['conversion_error']=str(e)
                        item['errors'].append({'file':rel,'error':str(e)})
                    item['files'].append(f)
            except (BadZipFile, ValueError, RuntimeError, OSError) as e:
                item['errors'].append({'stage':'download-or-extract','error':str(e)})
                index['errors'].append({'url':url,'error':str(e)})
            index['entries'].append(item)
            (out/'index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"Finished {len(index['entries'])} entries, {len(index['errors'])} download failures")
    return 0 if not index['errors'] else 1

if __name__=='__main__': raise SystemExit(main())