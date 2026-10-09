"""Trace actual native fusion eligibility calls, without re-running any gate."""
import struct
from native_map import A,CRC,SERIAL
from prototype import Assembler
import fresh_team_combat as core
import fusion_partner_lifecycle as abi
import game_profile
BASE,END=0x074D0000,0x074E0000
CODE=BASE
CONTROL,ROWS=BASE+0xF000,BASE+0xF100
MAGIC=0x46495432
HOOK=A(0x203980)
STRIDE=256
# callsite, original target, result field; delays remain byte-identical.
CALLS=((0x2037CC,0x1CF0C8,64),(0x2037E0,0x1DAC78,68),
       (0x2037F0,0x1DC348,72),(0x203804,0x20E340,12),
       (0x203814,0x20E3E8,24),(0x203830,abi.SIDE,76),
       (0x203848,0x1CED60,80),(0x203884,0x1CE108,84),
       (0x2038A4,0x1CE198,224),(0x2038BC,0x1CE198,232))
GATE_HOOKS=tuple(A(site) for site,_,_ in CALLS)

def save_hi(a):
    for off,op,bank in ((0x288,16,0),(0x290,18,0),(0x2B0,16,1),(0x2B8,18,1)):
        if bank:a.emit((28<<26)|(8<<11)|op)
        else:a.r(op,8,0)
        a.i(63,8,29,off)

def restore_hi(a):
    for off,op,bank in ((0x288,17,0),(0x290,19,0),(0x2B0,17,1),(0x2B8,19,1)):
        a.i(55,8,29,off)
        if bank:a.emit((28<<26)|(8<<21)|op)
        else:a.r(op,0,8)

def code():
    a=Assembler(CODE);abi.save(a);save_hi(a);a.sw(0,29,0x2A0)
    a.lw(8,29,abi.OFFSETS[8]);a.sw(8,29,0x2AC)
    core.gate(a,'original');a.move(17,4);a.move(18,0)
    a.label('scan');a.r(0,8,0,18,2);a.li(9,core.POINTERS);a.r(0x21,9,9,8);a.lw(9,9)
    a.branch(4,9,17,'found');a.addiu(18,18,1);a.branch(5,18,10,'scan');a.jump('original')
    a.label('found');a.r(0,8,0,18,8);a.li(16,ROWS);a.r(0x21,16,16,8);a.sw(16,29,0x2A0)
    a.lw(8,16);a.addiu(8,8,1);a.branch(5,8,0,'sequence');a.addiu(8,0,1);a.label('sequence');a.sw(8,29,0x2A8)
    a.addiu(8,0,-1)
    for off in range(4,STRIDE,4):a.sw(8,16,off)
    a.sw(5,16,8);a.sw(6,16,52);a.sw(7,16,56);a.sw(17,16,92);a.sw(0,16,84)
    a.lw(8,17,0x1300);a.sw(8,16,244)
    a.lw(8,17,2376);a.sw(8,16,36);a.lw(8,17,0x99C);a.sw(8,16,48)
    a.lw(9,17,0x994);a.sw(9,16,60);a.i(11,8,9,5);a.branch(4,8,0,'model')
    abi.row_address(a,10,17,9,8);a.lw(8,10,0x54);a.sw(8,16,40)
    a.label('model');a.lw(8,17,12);a.i(11,9,8,12);a.branch(4,9,0,'original')
    a.r(0,8,0,8,2);a.li(9,core.MODELS);a.r(0x21,9,9,8);a.lw(9,9)
    abi.pointer(a,9,0x1670,'original',11,12);a.lw(8,9,12);a.sw(8,16,4)
    a.lw(9,9,0x91C);abi.pointer(a,9,0xC7,'original',11,12);a.sw(9,16,88)
    for i in range(25):a.i(36,8,9,0xAE+i);a.i(40,8,16,96+i)
    a.lw(8,16,8);a.i(11,10,8,3);a.branch(4,10,0,'original');a.r(0x21,9,9,8)
    a.i(36,8,9,0xB7);a.sw(8,16,16);a.i(36,8,9,0xB1);a.sw(8,16,20)
    a.label('original');a.li(8,CONTROL);a.lw(9,29,0x2A0);a.sw(9,8,4)
    restore_hi(a);abi.restore(a,finish=False);a.call(A(0x203788));abi.save(a,after=True);save_hi(a)
    a.li(8,CONTROL);a.sw(0,8,4)
    a.lw(16,29,0x2A0);a.branch(4,16,0,'done');a.lw(8,29,abi.OFFSETS[2]);a.sw(8,16,28)
    a.branch(4,8,0,'done');a.lw(9,29,0x2AC);a.branch(4,9,0,'done');a.lw(9,9);a.sw(9,16,32)
    a.i(11,8,9,5);a.branch(4,8,0,'done');a.lw(17,16,92);abi.row_address(a,10,17,9,8);a.lw(8,10);a.sw(8,16,44)
    a.label('done');a.branch(4,16,0,'return');a.lw(8,29,0x2A8);a.sw(8,16)
    a.label('return');restore_hi(a);abi.restore(a);a.jr();body=a.finish();assert len(body)<0x2000;return body

