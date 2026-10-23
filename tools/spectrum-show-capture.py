#!/usr/bin/env python3
"""Run exported Spectrum Show BASIC tapes in Fuse, capture timed frames and key events.

The frames are real X11 screenshots of Fuse. Gameplay is labeled as a candidate
until a person confirms the displayed game state; screen changes alone cannot
establish playable behavior. No original BASIC or tape is modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import traceback
import zipfile
from collections import Counter

from PIL import Image, ImageChops, ImageGrab, ImageStat
from Xlib import X, XK, display
from Xlib.ext import xtest

START_KEYS = {
    '01-searcher': ['Return', '7', '9'],
    '02-newyork': ['Return', '3', 'Return', '5', '8'],
    '03-starswarm': ['text:ace', 'Return', 'space', 'space', '5'],
    '05-moonbuggy': ['1', 'Return', 'space', '5', '8'],
    '07-santanightmare': ['q', 'a', 'o', 'p', 'space', 'Return'],
    '10-galaxiansfix2': ['Return', 'space', '5', '8', '0'],
    '13-firefoxcomplete': ['text:y', 'Return', 'space', '5'],
    '14-outlander': ['text:n', 'Return', 'space', '5', '8'],
    '15-potholefix': ['text:n', 'Return', 'space', '5', '8'],
    '20-spacewaste': ['space', '5', '8', '0'],
    '21-mower': ['space', 'q', 'a', 'o', 'p'],
    '22-xmas2022': ['space', 'Return', '5', '8'],
    '23-scrumping': ['Return', 'space', 'q', 'a', 'o'],
    '27-donkeyape': ['space', '5', '8', '0'],
    '30-chickens': ['text:15', 'Return', 'text:10', 'Return', 'space', '5'],
    '32-poojan': ['space', 'Return', '5', '8'],
    '33-groto': ['space', 'p', 'l', 'z', 'x'],
    '34-redcarpet': ['space', 'text:n', 'Return', '5', '8'],
    '36-docked': ['space', '5', '8', '0'],
    '37-spaceinv': ['Return', 'text:n', 'Return', '5', '0'],
    '38-gun': ['space', '5', '8', '0'],
    '39-compspacegames': ['text:1', 'Return', 'text:5', 'Return', 'space'],
    '42-robot-final': ['text:y', 'Return', 'text:5', 'Return', 't', 'f'],
    '43-dungeonfix': ['space', 'c', 'Return', '1', 'Return'],
    '44-races': ['space', 'Return', 'text:5', 'Return', '5'],
    '45-astrocrash': ['space', 'space', '5', '8', '0'],
    '46-chasm-final': ['p', '5', '8', '0'],
    '49-bankraid': ['space', '5', '8', '0'],
    '50-monsters': ['n', 'space', '5', '8'],
}
DEFAULT_KEYS = ['Return', 'space', '1', 'Return', '5']


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def do_key(d, key, held=0.10):
    key = 'space' if key in ('Space', ' ') else key
    symbol = XK.string_to_keysym(key)
    code = d.keysym_to_keycode(symbol)
    if not code:
        raise ValueError('Unrecognized X key '+key)
    xtest.fake_input(d, 2, code)
    d.sync()
    time.sleep(held)
    xtest.fake_input(d, 3, code)
    d.sync()
    time.sleep(0.10)


def symbol_quote(d):
    # In Fuse, X Control maps to the Spectrum Symbol Shift key.
    symbol = XK.string_to_keysym('Control_L')
    code = d.keysym_to_keycode(symbol)
    xtest.fake_input(d, 2, code)
    d.sync()
    time.sleep(0.05)
    do_key(d, 'p', 0.09)
    xtest.fake_input(d, 3, code)
    d.sync()
    time.sleep(0.07)


def action(d, value):
    if value.startswith('text:'):
        for char in value[5:]:
            do_key(d, char.lower(), 0.07)
    else:
        do_key(d, value)


def plan_for(name):
    for prefix, keys in START_KEYS.items():
        if name.startswith(prefix):
            return keys
    return DEFAULT_KEYS


def screen_stats(img):
    # Keep this strictly observational, no speculative state classification.
    rgb = img.convert('RGB')
    colors = rgb.getcolors(rgb.width*rgb.height) or []
    palette = sorted(((n, rgbv) for n, rgbv in colors), reverse=True)
    return {'distinct_rgb':len(colors), 'dominant_rgb':[list(c) for _, c in palette[:3]],
            'dominant_pixel_fraction':round((palette[0][0]/(rgb.width*rgb.height)) if palette else 0,4)}


def detect_source_issues(code):
    out=[]
    if re.search(r'\bLOAD\s*""\s*CODE\b',code, re.I):out.append('tape expects a separate machine-code block')
    if 'USR ' in code.upper():out.append('program may depend on machine code or custom characters')
    if re.search(r'\bRANDOMIZE\s+USR\b',code,re.I):out.append('program invokes machine code')
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tapes',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--rom',required=True)
    ap.add_argument('--speed',type=int,default=400)
    ap.add_argument('--limit',type=int,default=0)
    ap.add_argument('--base-wait',type=float,default=1.5)
    ap.add_argument('--intro-wait',type=float,default=2.25)
    ap.add_argument('--step-wait',type=float,default=1.35)
    ap.add_argument('--fuse',default='fuse')
    ap.add_argument('--select-file',default='')
    ap.add_argument('--key-map',default='')
    args=ap.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=True)
    z=zipfile.ZipFile(args.tapes)
    tapes=sorted(x for x in z.namelist() if x.startswith('tap/') and x.lower().endswith('.tap'))
    if args.select_file:
        selected=set(json.loads(Path(args.select_file).read_text()))
        tapes=[x for x in tapes if Path(x).stem in selected]
        assert len(tapes)==len(selected),(len(tapes),len(selected))
    if args.limit:tapes=tapes[:args.limit]
    key_overrides=json.loads(Path(args.key_map).read_text()) if args.key_map else {}
    d=display.Display(os.environ.get('DISPLAY',':99'))
    records=[]
    for idx, member in enumerate(tapes,1):
        name=Path(member).stem
        sub=root/'frames'/name
        sub.mkdir(parents=True,exist_ok=True)
        content=z.read(member)
        local=sub/(name+'.tap');local.write_bytes(content)
        src='basic-for-zmakebas/'+name+'.bas'
        listing=z.read(src).decode('utf8','replace') if src in z.namelist() else ''
        cues=[line.strip()[:200] for line in listing.splitlines() if re.search('PRESS|INPUT|PAUSE 0|KEYS|START',line,re.I)][:20]
        rec={'name':name,'tape':member,'tape_sha256':hash_bytes(content),'source_listing':src,'notes':detect_source_issues(listing),
             'instruction_cues':cues,'input_plan':key_overrides.get(name, plan_for(name)),'captures':[], 'errors':[], 'state':'not_started'}
        proc=None
        print(f'[{idx}/{len(tapes)}] {name}',flush=True)
        try:
            env=os.environ.copy();env.setdefault('SDL_AUDIODRIVER','dummy')
            proc=subprocess.Popen([args.fuse,'--machine','48','--rom-48',str(Path(args.rom).resolve()),
                '--no-sound','--speed',str(args.speed),'--tape',str(local.resolve())],
                stdout=(sub/'fuse.log').open('wb'),stderr=subprocess.STDOUT,env=env)
            time.sleep(args.base_wait)
            # Focus the newest SDL Spectrum window on the shared Xvfb desktop.
            for window in reversed(d.screen().root.query_tree().children):
                try:
                    geometry=window.get_geometry()
                    if geometry.width>=250 and geometry.height>=200:
                        window.set_input_focus(X.RevertToParent,X.CurrentTime)
                        d.sync()
                        break
                except Exception:
                    continue
            if proc.poll() is not None:raise RuntimeError('Fuse exited immediately with code '+str(proc.returncode))
            # Sinclair 48K editor: J generates LOAD; Symbol Shift + P generates the quotation mark.
            do_key(d,'j');symbol_quote(d);symbol_quote(d);do_key(d,'Return');time.sleep(1.10)
            capture(root, sub,rec,'loaded')
            do_key(d,'r');do_key(d,'Return')
            time.sleep(args.intro_wait)
            capture(root,sub,rec,'intro_early')
            time.sleep(args.intro_wait)
            capture(root,sub,rec,'intro_late')
            for num, key in enumerate(rec['input_plan'],1):
                action(d,key)
                time.sleep(args.step_wait)
                capture(root,sub,rec,f'after_{num:02d}_{re.sub("[^a-zA-Z0-9]","_",key)}')
                if proc.poll() is not None:
                    rec['errors'].append('Fuse closed during key sequence');break
            time.sleep(args.step_wait)
            capture(root,sub,rec,'after_wait')
            # This only proves frames were captured, not that gameplay occurred.
            baseline = next((x for x in rec['captures'] if x['label']=='intro_late'),None)
            after = [x for x in rec['captures'] if x['label'].startswith('after_')]
            changed=[x for x in after if baseline and x['center_sha256']!=baseline['center_sha256']]
            rec['state']='screen_change_after_keys' if changed else 'captured_no_observed_change'
            rec['distinct_after_frames']=len({x['center_sha256'] for x in after})
            if changed:
                # Actual final game state must be checked by examining the frame.
                (sub/'candidate_gameplay.png').write_bytes((sub/(changed[-1]['label']+'.png')).read_bytes())
            else:
                (sub/'candidate_gameplay.png').write_bytes((sub/'after_wait.png').read_bytes())
            (sub/'candidate_intro.png').write_bytes((sub/'intro_early.png').read_bytes())
        except Exception as exc:
            rec['state']='execution_error';rec['errors'].append(str(exc));rec['errors'].append(traceback.format_exc()[-2400:])
        finally:
            if proc:
                try:
                    proc.terminate();proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=2)
            # do not preserve redundant local tapes inside screenshot archive
            if local.exists():local.unlink()
            records.append(rec)
            (root/'report.json').write_text(json.dumps({'records':records,'total':len(tapes),
                   'counts':dict(Counter(r['state'] for r in records)),
                   'notice':'Screen change after keys does not confirm actual game state or full gameplay'},indent=2)+'\n')
        print('  ->',rec['state'],'frames',len(rec['captures']),'errors',len(rec['errors']),flush=True)
    try:
        from PIL import ImageDraw
        for offset in range(0,len(records),12):
            batch=records[offset:offset+12]
            img=Image.new('RGB',(660, (len(batch)+1)*190), (255,255,255))
            draw=ImageDraw.Draw(img)
            draw.text((3,2),'Fuse screenshots: intro (left) / candidate later frame (right)',fill=(0,0,0))
            for i,r in enumerate(batch):
                path=root/'frames'/r['name'];y=(i+1)*190
                draw.text((3,y-17),r['name'][:75]+'  ['+r['state']+']',fill=(0,0,0))
                for j,label in enumerate(['candidate_intro','candidate_gameplay']):
                    p=path/(label+'.png')
                    if p.exists():
                        shot=Image.open(p).convert('RGB').resize((320,168))
                        img.paste(shot,(j*330,y))
            img.save(root/f'contact-sheet-{offset//12+1:02d}.png')
    except Exception as e:print('Contact sheet error:',e,flush=True)
    (root/'README.txt').write_text('Actual screenshots from Fuse 48K using the generated TAP images.\n'
        'Screens captured before and after sending keys. Files called candidate_gameplay are\n'
        'later frames, NOT independently proven active play. Inspect the stage screenshots and\n'
        'report.json for each attempt. intro and later frames may be identical, and games with\n'
        'missing machine code or broken BASIC cannot be counted as running.\n')
    with zipfile.ZipFile(root.parent/'spectrum-show-fuse-screenshots.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for f in sorted(root.rglob('*')):
            if f.is_file():out.write(f,str(f.relative_to(root)))
    print('FINISHED',len(records),'captures',sum(len(r['captures']) for r in records),
          'statuses',dict(Counter(r['state'] for r in records)),flush=True)

def capture(root,sub,rec,label):
    # Fuse SDL defaults to the center of an 800x600 Xvfb desktop at 320x240.
    # We save exactly the actual observed screen pixels, not a redraw of BASIC.
    full=ImageGrab.grab()
    w,h=full.size
    rect=(w//2-160,h//2-120,w//2+160,h//2+120)
    center=full.crop(rect)
    p=sub/(label+'.png')
    center.save(p)
    rec['captures'].append({'label':label,'file':str(p.relative_to(root)),
       'center_sha256':hash_bytes(center.tobytes()),'image_sha256':hash_bytes(p.read_bytes()),
       'pixel_stats':screen_stats(center)})

if __name__=='__main__':main()