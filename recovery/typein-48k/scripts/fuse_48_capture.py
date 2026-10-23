#!/usr/bin/env python3
"""Start a full input tape in Fuse SDL 16K and capture genuine screens.

Needs Xvfb, FUSE SDL, the original 48K ROM, python-xlib and Pillow.
The runner uses real key events. It does NOT assert game correctness or that
later tape blocks were loaded; review screenshots and interact with prompts.

    python run_fuse_playback.py FILE.tzx --rom 48.rom --out smoke/
    python run_fuse_playback.py FILE.tzx --rom 48.rom --wait 12 --after-key space
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, time, hashlib
from pathlib import Path
from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest
from Xlib.support import unix_connect
unix_connect.get_auth = lambda *unused: ('', '')

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('tape',type=Path);p.add_argument('--rom',type=Path,required=True)
 p.add_argument('--fuse',default='fuse-sdl');p.add_argument('--out',type=Path,default=Path('fuse-smoke'))
 p.add_argument('--wait',type=float,default=9.0)
 p.add_argument('--boot-wait',type=float,default=14.0)
 p.add_argument('--after-key',default='',help='Comma-separated keys to press after LOAD screenshot, e.g. space,n or Return')
 p.add_argument('--after-wait',type=float,default=5.0)
 p.add_argument('--final-wait',type=float,default=0.0)
 p.add_argument('--hold-after-load',default='',help='Optional key:seconds to hold before --after-key, e.g. a:0.3')
 p.add_argument('--display',default=':97')
 p.add_argument('--fuse-speed',type=int,default=100,help='FUSE emulation speed percent (100=normal)')
 p.add_argument('--action-hold',type=float,default=0.05)
 p.add_argument('--capture-input-before-enter',action='store_true')
 p.add_argument('--type-lines', default='', help='Pipe-separated text INPUT responses, each followed by Return')
 p.add_argument('--type-action', default='', help='Pipe-separated single key presses after RUN')
 p.add_argument('--pre-action-wait',type=float,default=0.0,help='Extra wait after RUN, before scripted interactions')
 p.add_argument('--sample-interval',type=float,default=0.0,help='Seconds between extra on-emulator screen samples')
 p.add_argument('--samples',type=int,default=0,help='Number of post-action screenshots to take at sample-interval')
 p.add_argument('--post-sample-action',default='',help='Pipe-separated key presses after the timed samples')
 p.add_argument('--post-sample-hold',type=float,default=0.12)
 p.add_argument('--post-sample-wait',type=float,default=2.0)
 p.add_argument('--script-steps',default='',help='Ordered K:key, L:text, H:key:seconds, W:seconds or C:label actions separated by |, after RUN')
 p.add_argument('--pre-action-capture',default='',help='Capture settled intro before script steps')
 p.add_argument('--step-wait', type=float, default=2.0)
 p.add_argument('--finish-action', default='', help='Single key to press after all input lines')
 p.add_argument('--finish-hold', type=float, default=0.05, help='Seconds to hold final key for INKEY$ polling')
 p.add_argument('--snapshot-dialog',action='store_true',help='Capture F2 save-snapshot dialog after program (diagnostic)')
 p.add_argument('--save-snapshot',default='',help='Write FUSE state using F2 dialog to a simple relative .sna filename')
 a=p.parse_args(argv)
 started=time.monotonic();events=[];screens=[]
 if not a.tape.is_file() or not a.rom.is_file():p.error('Tape and ROM must be existing files')
 if not (shutil.which(a.fuse) or Path(a.fuse).is_file()):p.error('FUSE SDL executable not found')
 if not shutil.which('Xvfb'):p.error('Xvfb not installed')
 a.out.mkdir(parents=True,exist_ok=True)
 env=os.environ.copy()
 env.update(DISPLAY=a.display,SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy')
 xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 proc=None;d=None
 def key(symbol,pressed):
  if pressed:events.append({"seconds":round(time.monotonic()-started,3),"key":symbol})
  key_id = XK.string_to_keysym({'.':'period','-':'minus','_':'underscore'}.get(symbol,symbol))
  c = d.keysym_to_keycode(key_id)
  if not c:raise RuntimeError('X11 keysym unavailable: '+symbol)
  xtest.fake_input(d,X.KeyPress if pressed else X.KeyRelease,c)
  d.sync();time.sleep(max(0.12,.05*100/a.fuse_speed))
 def tap(symbol):key(symbol,True);key(symbol,False)
 def capture(win,path):
  geo=win.get_geometry();result=win.get_image(0,0,geo.width,geo.height,X.ZPixmap,0xffffffff)
  raw=result.data.encode('latin1') if isinstance(result.data,str) else result.data
  fmt='BGRX' if len(raw)==geo.width*geo.height*4 else 'BGR'
  img=Image.frombytes('RGB',(geo.width,geo.height),raw,'raw',fmt)
  img.save(path)
  screens.append({"seconds":round(time.monotonic()-started,3),"file":path.name})
 try:
  time.sleep(.7)
  d=display.Display(a.display)
  proc=subprocess.Popen([a.fuse,'--machine','48','--speed',str(a.fuse_speed),'--no-sound','--no-auto-load','--traps','--rom-48',str(a.rom),'--tape',str(a.tape.resolve())],env=env,cwd=str(a.out.resolve()),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  root=d.screen().root
  def children(node, depth=0):
   if depth>3:return []
   acc=[]
   for child in node.query_tree().children:
    g=child.get_geometry()
    acc.append((child,g.width,g.height,depth))
    acc.extend(children(child,depth+1))
   return acc
  wins=[]
  seen=[]
  for attempt in range(15):
   if proc.poll() is not None:raise RuntimeError('FUSE exited '+str(proc.returncode))
   seen=children(root)
   wins=[row for row in seen if 250<=row[1]<=900 and 180<=row[2]<=700]
   if wins:break
   time.sleep(.6)
  if not wins:
   raise RuntimeError('FUSE window not found; discovered '+str([(v[1],v[2],v[3]) for v in seen]))
  win=sorted(wins,key=lambda v:(abs(v[1]-320)+abs(v[2]-240),v[3]))[0][0]
  win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(a.boot_wait)
  capture(win,a.out/'01-boot.png')
  # Real Spectrum keyword mode: J is LOAD, Symbol Shift+P (Ctrl+P on
  # Fuse mapping) is the double quote character.
  tap('j')
  for _ in range(2):
   key('Control_L',True);tap('p');key('Control_L',False)
  capture(win,a.out/'02-load-typed.png')
  tap('Return');time.sleep(a.wait)
  capture(win,a.out/'03-after-load.png')
  if a.hold_after_load:
   hold_symbol,hold_s=a.hold_after_load.split(':',1)
   key(hold_symbol,True);time.sleep(float(hold_s));key(hold_symbol,False)
   time.sleep(.3);capture(win,a.out/'03b-after-hold.png')
  followups=[key.strip() for key in a.after_key.split(',') if key.strip()]
  for idx,symbol in enumerate(followups,4):
   tap(symbol);time.sleep(a.after_wait)
   capture(win,a.out/f'{idx:02d}-after-{symbol}.png')
  if a.pre_action_wait:time.sleep(a.pre_action_wait)
  if a.pre_action_capture:capture(win,a.out/('06-'+a.pre_action_capture+'.png'))
  if a.type_action:
   for idx,symbol in enumerate(a.type_action.split('|'),1):
    key(symbol,True);time.sleep(a.action_hold);key(symbol,False);time.sleep(a.step_wait)
    capture(win,a.out/f'70-action-{idx:02d}.png')
  if a.type_lines:
   for idx,entry in enumerate(a.type_lines.split('|'),1):
    for char in entry:
     if char.isupper():
      key('Shift_L',True);tap(char.lower());key('Shift_L',False)
     elif char==' ':tap('space')
     else:tap(char)
    if a.capture_input_before_enter: capture(win,a.out/f'74-input-{idx:02d}-before-enter.png')
    tap('Return');time.sleep(a.step_wait)
    capture(win,a.out/f'75-input-{idx:02d}.png')
  if a.script_steps:
   for k,chunk in enumerate(a.script_steps.split('|'),1):
    print('BEGIN step',k,chunk,round(time.monotonic()-started,1),flush=True)
    if ':' not in chunk:raise RuntimeError('script step must start K: or L:')
    kind,value=chunk.split(':',1)
    if kind=='W':
     time.sleep(float(value))
    elif kind=='C':
     if not value or any(x in value for x in '/\\'):raise ValueError('Unsafe capture name')
     capture(win,a.out/('90-'+value+'.png'))
    elif kind=='H':
     symbol,hold=value.split(':',1)
     key(symbol,True);time.sleep(float(hold));key(symbol,False)
    elif kind=='K':
     symbol='space' if value.lower()=='space' else value
     key(symbol,True);time.sleep(a.action_hold);key(symbol,False)
    elif kind=='S':
     key('Shift_L',True);key(value.lower(),True);time.sleep(a.action_hold);key(value.lower(),False);key('Shift_L',False)
    elif kind=='L':
     for char in value:
      if char.isupper():
       key('Shift_L',True);tap(char.lower());key('Shift_L',False)
      elif char==' ':tap('space')
      else:tap(char)
     capture(win,a.out/f'92-step-{k:02d}-before-enter.png')
     tap('Return')
    else:raise RuntimeError('invalid script step '+kind)
    if kind not in {'C','W'}:time.sleep(a.step_wait)
    capture(win,a.out/f'93-step-{k:02d}.png')
    print('END step',k,round(time.monotonic()-started,1),flush=True)
  if a.finish_action:
   key(a.finish_action,True);time.sleep(a.finish_hold);key(a.finish_action,False);time.sleep(a.step_wait)
   capture(win,a.out/'76-after-finish-action.png')
  if a.samples:
   if a.sample_interval <= 0 or a.samples > 60:p.error('samples must be 1..60, sample-interval >0')
   for k in range(1,a.samples+1):
    time.sleep(a.sample_interval);capture(win,a.out/f'81-sample-{k:02d}.png')
  if a.post_sample_action:
   for j,symbol in enumerate(a.post_sample_action.split('|'),1):
    key(symbol,True);time.sleep(a.post_sample_hold);key(symbol,False)
    time.sleep(a.post_sample_wait);capture(win,a.out/f'91-post-sample-{j:02d}.png')
  if a.final_wait:
   time.sleep(a.final_wait)
   capture(win,a.out/'80-after-final-wait.png')
  if a.snapshot_dialog or a.save_snapshot:
   tap('F2');time.sleep(.5)
   capture(win,a.out/'99-snapshot-dialog.png')
  if a.save_snapshot:
   if not a.save_snapshot.endswith(('.sna','.szx','.z80')) or '/' in a.save_snapshot or '\\' in a.save_snapshot:
    p.error('--save-snapshot must be a simple .sna filename')
   tap('Tab')
   for ch in a.save_snapshot:tap(ch)
   capture(win,a.out/'98-snapshot-filename.png')
   tap('Return');time.sleep(.8)
   capture(win,a.out/'97-snapshot-after-enter.png')
   tap('Return');time.sleep(.5)
   capture(win,a.out/'96-snapshot-after-confirm.png')
   if not (a.out/a.save_snapshot).is_file():
    raise RuntimeError('FUSE did not save snapshot '+a.save_snapshot)
  (a.out/'test-info.json').write_text(json.dumps({
    'tape':str(a.tape),'tape_sha256':hashlib.sha256(a.tape.read_bytes()).hexdigest(),
    'emulator':'Fuse SDL with Sinclair ZX Spectrum ROM in 48K mode',
    'commands':['LOAD ""','Return']+followups,
    'script_steps':a.script_steps,
    'keypress_events':events,
    'screenshot_timeline':screens,
    'runner_settings':{k:(str(v) if isinstance(v,Path) else v) for k,v in vars(a).items()},
    'emulator_alive':proc.poll() is None,
    'proof_limit':'screenshots only; runtime memory/final BASIC not independently verified'
  },indent=2),encoding='utf8')
  print('Screenshots:',a.out,'FUSE alive:',proc.poll() is None)
 finally:
  if proc:
   proc.terminate()
   try:proc.wait(timeout=2)
   except subprocess.TimeoutExpired:proc.kill()
  if d:d.close()
  xv.terminate()
  try:xv.wait(timeout=2)
  except subprocess.TimeoutExpired:xv.kill()
if __name__=='__main__':main()