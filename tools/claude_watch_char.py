"""Claude: tiny read-only watcher: prints when side-0/side-1 leader (character, costume) changes in an ordinary 1v1 (short connections, 3 Hz)."""
import sys,time,struct
from pathlib import Path
T=Path(__file__).resolve().parent/'power-scale-trial'
sys.path.insert(0,str(T/'controller/game/tools'))
import pine
last=None;end=time.time()+float(sys.argv[1]) if len(sys.argv)>1 else time.time()+240
while time.time()<end:
    try:
        with pine.PineClient(port=28012,timeout=2) as p:
            m=p.read_u32(0x2FEB14)
            if 0x100000<=m<=0x7ff0000 and p.read_u32(m)==2:
                arr=p.read_u32(m+4);out=[]
                for side in range(2):
                    a=arr+side*0x1600;slot=p.read_u32(a+0x994)
                    if slot<5:
                        row=a+0x9A4+slot*0xA4;c,co=struct.unpack('<2I',p.read(row,8));out.append((c,co,p.read_u32(a+0x948)))
                key=tuple((c,co) for c,co,_ in out)
                if key!=last:
                    print(time.strftime('%H:%M:%S'),'leaders (char,costume):',key,'actions',[x[2] for x in out],flush=True);last=key
    except (OSError,pine.PineError,struct.error):pass
    time.sleep(0.3)
