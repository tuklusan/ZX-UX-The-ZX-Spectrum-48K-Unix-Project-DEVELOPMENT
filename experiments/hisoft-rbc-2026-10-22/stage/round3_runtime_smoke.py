"""Bounded actual ZX-UX kernel smoke for published Round 2 SSX binaries.

Every result identifies the existing linked file and its real ZX-UX run status.
A start is not a completion, and a frame limit is not a successful game run.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/zx-ux-sdk'))
import rld
import rvm


def main():
    games=sorted((ROOT/'src/bonus/60-programs').glob('[0-9][0-9]-*'))
    targets=sorted(p for game in games for p in (game/'bin').glob('*.ssx'))
    if len(games)!=60 or len(targets)!=15:
        raise RuntimeError(f'expected 60 game directories and 15 linked SSX files, got {len(games)} and {len(targets)}')
    system=ROOT/'dist/zx-ux/tzx/ZX-UX.tzx'
    if not system.is_file():
        raise RuntimeError('missing frozen ZX-UX system tape')
    rows=[]
    for p in targets:
        data=p.read_bytes()
        rld.parse_ssx(data)
        row={'game':p.parents[1].name,'ssx_sha256':hashlib.sha256(data).hexdigest(),
             'ssx_bytes':len(data),'booted':False,'started':False,
             'reason':'not attempted','runtime_finished':False}
        try:
            result=rvm.run_kernel(p,frames=300,system=system,cache=True)
            row['booted']=True
            row['started']=result.fg is not None and result.fg.started is not None
            row['reason']=result.why
            row['runtime_finished']=result.why=='exit'
            row['runtime_status']=result.fg.status if result.why=='exit' else None
            row['machine_syscalls']=result.session.syscalls
            screen,_=result.picture()
            row['screen_sha256']=hashlib.sha256(screen).hexdigest()
        except Exception as exc:
            row['reason']=type(exc).__name__
            row['detail']=str(exc)
        rows.append(row)
        print('ZX-UX runtime',row['game'],'started',row['started'],
              'reason',row['reason'],'status',row.get('runtime_status'),flush=True)
    out=ROOT/'build/tmp/rbc-round3'
    out.mkdir(parents=True,exist_ok=True)
    (out/'runtime-15.json').write_text(json.dumps({'system_tape':'dist/zx-ux/tzx/ZX-UX.tzx',
                                                   'frames_per_game':300,'results':rows},indent=2)+'\n')
    print('Runtime smoke counts',sum(x['started'] for x in rows),'started;',
          sum(x['runtime_finished'] for x in rows),'finished;',len(rows),'attempted')
    if len(rows)!=15:
        raise RuntimeError('runtime outcome set incomplete')

if __name__=='__main__':main()