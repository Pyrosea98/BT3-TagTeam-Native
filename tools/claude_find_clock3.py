import sys,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine,native_preparation as native
with pine.PineClient(port=28012,timeout=120) as p:
    ram=native.read_ram(p)
new=np.frombuffer(ram,dtype='<u4');old=np.frombuffer(open(TRIAL/'clock-paused.bin','rb').read(),dtype='<u4')
d=old.astype(np.int64)-new.astype(np.int64)
for lo,hi,name in ((3000,3700,'frames@60'),(1500,1800,'frames@30'),(2700,2950,'frames@50'),(5500,5800,'x100'),(50,60,'seconds'),(55000,58000,'ms')):
    m=(old>=lo)&(old<=hi)&(d>0)&(d<(hi-lo))
    idx=np.nonzero(m)[0]
    print(name,len(idx),[(hex(int(i)*4),int(old[i]),int(new[i])) for i in idx[:12]])
