"""Replay two actual consecutive co-op captures without a live game."""
from pathlib import Path
import json
import struct
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import codex_native_rematch_rebuild as rebuild
import quad_controller as pads
import four_player_mode as quad
import fresh_team_trainer as trainer
import fresh_team_ai as ai
import fusion_partner_lifecycle
# Match the verified native MOD.BIN relocation used by the launcher.
fusion_partner_lifecycle.POWER_SCALE_SIDE_TARGET=0x008CA9C0+0x2264

root=HERE/'power-scale-trial/controller/game/analysis/prepared-states'
first=root/'20261007-225441-552469c1'
second=root/'20261007-225755-5d445eec'
baseline=(first/'00-original-selected-match.bin').read_bytes()
ready=(first/'16-ready-held.bin').read_bytes()
assert quad.installed(ready)
assert not any(baseline[pads.BASE:pads.END])
class Client:
    def __init__(self,ram):self.ram=bytearray(ram)
    def read(self,at,n):return bytes(self.ram[at:at+n])
    def write(self,at,data):self.ram[at:at+len(data)]=data
p=Client(ready)
writes,receipt=rebuild.cave_restore_plan(p,baseline)
for at,data in writes:p.write(at,data)
rebuild.verify_caves(p,baseline)
assert not any(p.ram[pads.BASE:pads.END])
assert not quad.installed(p.ram)
for lo,hi,_ in rebuild.CAVE_LIVE:assert p.ram[lo:hi]==ready[lo:hi]
print('PASS: production cave cleanup removes old quad owner/code/mailbox/pads; all live selector/UI services retained')
del p,ready
ram=bytearray((second/'current-ee.bin').read_bytes())
try:quad.installed(ram)
except ValueError as error:assert 'another capture' in str(error)
else:raise AssertionError('Archived second-match failure not reproduced')
ram[pads.BASE:pads.END]=baseline[pads.BASE:pads.END]
assert not quad.installed(ram)
session=json.loads((second/'session.json').read_text(encoding='utf-8'))
selection=json.loads((second/'selection.json').read_text(encoding='utf-8'))
installation=json.loads((second/'ai-installation.json').read_text(encoding='utf-8'))
support=json.loads((second/'support.json').read_text(encoding='utf-8'))
cpu_check='--cpu-tactics' in sys.argv
if cpu_check:
    session['settings'].update(cpu_transform_allies='more_often',cpu_transform_enemies='outmatched',cpu_tactics_preset='aggressive',disable_npc_giant_transformations=True)
form_check='--fusion-form' in sys.argv
if form_check:
    session['settings'].update(fusion_duration_enabled=True,fusion_time_by_form=True,fusion_form_penalty='normal')
