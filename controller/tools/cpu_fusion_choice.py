"""Diversify only the native AI's already accepted variant-zero fusion command.

No polling, pacing or forced starts. Human selections and scripted BEGIN calls
retain their exact arguments. An unavailable preferred recipe falls back to the
already checked original tuple; a refused BEGIN does not advance the cursor.
"""
import struct
from native_map import A,CRC,SERIAL
from prototype import Assembler
import fusion_partner_lifecycle as abi
import fresh_team_combat as core
import battle_mode_policy as modes
import quad_lifecycle as seats
import quad_controller as pads

BASE,END=0x074C0000,0x074D0000
CODE,CONTROL,ROWS=BASE,BASE+0xF000,BASE+0xF100
HOOK,RETURN,NATIVE_BEGIN,NATIVE_ELIGIBILITY=A(0x203994),A(0x20399C),A(0x2039B0),A(0x203788)
MAGIC=0x43465531
STRIDE=8
HI_OFFSETS=(0x288,0x290,0x298,0x2A0)
OUT,ROW,PREFERRED,ORIGINAL_VARIANT,ORIGINAL_PARTNER,CANDIDATE_ROW=0x300,0x308,0x30C,0x314,0x318,0x31C

def hi_save(a):
    for bank in range(2):
        for which,fn in enumerate((0x10,0x12)):
            a.emit((28<<26 if bank else 0)|(8<<11)|fn)
            a.i(63,8,29,HI_OFFSETS[bank*2+which])

def hi_restore(a):
    for bank in range(2):
        for which,fn in enumerate((0x11,0x13)):
            a.i(55,8,29,HI_OFFSETS[bank*2+which])
            a.emit((28<<26 if bank else 0)|(8<<21)|fn)

def code():
    a=Assembler(CODE);abi.save(a);hi_save(a);a.sw(0,29,ROW)
    a.lw(8,29,abi.OFFSETS[5]);a.sw(8,29,ORIGINAL_VARIANT)
    a.lw(8,29,abi.OFFSETS[6]);a.sw(8,29,ORIGINAL_PARTNER)
    a.lw(8,29,abi.OFFSETS[31]);a.li(9,RETURN);a.branch(5,8,9,'dispatch')
    a.lw(8,29,abi.OFFSETS[5]);a.branch(5,8,0,'dispatch')
    core.gate(a,'dispatch')
    a.li(8,core.PAIR)
    for offset in (0,4):a.lw(9,8,offset);a.branch(5,9,0,'dispatch')
    a.li(8,CONTROL);a.lw(9,8);a.li(11,MAGIC);a.branch(5,9,11,'dispatch')
    a.lw(9,8,4);a.lw(11,28,-22364);a.branch(5,9,11,'dispatch')
    a.lw(9,8,8);a.branch(5,9,10,'dispatch')
    a.lw(16,29,abi.OFFSETS[4]);abi.pointer(a,16,0x1600,'dispatch')
    a.lw(17,16);a.r(0x2B,8,17,10);a.branch(4,8,0,'dispatch')
    a.r(0,8,0,17,2);a.li(9,core.POINTERS);a.r(0x21,9,9,8);a.lw(9,9);a.branch(5,9,16,'dispatch')
    a.lw(8,16,0x1278);a.branch(4,8,0,'dispatch')
    # Legacy human input and spectator_takeover both clear actor+1278 before
    # routing a human pad. Quad takeover additionally publishes seat ownership;
    # consult that lease when installed, never require it in ordinary teams.
    a.li(8,pads.CONTROL);a.lw(9,8);a.branch(4,9,0,'ownership_checked')
    a.li(11,pads.MAGIC);a.branch(5,9,11,'dispatch')
    a.lw(9,8,4);a.lw(11,28,-22364);a.branch(5,9,11,'dispatch')
    a.lw(9,8,8);a.branch(5,9,10,'dispatch')
    a.lw(9,8,12);a.branch(4,9,0,'dispatch')
    for seat in range(4):
        a.li(8,seats.CONTROL+seats.F['owned']+seat*4);a.lw(9,8);a.branch(4,9,17,'dispatch')
    a.label('ownership_checked')
    a.r(0,8,0,17,3);a.li(18,ROWS);a.r(0x21,18,18,8)
    a.lw(8,18);a.branch(5,8,16,'dispatch')
    a.lw(19,18,4);a.i(11,8,19,3);a.branch(4,8,0,'dispatch');a.sw(19,29,PREFERRED);a.sw(18,29,CANDIDATE_ROW)
    a.move(4,16);a.move(5,19);a.addiu(6,0,1);a.addiu(7,0,1);a.addiu(8,29,OUT)
    a.call(NATIVE_ELIGIBILITY);a.branch(4,2,0,'dispatch')
    a.lw(8,29,OUT);a.i(11,9,8,modes.emitted_capacity());a.branch(4,9,0,'dispatch')
    a.lw(9,29,CANDIDATE_ROW);a.sw(9,29,ROW)
    a.lw(9,29,PREFERRED);a.sw(9,29,abi.OFFSETS[5]);a.sw(8,29,abi.OFFSETS[6])
    a.label('dispatch');hi_restore(a);abi.restore(a,False);a.call(NATIVE_BEGIN)
    # Preserve the actual native success result, while restoring the full
    # incoming GPR/FPU and multiplication-unit state around our extra query.
    a.i(31,2,29,abi.OFFSETS[2]);a.branch(4,2,0,'done');a.lw(8,29,ROW);a.branch(4,8,0,'done')
    a.lw(9,29,PREFERRED);a.addiu(9,9,1);a.i(11,10,9,3);a.branch(5,10,0,'advance');a.move(9,0)
    a.label('advance');a.sw(9,8,4)
    a.label('done');a.lw(8,29,ORIGINAL_VARIANT);a.sw(8,29,abi.OFFSETS[5])
    a.lw(8,29,ORIGINAL_PARTNER);a.sw(8,29,abi.OFFSETS[6])
    hi_restore(a);abi.restore(a);a.jr()
    result=a.finish();assert len(result)<CONTROL-CODE;return result

