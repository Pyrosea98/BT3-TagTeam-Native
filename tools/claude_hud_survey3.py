import sys,struct,collections,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
iso=pycdlib.PyCdlib();iso.open(str(ISO))
res={}
for name in ('PZS3US0','PZS3US2','PZS3US1'):
    found=[];psms=collections.Counter();t=time.time()
    def scan(blob,path,depth=0):
        if len(blob)>=0x100:
            try:tex0=struct.unpack_from('<Q',blob,0x50)[0]
            except struct.error:tex0=0
            psm=(tex0>>20)&63;tw=1<<((tex0>>26)&15);th=1<<((tex0>>30)&15)
            if psm in (19,20,0,2) and 8<=tw<=1024 and 8<=th<=1024:
                bpp={19:8,20:4,0:32,2:16}[psm]
                need=0xC0+tw*th*bpp//8
                if need<=len(blob)<=need+0x600:
                    psms[psm]+=1;found.append((path,psm,tw,th,len(blob)));return
        if depth>=3:return
        try:sub=ex.package(blob)
        except Exception:
            try:sub=ex.package(ex.unpack_bpe(blob))
            except Exception:return
        for i,b in enumerate(sub):scan(b,path+[i],depth+1)
    try:
        with iso.open_file_from_iso(iso_path=f'/DATA/{name}.AFS;1') as s:
            magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
            for i in range(cnt):
                off,size=struct.unpack_from('<II',tab,i*8)
                if size>6*1024*1024 or size<64:continue
                s.seek(off);scan(s.read(size),[i])
    except Exception as e:print(name,'ERR',e);continue
    print(name,cnt,'entries;',round(time.time()-t),'s; textures by psm',dict(psms))
    res[name]=found
json.dump(res,open(TRIAL/'textures-all-afs.json','w'))
