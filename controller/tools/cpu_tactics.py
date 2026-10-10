"""Optional 3 Hz ordinary CPU transformation planner; no host battle poller.

The scripted transform API is deliberately avoided: it can grant stocks.
Admission and initiation use the same guarded native calls as ordinary input.
"""
import json
import struct
from pathlib import Path
from prototype import Assembler
from native_map import A, CRC, SERIAL, ACTOR_HZ
import fresh_team_combat as core
import fusion_partner_lifecycle as abi
import fusion_duration as timer
import guest_killfeed as feed
import team_start_gate as start
import team_participation as part
import battle_mode_policy as modes
import mod_settings as prefs

FRAME, APPLY, MODEL, SCORE = 0x074A0000, 0x074A1000, 0x074A3000, 0x074A3800
CONTROL, ROWS, TIERS, FAMILIES, END = 0x074AF000, 0x074AF100, 0x074AF400, 0x074AF500, 0x074B0000
DIAGNOSTICS, DIAG_STRIDE = CONTROL+0x600, 64
MAGIC = 0x43505431
INTERVAL = max(1, round(ACTOR_HZ / 3))
KEYS = ('cpu_transform_allies', 'cpu_transform_enemies', 'cpu_tactics_preset')
# Local Power Scale trial candidates. Runtime labels and forward slot costs
# captured in the 2026-10-09 20:48..20:52 session; live acceptance still pending.
# Tier order authorizes upgrades only, never a reverse or cross-family slot.
POWER_SCALE_TRIAL_FAMILIES = ((31,32,33), (60,181,183,184,72), (119,76,167,179,83))
HELP = ('CPU transformations use native stock costs, character exceptions, giant restrictions and chance limits. '
        'Allies means the first player team; free-for-all CPUs are enemies. Native leaves the existing AI unchanged. '
        'When outmatched considers health, ki, recent damage and reviewed form tiers; unknown tiers add no score. '
        'Presets tune thresholds and cooldowns. Applies next match; Training keeps its own CPU behavior. '
        'CPU revival and autonomous fusion are not included yet.')


def frame_code(previous):
    a=Assembler(FRAME);abi.save(a);abi.restore(a,finish=False);a.call(previous);abi.save(a,after=True)
    # Preserve the previous continuation's complete integer/FPU/HI/LO result.
    a.r(16,8,0);a.i(63,8,29,0x288);a.r(18,8,0);a.i(63,8,29,0x290)
    a.call(APPLY);a.i(55,8,29,0x288);a.r(17,0,8);a.i(55,8,29,0x290);a.r(19,0,8)
    abi.restore(a);a.jr();return a.finish()


def model_code():
    # a0 actor -> v0 authenticated form parameter table; v1 current runtime ID.
    a=Assembler(MODEL);a.lw(8,4,12);a.i(11,9,8,12);a.branch(4,9,0,'no')
    a.r(0,9,0,8,2);a.li(10,core.MODELS);a.r(0x21,10,10,9);a.lw(2,10)
    abi.pointer(a,2,0x1670,'no',10,11);a.lw(9,2,16);a.branch(5,8,9,'no')
    a.lw(3,2,12);a.i(11,9,3,253);a.branch(4,9,0,'no')
    a.lw(2,2,0x91C);abi.pointer(a,2,0xB0,'no',10,11);a.jr()
    a.label('no');a.move(2,0);a.addiu(3,0,-1);a.jr();return a.finish()


def percent(a,out,row):
    a.lw(8,row);a.lw(9,row,4);a.branch(6,9,0,'invalid')
    a.li(10,1000000);a.r(0x2B,10,10,9);a.branch(5,10,0,'invalid')
    a.r(0x2B,10,9,8);a.branch(5,10,0,'invalid')
    a.addiu(10,0,100);a.r(24,0,8,10);a.r(18,8,0);a.r(26,0,8,9);a.r(18,out,0)


