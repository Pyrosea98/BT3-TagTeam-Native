"""Independent MIPS execution vs compiled C++ pack: registers/PC/stack writes."""
from pathlib import Path
import ctypes as C
import json
import random
import struct
import codex_freeze_target_pack # installs the same offline staged module oracle
import inactive_actor_guard as inactive
import teammate_revive as revive
import hud_subject as hud
import team_participation as participation
import fresh_team_camera as camera
import multi_contact as contact
import beam_clash as beam
import dash_clash as dash
import giant_options as giant
import extra_throws as throws
import lockoff_target as lockoff

HERE=Path(__file__).resolve().parent
MASK64=(1<<64)-1
ram=bytearray(0x8000000)
view=(C.c_uint8*len(ram)).from_buffer(ram)
dll=C.CDLL(str(HERE/'power-scale-trial/codex_target_pack_test.dll'))
dll.run_targets.argtypes=[C.POINTER(C.c_uint8),C.POINTER(C.c_uint64),C.c_uint32,C.POINTER(C.c_uint32)]
dll.run_targets.restype=C.c_int
rows=json.loads((HERE/'codex_target_pack_oracle.json').read_text())
rng=random.Random(7368000)


def put(p,*values):struct.pack_into('<'+'I'*len(values),ram,p,*values)
def read32(p):return struct.unpack_from('<I',ram,p&0x7ffffff)[0]
def sx32(v):return (v&0xffffffff) if v&0x80000000==0 else (v&0xffffffff)-0x100000000


def oracle(base,data,regs):
    end=base+len(data);pc=base
    def set64(r,v):
        if r:regs[2*r]=v&MASK64
    def set32(r,v):set64(r,sx32(v&0xffffffff))
    def simple(w):
        op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;sa=(w>>6)&31
        imm=w&65535;simm=imm if imm<32768 else imm-65536
        lhs=regs[2*rs];rhs=regs[2*rt];addr=((lhs&0xffffffff)+simm)&0xffffffff
        if w==0:return
        if op==0:
            fn=w&63
            if fn==0:set32(rd,(rhs&0xffffffff)<<sa)
            elif fn==2:set32(rd,(rhs&0xffffffff)>>sa)
            elif fn==3:set32(rd,sx32(rhs&0xffffffff)>>sa)
            elif fn==4:set32(rd,(rhs&0xffffffff)<<(lhs&31))
            elif fn==33:set32(rd,(lhs&0xffffffff)+(rhs&0xffffffff))
            elif fn==36:set64(rd,lhs&rhs)
            elif fn==37:set64(rd,lhs|rhs)
            elif fn==38:set64(rd,lhs^rhs)
            elif fn==39:set64(rd,~(lhs|rhs))
            elif fn==42:set64(rd,int((lhs if lhs<1<<63 else lhs-(1<<64))<(rhs if rhs<1<<63 else rhs-(1<<64))))
            elif fn==43:set64(rd,int(lhs<rhs))
            elif fn==45:set64(rd,lhs+rhs)
            else:raise AssertionError(f'Unknown SPECIAL {w:08x}')
        elif op==9:set32(rt,(lhs&0xffffffff)+simm)
        elif op==11:set64(rt,int(lhs<(simm&MASK64)))
        elif op==12:set64(rt,lhs&imm)
        elif op==13:set64(rt,lhs|imm)
        elif op==15:set32(rt,imm<<16)
        elif op==35:set32(rt,read32(addr))
        elif op==36:set64(rt,ram[addr&0x7ffffff])
        elif op==43:struct.pack_into('<I',ram,addr&0x7ffffff,rhs&0xffffffff)
        elif op==30:
            if rt:regs[2*rt:2*rt+2]=struct.unpack_from('<2Q',ram,(addr&0x7ffffff)&~15)
        elif op==31:struct.pack_into('<2Q',ram,(addr&0x7ffffff)&~15,*regs[2*rt:2*rt+2])
        elif op==55:set64(rt,struct.unpack_from('<Q',ram,addr&0x7ffffff)[0])
        elif op==63:struct.pack_into('<Q',ram,addr&0x7ffffff,rhs)
        else:raise AssertionError(f'Unknown opcode {w:08x}')
    for _ in range(1000):
        if not base<=pc<end:return pc
        w=read32(pc);op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31
        if op in (4,5):
            equal=regs[2*rs]==regs[2*rt]
            imm=w&65535;simm=imm if imm<32768 else imm-65536
            target=pc+4+4*simm if equal==(op==4) else pc+8
            simple(read32(pc+4));pc=target
        elif op==2:
            target=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)
            simple(read32(pc+4));pc=target
        elif op==0 and w&63==8:
            target=regs[2*rs]&0xffffffff;simple(read32(pc+4));pc=target
        else:simple(w);pc+=4
    raise AssertionError('Oracle loop did not terminate')


