import sys,struct,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
WANT={(20,7,7):'P4_128x128',(19,8,6):'P8_256x64',(19,7,6):'P8_128x64'}
hits=[]
def scan_blob(blob,path):
    n=len(blob)//8
    if not n:return
    w=struct.unpack_from('<%dQ'%n,blob,0)
    for i,v in enumerate(w):
        k=((v>>20)&63,(v>>26)&15,(v>>30)&15)
        if k in WANT and i+1<n and w[i+1] in (6,7):hits.append((path,i*8,WANT[k],v&0x3FFF,(v>>14)&63))
def descend(blob,path,depth):
    scan_blob(blob,path)
    if depth>=5:return
    try:sub=ex.package(blob)
    except Exception:
        try:sub=ex.package(ex.unpack_bpe(blob))
        except Exception:return
    for i,b in enumerate(sub):
        if len(b)>64:descend(b,path+[i],depth+1)
def run(afs,name,lo,hi):
    with open(afs,'rb') as s:
        magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
        for i in range(cnt):
            off,size=struct.unpack_from('<II',tab,i*8)
            if not lo<=size<=hi:continue
            s.seek(off);descend(s.read(size),[name,i],0)
    print(name,'done',len(hits),flush=True)
t=time.time()
D=HERE/'power-scale-input/DATA'
run(D/'MOD.AFS','MOD',128,32*1024*1024)
run(D/'DLC.AFS','DLC',128,32*1024*1024)
import pycdlib
iso=pycdlib.PyCdlib();iso.open(str(HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'))
# big AFS1 entries
with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as s:
    magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
    for i in range(cnt):
        off,size=struct.unpack_from('<II',tab,i*8)
        if size>6*1024*1024:
            s.seek(off);descend(s.read(min(size,64*1024*1024)),['PZS3US1-big',i],0)
print('all done',round(time.time()-t),'s')
p8=[h for h in hits if h[2]!='P4_128x128'];print('P8 hits',len(p8),p8[:12])
import collections
p4=collections.Counter((h[0][0],h[0][1]) for h in hits if h[2]=='P4_128x128');print('P4 entries',len(p4),p4.most_common(5))
json.dump(hits,open(TRIAL/'hud-provenance-scan2.json','w'))