def wrapper(index):
    site,target,offset=CALLS[index];site=A(site);target=A(target) if target<0x06000000 else target
    base=BASE+0x2000+index*0x800
    a=Assembler(base);abi.save(a);save_hi(a)
    a.sw(4,29,0x300);a.sw(5,29,0x304);a.sw(6,29,0x308)
    restore_hi(a);abi.restore(a,finish=False);a.call(target);abi.save(a,after=True);save_hi(a)
    a.lw(8,29,abi.OFFSETS[31]);a.li(9,site+8);a.branch(5,8,9,'done')
    a.li(8,CONTROL);a.lw(9,8);a.li(10,MAGIC);a.branch(5,9,10,'done');a.lw(16,8,4);a.li(9,ROWS);a.r(0x2B,10,16,9);a.branch(5,10,0,'done')
    a.li(9,ROWS+10*STRIDE);a.r(0x2B,10,16,9);a.branch(4,10,0,'done')
    a.i(12,9,16,255);a.branch(5,9,0,'done')
    a.lw(17,29,abi.OFFSETS[2])
    if offset==84:
        a.lw(18,16,84);a.i(11,8,18,4);a.branch(4,8,0,'done');a.addiu(8,18,1);a.sw(8,16,84)
        a.r(0,8,0,18,4);a.r(0,9,0,18,3);a.r(0x21,8,8,9);a.r(0x21,18,16,8);a.addiu(18,18,128)
        a.lw(8,29,0x304);a.sw(8,18);a.sw(17,18,4)
        a.i(11,8,17,5);a.branch(4,8,0,'done');a.lw(19,29,0x300);abi.row_address(a,20,19,17,8)
        for source,dest in ((0,8),(0x40,12),(0x70,16)):
            a.lw(8,20,source);a.sw(8,18,dest)
    else:
        a.sw(17,16,offset)
        if offset in (224,232):
            abi.pointer(a,17,0x34,'done',8,9);a.lw(8,17,0x30 if offset==224 else 0);a.sw(8,16,offset+4)
    a.label('done');restore_hi(a);abi.restore(a);a.jr();body=a.finish();assert len(body)<0x800;return base,body

def build_memory(ram,source='memory'):
    empty=dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[])
    profile=game_profile.installed()
    if not profile or profile.get('runtime_variant')!=game_profile.POWER_SCALE_VARIANT:return empty
    if len(ram)!=0x8000000:raise ValueError('Fusion trace requires128MiB RAM')
    if ram[HOOK:HOOK+8]!=abi.NATIVE(HOOK,8):raise ValueError('Native fusion input call changed')
    if any(ram[BASE:END]):raise ValueError('Fusion input trace reservation occupied')
    parts=[(CODE,code()),(CONTROL,struct.pack('<2I',MAGIC,0)),(ROWS,bytes(10*STRIDE)),
           (HOOK,struct.pack('<I',(3<<26)|(CODE>>2)))]
    for index,(site,target,offset) in enumerate(CALLS):
        site=A(site);expected=abi.NATIVE(site,8)
        if site==A(0x203830):expected=struct.pack('<I',(3<<26)|(abi.SIDE>>2))+expected[4:]
        if ram[site:site+8]!=expected:raise ValueError(f'Fusion native gate call changed:{site:08X}')
        base,body=wrapper(index);parts.extend(((base,body),(site,struct.pack('<I',(3<<26)|(base>>2)))))
    return dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[dict(address=p,expected_hex=ram[p:p+len(d)].hex(),data_hex=d.hex()) for p,d in parts])

