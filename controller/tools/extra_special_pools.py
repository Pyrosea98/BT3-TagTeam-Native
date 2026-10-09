"""Initialize separate native special-effect rows for captured extra fighters.

Offline manifest builder. Requires a held, idle checkpoint without any active
special descendants. Original leader effect pools are retained. No PINE calls.
"""
from native_map import A, CRC, RANGE, SERIAL, elf_path
import argparse
import json
import struct
from pathlib import Path

import fresh_team_combat as core
import opponent_events as events
import team_start_gate as start
import team_intro as intro
from camera_snapshot import read_ram
from prototype import Assembler, ROOT, elf_reader
from battle_mode_policy import ACTOR_COUNTS
from native_map import FILE_ID
import regional

CODE, RESOURCE, BLAST1, BLAST2 = 0x07500000,0x07504000,0x07504200,0x07504400
FREE, FREE_TAIL, NOOP, CALLBACKS = 0x07504600,0x07504700,0x07504800,0x07504900
CONTROL, RECORDS = 0x0750F000,0x0750F200
ROWS, NODES, EVENT_NODES, EVENT_PAYLOADS = 0x07510000,0x07515000,0x07515200,0x07515400
END, ROW_BYTES, ROW_COUNT, ARENA_BYTES = 0x07520000,1344,12,0x100000
GLOBAL, ALLOC_GLOBAL, HOOK = A(0x2FE9F8),A(0x2FEAE0),A(0x1C2A28)
SAVED = tuple(range(1,29))+(30,31)
META_CALLS = ((A(0x14AEC0),RESOURCE,A(0x14BC98),156),
              (A(0x14B27C),BLAST1,A(0x205370),2352),(A(0x14B588),BLAST2,A(0x205330),2348))


def immutable_combat_literals(ram,models,addresses):
    """Prove apparent aliases are unchanged bytes of a loaded original asset.

    Character animation/combat files can contain packed constants that numerically equal
    an effect-row address. Never relocate those values. This narrow exception
    requires an actual registered owner's correctly identified animation/combat bundle
    and byte-for-byte agreement of the entire file with the original USA ISO.
    Unknown heap/stack/code values and any modified file still fail closed.
    """
    if not addresses:return set(),[]
    import hashlib
    import pycdlib
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    registry=u(A(0x2FEC44))+439276;files={}
    for model in models:
        resource=u(model+20);character=u(model+12)
        if not 0x100000<=resource<=len(ram)-56:continue
        handle=u(resource+52)
        expected=registry+0x2A0+56*handle if handle<2 else registry+56*(handle-2)
        if not 0<=character<=160 or not 0<=handle<14 or resource!=expected or u(resource+48) not in (1,3):continue
        for field,logical in ((16,1432),(32,1433)):
            base,size,file_id=(u(resource+field),u(resource+field+4),u(resource+field+8))
            if (file_id!=FILE_ID(10*character+logical) or not 0<size<=0x800000 or
                    not 0x100000<=base<=len(ram)-size):continue
            found={p for p in addresses if base<=p and p+4<=base+size}
            if found:files[(base,size,file_id)]=found
    if not files:return set(),[]
    import game_profile
    path=game_profile.source_iso(ROOT.parent/'games'/regional.ISO_NAME)
    if not path.is_file():return set(),[]
    if regional.PAL:
        # file_id is the loaded (European) global ID: read that very file, by the disc's own numbering.
        verified=set();receipts=[]
        with regional.open_disc(path) as disc:
            for (base,size,file_id),found in files.items():
                data=disc.read(file_id);length=len(data)
                if length<=0 or ((length+2047)&-2048)!=size or ram[base:base+length]!=data:continue
                literals={p for p in found if p+4<=base+length}
                verified.update(literals)
                receipts.append(dict(resource_file=file_id,address=base,bytes=length,
                                     sha256=hashlib.sha256(data).hexdigest(),literals=sorted(literals)))
        return verified,receipts
    iso=pycdlib.PyCdlib();iso.open(str(path));verified=set();receipts=[]
    try:
        with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as afs:
            for (base,size,file_id),found in files.items():
                afs.seek(8+(file_id-1)*8);offset,length=struct.unpack('<2I',afs.read(8))
                if length<=0 or ((length+2047)&-2048)!=size:continue
                afs.seek(offset);data=afs.read(length)
                if len(data)!=length or ram[base:base+length]!=data:continue
                literals={p for p in found if p+4<=base+length}
                verified.update(literals)
                receipts.append(dict(resource_file=file_id,address=base,bytes=length,
                                     sha256=hashlib.sha256(data).hexdigest(),literals=sorted(literals)))
    finally:iso.close()
    return verified,receipts


