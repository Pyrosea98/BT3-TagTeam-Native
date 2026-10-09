import sys,struct,collections,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import claude_menu_names_audit as aud
ram=(TRIAL/'select-screen-ram-scene26.bin').read_bytes()
por=aud.iso_portraits()
print('iso portraits',len(por),'sizes',collections.Counter(len(p) for p in por).most_common(5))
t=time.time();hits={}
for j,pb in enumerate(por):
    if len(pb)<0x200:continue
    found=[]
    for off in (0,0x40,0x100,len(pb)//2,len(pb)-0x80):
        a=ram.find(pb[off:off+48],0x100000,0x8000000)
        found.append(a-off if a>=0 else None)
    hits[j]=found
have=[j for j,f in hits.items() if any(x is not None for x in f)]
print('portraits with ANY window in RAM',len(have),'of',len(por),round(time.time()-t),'s')
full=[j for j,f in hits.items() if None not in f and len(set(f))==1]
print('portraits fully contiguous',len(full),full[:20])
print({j:hits[j] for j in have[:8]})
