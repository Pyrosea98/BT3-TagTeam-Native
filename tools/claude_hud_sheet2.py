import sys,struct,json
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
res=json.load(open(TRIAL/'textures-all-afs.json'))
iso=pycdlib.PyCdlib();iso.open(str(ISO))
def fetch(name,path):
    with iso.open_file_from_iso(iso_path=f'/DATA/{name}.AFS;1') as s:
        magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
        off,size=struct.unpack_from('<II',tab,path[0]*8);s.seek(off);blob=s.read(size)
    for i in path[1:]:
        try:sub=ex.package(blob)
        except Exception:sub=ex.package(ex.unpack_bpe(blob))
        blob=sub[i]
    return blob
def ct32(blob,w,h):
    data=blob[0xC0:0xC0+w*h*4];im=Image.new('RGBA',(w,h));px=im.load()
    for y in range(h):
        for x in range(w):
            r,g,b,a=data[(y*w+x)*4:(y*w+x)*4+4];px[x,y]=(r,g,b,min(255,a*2))
    return im
def t4(blob,w,h):
    pix=blob[0xC0:0xC0+w*h//2];pal=blob[0xC0+w*h//2:0xC0+w*h//2+0x40+0x80]
    # palette location unknown: search 64-byte palette after 0x80 header
    po=0xC0+w*h//2+0x80;pal=blob[po:po+64]
    cols=[]
    for i in range(16):
        r,g,b,a=pal[i*4:i*4+4] if len(pal)>=64 else (i*16,i*16,i*16,255);cols.append((r,g,b,min(255,a*2)))
    im=Image.new('RGBA',(w,h));px=im.load()
    for y in range(h):
        for x in range(w):
            i=y*w+x;v=pix[i>>1];v=(v>>4) if i&1 else v&15;px[x,y]=cols[v]
    return im
tiles=[]
for name,lst in res.items():
    for path,psm,w,h,_ in lst:
        if psm not in (0,20):continue
        if name=='PZS3US2' :continue
        try:
            blob=fetch(name,path);im=ct32(blob,w,h) if psm==0 else t4(blob,w,h)
        except Exception as e:continue
        tiles.append((f'{name[-1]}:{".".join(map(str,path))} p{psm}',im))
print('tiles',len(tiles))
W=1100;sheets=[];cur=Image.new('RGBA',(W,1400),(60,60,60,255));d=ImageDraw.Draw(cur);x=y=0;rowh=0
for label,im in tiles:
    w,h=im.size
    if w>W:im=im.resize((W,max(1,h*W//w)));w,h=im.size
    if x+w>W:x=0;y+=rowh+14;rowh=0
    if y+h+14>1400:sheets.append(cur);cur=Image.new('RGBA',(W,1400),(60,60,60,255));d=ImageDraw.Draw(cur);x=y=0;rowh=0
    cur.alpha_composite(im,(x,y+12));d.text((x,y),label,fill=(255,255,0,255));x+=w+6;rowh=max(rowh,h+12)
sheets.append(cur)
out=TRIAL/'hud-sheets2';out.mkdir(exist_ok=True)
for i,sh in enumerate(sheets):sh.convert('RGB').save(out/f'sheet{i}.png')
print('sheets',len(sheets))