def bridge(code, previous, field):
    a=Assembler(code);a.addiu(29,29,-0x20)
    for i,r in enumerate((8,9,10)):a.i(63,r,29,i*8)
    a.li(8,CONTROL);a.lw(9,8,16);a.branch(4,9,0,'old')
    a.lw(9,8,20);a.branch(5,9,4,'old')
    a.lw(9,8,4);a.lw(10,28,-22364);a.branch(5,9,10,'old')
    a.lw(9,8,24)
    if field==156:
        a.i(11,10,5,5);a.branch(4,10,0,'zero')
        a.r(0,10,0,5,2);a.r(0x2D,9,9,10)
    a.lw(2,9,field);a.jump('done')
    a.label('zero');a.move(2,0)
    a.label('done')
    for i,r in enumerate((8,9,10)):a.i(55,r,29,i*8)
    a.addiu(29,29,0x20);a.jr()
    a.label('old')
    for i,r in enumerate((8,9,10)):a.i(55,r,29,i*8)
    a.addiu(29,29,0x20);a.jump(previous)
    return a.finish()


def free_code():
    a=Assembler(FREE);a.addiu(29,29,-0x20)
    for i,r in enumerate((8,9,10)):a.i(63,r,29,i*8)
    a.li(8,CONTROL);a.lw(9,8,28);a.lw(10,28,-22648)
    a.branch(5,9,10,'old');a.lw(9,10,4);a.li(8,ROWS);a.branch(5,9,8,'old')
    a.li(8,CONTROL);a.lw(9,8,32);a.sw(9,10,4);a.addiu(9,0,2);a.sw(9,10,8)
    a.addiu(9,0,90);a.sw(9,8);a.sw(0,8,16)
    a.label('old')
    for i,r in enumerate((8,9,10)):a.i(55,r,29,i*8)
    a.addiu(29,29,0x20);a.jump(FREE_TAIL)
    return a.finish()


