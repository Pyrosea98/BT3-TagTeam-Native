"""Reviewed effects-arena refusals, shared by CPU and ordinary extra input."""
import json
import os
from pathlib import Path

TABLE=Path(__file__).with_name('extra_form_effect_sizes.json')


def blocked_destinations():
    import game_profile
    profile=game_profile.installed()
    table=json.loads(TABLE.read_text(encoding='utf-8'))
    if not profile or profile.get('runtime_variant')!=table['runtime_variant']:return ()
    if os.environ.get('BT3_CPU72_DIAGNOSTIC')=='1' and os.environ.get('BT3_FORM_AUDIT_DIR'):return ()
    # The reload resets the arena before rebuilding; old usage is not additive.
    return tuple(row['cid'] for row in table['destinations']
                 if row['required_bytes']>table['arena_capacity'])


def admission_guard(a,rejected,fallback):
    """a0 matched extra actor, a1 ordinary slot. Scratch t0..t2 only."""
    denied=blocked_destinations()
    if not denied:return
    import fresh_team_combat as core
    a.i(11,8,5,4);a.branch(4,8,0,fallback)
    a.lw(8,4,12);a.i(11,9,8,12);a.branch(4,9,0,fallback)
    a.r(0,8,0,8,2);a.li(9,core.MODELS);a.r(0x21,9,9,8);a.lw(8,9)
    for register,extent in ((8,0x1670),(8,0xB0)):
        a.li(9,0x100000);a.r(0x2B,9,register,9);a.branch(5,9,0,fallback)
        a.li(9,0x08000000-extent);a.r(0x2B,9,9,register);a.branch(5,9,0,fallback)
        a.i(12,9,register,3);a.branch(5,9,0,fallback)
        if extent==0x1670:a.lw(8,8,0x91C)
    a.r(0x21,8,8,5);a.i(36,8,8,0x98)
    for cid in denied:
        a.addiu(9,0,cid);a.branch(4,8,9,rejected)
