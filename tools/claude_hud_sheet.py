import sys,struct,json
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
found=json.load(open(TRIAL/'psmt8-textures-afs1.json'))
want=[f for f in found if (f[1],f[2])!=(64,64)]
iso=pycdlib.PyCdlib();iso.open(str(ISO))
def fetch(path):
    with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as s:
        magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
        off,size=struct.unpack_from('<II',tab,path[0]*8);s.seek(off);blob=s.read(size)
    for i in path[1:]:
        try:sub=ex.package(blob)
        except Exception:sub=ex.package(ex.unpack_bpe(blob))
        blob=sub[i]
    return blob
def decode(blob,w,h):
    pix=blob[0xC0:0xC0+w*h];pal=blob[0xC0+w*h+0x80:0xC0+w*h+0x80+0x400]
    cols=[]
    for i in range(256):
        e=(i&0xE7)|((i&8)<<1)|((i&16)>>1);r,g,b,a=pal[e*4:e*4+4];cols.append((r,g,b,min(255,a*2)))
    im=Image.new('RGBA',(w,h))
    px=im.load()
    for y in range(h):
        for x in range(w):
            block=(y&~15)*w+(x&~15)*2;swap=(((y+2)>>2)&1)*4;row=(((y&~3)>>1)+(y&1))&7
            src=block+row*w*2+((x+swap)&7)*4+((y>>1)&1)+((x>>2)&2)
            px[x,y]=cols[pix[src]] if src<len(pix) else (255,0,255,255)
    return im
tiles=[]
seen=set()
for path,w,h,_ in want:
    key=(tuple(path[:1]),w,h)
    try:blob=fetch(path);im=decode(blob,w,h)
    except Exception as e:continue
    tiles.append((path,im))
print('decoded',len(tiles))
# contact sheets: width 1100
sheets=[];x=y=0;rowh=0;W=1100;cur=Image.new('RGBA',(W,1400),(40,40,40,255));d=ImageDraw.Draw(cur)
for path,im in tiles:
    w,h=im.size
    if x+w>W:x=0;y+=rowh+14;rowh=0
    if y+h+14>1400:sheets.append(cur);cur=Image.new('RGBA',(W,1400),(40,40,40,255));d=ImageDraw.Draw(cur);x=y=0;rowh=0
    cur.alpha_composite(im,(x,y+12));d.text((x,y),'.'.join(map(str,path)),fill=(255,255,0,255));x+=w+6;rowh=max(rowh,h+12)
sheets.append(cur)
out=TRIAL/'hud-sheets';out.mkdir(exist_ok=True)
for i,sh in enumerate(sheets):sh.convert('RGB').save(out/f'sheet{i}.png')
print('sheets',len(sheets))