def payload(previous, actors, mids, models, allocator, primary, rootpool):
    a=Assembler(CODE);a.addiu(29,29,-0x160)
    for i,r in enumerate(SAVED):a.i(63,r,29,i*8)
    for i in range(12):a.i(57,20+i,29,0x100+i*4)
    a.li(16,CONTROL);a.lw(8,16);a.branch(5,8,0,'done')
    a.lw(8,16,4);a.lw(9,28,-22364);a.branch(5,8,9,'error101')
    for address,value in ((core.MODE,1),(core.MODE+4,len(actors)),(core.MODE+12,len(actors)),
                          (core.PAIR+4,0),(GLOBAL,primary),(ALLOC_GLOBAL,allocator),
                          (primary+4,ROWS),(primary+8,2),(rootpool+12,0)):
        a.li(8,address);a.lw(8,8);a.li(9,value);a.branch(5,8,9,'error101')
    for i,(actor,mid,model) in enumerate(zip(actors,mids,models)):
        for address,value in ((core.POINTERS+i*4,actor),(actor,i),(actor+12,mid),
                              (core.MODELS+mid*4,model),(actor+0x948,11),
                              (actor+0x1278,0),(actor+0x127C,0),(actor+0x1280,0),(actor+0x1284,0)):
            a.li(8,address);a.lw(8,8);a.li(9,value);a.branch(5,8,9,'error102')
    # Borrow neither native side's bounded bump storage. Each extra gets its
    # own arena before any initializer can be called or any command unblocked.
    a.addiu(8,0,1);a.sw(8,16)
    for i in range(len(actors)-2):
        a.li(4,ARENA_BYTES);a.addiu(5,0,32);a.move(6,0);a.addiu(7,0,1)
        a.call(A(0x2554D8));a.branch(4,2,0,'error110')
        a.li(17,RECORDS+i*64);a.sw(2,17,12)
        a.move(4,2);a.move(5,0);a.li(6,ARENA_BYTES);a.call(A(0x2A9ACC))
    a.li(18,allocator+5*16)
    for off in (0,4,8,12):a.lw(8,18,off);a.sw(8,16,0x80+off)
    a.li(8,allocator);a.lw(9,8,148);a.sw(9,16,0x90)
    a.li(8,rootpool);a.li(9,NODES);a.sw(9,8,12)
    for i,(mid,model) in enumerate(zip(mids[2:],models[2:])):
        a.li(17,RECORDS+i*64);a.lw(19,17,12)
        a.sw(19,18);a.sw(19,18,4);a.li(8,ARENA_BYTES);a.sw(8,18,8);a.sw(0,18,12)
        a.li(8,mid);a.sw(8,16,20);a.li(8,model);a.sw(8,16,24)
        a.addiu(8,0,1);a.sw(8,16,16)
        a.li(4,rootpool);a.li(5,CALLBACKS);a.addiu(6,17,4);a.call(A(0x1AD7B8))
        a.sw(2,17,16);a.li(8,ROWS+mid*ROW_BYTES);a.sw(2,8,1324)
        a.lw(8,18,12);a.sw(8,17,20)
        a.sw(0,16,16)
        # Restore native allocator state before every verification/failure.
        for off in (0,4,8,12):a.lw(8,16,0x80+off);a.sw(8,18,off)
        a.lw(8,16,0x90);a.li(9,allocator);a.sw(8,9,148)
        a.lw(8,17,16);a.branch(4,8,0,'error120')
        a.lw(8,17,20);a.li(9,ARENA_BYTES);a.r(0x2B,9,9,8);a.branch(5,9,0,'error121')
        a.li(19,ROWS+mid*ROW_BYTES)
        a.lw(8,19,1320);a.branch(4,8,0,'error122')
        for slot in range(5):
            a.lw(8,19,slot*80+36);a.li(9,ROWS+mid*ROW_BYTES+480+slot*140)
            a.branch(5,8,9,'error122')
            a.li(8,model);a.lw(8,8,156+slot*4);a.lw(9,19,slot*80+28)
            a.branch(5,8,9,'error122');a.branch(4,8,0,f'absent{i}_{slot}')
            a.lw(8,19,slot*80+40);a.branch(4,8,0,'error122')
            a.label(f'absent{i}_{slot}')
        a.lw(8,16,12);a.addiu(8,8,1);a.sw(8,16,12)
    a.li(8,primary);a.addiu(9,0,ROW_COUNT);a.sw(9,8,8)
    a.addiu(8,0,5);a.sw(8,16);a.jump('done')
    for error in (101,102,110,120,121,122):
        a.label(f'error{error}');a.addiu(8,0,error);a.sw(8,16);a.sw(0,16,16);a.jump('done')
    a.label('done');a.li(16,CONTROL);a.lw(8,16);a.addiu(9,0,5);a.branch(4,8,9,'restore')
    a.lw(11,16,4);a.lw(9,28,-22364);a.branch(5,11,9,'restore')
    for name,ctrl in (('start',start.CONTROL),('intro',intro.CONTROL)):
        a.li(8,ctrl);a.lw(9,8);a.addiu(10,0,1);a.branch(5,9,10,f'skip_{name}')
        a.lw(9,8,8);a.branch(5,9,11,f'skip_{name}');a.sw(0,8,4)
        a.label(f'skip_{name}')
    a.label('restore')
    for i in range(12):a.i(49,20+i,29,0x100+i*4)
    for i,r in enumerate(SAVED):a.i(55,r,29,i*8)
    a.addiu(29,29,0x160);a.jump(previous)
    data=a.finish();assert len(data)<RESOURCE-CODE;return data