def score_code():
    # s2/s3 own actor/row, s4 target actor, s5 own telemetry row. v0 score.
    a=Assembler(SCORE);regs=(16,17,22,23,31);a.addiu(29,29,-0x30)
    for n,r in enumerate(regs):a.i(63,r,29,n*8)
    a.move(16,0);a.sw(0,24,4);a.move(4,20);a.call(feed.ROW);a.branch(4,2,0,'invalid')
    a.move(22,2);a.lw(8,22);a.branch(6,8,0,'invalid')
    percent(a,23,19);percent(a,17,22)
    a.addiu(8,23,-50);a.branch(1,8,0,'low');a.jump('gap')
    a.label('low');a.addiu(16,16,1);a.lw(8,24,4);a.i(13,8,8,1);a.sw(8,24,4)
    a.label('gap');a.r(0x23,8,17,23);a.i(10,9,8,25);a.branch(5,9,0,'ki');a.addiu(16,16,2);a.lw(8,24,4);a.i(13,8,8,2);a.sw(8,24,4)
    a.label('ki');a.lw(8,22,12);a.lw(9,19,12);a.r(0x23,8,8,9);a.li(9,20000)
    a.r(0x2A,9,8,9);a.branch(5,9,0,'hit');a.addiu(16,16,1);a.lw(8,24,4);a.i(13,8,8,4);a.sw(8,24,4)
    a.label('hit');a.lw(8,21,4);a.lw(9,19);a.r(0x2B,8,9,8)
    a.branch(4,8,0,'tier');a.addiu(16,16,1);a.lw(8,24,4);a.i(13,8,8,8);a.sw(8,24,4)
    a.label('tier');a.addiu(8,0,1);a.sw(8,24,8);a.move(4,18);a.call(MODEL);a.branch(4,2,0,'done')
    a.li(8,TIERS);a.r(0x21,8,8,3);a.i(36,23,8,0);a.addiu(9,0,255);a.branch(4,23,9,'done')
    a.move(4,20);a.call(MODEL);a.branch(4,2,0,'done')
    a.li(8,TIERS);a.r(0x21,8,8,3);a.i(36,8,8,0);a.addiu(9,0,255);a.branch(4,8,9,'done')
    a.sw(0,24,8);a.r(0x2B,8,23,8);a.branch(4,8,0,'done');a.addiu(16,16,2);a.lw(8,24,4);a.i(13,8,8,16);a.sw(8,24,4)
    a.label('done');a.addiu(3,0,1);a.jump('return');a.label('invalid');a.move(16,0);a.move(3,0)
    a.label('return');a.move(2,16)
    for n,r in enumerate(regs):a.i(55,r,29,n*8)
    a.addiu(29,29,0x30);a.jr();return a.finish()


