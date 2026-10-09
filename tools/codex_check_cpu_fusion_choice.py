"""Execute actual emitted CPU-choice code with guarded native call boundaries.

This verifies wrapper routing/ABI, not native fusion resource loading or live AI.
"""
from pathlib import Path
import struct,sys
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import cpu_fusion_choice as c
MASK64=(1<<64)-1;MASK128=(1<<128)-1

class Machine:
    def __init__(self):
        self.mem={};self.manager=0x1800000;self.actor=0x1900000;self.calls=[]
        self.put(c.CODE,c.code())
        self.regs=[((0xABCD0000+i)<<96)|((0x12340000+i)<<64)|0x10000+i for i in range(32)]
        for r,n in ((0,0),(4,self.actor),(5,0),(6,0),(28,0x304270),(29,0x7FFE000),(31,c.RETURN)):
            self.regs[r]=n
        self.fpu=[0x3F800000+i for i in range(32)];self.fcr=0x1820000
        self.units=[0xF010000000000001,0xF020000000000002,0xF030000000000003,0xF040000000000004]
        self.word(self.regs[28]-22364,self.manager);self.word(self.manager,2)
        for off,n in ((0,1),(4,4),(8,self.manager),(12,4)):self.word(c.core.MODE+off,n)
        for off,n in ((0,c.MAGIC),(4,self.manager),(8,4)):self.word(c.CONTROL+off,n)
        for off,n in ((0,c.pads.MAGIC),(4,self.manager),(8,4),(12,1)):self.word(c.pads.CONTROL+off,n)
        for seat in range(4):self.word(c.seats.CONTROL+c.seats.F['owned']+4*seat,0xFFFFFFFF)
        for index in range(4):
            actor=self.actor+index*0x10000
            self.word(c.core.POINTERS+index*4,actor);self.word(actor,index);self.word(actor+0x1278,1)
            self.word(c.ROWS+index*c.STRIDE,actor);self.word(c.ROWS+index*c.STRIDE+4,1)
        self.eligible={0:0,1:1,2:2};self.accepted=1
    def put(self,at,data):self.mem.update((at+i,b) for i,b in enumerate(data))
    def word(self,at,n):self.put(at,struct.pack('<I',n&0xFFFFFFFF))
    def get(self,at,size=4):return int.from_bytes(bytes(self.mem.get(at+i,0) for i in range(size)),'little')
    def low(self,r):return self.regs[r]&MASK64
    def write(self,r,value):self.regs[r]=(self.regs[r]&(~MASK64&MASK128))|(value&MASK64)
    def execute(self):
        before=list(self.regs);fpu=list(self.fpu);units=list(self.units);fcr=self.fcr
        pc=c.CODE;pending=None
        for step in range(3000):
            if pc==before[31]&0xFFFFFFFF:break
            if pc in (c.NATIVE_ELIGIBILITY,c.NATIVE_BEGIN):
                target=pc;ret=self.low(31)&0xFFFFFFFF
                args=tuple(self.low(r)&0xFFFFFFFF for r in (4,5,6,7,8));self.calls.append((target,args))
                if target==c.NATIVE_BEGIN:
                    assert self.fpu==fpu and self.fcr==fcr and self.units==units,'native BEGIN sees clobbered caller state'
                # Native boundaries deliberately clobber full128bit GPRs and
                # every FP/HI/LO value, stressing the emitted save/restore.
                for r in range(1,29):self.regs[r]=(0xBADCAFE<<96)|(0xBAADF00D<<64)|r
                self.fpu=[0xFE000000+i for i in range(32)];self.fcr=0xBAD;self.units=[11,22,33,44]
                if target==c.NATIVE_ELIGIBILITY:
                    assert args[2:4]==(1,1),'candidate bypassed stock/native-state guard'
                    slot=self.eligible.get(args[1]);self.regs[2]=int(slot is not None)
                    if slot is not None:self.word(args[4],slot)
                else:self.regs[2]=self.accepted
                pc=ret;pending=None;continue
            ins=self.get(pc);op=ins>>26;rs=ins>>21&31;rt=ins>>16&31;rd=ins>>11&31;shift=ins>>6&31;fn=ins&63
            imm=ins&65535;simm=imm if imm<32768 else imm-65536;target=None
            address=(self.low(rs)+simm)&0xFFFFFFFF
            if op in (0,28):
                bank=2 if op==28 else 0
                if fn in (16,18):self.write(rd,self.units[bank+(fn==18)])
                elif fn in (17,19):self.units[bank+(fn==19)]=self.low(rs)
                elif op==0 and fn in (0x21,0x2D):
                    value=self.low(rs)+self.low(rt)
                    if fn==0x21:value=(value&0xFFFFFFFF) if value&0x80000000==0 else (value&0xFFFFFFFF)|0xFFFFFFFF00000000
                    self.write(rd,value)
                elif op==0 and fn==0:self.write(rd,(self.low(rt)&0xFFFFFFFF)<<shift)
                elif op==0 and fn==0x2B:self.write(rd,int(self.low(rs)<self.low(rt)))
                elif op==0 and fn==8:target=self.low(rs)&0xFFFFFFFF
                else:raise AssertionError((hex(pc),hex(ins)))
            elif op==9:
                value=(self.low(rs)+simm)&0xFFFFFFFF;self.write(rt,value if value<0x80000000 else value|0xFFFFFFFF00000000)
            elif op==15:self.write(rt,imm<<16)
            elif op==13:self.write(rt,self.low(rs)|imm)
            elif op==12:self.write(rt,self.low(rs)&imm)
            elif op==11:self.write(rt,int(self.low(rs)<(simm&MASK64)))
            elif op in (35,55,30):
                size={35:4,55:8,30:16}[op];value=self.get(address,size)
                if op==30:self.regs[rt]=value
                else:
                    if op==35 and value>=0x80000000:value|=0xFFFFFFFF00000000
                    self.write(rt,value)
            elif op in (43,63,31):
                size={43:4,63:8,31:16}[op];self.put(address,(self.regs[rt]&((1<<(8*size))-1)).to_bytes(size,'little'))
            elif op==49:self.fpu[rt]=self.get(address)
            elif op==57:self.word(address,self.fpu[rt])
            elif op==17:
                assert rd==31
                if rs==2:self.write(rt,self.fcr)
                elif rs==6:self.fcr=self.low(rt)&0xFFFFFFFF
                else:raise AssertionError(hex(ins))
            elif op in (4,5):
                if (self.low(rs)==self.low(rt))==(op==4):target=pc+4+simm*4
            elif op in (2,3):
                target=((pc+4)&0xF0000000)|((ins&0x3FFFFFF)<<2)
                if op==3:self.write(31,pc+8)
            else:raise AssertionError((hex(pc),hex(ins)))
            self.regs[0]=0;nextpc=pc+4 if pending is None else pending;pending=target;pc=nextpc
        else:raise AssertionError('wrapper never returned')
        assert self.fpu==fpu and self.fcr==fcr and self.units==units
        assert all(self.regs[r]==before[r] for r in range(32) if r!=2),'full128bit caller GPR changed'
        assert self.regs[2]==self.accepted
        return [args for target,args in self.calls if target==c.NATIVE_BEGIN][-1]

