import sys,struct,collections,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
iso=pycdlib.PyCdlib();iso.open(str(ISO))
found=[];t=time.time()
def scan(blob,path,depth=0):
    # texture candidate?
    if len(blob)>=0xC0+0x80+0x400 and depth>=0:
        try:tex0=struct.unpack_from('<Q',blob,0x50)[0]
        except struct.error:return
        psm=(tex0>>20)&63;tw=1<<((tex0>>26)&15);th=1<<((tex0>>30)&15)
        if psm==19 and 8<=tw<=512 and 8<=th<=512 and 0xC0+tw*th+0x80+0x400<=len(blob)<=0xC0+tw*th+0x80+0x400+0x100:
            found.append((path,tw,th,len(blob)));return
    if depth>=3:return
    try:sub=ex.package(blob)
    except Exception:
        try:sub=ex.package(ex.unpack_bpe(blob))
        except Exception:return
    for i,b in enumerate(sub):scan(b,path+[i],depth+1)
with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as s:
    magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
    for i in range(cnt):
        off,size=struct.unpack_from('<II',tab,i*8)
        if size>6*1024*1024:continue
        s.seek(off);scan(s.read(size),[i])
print(round(time.time()-t),'s; PSMT8 textures',len(found))
by=collections.Counter((w,h) for _,w,h,_ in found);print(by.most_common(12))
json.dump(found,open(TRIAL/'psmt8-textures-afs1.json','w'))
ents=collections.Counter(p[0] for p,_,_,_ in found);print('top entries',ents.most_common(15))
