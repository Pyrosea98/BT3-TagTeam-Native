import sys,time,struct,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine,native_preparation as native
import numpy as np
mode=sys.argv[1]
with pine.PineClient(port=28012,timeout=120) as p:
    ram=native.read_ram(p)
a=np.frombuffer(ram,dtype='<u4')
if mode=='paused':
    f=np.frombuffer(ram,dtype='<f4')
    targets={'57':57,'57*60':3420,'57*30':1710,'57*50':2850,'57*100':5700,'57*1000':57000}
    out={}
    for k,v in targets.items():
        idx=np.nonzero(a==v)[0];out[k]=[int(i)*4 for i in idx[:200]];print(k,'matches',len(idx))
    fi=np.nonzero((f>56.5)&(f<57.5))[0];out['float~57']=[int(i)*4 for i in fi[:200]];print('float ~57 matches',len(fi))
    json.dump(out,open(TRIAL/'clock-paused-matches.json','w'))
    open(TRIAL/'clock-paused.bin','wb').write(ram)
else:
    prev=json.load(open(TRIAL/'clock-paused-matches.json'));old=np.frombuffer(open(TRIAL/'clock-paused.bin','rb').read(),dtype='<u4');oldf=old.view('<f4');f=a.view('<f4')
    for k,addrs in prev.items():
        rows=[]
        for ad in addrs:
            i=ad//4
            if k=='float~57':
                if f[i]<oldf[i]-0.4:rows.append((hex(ad),float(oldf[i]),float(f[i])))
            elif a[i]<old[i] and old[i]-a[i]<old[i]:rows.append((hex(ad),int(old[i]),int(a[i])))
        print(k,'decreased:',len(rows),rows[:10])