def hook_bytes():
    # Redirect only the JAL; the native daddu a1,s0,zero delay slot is retained.
    return struct.pack('<I',(3<<26)|(CODE>>2))+abi.NATIVE(HOOK+4,4)

def build_memory(ram,source='memory'):
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    if len(ram)!=0x8000000:raise ValueError('CPU fusion choice needs complete native EE RAM')
    if bytes(ram[HOOK:HOOK+8])!=abi.NATIVE(HOOK,8):raise ValueError('Native accepted-fusion command callsite changed')
    if any(ram[BASE:END]):raise ValueError('CPU fusion choice reservation occupied')
    manager=u(core.MODE+8);count=u(core.MODE+12)
    if count not in modes.ACTOR_COUNTS or not manager:raise ValueError('CPU fusion choice requires a prepared match')
    if u(pads.CONTROL) and (u(pads.CONTROL),u(pads.CONTROL+4),u(pads.CONTROL+8))!=(pads.MAGIC,manager,count):
        return dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[],limitations=['Stale quad-controller lease: CPU diversity omitted; existing native choice retained.'])
    rows=bytearray(modes.ENGINE_ACTORS*STRIDE)
    for index in range(count):
        actor=u(core.POINTERS+4*index)
        if not 0x100000<=actor<len(ram)-0x1600 or u(actor)!=index:raise ValueError('CPU fusion choice actor identity differs')
        struct.pack_into('<2I',rows,index*STRIDE,actor,1)
    pieces=((CODE,code()),(CONTROL,struct.pack('<4I',MAGIC,manager,count,0)),(ROWS,bytes(rows)),(HOOK,hook_bytes()))
    return dict(serial=SERIAL,crc=CRC,source=str(source),control=CONTROL,
        blocks=[dict(address=p,expected_hex=bytes(ram[p:p+len(data)]).hex(),data_hex=data.hex()) for p,data in pieces],
        limitations=['Diversifies only accepted native variant-zero commands; no autonomous fusion or pacing change.',
                     'Unavailable preferred recipe keeps the original tuple and cursor. Cursor advances only after the preferred BEGIN accepts.'])