def absent_special_resource(ram, model, slot):
    """Match native 24FA20: equal adjacent bundle offsets mean no effect.

    A null model field alone is not enough: prove that its own fully loaded
    combat bundle declares this slot empty. Buffs without an effect parent
    still have move metadata, which native 14B018 initializes separately.
    """
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    valid=lambda p,n:0x100000<=p<=len(ram)-n
    if not 0<=slot<5 or not valid(model,176):return False
    resource=u(model+20)
    if not valid(resource,56) or u(resource+48) not in (1,3):return False
    base,size=u(resource+32),u(resource+36)
    if not 32<=size<=0x800000 or not valid(base,size):return False
    count=u(base)
    if not 5<=count<=256 or 4*(count+2)>size:return False
    start,end=u(base+4*(slot+1)),u(base+4*(slot+2))
    return start==end and 4*(count+2)<=start<=size


def pointer_word_indices(words, base, span):
    """Exactly np.flatnonzero((words>=base)&(words<base+span)&((words&3)==0)).

    For uint32 words one wrapping subtraction tests both bounds, and only the
    few candidates are tested for alignment; the ascending index order is kept.
    The identity needs base+span within 32 bits, which every caller's pointer
    validation (inside 128 MiB) already guarantees."""
    import numpy as np
    if words.dtype!=np.dtype('<u4') or not (0<=base<1<<32 and 0<=span<1<<32 and base+span<=1<<32):
        raise ValueError('Pointer scan requires uint32 words and a 32-bit range')
    candidates=np.flatnonzero((words-np.uint32(base))<np.uint32(span))
    return candidates[(words[candidates]&3)==0]