with tempfile.TemporaryDirectory(prefix='quad-replay-',dir=HERE/'power-scale-trial') as temp:
    path=Path(temp)/'ai-ready.bin';path.write_bytes(ram)
    activation=ai.build_activation(path,installation,support)
    manifest=trainer.final_team_manifest(ram,activation,second/'00-original-selected-match.bin',
        settings=session['settings'],battle_mode='teams',humans=2,assignment=(0,2),
        present_mask=selection['participation_mask'],play_intro=True)
    for block in manifest['blocks']:
        at=block['address'];data=bytes.fromhex(block['data_hex'])
        ram[at:at+len(data)]=data
    assert quad.installed(ram)
    import os
    if os.environ.get('PS2X_NATIVE_UI_SLICE') is not None:
        import guest_killfeed,display_settings
        quiet=struct.pack('<2I',0x03E00008,0)
        assert ram[guest_killfeed.DRAW:guest_killfeed.DRAW+8]==struct.pack('<2I',(2<<26)|(display_settings.FEED_FILTER>>2),0)
        assert ram[display_settings.FEED_DRAW:display_settings.FEED_DRAW+8]==quiet
        print('PASS production native preparation disables BOTH original and relocated kill-feed glyph emitters; recording retained')
    if cpu_check:
        import cpu_tactics as tactics
        assert struct.unpack_from('<I',ram,tactics.CONTROL)[0]==tactics.MAGIC
        assert struct.unpack_from('<2I',ram,tactics.CONTROL+12)==(1,2)
        assert struct.unpack_from('<I',ram,tactics.CONTROL+28)[0]==2
        assert struct.unpack_from('<I',ram,tactics.CONTROL+40)[0]==15
        import four_player_mode,team_start_gate
        tactics_manifest_previous=struct.unpack_from('<I',ram,tactics.CONTROL+56)[0]
        assert four_player_mode.dependency_override(ram,team_start_gate.HOOK,struct.pack('<2I',(2<<26)|(tactics_manifest_previous>>2),0))==struct.pack('<2I',(2<<26)|(tactics.FRAME>>2),0)
        corrupted=ram[tactics.APPLY];ram[tactics.APPLY]^=1
        try:four_player_mode.dependency_override(ram,team_start_gate.HOOK,struct.pack('<2I',(2<<26)|(tactics_manifest_previous>>2),0))
        except ValueError:pass
        else:raise AssertionError('Changed CPU planner accepted by dependency validator')
        ram[tactics.APPLY]=corrupted
        print('PASS actual final preparation installs CPU scopes/preset after quad and NPC giant policy; full-code dependency accepts exact planner and rejects corruption')
    if form_check:
        import fusion_duration as timer
        timer.validate_memory(ram)
        assert timer.u32(ram,timer.CONTROL+52)==1 and timer.u32(ram,timer.CONTROL+56)==1
        timer.build_memory(ram,session['settings']['fusion_duration_seconds'],session['settings']['show_fusion_timer'],
                           animate=session['settings']['fusion_defusion_animation'],by_form=True,penalty='normal')
        try:timer.build_memory(ram,by_form=True,penalty='heavy')
        except ValueError:pass
        else:raise AssertionError('Changed form options accepted in existing match')
        print('PASS current final preparation installs form settings and authenticates current timer/quad code; existing-match changes rejected')
    print('PASS: archived second-match final preparation now generates a fresh two-human quad owner; blocks='+str(len(manifest['blocks'])))
    # New fusion selectors/diagnostics must be reclaimed on clean rematch.
    import power_scale_fusion_recipes as recipes, cpu_fusion_choice as choices, fusion_input_trace as trace
    (Path(temp)/'00-original-selected-match.bin').write_bytes((second/'00-original-selected-match.bin').read_bytes())
    path.write_bytes(ram)
    (Path(temp)/'final.json').write_text(json.dumps(manifest))
    clean,prepared,spans=rebuild.ownership_plan(path,strict=False)
    for module in (recipes,choices,trace):
        assert any(a<=module.BASE and end>=module.END for a,end,_ in spans) or all(
            any(a<=block['address'] and block['address']+len(bytes.fromhex(block['data_hex']))<=end
                for a,end,_ in spans)
            for block in manifest['blocks'] if module.BASE<=block['address']<module.END)
    for hook in (*(entry[0] for entry in recipes.HOOKS),choices.HOOK,trace.HOOK,*trace.GATE_HOOKS):
        assert any(a<=hook<hook+4<=end and code for a,end,code in spans),hex(hook)
    p=Client(prepared)
    # Simulate spent per-match cursor and trace rows, then use production cleanup.
    p.write(choices.ROWS,b'\xff'*80);p.write(trace.ROWS,b'\xff'*(10*trace.STRIDE))
    writes,_=rebuild.cave_restore_plan(p,clean)
    for at,data in writes:p.write(at,data)
    rebuild.verify_caves(p,clean)
    for module in (recipes,choices,trace):assert p.read(module.BASE,module.END-module.BASE)==clean[module.BASE:module.END]
    print('PASS new fusion hooks are owned executable ranges; production rematch cleanup removes recipe code, choice cursors and trace state')
