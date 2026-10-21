#!/usr/bin/env python3
"""Verify current TZXs preserve each unique original TAP except BASIC autostart."""
from pathlib import Path
import hashlib, json, sys, zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from zx_basic_tape import parse_tap, parse_standard_tzx
root=Path(__file__).resolve().parent.parent
entries=json.loads((root/'CLEAN-INDEX.json').read_text())
with zipfile.ZipFile(root/'TOOLS/SOURCE/Spectrum-60-TAP-original.zip') as z:
    originals={p:parse_tap(z.read(p)) for p in z.namelist() if p.lower().endswith('.tap')}
assert len(originals)==60,len(originals)
used=set()
for e in entries:
    folder=e['folder']; number=e['number']
    tape=(root/folder/'BASIC'/(folder+'.tzx')).read_bytes()
    assert hashlib.sha256(tape).hexdigest()==e['original_tzx_sha256'],folder
    blocks=parse_standard_tzx(tape)
    head=blocks[0]
    assert len(head)==19 and head[:2]==b'\x00\x00' and int.from_bytes(head[14:16],'little')==32768,folder
    assert __import__('functools').reduce(lambda a,b:a^b,head,0)==0,folder
    matches=[]
    for name,orig in originals.items():
        if len(orig)!=len(blocks):continue
        old=orig[0]
        if len(old)!=19:continue
        if old[:14]==head[:14] and old[16:-1]==head[16:-1] and orig[1:]==blocks[1:]:matches.append(name)
    assert len(matches)==1,(number,matches)
    assert matches[0] not in used,matches[0]
    used.add(matches[0])
assert len(entries)==len(used)==60
print('PASS: 60 unique TZX tapes; BASIC/data preserved, non-auto-run headers and checksums valid')