def apply_code(ffa=False,eligibility=0x073F8000,initiation=0x073F8400):
    a=Assembler(APPLY);abi.save(a)
    # Calls below use integer arithmetic, so preserve HI/LO even standalone.
    a.r(16,8,0);a.i(63,8,29,0x288);a.r(18,8,0);a.i(63,8,29,0x290)
    core.gate(a,'done');a.move(17,10);a.li(8,CONTROL);a.lw(9,8);a.li(11,MAGIC)
    a.branch(5,9,11,'done');a.lw(9,8,4);a.lw(11,28,-22364);a.branch(5,9,11,'done')
    a.lw(9,8,8);a.branch(5,9,17,'done');timer.active_combat(a,'done')
    a.li(8,part.CONTROL);a.lw(9,8);a.addiu(11,0,5);a.branch(5,9,11,'done')
    a.lw(9,8,4);a.lw(11,28,-22364);a.branch(5,9,11,'done')
    a.lw(9,8,8);a.branch(5,9,17,'done')
    a.li(8,CONTROL);a.lw(9,8,20);a.addiu(9,9,-1);a.sw(9,8,20)
    a.branch(7,9,0,'done');a.addiu(9,0,INTERVAL);a.sw(9,8,20)
    a.lw(9,8,32);a.addiu(9,9,1);a.sw(9,8,32);a.move(16,0)
    a.label('actor');a.r(0,9,0,16,6);a.li(24,DIAGNOSTICS);a.r(0x21,24,24,9);a.sw(24,29,0x298)
    a.addiu(8,0,2);a.sw(8,24);a.r(0,9,0,16,5);a.li(21,ROWS);a.r(0x21,21,21,9)
    a.lw(8,21,8);a.branch(6,8,0,'mask');a.addiu(8,8,-1);a.sw(8,21,8)
    a.label('mask');a.li(8,part.CONTROL);a.lw(9,8,12);a.lw(8,8,16)
    a.r(0x27,8,8,0);a.r(0x24,9,9,8);a.addiu(8,0,1);a.r(4,8,16,8)
    a.r(0x24,8,8,9);a.branch(4,8,0,'next')
    a.r(0,9,0,16,2);a.li(8,core.POINTERS);a.r(0x21,8,8,9);a.lw(18,8)
    a.lw(8,21);a.branch(5,8,18,'next');a.lw(8,18);a.branch(5,8,16,'next')
    a.addiu(8,0,1);a.sw(8,24);a.lw(8,18,0x1278);a.addiu(9,0,1);a.branch(5,8,9,'next')
    a.addiu(8,0,3);a.sw(8,24);a.move(4,18);a.call(feed.ROW);a.lw(24,29,0x298);a.branch(4,2,0,'next');a.move(19,2)
    a.lw(8,19);a.branch(6,8,0,'next');a.li(9,1000000);a.r(0x2B,9,9,8);a.branch(5,9,0,'next')
    a.lw(8,19,20);a.sw(8,24,12);a.addiu(8,0,4);a.sw(8,24);a.li(8,CONTROL)
    if ffa:a.lw(22,8,16)
    else:
        a.i(12,9,16,1);a.lw(11,8,24);a.branch(5,9,11,'enemy');a.lw(22,8,12);a.jump('scope')
        a.label('enemy');a.lw(22,8,16)
    a.label('scope');a.branch(4,22,0,'remember')
    a.addiu(8,0,5);a.sw(8,24);a.r(0,9,0,16,2);a.li(8,core.TABLE);a.r(0x21,8,8,9);a.lw(20,8)
    a.r(0x2B,8,20,17);a.branch(4,8,0,'remember');a.branch(4,16,20,'remember')
    if not ffa:
        a.i(12,8,16,1);a.i(12,9,20,1);a.branch(4,8,9,'remember')
    a.li(8,part.CONTROL);a.lw(9,8,12);a.lw(8,8,16);a.r(0x27,8,8,0);a.r(0x24,9,9,8)
    a.addiu(8,0,1);a.r(4,8,20,8);a.r(0x24,8,8,9);a.branch(4,8,0,'remember')
    a.r(0,9,0,20,2);a.li(8,core.POINTERS);a.r(0x21,8,8,9);a.lw(20,8)
    a.r(0,9,0,9,3);a.li(8,ROWS);a.r(0x21,8,8,9);a.lw(8,8);a.branch(5,8,20,'remember')
    abi.pointer(a,20,0x1600,'remember');a.call(SCORE);a.lw(24,29,0x298);a.sw(2,21,12);a.branch(4,3,0,'remember')
    a.addiu(8,0,6);a.sw(8,24);a.addiu(8,0,2);a.branch(5,22,8,'remember_then_try')
    a.li(8,CONTROL);a.lw(8,8,28);a.r(0x2B,8,2,8);a.branch(5,8,0,'remember')
    a.label('remember_then_try');a.lw(8,19);a.sw(8,21,4);a.addiu(8,0,7);a.sw(8,24);a.lw(8,21,8);a.branch(7,8,0,'next')
    # Idle-only. No interruption of attacks, stun, transform/fusion or pending hits.
    a.addiu(8,0,8);a.sw(8,24);a.lw(8,18,2376);a.addiu(9,0,11);a.branch(4,8,9,'idle');a.addiu(9,0,15);a.branch(5,8,9,'next')
    a.label('idle');a.addiu(9,0,-1)
    for off in (2380,2388,2392,2396,2400):a.lw(8,18,off);a.branch(5,8,9,'next')
    for off in (3480,3500,3512):a.lw(8,18,off);a.branch(5,8,0,'next')
    a.addiu(8,0,9);a.sw(8,24);a.move(4,18);a.call(MODEL);a.lw(24,29,0x298);a.branch(4,2,0,'next');a.move(23,2)
    # Positive native costs, plus reviewed zero-cost upward slots, exclude reverts. Best reviewed tier wins,
    # otherwise native stock requirement ranks valid forms; no CID ordering.
    a.sw(3,24,16);a.addiu(8,0,10);a.sw(8,24);a.sw(0,24,20);a.sw(0,24,24);a.sw(0,24,28);a.sw(3,21,16);a.addiu(8,0,-1);a.sw(8,21,20);a.sw(0,21,24);a.move(22,0)
    a.label('form');a.r(0x21,8,23,22);a.i(36,9,8,0x98);a.i(11,10,9,253)
    a.branch(4,10,0,'next_form');a.lw(10,21,16);a.branch(4,9,10,'next_form')
    a.i(36,8,8,0x9C);a.lw(11,24,28);a.addiu(11,11,1);a.sw(11,24,28)
    a.branch(5,8,0,'cost_ok')
    # Zero-cost upward forms are accepted ONLY for reviewed same-family tiers.
    a.li(11,FAMILIES);a.r(0x21,12,11,10);a.i(36,12,12,0);a.r(0x21,11,11,9);a.i(36,11,11,0)
    a.branch(4,12,0,'zero_skip');a.branch(5,12,11,'zero_skip')
    a.li(11,TIERS);a.r(0x21,12,11,10);a.i(36,12,12,0);a.r(0x21,11,11,9);a.i(36,11,11,0)
    a.r(0x2B,11,12,11);a.branch(5,11,0,'cost_ok')
    a.label('zero_skip');a.addiu(8,0,11);a.sw(8,24);a.jump('next_form')
    a.label('cost_ok');a.sw(8,21,28)
    a.lw(11,24,20);a.addiu(12,0,1);a.r(4,12,22,12);a.r(0x25,11,11,12);a.sw(11,24,20)
    # Reviewed same-family forms must strictly increase tier. Unknown remains neutral.
    a.li(11,FAMILIES);a.r(0x21,12,11,10);a.i(36,12,12,0);a.r(0x21,11,11,9);a.i(36,11,11,0)
    a.branch(4,12,0,'rank');a.branch(5,12,11,'rank')
    a.li(11,TIERS);a.r(0x21,12,11,10);a.i(36,12,12,0);a.r(0x21,11,11,9);a.i(36,11,11,0)
    a.r(0x2B,10,12,11);a.branch(4,10,0,'next_form');a.r(0,11,0,11,8)
    a.r(0x21,8,8,11);a.sw(8,21,28)
    a.label('rank');a.lw(9,21,24);a.r(0x2B,9,9,8);a.branch(4,9,0,'next_form')
    a.move(4,18);a.move(5,22);a.addiu(6,0,1);a.addiu(7,0,1);a.call(eligibility);a.lw(24,29,0x298)
    a.branch(5,2,0,'eligible');a.addiu(8,0,12);a.sw(8,24);a.jump('next_form')
    a.label('eligible');a.lw(11,24,24);a.addiu(12,0,1);a.r(4,12,22,12);a.r(0x25,11,11,12);a.sw(11,24,24);a.lw(8,21,28);a.sw(8,21,24);a.sw(22,21,20)
    a.label('next_form');a.addiu(22,22,1);a.i(11,8,22,4);a.branch(5,8,0,'form')
    a.lw(22,21,20);a.branch(1,22,0,'next')
    # Recheck after selection; native hook can veto if resources/policy changed.
    a.move(4,18);a.move(5,22);a.addiu(6,0,1);a.addiu(7,0,1);a.call(eligibility);a.lw(24,29,0x298)
    a.branch(4,2,0,'next');a.addiu(8,0,13);a.sw(8,24);a.move(4,18);a.move(5,22);a.call(initiation);a.lw(24,29,0x298)
    # initiation returns native success; a refused resource transaction must not
    # claim a successful transform or consume the full cooldown.
    a.branch(4,2,0,'next');a.li(8,CONTROL);a.lw(9,8,36);a.addiu(9,9,1);a.sw(9,8,36)
    a.addiu(9,0,14);a.sw(9,24);a.sw(22,24,32);a.lw(9,24,36);a.addiu(9,9,1);a.sw(9,24,36)
    a.lw(9,8,52);a.branch(5,9,0,'enemy_start');a.i(12,9,16,1);a.lw(11,8,24);a.branch(5,9,11,'enemy_start');a.lw(9,8,72);a.addiu(9,9,1);a.sw(9,8,72);a.jump('counted')
    a.label('enemy_start');a.lw(9,8,76);a.addiu(9,9,1);a.sw(9,8,76);a.label('counted')
    a.lw(9,8,40);a.sw(9,21,8);a.sw(16,8,44);a.sw(22,8,48);a.jump('done')
    a.label('remember');a.lw(8,19);a.sw(8,21,4)
    a.label('next');a.addiu(16,16,1);a.branch(5,16,17,'actor')
    a.label('done');a.i(55,8,29,0x288);a.r(17,0,8);a.i(55,8,29,0x290);a.r(19,0,8)
    abi.restore(a);a.jr();return a.finish()


