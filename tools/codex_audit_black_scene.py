from pathlib import Path
import json,struct
import numpy as np
HERE=Path(__file__).resolve().parent
root=HERE/'power-scale-trial/guest-exit-captures/black-scene-156042044107000'
ram=(root/'ram.bin').read_bytes()
u=lambda p:struct.unpack_from('<I',ram,p)[0]
result={'globals':{hex(p):u(p) for p in (0x2FEB14,0x2FEB38,0x333700,0x3337B8,0x331DEC,0xC4004,0xD8084,0x304270-22172,0x304270-22176,0x304270-22180)},'actors':[], 'controls':{}}
for p,n in ((0x0711F000,29),(0x06C0F000,24),(0x0762F000,16),(0x0767F000,16),(0x077CF000,8)):
    result['controls'][hex(p)]=[u(p+4*i) for i in range(n)]
manager=u(0x2FEB14);result['manager']={str(o):u(manager+o) for o in (0,600,604,608,612,616,620,624,628)}
for i in range(u(0xD8084)):
    p=u(0xD8040+4*i);mid=u(p+12);m=u(0x31C640+4*mid)
    result['actors'].append(dict(id=i,pointer=hex(p),model=hex(m),mid=mid,character=u(m+12),action=u(p+2376),
        model_flags=[u(m+4),u(m+8)],flags={str(o):ram[p+o] for o in (4255,4295,0x10A9,0x10D1)},
        hp=u(p+0x9E4+164*u(p+0x994)),holds=[u(p+o) for o in (0x1278,0x127C,0x1280,0x1284)]))
result['cameras']={}
result['stage']={hex(p):u(p) for p in (0x31BE68,0x31BE74,0x2FE9C8,0x2FE9B0,0x304270-0x5154)}
for key,global_at,size in (('asset_bank',0x304270-0x5154,0x80),('director',0x2FE9B0,0x40)):
    p=u(global_at);result['stage'][key]=dict(pointer=hex(p),words=[u(p+i) for i in range(0,size,4)])
words=np.frombuffer(ram,dtype='<u4')
result['scene_callbacks']={}
for target in (0x1272B0,0x127430,0x127680,0x1278B0):
    found=[int(i)*4 for i in np.flatnonzero(words==target) if int(i)*4>=0x2C0000]
    result['scene_callbacks'][hex(target)]=[dict(at=hex(p),words=[u(p-4+i) for i in range(0,64,4)]) for p in found[:20]]
# Native 127120 returns the fixed job pool at 301058, not the asset bank.
result['scene_jobs']={'slots':[[u(0x301058+64*i+j) for j in range(0,64,4)] for i in range(8)],
                      'free_list':[u(0x301258+j) for j in range(0,12,4)]}
result['scene_flags64']=hex(struct.unpack_from('<Q',ram,0x3337B8)[0])
for key,p in [('bound',u(0x304270-22176)),('cinematic',u(0x304270-22180))]+[('quad'+str(i),0x06C05000+1024*i) for i in range(2)]:
    result['cameras'][key]=dict(pointer=hex(p),words={str(o):u(p+o) for o in (512,516,520,524,640,644,648,704,768,772,776,812)})
print(json.dumps(result,indent=2))
(HERE/'power-scale-trial/codex-black-scene-audit.json').write_text(json.dumps(result,indent=2))
