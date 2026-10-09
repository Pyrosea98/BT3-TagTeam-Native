"""Execute emitted Super pairing selector with adversarial ownership/rows."""
from pathlib import Path
import struct,sys
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import power_scale_fusion_recipes as p
from prototype import Assembler
import fresh_team_combat as core
import team_participation as part
import fusion_partner_lifecycle as fusion

def run(change=None,source=119,variant=0):
    mem={};counterpart=p.PAIRS[source]
    def put(at,data):mem.update((at+i,b) for i,b in enumerate(data))
    def word(at,n):put(at,struct.pack('<I',n))
    def u(at):return sum(mem.get(at+i,0)<<(i*8) for i in range(4))
    manager=0x1800000;actor=0x1900000;other=0x1910000;model=0x980000;othermodel=0x990000
    param=0xA00000;otherparam=0xA10000
    word(0x304270-22364,manager);word(manager,2)
    for off,n in ((0,1),(4,4),(8,manager),(12,4)):word(core.MODE+off,n)
    for control,magic in ((fusion.CONTROL,1),(part.CONTROL,5)):
        for off,n in ((0,magic),(4,manager),(8,4)):word(control+off,n)
    word(part.CONTROL+12,15);word(part.CONTROL+16,0)
    word(core.POINTERS,actor);word(core.POINTERS+8,other)
    for body,physical,mdl,par,cid in ((actor,0,model,param,source),(other,2,othermodel,otherparam,counterpart)):
        word(body,physical);word(body+12,physical);word(core.MODELS+4*physical,mdl)
        word(mdl+12,cid);word(mdl+16,physical);word(mdl+0x91C,par);put(par+0xAE,p.RECIPES[cid])
    word(actor+0x998,2)
    bench=actor+0x9A4+164
    for off,n in ((0,counterpart),(8,1),(64,100),(112,0)):word(bench+off,n)
    if change:change(word,put,mem,dict(actor=actor,other=other,bench=bench,param=param))
    code=p.select();put(p.SELECT,code)
    regs=[0]*32;regs[4]=actor;regs[5]=variant;regs[28]=0x304270;regs[31]=0xFFFFFFFF
    pc=p.SELECT;pending=None
    def signed(n):return n if n<0x80000000 else n-0x100000000
    for step in range(12000):
        if pc==0xFFFFFFFF:return regs[2]
        ins=u(pc);op=ins>>26;rs=(ins>>21)&31;rt=(ins>>16)&31;rd=(ins>>11)&31;shift=(ins>>6)&31;fn=ins&63
        imm=ins&65535;simm=imm if imm<32768 else imm-65536
        target=None
        if op==0:
            if fn in (0x21,0x2D):regs[rd]=regs[rs]+regs[rt]
            elif fn==0:regs[rd]=regs[rt]<<shift
            elif fn==2:regs[rd]=regs[rt]>>shift
            elif fn==4:regs[rd]=regs[rt]<<(regs[rs]&31)
            elif fn==0x24:regs[rd]=regs[rs]&regs[rt]
            elif fn==0x2B:regs[rd]=int(regs[rs]<regs[rt])
            elif fn==8:target=regs[rs]
            else:raise AssertionError((hex(pc),hex(ins)))
        elif op==9:regs[rt]=regs[rs]+simm
        elif op==15:regs[rt]=imm<<16
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==12:regs[rt]=regs[rs]&imm
        elif op==10:regs[rt]=int(signed(regs[rs])<simm)
        elif op==11:regs[rt]=int(regs[rs]<(simm&0xFFFFFFFF))
        elif op==35:regs[rt]=u((regs[rs]+simm)&0xFFFFFFFF)
        elif op==36:regs[rt]=mem.get((regs[rs]+simm)&0xFFFFFFFF,0)
        elif op in (4,5):
            taken=regs[rs]==regs[rt] if op==4 else regs[rs]!=regs[rt]
            if taken:target=pc+4+4*simm
        elif op==2:target=((pc+4)&0xF0000000)|((ins&0x3FFFFFF)<<2)
        else:raise AssertionError((hex(pc),hex(ins)))
        regs=[v&0xFFFFFFFF for v in regs];regs[0]=0
        nextpc=pc+4 if pending is None else pending;pending=target;pc=nextpc
    raise AssertionError('selector did not return')

