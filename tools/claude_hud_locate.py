import sys,struct,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
res=json.load(open(TRIAL/'textures-all-afs.json'))
ram=(TRIAL/'controller/game/analysis/prepared-states/20261006-194551-a32ecc27/16-ready-held.bin').read_bytes()
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
out=[]
for path,psm,w,h,size in res['PZS3US1']:
    if psm not in (20,0) and not (psm==19 and (w,h)!=(64,64)):continue
    blob=fetch(path);body=blob[0xC0:0xC0+min(len(blob)-0xC0,w*h*(4 if psm==0 else 1 if psm==19 else 1)//(1 if psm!=20 else 2))]
    if len(body)<512:continue
    hits=[]
    for off in (len(body)//5,len(body)//2,len(body)*4//5):
        a=ram.find(body[off:off+64],0x100000,0x8000000)
        hits.append(None if a<0 else a-off)
    if any(h_ is not None for h_ in hits):out.append((path,psm,w,h,hits))
print('textures found verbatim in the battle-ready RAM:',len(out))
bypsm={}
for path,psm,w,h,hits in out:
    if psm==20 or (psm==0) or (w,h)!=(64,64):print('.'.join(map(str,path)),'psm',psm,w,h,[hex(x) if x is not None else None for x in hits])
