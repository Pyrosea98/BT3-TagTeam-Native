"""Emit a Q16 life clock; no frame-time host polling or resource changes."""
import json
from pathlib import Path

UNIT = 65536
MAGIC = 0x464F5231
PRESETS = ('mild', 'normal', 'heavy')
PENALTIES = ((0,5,10,15,20,25), (0,10,20,30,40,50), (0,20,35,50,60,70))

def load_tiers():
    data=json.loads(Path(__file__).with_name('fusion_form_tiers.json').read_text(encoding='utf-8'))
    if data.get('schema')!=1:raise ValueError('Unsupported fusion form table')
    result={}
    for row in data['forms']:
        cid,tier=row['character_id'],row['tier']
        if type(cid)is not int or not 0<=cid<=252 or type(tier)is not int or not 0<=tier<=5 or cid in result:
            raise ValueError('Invalid or duplicate fusion form tier')
        result[cid]=tier
    return result

TIERS=load_tiers()  # Match code stays stable; editing this file requires restart.

def rate(tier,preset='normal'):
    penalty=PENALTIES[PRESETS.index(preset)][tier]
    denominator=100-penalty
    return (100*UNIT+denominator//2)//denominator

def emit(a,legacy,expired,next_row):
    """s0 receipt, s2 actor, s5 current character. s6 rate, s7 life.

    Only a receipt authenticated as native Fusion Dance participates.
    Ordinary timed Potara retains its existing behavior when lore is enabled.
    """
    import fusion_duration as timer
    from native_map import ACTOR_HZ
    a.li(8,timer.CONTROL);a.lw(9,8,52);a.branch(4,9,0,legacy)
    a.lw(9,16,104);a.addiu(10,0,241);a.branch(5,9,10,legacy)
    # Never expire or consume time in an actor's transform animation, even
    # when the shared scene policy does not own that particular cinematic.
    a.lw(9,18,2376);a.addiu(9,9,-236);a.i(11,10,9,8);a.branch(5,10,0,next_row)
    a.li(22,UNIT);a.lw(20,8,56)
    for cid,tier in sorted(TIERS.items()):
        if not tier:continue
        a.addiu(9,0,cid);a.branch(4,21,9,f'form_tier_{tier}')
    a.jump('form_rate_ready')
    for tier in range(1,6):
        a.label(f'form_tier_{tier}')
        for index,preset in enumerate(PRESETS[:-1]):
            a.addiu(9,0,index);a.branch(4,20,9,f'form_rate_{tier}_{index}')
        a.li(22,rate(tier,'heavy'));a.jump('form_rate_ready')
        for index,preset in enumerate(PRESETS[:-1]):
            a.label(f'form_rate_{tier}_{index}');a.li(22,rate(tier,preset));a.jump('form_rate_ready')
    a.label('form_rate_ready');a.sw(22,16,116)
    a.lw(9,16,124);a.li(10,MAGIC);a.branch(4,9,10,'form_initialized')
    a.lw(23,16,4);a.r(0,23,0,23,16);a.sw(23,16,108);a.sw(21,16,112);a.sw(10,16,124)
    a.label('form_initialized');a.lw(23,16,108);a.lw(9,16,112)
    a.branch(4,21,9,'form_drain');a.i(11,9,21,253);a.branch(4,9,0,'form_drain')
    a.sw(21,16,112)
    # One full combat second at the NEW rate, including Blue and Heavy.
    # Skip drain on the completion boundary so the player receives all HZ
    # subsequent updates. This is the sole minimum-grace exception to no refund.
    a.li(9,ACTOR_HZ);a.sw(9,16,120);a.r(24,0,22,9);a.r(18,10,0)
    # T can be only one second. Keep life <= its original budget and use
    # the separate combat grace counter if that budget drains sooner.
    a.lw(8,16,100);a.r(0,8,0,8,16);a.r(0x2B,9,8,10)
    a.branch(4,9,0,'form_floor_ready');a.move(10,8);a.label('form_floor_ready')
    a.r(0x2B,9,23,10);a.branch(4,9,0,'form_publish');a.move(23,10);a.jump('form_publish')
    a.label('form_drain');a.lw(9,16,120);a.branch(4,9,0,'form_grace_done');a.addiu(9,9,-1);a.sw(9,16,120)
    a.label('form_grace_done');a.r(0x2B,9,22,23);a.branch(4,9,0,'form_zero')
    a.r(0x23,23,23,22);a.jump('form_publish')
    a.label('form_zero');a.move(23,0)
    a.label('form_publish');a.sw(23,16,108);a.li(9,UNIT-1);a.r(0x21,8,23,9);a.r(2,8,0,8,16);a.sw(8,16,4)
    a.branch(5,23,0,next_row);a.lw(9,16,120);a.branch(5,9,0,next_row);a.jump(expired)