def build_memory(ram, config=None, source='<offline-memory>'):
    import numpy as np
    if len(ram)!=0x8000000:raise ValueError('Requires128MiB captured RAM')
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    valid=lambda p,n:0x100000<=p<=len(ram)-n
    manager,count=u(core.ACTORS),u(core.MODE+4)
    if count not in ACTOR_COUNTS or u(core.MODE)!=1 or u(core.MODE+8)!=manager or u(core.MODE+12)!=count:
        raise ValueError('Requires captured4/6 mode')
    if u(core.PAIR+4):raise ValueError('AI aliases must be restored')
    actors=[u(core.POINTERS+i*4) for i in range(count)];mids=[u(p+12) for p in actors]
    if mids[:2]!=[0,1] or len(set(mids))!=count or any(i>=12 for i in mids):raise ValueError('Model identity mismatch')
    models=[u(core.MODELS+i*4) for i in mids]
    for i,(p,mid,model) in enumerate(zip(actors,mids,models)):
        if not valid(p,0x1600) or u(p)!=i or not valid(model,0x1670) or u(model+16)!=mid:raise ValueError('Invalid actual fighter')
        if u(p+0x948)!=11 or any(u(p+o) for o in (0x1278,0x127C,0x1280,0x1284)):
            raise ValueError('Hold every actor idle with CPU/input disabled before effect initialization')
        for off in (2348,2352):
            if not valid(u(model+off),0x400):raise ValueError('Missing own move metadata')
        for slot in range(5):
            effect=u(model+156+slot*4)
            if not valid(effect,16) and not (effect==0 and absent_special_resource(ram,model,slot)):
                raise ValueError(f'Missing own special resource: fighter {i}, character {u(model+12)}, slot {slot+1}, pointer {effect:#010x}')
    primary=u(GLOBAL);old=u(primary+4);rootpool=u(primary);allocator=u(ALLOC_GLOBAL)
    if not valid(primary,12) or u(primary+8)!=2 or not valid(old,2688) or not valid(rootpool,24):raise ValueError('Expected native primary table')
    if not valid(allocator,156) or u(allocator+152)!=0x3FE:raise ValueError('Unexpected native bump allocator mode')
    if u(rootpool+12):raise ValueError('Unexpected original root free list')
    if any(ram[CODE:END]):raise ValueError('Special effect reservation occupied')
    rows=bytearray(ROW_BYTES*ROW_COUNT);rows[:2688]=ram[old:old+2688]
    refs={primary+4};patches=[]
    for mid in range(2):
        for slot in range(5):
            row=old+mid*ROW_BYTES+slot*80;n=u(row+40)
            if u(row+36)!=old+mid*ROW_BYTES+480+slot*140:raise ValueError('Native row layout mismatch')
            refs.add(row+36)
            struct.pack_into('<I',rows,mid*ROW_BYTES+slot*80+36,ROWS+mid*ROW_BYTES+480+slot*140)
            if n==0 and u(row+28)==0 and u(models[mid]+156+slot*4)==0 and absent_special_resource(ram,models[mid],slot):
                continue  # Native 14AE50 skips parent creation for empty effects.
            if not valid(n,64):raise ValueError('Native row layout mismatch')
            body,pool=u(n+56),u(n+36)
            if not valid(body,8192) or not valid(pool,24) or u(pool+4) or u(pool+8):raise ValueError('Active special descendants must finish before relocation')
            matches=[body+off for off in range(0,8192,4) if u(body+off)==row]
            # Empty-effect parent classes do not cache a row pointer. Other
            # classes may leave copies in inactive descendant payloads too.
            refs.update(matches)
    words=np.frombuffer(ram,dtype='<u4');indices=pointer_word_indices(words,old,2688)
    observed=set(int(i)*4 for i in indices)
    permitted_targets={old+mid*ROW_BYTES+slot*80 for mid in range(2) for slot in range(5)}
    permitted_targets.update(old+mid*ROW_BYTES+480+slot*140 for mid in range(2) for slot in range(5))
    arenas=[]
    for group in range(9):
        base,_,capacity,used=struct.unpack_from('<4I',ram,allocator+group*16)
        if used>capacity or not valid(base,capacity):raise ValueError('Native effect arena is not intact')
        arenas.append((base,base+used))
    unknown={address for address in observed if u(address) not in permitted_targets or
             not any(lo<=address<=hi-4 for lo,hi in arenas)}
    immutable,asset_receipts=immutable_combat_literals(ram,models,unknown)
    for address in observed-immutable:
        # Reject stack/code/unknown-heap aliases. Only pointers to exact typed
        # row/metadata boundaries inside captured native effect bump arenas
        # can be migrated. This includes native scratch and inactive children.
        if u(address) not in permitted_targets or not any(lo<=address<=hi-4 for lo,hi in arenas):
            raise ValueError('Additional cached primary-row reference prevents safe relocation')
        if address!=primary+4 and not old<=address<old+2688:
            patches.append((address,struct.pack('<I',ROWS+u(address)-old)))
    if not refs<=observed:raise ValueError('Missing expected typed row reference')
    refs=observed-immutable
    for mid in range(2,ROW_COUNT):struct.pack_into('<I',rows,mid*ROW_BYTES+1328,0xFFFFFFFF)
    extra=count-2;nodes=bytearray(extra*64);records=bytearray(extra*64)
    for i,(actor,mid,model) in enumerate(zip(actors[2:],mids[2:],models[2:])):
        struct.pack_into('<H',nodes,i*64+2,3+i);struct.pack_into('<I',nodes,i*64+32,rootpool)
        struct.pack_into('<I',nodes,i*64+52,NODES+(i+1)*64 if i+1<extra else 0)
        struct.pack_into('<3I',records,i*64,actor,mid,model)
    # Existing opponent-event rows are already twelve-wide. Add monitor pool
    # storage without changing its original allocation/free pointers.
    event=u(events.EVENT_GLOBAL);epool=u(event)
    if u(event+4)!=events.ROWS or u(event+8)!=2 or u(events.CONTROL+12)!=event:raise ValueError('Reviewed expanded event rows required')
    if u(epool+4) or u(epool+8):raise ValueError('Active special monitors prevent initialization')
    free=u(epool+12);seen=[]
    while free:
        if not valid(free,64) or free in seen or len(seen)>=2:raise ValueError('Invalid native monitor free list')
        seen.append(free);free=u(free+52)
    if len(seen)!=2:raise ValueError('Native monitor pool must have two idle nodes')
    enodes=bytearray(extra*64)
    for i in range(extra):
        struct.pack_into('<H',enodes,i*64+2,2+i);struct.pack_into('<I',enodes,i*64+32,epool)
        struct.pack_into('<I',enodes,i*64+52,EVENT_NODES+(i+1)*64 if i+1<extra else 0)
        struct.pack_into('<I',enodes,i*64+56,EVENT_PAYLOADS+i*28)
    _,_,native=elf_reader(elf_path(ROOT))
    previous=(u(HOOK)&0x3FFFFFF)<<2
    if u(HOOK)>>26!=2 or u(HOOK+4) or not 0x07000000<=previous<0x08000000:raise ValueError('Expected captured frame chain')
    for p,n in ((A(0x14AE50),0xC8),(A(0x14B018),0xF0),RANGE(0x14B108,0x7D8),(A(0x14B918),0x98),(A(0x1AD988),0x70),(A(0x14ADE8),8)):
        if ram[p:p+n]!=native(p,n):raise ValueError(f'Changed native special initializer {p:X}')
    control=bytearray(0x100)
    for off,value in ((4,manager),(8,count),(28,primary),(32,old),(36,rootpool),(40,allocator)):
        struct.pack_into('<I',control,off,value)
    pieces=[(CODE,payload(previous,actors,mids,models,allocator,primary,rootpool)),
            (FREE,free_code()),(FREE_TAIL,native(A(0x14ADE8),8)+struct.pack('<2I',(2<<26)|(A(0x14ADF0)>>2),0)),
            (NOOP,struct.pack('<2I',0x03E00008,0)),(CALLBACKS,struct.pack('<3I',A(0x14AF30),A(0x14AE50),NOOP)),
            (CONTROL,bytes(control)),(RECORDS,bytes(records)),(ROWS,bytes(rows)),(NODES,bytes(nodes)),
            (EVENT_NODES,bytes(enodes)),(EVENT_PAYLOADS,bytes(extra*28))]+patches
    for hook,code,previous_helper,field in META_CALLS:
        if u(hook)!=(3<<26)|(previous_helper>>2):raise ValueError('Changed metadata call')
        pieces += [(code,bridge(code,previous_helper,field)),(hook,struct.pack('<I',(3<<26)|(code>>2)))]
    pieces += [(seen[-1]+52,struct.pack('<I',EVENT_NODES)),(primary+4,struct.pack('<I',ROWS)),
               (A(0x14ADE8),struct.pack('<2I',(2<<26)|(FREE>>2),0)),(HOOK,struct.pack('<2I',(2<<26)|(CODE>>2),0))]
    blocks=[dict(address=p,expected_hex=ram[p:p+len(d)].hex(),data_hex=d.hex()) for p,d in pieces]
    intervals=sorted((b['address'],b['address']+len(bytes.fromhex(b['data_hex']))) for b in blocks)
    assert all(end<=b for (_,end),(b,_) in zip(intervals,intervals[1:]))
    return dict(serial=SERIAL,crc=CRC,source=str(source),blocks=blocks,
                status='HELD NATIVE EXTRA SPECIAL INITIALIZATION; WAIT STATUS5 BEFORE START',
                control=CONTROL,records=RECORDS,record_stride=64,rows=ROWS,capacity=ROW_COUNT,
                previous_frame=previous,old_rows=old,rebased_references=sorted(refs),
                immutable_asset_literals=sorted(immutable),verified_asset_files=asset_receipts,
                limitations=['Requires an idle preparation checkpoint, no active special effects.',
                             'Extra effect arenas remain allocated until checkpoint reset; no extra transforms.',
                             'Generic ki projectile compatibility guards remain in force.'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    x=p.parse_args();m=build_memory(read_ram(x.source),source=x.source);x.out.write_text(json.dumps(m,indent=2)+'\n');print(x.out)
