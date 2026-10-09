import sys,struct,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import pycdlib
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
iso=pycdlib.PyCdlib();iso.open(str(ISO))
print([r for r in (c.file_identifier().decode() for c in iso.list_children(iso_path='/DATA')) if r.endswith(';1')][:40])
with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as s:
    magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8)
    print('AFS entries',cnt)
    stats=collections.Counter();tm2=[]
    for i in range(cnt):
        off,size=struct.unpack_from('<II',tab,i*8)
        s.seek(off);head=s.read(min(size,64))
        k=head[:4]
        stats[k]+=1
        if k==b'TIM2':tm2.append((i,size))
    print('magic counts',stats.most_common(8))
    print('TIM2 entries',len(tm2),tm2[:20])