machine=Machine()
for expected,next_cursor in ((1,2),(2,0),(0,1)):
    machine.calls=[];assert machine.execute()[:3]==(machine.actor,expected,expected)
    assert machine.get(c.ROWS+4)==next_cursor
assert struct.unpack('<I',c.hook_bytes()[4:])[0]==0x0200282D
for mutation in (
    lambda m:m.regs.__setitem__(5,2),
    lambda m:m.regs.__setitem__(31,0x06FF0000),
    lambda m:m.word(m.actor+0x1278,0),
    lambda m:m.word(c.seats.CONTROL+c.seats.F['owned'],0),
    lambda m:m.word(c.core.PAIR+4,1),
    lambda m:m.word(c.core.MODE,0),
    lambda m:m.word(c.CONTROL+4,0),
    lambda m:m.word(c.pads.CONTROL+4,0),
    lambda m:m.word(c.pads.CONTROL+12,0),
    lambda m:m.word(c.core.POINTERS,m.actor+0x10000),
    lambda m:m.word(c.ROWS,m.actor+0x10000),
    lambda m:m.word(c.ROWS+4,3),
):
    m=Machine();mutation(m);original=(m.actor,m.regs[5]&0xFFFFFFFF,m.regs[6]&0xFFFFFFFF)
    assert m.execute()[:3]==original
    assert not any(target==c.NATIVE_ELIGIBILITY for target,_ in m.calls)
    assert m.get(c.ROWS+4)==(3 if m.get(c.ROWS+4)==3 else 1)
m=Machine();m.eligible={0:0};m.regs[6]=3
assert m.execute()[:3]==(m.actor,0,3) and m.get(c.ROWS+4)==1
m=Machine();m.eligible[1]=-1
assert m.execute()[:3]==(m.actor,0,0)
m=Machine();m.accepted=0
assert m.execute()[:3]==(m.actor,1,1) and m.get(c.ROWS+4)==1
m=Machine();m.regs[4]=m.actor+0x20000
assert m.execute()[:3]==(m.actor+0x20000,1,1)
assert m.get(c.ROWS+2*c.STRIDE+4)==2 and m.get(c.ROWS+4)==1
m=Machine();m.word(c.pads.CONTROL,0)
assert m.execute()[:3]==(m.actor,1,1) and m.get(c.ROWS+4)==2
m=Machine();m.word(c.pads.CONTROL,0);m.word(m.actor+0x1278,0)
assert m.execute()[:3]==(m.actor,0,0) and m.get(c.ROWS+4)==1
ram=bytearray(0x8000000);m=Machine()
for at,byte in m.mem.items():ram[at]=byte
ram[c.BASE:c.END]=bytes(c.END-c.BASE)
ram[c.HOOK:c.HOOK+8]=c.abi.NATIVE(c.HOOK,8)
manifest=c.build_memory(ram)
assert len(manifest['blocks'])==4
struct.pack_into('<I',ram,c.pads.CONTROL,0)
assert len(c.build_memory(ram)['blocks'])==4,'ordinary teams must not require a quad lease'
struct.pack_into('<I',ram,c.pads.CONTROL,c.pads.MAGIC)
struct.pack_into('<I',ram,c.pads.CONTROL+4,0)
assert c.build_memory(ram)['blocks']==[],'stale optional lease must not block match preparation'
ram[c.HOOK+4]^=1
try:c.build_memory(ram)
except ValueError as exc:assert 'callsite changed' in str(exc)
else:raise AssertionError('changed native delay slot accepted')
print('PASS actual emitted wrapper: variants1/2/0, new partner slots, per-actor cursor, refused BEGIN, ineligible preferred fallback, ownership/alias/lease guards.')
print('PASS full128bit GPR, FPU/FCR31, HI0/LO0/HI1/LO1 preservation across deliberately clobbering native boundaries; exact callsite/delay guard; no game.')
