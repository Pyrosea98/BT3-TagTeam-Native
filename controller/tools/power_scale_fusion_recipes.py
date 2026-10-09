"""Narrow Power Scale base-Super pairing, retaining authored native recipes.

Runtime119/60 and192/194 use guarded reviewed pairs. Slot0 prefers the one
alive, unconsumed base-Super ally only when its mirrored native bench entry is
eligible. Other slots retain their original Z forms. No eligible Super ally:
all original getters remain unchanged. B7 is partner restoration metadata,
AE is stock cost. Base Super pair is free as confirmed by the user. Black's
authored three-stock cost is retained. The user confirmed Vegito/Gogeta choices;
the Dance entry incorrectly naming Cui uses the verified native Gogeta identity.
"""
import struct
from native_map import A,CRC,SERIAL
from prototype import Assembler
import fresh_team_combat as core
import fusion_partner_lifecycle as fusion
import team_participation as part
import game_profile

BASE,END=0x074B0000,0x074C0000
SELECT=BASE;PARTNER=BASE+0x2000;METADATA=BASE+0x3000
PARTNER_TRAMP=BASE+0x4000;METADATA_TRAMP=BASE+0x4100
RESULT,COST=BASE+0x5000,BASE+0x6000
RESULT_TRAMP,COST_TRAMP=BASE+0x4200,BASE+0x4300
HOOKS=((A(0x20E3A0),PARTNER,PARTNER_TRAMP),(A(0x20E370),METADATA,METADATA_TRAMP),
       (A(0x20E340),RESULT,RESULT_TRAMP),(A(0x20E3E8),COST,COST_TRAMP))
SAVED=tuple(r for r in range(1,32) if r not in (2,29))
FRAME=0x200
# Direct main-resource entry17 bytes from supported expanded Power Scale ISO.
RECIPES={119:bytes.fromhex('03 03 04 02 01 01 33 55 35 1f 1f 1f 1f 20 24 ff 1f 20 24 ff 1f 20 24 ff'),
          60:bytes.fromhex('03 03 04 02 01 01 33 55 35 03 03 03 03 04 05 06 03 04 05 06 03 04 05 06'),
          192:bytes.fromhex('03 00 00 02 00 00 4c ff ff 9d ff ff 9d ff ff ff 9d ff ff ff 9d ff ff ff'),
          194:bytes.fromhex('03 00 00 02 00 00 4c ff ff 22 ff ff 22 ff ff ff 22 ff ff ff 22 ff ff ff')}
PAIRS={119:60,60:119,192:194,194:192}

def recipe_guard(a,param,cid,fail,tag):
    for character,blob in RECIPES.items():
        a.addiu(8,0,character);a.branch(5,cid,8,tag+str(character))
        for offset,value in enumerate(blob,0xAE):
            a.i(36,8,param,offset);a.addiu(9,0,value);a.branch(5,8,9,fail)
        a.jump(tag+'done');a.label(tag+str(character))
    a.jump(fail);a.label(tag+'done')

def select():
    """a0 actor,a1 variant -> counterpart base CID, else zero; leaf."""
    a=Assembler(SELECT);a.move(16,4);a.move(17,5);core.gate(a,'no');a.move(18,10)
    a.i(11,8,17,3);a.branch(4,8,0,'no')
    for control,magic in ((fusion.CONTROL,1),(part.CONTROL,5)):
        a.li(8,control);a.lw(9,8);a.addiu(11,0,magic);a.branch(5,9,11,'no')
        a.lw(9,8,4);a.lw(11,28,-22364);a.branch(5,9,11,'no')
        a.lw(9,8,8);a.branch(5,9,18,'no')
    a.move(19,0)
    a.label('find');a.r(0,8,0,19,2);a.li(9,core.POINTERS);a.r(0x21,9,9,8);a.lw(9,9)
    a.branch(4,9,16,'owner');a.addiu(19,19,1);a.branch(5,19,18,'find');a.jump('no')
    a.label('owner');a.li(8,part.CONTROL);a.lw(9,8,12);a.lw(11,8,16)
    a.addiu(8,0,1);a.r(4,8,19,8);a.r(0x24,9,9,8);a.branch(4,9,0,'no')
    a.r(0x24,11,11,8);a.branch(5,11,0,'no')
    a.lw(8,16,12);a.i(11,9,8,12);a.branch(4,9,0,'no')
    a.r(0,8,0,8,2);a.li(9,core.MODELS);a.r(0x21,9,9,8);a.lw(20,9)
    fusion.pointer(a,20,0x1670,'no');a.lw(8,20,16);a.lw(9,16,12);a.branch(5,8,9,'no')
    a.lw(21,20,12);a.lw(22,20,0x91C)
    fusion.pointer(a,22,0x100,'no');recipe_guard(a,22,21,'no','source_')
    for cid,counterpart in PAIRS.items():
        a.addiu(8,0,cid);a.branch(5,21,8,f'pair_next{cid}')
        if cid in (192,194):a.branch(5,17,0,'no')
        a.addiu(23,0,counterpart);a.jump('chosen');a.label(f'pair_next{cid}')
    a.jump('no');a.label('chosen');a.move(24,0);a.move(25,0)
    a.label('scan');a.branch(4,24,19,'next');a.i(12,8,24,1);a.i(12,9,19,1);a.branch(5,8,9,'next')
    a.li(8,part.CONTROL);a.lw(9,8,12);a.lw(11,8,16);a.addiu(8,0,1);a.r(4,8,24,8)
    a.r(0x24,9,9,8);a.branch(4,9,0,'next');a.r(0x24,11,11,8);a.branch(5,11,0,'next')
    a.r(0,8,0,24,2);a.li(9,core.POINTERS);a.r(0x21,9,9,8);a.lw(26,9)
    fusion.pointer(a,26,0x1A00,'next');a.lw(8,26);a.branch(5,8,24,'next')
    a.lw(8,26,12);a.i(11,9,8,12);a.branch(4,9,0,'next')
    a.r(0,8,0,8,2);a.li(9,core.MODELS);a.r(0x21,9,9,8);a.lw(20,9)
    fusion.pointer(a,20,0x1670,'next');a.lw(8,20,16);a.lw(9,26,12);a.branch(5,8,9,'next')
    a.lw(21,20,12);a.branch(5,21,23,'next')
    a.lw(22,20,0x91C);fusion.pointer(a,22,0x100,'next');recipe_guard(a,22,21,'next','other_')
    # Exactly the native 1CE108 entry and 203898 eligibility fields. Health
    # is entry+0x40; native +0x30 status is relative to that health subrecord.
    a.r(2,27,0,24,1);a.lw(8,16,0x998);a.i(11,9,8,6);a.branch(4,9,0,'next')
    a.r(0x2B,9,27,8);a.branch(4,9,0,'next');fusion.row_address(a,22,16,27,8)
    a.lw(8,22);a.branch(5,8,23,'next');a.lw(8,22,8);a.branch(4,8,0,'next')
    a.lw(8,22,64);a.i(10,9,8,1);a.branch(5,9,0,'next')
    a.lw(8,22,112);a.branch(5,8,0,'next');a.addiu(25,25,1)
    a.label('next');a.addiu(24,24,1);a.branch(5,24,18,'scan')
    a.addiu(8,0,1);a.branch(5,25,8,'no');a.move(2,23);a.jr()
    a.label('no');a.move(2,0);a.jr();return a.finish()