def tables():
    tiers=bytearray([255]*253);families=bytearray(253)
    data=json.loads(Path(__file__).with_name('fusion_form_tiers.json').read_text(encoding='utf-8'))
    names={name:i+1 for i,name in enumerate(sorted({r['family'] for r in data['forms']}))}
    for row in data['forms']:
        tiers[row['character_id']]=row['tier'];families[row['character_id']]=names[row['family']]
    # IDs/labels and forward slots verified in the user's20261008-13 captures.
    for family,forms in enumerate(((3,4,5,6),(34,35,36,20),(44,45),(46,47)),3):
        for tier,cid in enumerate(forms):tiers[cid]=tier;families[cid]=family
    import game_profile
    profile=game_profile.installed()
    if profile and profile.get('runtime_variant')=='BT3 Power Scale BETA 1.5.1 (experimental)':
        for forms in POWER_SCALE_TRIAL_FAMILIES:
            family=max(families)+1
            for tier,cid in enumerate(forms):
                if families[cid]:raise ValueError('Conflicting Power Scale CPU trial family')
                tiers[cid]=tier;families[cid]=family
    # Expanded zero-cost upgrades: review names AND forward slots. Slot order
    # alone cannot distinguish reverts, alternate forms or fusion bodies.
    reviewed=json.loads(Path(__file__).with_name('cpu_transform_form_tiers.json').read_text(encoding='utf-8'))
    used=set();next_family=max(families)+1
    for chain in reviewed['families']:
        if next_family>=256:raise ValueError('Too many reviewed CPU form families')
        for row in chain['forms']:
            cid,tier=row['character_id'],row['tier']
            if type(cid)is not int or not 0<=cid<253 or type(tier)is not int or not 0<=tier<255 or cid in used or families[cid]:
                raise ValueError('Invalid or conflicting reviewed CPU form tier')
            used.add(cid);tiers[cid]=tier;families[cid]=next_family
        next_family+=1
    return bytes(tiers),bytes(families)