count=0
for row in rows:
    base=row['base'];data=bytes.fromhex(row['data_hex']);ram[base:base+len(data)]=data
    for case in range(160):
        regs=[rng.getrandbits(64) for _ in range(64)];regs[0:2]=[0,0]
        gp=0x2FEB14+22364;sp=0x200000;manager=0x180000
        regs[56]=gp;regs[58]=sp;regs[62]=0x101000
        actors=[0x190000+0x2000*i for i in range(12)]
        for i,actor in enumerate(actors):
            put(actor,i,0,i&1,i)
            model=0x220000+0x2000*i;param=0x260000+0x100*i
            put(0x31C640+4*i,model);put(model+16,i);put(model+2332,param)
            ram[param+2]=4 if case%3 else 0
            for offset in throws.ACTION_FIELDS:put(actor+offset,180 if case%2 else 11)
            put(actor+3732,i&~1,(i&~1)+1)
            put(actor+0x1278,case%4)
            put(actor+0x994,case%5,5)
            put(actor+4896,rng.choice((0,1,0xffffffff)))
        put(manager,2,actors[0])
        put(gp-22364,manager)
        n=rng.choice((2,3,4,5,6,8,10,11));enabled=rng.choice((0,1,1))
        put(0xD8080,enabled,n,manager,n)
        put(participation.CONTROL,5,manager,n,(1<<n)-1,0)
        put(revive.CONTROL,revive.MAGIC,manager,n,0)
        put(contact.CONTROL,contact.MAGIC,manager,n)
        put(giant.CONTROL,giant.MAGIC,manager,n,1)
        put(throws.CONTROL,1,manager,n)
        put(lockoff.CONTROL,lockoff.MAGIC,manager)
        for i in range(12):
            put(throws.ROWS+4*i,(i^1)+1 if case%3 else 0)
            put(lockoff.ROWS+lockoff.STRIDE*i,case%2)
        for feature in (beam,dash):put(feature.CONTROL,feature.MAGIC,manager,n,0x1E0000)
        put(0x3337B8,0)
        for i,actor in enumerate(actors):put(revive.ROWS+i*revive.STRIDE,actor)
        put(0x333700,0);put(0x2FEB38,0x1E0000);put(0x1E0000,3)
        put(hud.CONTROL,hud.MAGIC,1,manager,1,0,0,0,1)
        put(hud.SCENE+hud.SPLIT_OFF,case%2)
        put(camera.LEADER_CONTROL+12,case%2)
        if case%5==0:put(participation.CONTROL+16,1<<rng.randrange(12))
        if case%13==0:put(0x1E0000,2)
        for i,actor in enumerate(actors):put(0xD8040+4*i,actor)
        for i in range(12):put(0xD8000+4*i,rng.randrange(14))
        aliases=rng.randrange(4)
        put(0xC4000,actors[0] if aliases&1 else 0,actors[1] if aliases&2 else 0,
            actors[2],actors[3],2,3)
        if case%7==0:put(0xD8080+8,manager+16) # stale manager
        if case%9==0:put(0xD8080+12,n+1) # inconsistent publication
        if case%11==0:put(manager,0) # native manager not live
        kind=row['name'].split('_')[0]
        if kind=='physical':arg=rng.choice((0,1,2,5,9,10,0xffffffff))
        elif kind=='logical':arg=rng.choice((0,1,5,9,100))
        elif kind=='inactive':
            arg=rng.choice(actors[:10]+[0x1d0000]);regs[62]=rng.choice(inactive.CALLERS+(0x101000,))
        elif kind=='revive':arg=rng.choice((0,1,2,5,9,11))
        elif kind=='hud':arg=case%3
        elif row['name'].startswith('giant_model'):arg=0x220000+0x2000*(case%12)
        else:arg=rng.choice(actors[:10]+[0x1d0000])
        regs[8]=arg
        if kind=="elf":
            regs[10]=case%128
            if base==0x1da8a0:regs[8]=case%12
            regs[12]=actors[case%10];regs[14]=actors[(case+1)%10]
            if row["name"].startswith("elf_tail_"):
                regs[6]=regs[10]>>3;regs[10]&=7
        if kind=='lock':regs[10]=5 if case%2 else 7
        if '_tail_' in row['name']:regs[16]=0xD8080
        before=bytes(ram[sp-80:sp]);hud_before=bytes(ram[hud.CONTROL:hud.CONTROL+48]);throws_before=bytes(ram[throws.CONTROL:throws.CONTROL+320]);expected=regs.copy()
        exit=oracle(base,data,expected);after=bytes(ram[sp-80:sp]);hud_after=bytes(ram[hud.CONTROL:hud.CONTROL+48]);throws_after=bytes(ram[throws.CONTROL:throws.CONTROL+320])
        ram[sp-80:sp]=before;ram[hud.CONTROL:hud.CONTROL+48]=hud_before;ram[throws.CONTROL:throws.CONTROL+320]=throws_before
        actual=(C.c_uint64*64)(*regs);native_exit=C.c_uint32()
        assert dll.run_targets(view,actual,base,C.byref(native_exit))==1
        assert list(actual)==expected,(row['name'],case,'register mismatch')
        assert native_exit.value==exit,(row['name'],case,'PC mismatch')
        assert bytes(ram[sp-80:sp])==after,(row['name'],case,'stack mismatch')
        assert bytes(ram[hud.CONTROL:hud.CONTROL+48])==hud_after,(row['name'],case,'HUD writes mismatch')
        assert bytes(ram[throws.CONTROL:throws.CONTROL+320])==throws_after,(row['name'],case,'throw records mismatch')
        count+=1
    # A single altered byte must reject with absolutely no execution effects.
    ram[base+len(data)-1]^=1;actual=(C.c_uint64*64)(*regs);before=bytes(ram[sp-32:sp]);native_exit=C.c_uint32(123)
    assert dll.run_targets(view,actual,base,C.byref(native_exit))==0
    assert list(actual)==regs and bytes(ram[sp-32:sp])==before and native_exit.value==123
    ram[base+len(data)-1]^=1
assert dll.run_targets(view,actual,0x7368004,C.byref(native_exit))==0
print(f'PASS: {count} independent MIPS/C++ comparisons across {len(rows)} variants; registers incl. upper halves, PC, stack, HUD writes; altered code/interior PC rejected')