def wrapper(address,trampoline,partner=False,mode=None):
    a=Assembler(address);a.addiu(29,29,-FRAME)
    for i,r in enumerate(SAVED):a.i(31,r,29,16*i)
    if partner:a.branch(5,6,0,'fallback')
    a.call(SELECT);a.branch(4,2,0,'fallback')
    if mode in ('result','cost'):
        a.addiu(8,0,119);a.branch(4,2,8,'super');a.addiu(8,0,60);a.branch(4,2,8,'super')
        if mode=='cost':a.jump('fallback')
        else:a.addiu(2,0,195);a.jump('selected')
        a.label('super')
        if mode=='cost':a.move(2,0)
        else:
            a.lw(8,29,16*SAVED.index(5));a.branch(4,8,0,'vegito')
            a.addiu(9,0,2);a.branch(4,8,9,'gogeta')
            # User-confirmed Gogeta choice: native110 is base Gogeta;85 is Cui.
            a.addiu(2,0,110);a.jump('selected')
            a.label('vegito');a.addiu(2,0,51);a.jump('selected')
            a.label('gogeta');a.addiu(2,0,53)
        a.label('selected')
    for i,r in enumerate(SAVED):a.i(30,r,29,16*i)
    a.addiu(29,29,FRAME);a.jr()
    a.label('fallback')
    for i,r in enumerate(SAVED):a.i(30,r,29,16*i)
    a.addiu(29,29,FRAME);a.jump(trampoline);return a.finish()

def pieces():
    result=[(SELECT,select()),(PARTNER,wrapper(PARTNER,PARTNER_TRAMP,True)),(METADATA,wrapper(METADATA,METADATA_TRAMP)),
            (RESULT,wrapper(RESULT,RESULT_TRAMP,mode='result')),(COST,wrapper(COST,COST_TRAMP,mode='cost'))]
    for hook,_,tramp in HOOKS:
        result.append((tramp,fusion.NATIVE(hook,8)+struct.pack('<2I',(2<<26)|((hook+8)>>2),0)))
    for at,data in result:
        if not BASE<=at<at+len(data)<=END:raise ValueError('Fusion recipe reservation overflow')
    return result

def build_memory(ram,source='memory'):
    profile=game_profile.installed()
    if not profile or profile.get('runtime_variant')!=game_profile.POWER_SCALE_VARIANT:
        return dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[],limitations=['No reviewed Power Scale profile.'])
    if len(ram)!=0x8000000:raise ValueError('Requires128MiB RAM')
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    manager,count=u(core.ACTORS),u(core.MODE+4)
    if (u(fusion.CONTROL),u(fusion.CONTROL+4),u(fusion.CONTROL+8))!=(1,manager,count):raise ValueError('Install fusion lifecycle before Super recipes')
    blocks=pieces()
    for at,data in blocks:
        if any(ram[at:at+len(data)]):raise ValueError(f'Fusion recipe reservation occupied:{at:08X}')
    for hook,wrapper_address,_ in HOOKS:
        if ram[hook:hook+8]!=fusion.NATIVE(hook,8):raise ValueError(f'Native fusion recipe getter changed:{hook:08X}')
        blocks.append((hook,struct.pack('<2I',(2<<26)|(wrapper_address>>2),0)))
    return dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[dict(address=p,expected_hex=ram[p:p+len(d)].hex(),data_hex=d.hex()) for p,d in blocks],limitations=['Reviewed base Super119/60 and Black Rose192/Zamasu194 pairs; transformed Super forms unchanged.','Super free: Vegito51/Gogeta110/GogetaSSJ53, matching the user-confirmed Vegito/Gogeta choices.','Black pair result195, native three-stock cost unchanged. Prefer one eligible ally at slot0; original slots1..3 retained.'])
