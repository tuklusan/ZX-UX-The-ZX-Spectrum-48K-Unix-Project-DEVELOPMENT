#!/usr/bin/python3
import os,base64,json,hashlib,struct,subprocess,time,traceback
from pathlib import Path
from Xlib import display, X
from PIL import Image
p=Path('.github/galaxians-lab-temp')
out=p/'fuse-probe'
out.mkdir(exist_ok=True)
data=base64.b64decode((p/'HiSoft_BASIC_TAP_0.b64').read_text())
(out/'HiSoft_BASIC.tap').write_bytes(data)
at=0;blocks=[];last=None
while at<len(data):
 n=struct.unpack_from('<H',data,at)[0];at+=2
 b=data[at:at+n];at+=n
 info={'index':len(blocks),'bytes':len(b),'flag':b[0],'check_xor':__import__('functools').reduce(lambda x,y:x^y,b,0)}
 if len(b)==19 and b[0]==0:
  info.update(type=b[1],filename=b[2:12].decode('latin1'),length=struct.unpack_from('<H',b,12)[0],param1=struct.unpack_from('<H',b,14)[0],param2=struct.unpack_from('<H',b,16)[0])
 if len(b)>16 and b[0]==255:
  info['first_data_bytes']=b[1:24].hex()
 blocks.append(info)
json.dump({'tape_sha256':hashlib.sha256(data).hexdigest(),'blocks':blocks},open(out/'tape-blocks.json','w'),indent=2)
env=os.environ.copy();env['SDL_AUDIODRIVER']='dummy';env['HOME']=str(Path.cwd()/'/tmp') if False else '/tmp'
cmd=['fuse-sdl','--machine','48','--auto-load','--no-sound','--speed','400','--tape',str(out/'HiSoft_BASIC.tap')]
with open(out/'fuse-stdout.log','w') as stdout,open(out/'fuse-stderr.log','w') as stderr:
 proc=subprocess.Popen(cmd,env=env,stdout=stdout,stderr=stderr)
 try:
  time.sleep(12)
  d=display.Display()
  root=d.screen().root
  wins=[]
  for w in root.query_tree().children:
   try: wins.append(w.get_wm_name())
   except: pass
  sz=d.screen().width_in_pixels,d.screen().height_in_pixels
  raw=root.get_image(0,0,*sz,X.ZPixmap,0xffffffff).data
  img=Image.frombytes('RGB',sz,raw,'raw','BGRX')
  img.save(out/'after-compiler-load.png')
  json.dump({'cmd':cmd,'pid':proc.pid,'running':proc.poll() is None,'window_titles':wins,'screenshot':str(out/'after-compiler-load.png')},open(out/'fuse-result.json','w'),indent=2)
 finally:
  proc.terminate()
  try:proc.wait(timeout=3)
  except subprocess.TimeoutExpired:proc.kill()
print(json.dumps({'blocks':blocks,'fuse_result':json.load(open(out/'fuse-result.json'))},sort_keys=True))