@modes.matching_install
def build_memory(ram,settings=None,source='<prepared>',*,battle_mode='teams',ally_side=0):
    options=prefs.validate_settings(settings or {})
    empty=dict(serial=SERIAL,crc=CRC,source=str(source),blocks=[])
    if battle_mode in ('training','training_coop') or not any(options[k]!='native' for k in KEYS[:2]):return empty
    if len(ram)!=0x8000000:raise ValueError('CPU tactics require128MiB RAM')
    u=lambda p:struct.unpack_from('<I',ram,p)[0]
    manager,count=u(core.ACTORS),u(core.MODE+4)
    if count not in modes.ACTOR_COUNTS or (u(core.MODE),u(core.MODE+8),u(core.MODE+12))!=(1,manager,count):
        raise ValueError('CPU tactics require active captured actors')
    if any(ram[FRAME:END]):raise ValueError('CPU tactics reservation occupied')
    previous=(u(start.HOOK)&0x3FFFFFF)<<2
    if u(start.HOOK)>>26!=2 or u(start.HOOK+4) or not (0x07000000<=previous<0x08000000 or 0x06C10000<=previous<0x06C20000 or previous==0x06BB6000) or not any(ram[previous:previous+8]):
        raise ValueError(f'CPU tactics require a verified match frame continuation:{u(start.HOOK):08X}/{u(start.HOOK+4):08X} -> {previous:08X}')
    if (u(part.CONTROL),u(part.CONTROL+4),u(part.CONTROL+8))!=(5,manager,count):
        # Fresh preparation holds participation inactive until the start gate.
        if (u(part.CONTROL),u(part.CONTROL+4),u(part.CONTROL+8))!=(0,manager,count):raise ValueError('Participation lease mismatch')
    import ordinary_form_admission as forms
    from prototype import ROOT,elf_reader
    from native_map import elf_path
    import npc_transform_policy as npc
    native=elf_reader(elf_path(ROOT))[2]
    expected=dict((p,d) for p,_,d in forms.wrapper_parts(native))
    for (entry,cave,_),base in zip(npc.ordinary.ENTRIES,npc.WRAPPERS):
        valid=[npc.jump(cave),npc.jump(base)]
        if ram[entry:entry+8] not in valid:raise ValueError('Ordinary transform entry changed')
        if ram[cave:cave+len(expected[cave])]!=expected[cave]:raise ValueError('Ordinary transform admission changed')
        if ram[entry:entry+8]==npc.jump(base):
            for at,body in npc.pieces():
                if ram[at:at+len(body)]!=body:raise ValueError('NPC transformation policy changed')
    data=bytearray(256);preset=('native','aggressive','relentless').index(options[KEYS[2]])
    scope=lambda key:('native','more_often','outmatched').index(options[key])
    struct.pack_into('<13I',data,0,MAGIC,manager,count,scope(KEYS[0]),scope(KEYS[1]),1,ally_side,
                     (3,2,1)[preset],0,0,(24,15,9)[preset],0xFFFFFFFF,0xFFFFFFFF)
    eligibility=(u(A(0x2033C8))&0x3FFFFFF)<<2
    initiation=(u(A(0x203610))&0x3FFFFFF)<<2
    struct.pack_into('<4I',data,52,int(battle_mode=='ffa'),previous,eligibility,initiation)
    rows=bytearray(modes.ENGINE_ACTORS*32)
    for i in range(count):
        actor=u(core.POINTERS+4*i)
        if not 0x100000<=actor<len(ram)-0x1600 or u(actor)!=i:raise ValueError('CPU tactics actor identity mismatch')
        slot=u(actor+0x994)
        if slot>=5:raise ValueError('CPU tactics invalid HP row')
        struct.pack_into('<2I',rows,i*32,actor,u(actor+0x9E4+164*slot))
    tiers,families=tables()
    pieces=[(FRAME,frame_code(previous)),(APPLY,apply_code(battle_mode=='ffa',eligibility,initiation)),(MODEL,model_code()),(SCORE,score_code()),
            (CONTROL,bytes(data)),(ROWS,bytes(rows)),(TIERS,tiers),(FAMILIES,families),(DIAGNOSTICS,bytes(modes.ENGINE_ACTORS*DIAG_STRIDE)),
            (start.HOOK,struct.pack('<2I',(2<<26)|(FRAME>>2),0))]
    spans=sorted((p,p+len(d)) for p,d in pieces)
    if any(end>lo for (_,end),(lo,_) in zip(spans,spans[1:])):raise ValueError('CPU tactics code overlaps')
    return dict(serial=SERIAL,crc=CRC,source=str(source),control=CONTROL,previous=previous,settings={k:options[k] for k in KEYS},
                blocks=[dict(address=p,expected_hex=ram[p:p+len(d)].hex(),data_hex=d.hex()) for p,d in pieces],
                telemetry=dict(evaluations=CONTROL+32,starts=CONTROL+36,last_actor=CONTROL+44,last_slot=CONTROL+48))


def dependency_override(ram,address,expected):
    """Peel only the exact authenticated optional wrapper in existing validators."""
    u=lambda at:struct.unpack_from('<I',ram,at)[0]
    if address!=start.HOOK or u(CONTROL)!=MAGIC:return expected
    previous=u(CONTROL+56)
    if expected!=struct.pack('<2I',(2<<26)|(previous>>2),0):return expected
    if (u(CONTROL+4),u(CONTROL+8))!=(u(core.ACTORS),u(core.MODE+4)):
        raise ValueError('CPU tactics dependency belongs to another match')
    actual=struct.pack('<2I',(2<<26)|(FRAME>>2),0)
    for at,data in ((FRAME,frame_code(previous)),(APPLY,apply_code(bool(u(CONTROL+52)),u(CONTROL+60),u(CONTROL+64))),
                    (MODEL,model_code()),(SCORE,score_code()),(address,actual)):
        if ram[at:at+len(data)]!=data:raise ValueError(f'CPU tactics executable changed:{at:08X}')
    return actual