assert run()==60 and run(source=60)==119
assert run(source=192)==194 and run(source=194)==192
assert run(source=192,variant=1)==0 and run(source=194,variant=2)==0
for mutation in (
    lambda w,b,m,c:w(c['bench']+64,0),
    lambda w,b,m,c:w(c['bench']+112,1),
    lambda w,b,m,c:w(part.CONTROL+16,4),
    lambda w,b,m,c:w(part.CONTROL+12,3),
    lambda w,b,m,c:w(c['other'],3),
    lambda w,b,m,c:b(c['param']+0xB4,bytes([122])),
    lambda w,b,m,c:w(fusion.CONTROL+4,0),
    lambda w,b,m,c:w(core.MODE,0),
    lambda w,b,m,c:w(c['bench'],31),
):assert run(mutation)==0
for at,data in p.pieces():assert p.BASE<=at<at+len(data)<=p.END
def check_wrapper(partner,slot,selected,mode=None,variant=0,expected=None):
    address=(p.RESULT if mode=='result' else p.COST) if mode else p.PARTNER if partner else p.METADATA
    tramp=(p.RESULT_TRAMP if mode=='result' else p.COST_TRAMP) if mode else p.PARTNER_TRAMP if partner else p.METADATA_TRAMP
    blob=p.wrapper(address,tramp,partner,mode)
    memory={address+4*i:word for i,word in enumerate(struct.unpack('<'+'I'*(len(blob)//4),blob))}
    registers=[(0xABCD0000+i)<<96 | (0x12340000+i)<<64 | 0x10000+i for i in range(32)]
    registers[0]=0;registers[29]=0x7FFE000;registers[31]=(0x1234<<96)|0xFFFF0000;registers[6]=((0xABCD<<96)|slot)
    registers[5]=(0xABCD<<96)|variant
    before=list(registers);stack={};pc=address;pending=None
    for _ in range(250):
        if pc in (tramp,before[31]&0xFFFFFFFF):break
        if pc==p.SELECT:
            # Stress the wrapper ABI with a callee that changes every register
            # it can touch. Actual emitted SELECT is exercised above.
            ret=registers[31]&0xFFFFFFFF
            for r in p.SAVED:registers[r]=0xBAADF00D
            registers[2]=selected;pc=ret;pending=None;continue
        ins=memory[pc];op=ins>>26;rs=ins>>21&31;rt=ins>>16&31;imm=ins&65535;simm=imm if imm<32768 else imm-65536;target=None
        if op==31:stack[(registers[rs]&0xFFFFFFFF)+simm]=registers[rt]
        elif op==30:registers[rt]=stack[(registers[rs]&0xFFFFFFFF)+simm]
        elif op==9:registers[rt]=((registers[rs]&0xFFFFFFFF)+simm)&0xFFFFFFFF
        elif op==35:registers[rt]=stack[(registers[rs]&0xFFFFFFFF)+simm]&0xFFFFFFFF
        elif op in (4,5):
            equal=(registers[rs]&0xFFFFFFFF)==(registers[rt]&0xFFFFFFFF)
            if equal if op==4 else not equal:target=pc+4+4*simm
        elif op in (2,3):
            target=(ins&0x3FFFFFF)<<2
            if op==3:registers[31]=pc+8
        elif ins==0:pass
        elif op==0 and ins&63==8:target=registers[rs]&0xFFFFFFFF
        elif op==0 and ins&63 in (0x21,0x2D):registers[(ins>>11)&31]=(registers[rs]+registers[rt])&0xFFFFFFFF
        else:raise AssertionError(hex(ins))
        nextpc=pc+4 if pending is None else pending;pending=target;pc=nextpc
    else:raise AssertionError('wrapper did not exit')
    assert all(registers[r]==before[r] for r in p.SAVED)
    assert registers[29]==before[29]
    if pc==tramp:assert selected==0 or partner and slot!=0 or mode=='cost' and selected not in (60,119)
    else:assert registers[2]==(selected if expected is None else expected)
for partner in (True,False):
    check_wrapper(partner,0,60);check_wrapper(partner,0,0)
check_wrapper(True,1,60)
for cid in (60,119):
    for variant,result in enumerate((51,110,53)):
        check_wrapper(False,0,cid,'result',variant,result)
        check_wrapper(False,0,cid,'cost',variant,0)
for cid in (192,194):
    check_wrapper(False,0,cid,'result',0,195)
    check_wrapper(False,0,cid,'cost')
check_wrapper(False,0,0,'result');check_wrapper(False,0,0,'cost')
print('PASS Black mutual IDs/result195 with authored cost fallback; free Super Vegito/Gogeta/GogetaSSJ; preserved GPR128 and unknown-profile native fallback')
print('PASS emitted selector: both base directions; dead, busy, consumed, absent, wrong side, changed result, wrong owner, inactive, stale bench reject; bounds.')
print('PASS emitted wrappers: all preserved GPRs retain full128bit contents; slot0 override, metadata override, native fallback and nonzero slot fallback.')