def dependency_override(ram,address,data):
    """Recognize only the complete, audited installed native-call trace.

    Active-row and row contents are live telemetry, not executable ownership.
    No original predicate or unknown continuation is accepted as a substitute.
    """
    item=next(((i,site,target) for i,(site,target,_) in enumerate(CALLS) if A(site)==address),None)
    if item is None:return data
    if len(ram)!=0x8000000:raise ValueError('Fusion trace dependency requires128MiB RAM')
    if struct.unpack_from('<I',ram,CONTROL)[0]!=MAGIC:return data
    index,site,target=item
    predecessor=abi.NATIVE(address,8)
    if site==0x203830:predecessor=struct.pack('<I',(3<<26)|(abi.SIDE>>2))+predecessor[4:]
    if len(data) not in (4,8) or data!=predecessor[:len(data)]:
        raise ValueError('Fusion trace dependency predecessor changed')
    active=struct.unpack_from('<I',ram,CONTROL+4)[0]
    if active and (not ROWS<=active<ROWS+10*STRIDE or (active-ROWS)%STRIDE):
        raise ValueError('Fusion trace active row outside owned telemetry')
    main=code()
    if ram[CODE:CODE+len(main)]!=main:raise ValueError('Fusion trace entry code changed')
    entry=struct.pack('<I',(3<<26)|(CODE>>2))+abi.NATIVE(HOOK+4,4)
    if ram[HOOK:HOOK+8]!=entry:raise ValueError('Fusion trace entry hook/delay changed')
    for i,(at,_,_) in enumerate(CALLS):
        base,body=wrapper(i);at=A(at)
        if ram[base:base+len(body)]!=body:raise ValueError(f'Fusion trace gate code changed:{at:08X}')
        expected=struct.pack('<I',(3<<26)|(base>>2))+abi.NATIVE(at+4,4)
        if ram[at:at+8]!=expected:raise ValueError(f'Fusion trace gate hook/delay changed:{at:08X}')
    base,_=wrapper(index)
    return (struct.pack('<I',(3<<26)|(base>>2))+predecessor[4:])[:len(data)]


def poll(client,owner):
    if client.read_u32(CONTROL)!=MAGIC or client.read_u32(CONTROL+4):return
    count=client.read_u32(core.MODE+4)
    if not 2<=count<=10:return
    data=client.read(ROWS,count*STRIDE);previous=getattr(owner,'fusion_input_trace_counts',{})
    from autopilot import log
    for physical in range(count):
        row=struct.unpack_from('<64I',data,physical*STRIDE)
        if not row[0]:previous[physical]=0;continue
        if previous.get(physical)==row[0]:continue
        previous[physical]=row[0]
        candidates=[dict(query=row[32+6*i],index=row[33+6*i],cid=row[34+6*i],health=row[35+6*i],status=row[36+6*i]) for i in range(min(row[21],4))]
        raw=data[physical*STRIDE+96:physical*STRIDE+121].hex()
        log(f'Fusion input: physical={physical} cid={row[1]} variant={row[2]} result={row[3]} raw_restoration_partner={row[4]} raw_kind={row[5]} cost={row[6]} eligible={row[7]} partner_slot={row[8]:08X} action={row[9]} stocks={row[10]} ki99C={row[12]} partner_cid={row[11]:08X} stockFlag={row[13]} stateFlag={row[14]} snapshot1300={row[61]} currentSlot={row[15]} gates5E_AF_busy_SIDE_stock={[f"{v:08X}" for v in row[16:21]]} memberStatus={row[57]:08X} memberHealth={row[59]:08X} recipeAE_C6={raw} candidates={candidates}')
    owner.fusion_input_trace_counts=previous
