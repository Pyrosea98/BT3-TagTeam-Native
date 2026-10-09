"""Exercise MADD variants through the native interpreter on a diagnostic runner."""
from pathlib import Path
import sys,struct,time
sys.path.insert(0,str(Path(__file__).resolve().parent/'power-scale-trial/controller/game/tools'))
from pine import PineClient
CODE=0x07680000;CONTROL=0x0768f000;OUTPUT=0x07fff100
cases=[(0,20,12,8,2),(0,0xfffffffd,7,5,2),(1,0xffffffff,2,3,2),
       (0x20,0xfffffffd,7,5,2),(0x21,0xffffffff,2,3,2),(0,20,12,8,0)]
words=[]
def li(reg,value):words.extend([(15<<26)|(reg<<16)|((value>>16)&65535),(13<<26)|(reg<<21)|(reg<<16)|(value&65535)])
li(8,OUTPUT)
expected=[]
sx=lambda v:v|0xffffffff00000000 if v&0x80000000 else v
for index,(fn,a,b,acc,rd) in enumerate(cases):
    li(4,a);li(5,b);li(6,acc);li(7,0);li(2,0x12345678)
    bank=bool(fn&0x20)
    words.extend([((0x1c if bank else 0)<<26)|(6<<21)|0x13,((0x1c if bank else 0)<<26)|(7<<21)|0x11,
                  (0x1c<<26)|(4<<21)|(5<<16)|(rd<<11)|fn,
                  ((0x1c if bank else 0)<<26)|(10<<11)|0x12,((0x1c if bank else 0)<<26)|(11<<11)|0x10])
    for offset,reg in ((0,10),(8,11),(16,2)):words.append((0x3f<<26)|(8<<21)|(reg<<16)|(index*32+offset))
    signed=lambda v:v-0x100000000 if v&0x80000000 else v
    result=(acc+(a*b if fn&1 else signed(a)*signed(b)))&0xffffffffffffffff
    expected.append((sx(result&0xffffffff),sx(result>>32),sx(result&0xffffffff) if rd else 0x12345678))
li(9,1);words.extend([(0x2b<<26)|(8<<21)|(9<<16)|0x100,0x03e00008,0])
payload=struct.pack('<%dI'%len(words),*words)
with PineClient(port=28012) as p:
    original=p.read(CODE,len(payload));control=p.read(CONTROL,64)
    if any(control):raise RuntimeError('This test requires a fresh diagnostic boot without a controller')
    try:
        p.write(OUTPUT,bytes(0x104));p.write(CODE,payload);p.write_u32(CONTROL,0x42545032)
        deadline=time.monotonic()+5
        while p.read_u32(OUTPUT+0x100)!=1:
            if time.monotonic()>deadline:raise TimeoutError('Interpreter test did not run')
            time.sleep(.02)
        actual=[struct.unpack('<3Q',p.read(OUTPUT+index*32,24)) for index in range(len(cases))]
        if actual!=expected:raise AssertionError((actual,expected))
        print('Native MADD tests passed: signed, unsigned, both accumulator banks, and rd=zero')
    finally:
        p.write_u32(CONTROL,0);time.sleep(.1);p.write(CODE,original);p.write(CONTROL,control)
