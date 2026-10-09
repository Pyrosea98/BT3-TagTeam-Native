"""Prepare an isolated copy of the installed Python controller for native PINE."""
from pathlib import Path
import csv,json,shutil,sys

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'experiments/.full-install/game'
GAME=HERE/'power-scale-trial/controller/game'
TOOLS=GAME/'tools'
TOOLS.mkdir(parents=True,exist_ok=True)
for p in (SOURCE/'tools').iterdir():
    if p.is_file() and p.suffix in ('.py','.json'):shutil.copy2(p,TOOLS/p.name)
fusion=TOOLS/'fusion_partner_lifecycle.py'
text=fusion.read_text()
text='POWER_SCALE_SIDE_TARGET=0x008C8C24\n'+text
text=text.replace('native_target=0x008C8C24','native_target=POWER_SCALE_SIDE_TARGET')
text=text.replace("struct.pack('<I',0x0C232309)","struct.pack('<I',(3<<26)|(POWER_SCALE_SIDE_TARGET>>2))")
fusion.write_text(text)
trainer=TOOLS/'fresh_team_trainer.py'
text=trainer.read_text().replace("self.wait_word(ai.CONTROL, 5, 'Initializing individual NPCs...')",
    "self.wait_word(ai.CONTROL, 5, 'Initializing individual NPCs...')\n        self.wait_idle_leaders()")
text=text.replace("if label!='ready-held':","if label!='ready-held' or getattr(self,'native_runtime',False):")
text=text.replace("if label=='ready-held':","if label=='ready-held' and not getattr(self,'native_runtime',False):")
text=text.replace("or label=='original-selected-match'","or label=='original-selected-match' or (label=='ready-held' and getattr(self,'native_runtime',False))")
text=text.replace("        manifest = dict(serial=SERIAL, crc=CRC, blocks=[dict(\n            address=request, expected_hex='00000000', data_hex='01000000')])",
    "        if getattr(self,'native_runtime',False):\n            write_json(self.run/'native-ready.json',dict(ready=True,ram=str(self.source),rematch_checkpoint=False))\n            return\n        manifest = dict(serial=SERIAL, crc=CRC, blocks=[dict(\n            address=request, expected_hex='00000000', data_hex='01000000')])")
trainer.write_text(text)
for name in ('extra_reload_forms.py','extra_reload_worker.py','extra_reload_preload.py'):
    path=TOOLS/name;text=path.read_text()
    text=text.replace('power_call=0x0C232309','from fusion_partner_lifecycle import POWER_SCALE_SIDE_TARGET\n        power_call=(3<<26)|(POWER_SCALE_SIDE_TARGET>>2)')
    text=text.replace('side_target=0x008C8C24 if power_scale','from fusion_partner_lifecycle import POWER_SCALE_SIDE_TARGET\n            side_target=POWER_SCALE_SIDE_TARGET if power_scale')
    text=text.replace('    import game_profile\n','    import game_profile\n    from fusion_partner_lifecycle import POWER_SCALE_SIDE_TARGET\n    power_io=POWER_SCALE_SIDE_TARGET+(0x008C9398-0x008C8C24)\n') if name=='extra_reload_preload.py' else text
    text=text.replace('0x082324E6, 0','(2<<26)|(power_io>>2), 0').replace('ram[0x8C9398:0x8C93A8]','ram[power_io:power_io+16]')
    path.write_text(text)
contact=TOOLS/'multi_contact.py';text=contact.read_text()
text=text.replace('from battle_mode_policy import ACTOR_COUNTS','from battle_mode_policy import ACTOR_COUNTS\nfrom native_contact_probe import emit as contact_probe')
text=text.replace("a.label(f'n_{p:x}');word=struct.unpack('<I',NATIVE(p,4))[0];op=word>>26",
    "a.label(f'n_{p:x}');word=struct.unpack('<I',NATIVE(p,4))[0];op=word>>26\n        if p==A(0x1B0104):contact_probe(a,1,17,preserve=True)")
text=text.replace("a.label('all');actor(a,19,18);a.move(4,16);a.move(5,19);a.call(VALID)",
    "a.label('all');actor(a,19,18);a.move(4,16);a.move(5,19);a.call(VALID)\n    contact_probe(a,0,18)")
contact.write_text(text)
for name in ('mod-settings.json','mod-settings-defaults.json','Tag Team Mod Logo.png'):
    shutil.copy2(SOURCE/name,GAME/name)
profile=json.loads((SOURCE/'game-profile.json').read_text())
profile['iso']=str(SOURCE/'maps/expanded-2x.iso')
(GAME/'game-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
(GAME/'analysis').mkdir(exist_ok=True)
for asset in (SOURCE/'analysis').iterdir():
    if asset.is_file() and asset.suffix in ('.json','.bin'):
        shutil.copy2(asset,GAME/'analysis'/asset.name)
shutil.copytree(SOURCE/'assets',GAME/'assets',dirs_exist_ok=True)
shutil.copy2(HERE/'power-scale-input/SLUS_216.78',GAME/'analysis/SLUS_216.78')
# Index the functions that a live MIPS patch must supersede in compiled code.
rows=[]
for path in (HERE/'repo/games/bt3/work/functions_split.csv',HERE/'repo/games/bt3/dbzp_funcs.csv',HERE/'repo/games/bt3/dbzp_gaps.csv',HERE/'repo/games/bt3/dbzp_missing.csv'):
    for row in csv.DictReader(path.open()):
        row={k.lower():v for k,v in row.items()}
        start=int(row['start'],0);end=int(row['end'],0)
        if 0<start<end<=0x400000:rows.append((start,end))
(HERE/'repo/ps2xRuntime/src/lib/tagteam_ranges.inc').write_text(''.join(f'{{0x{a:x}u,0x{b:x}u}},\n' for a,b in sorted(set(rows))))
sys.path.insert(0,str(TOOLS))
import guest_loading_screen
boot=HERE/'power-scale-trial/tagteam-bootstrap.pnach'
boot.write_bytes(guest_loading_screen.pnach())
print(f'Copied controller to {GAME}; indexed {len(rows)} functions; bootstrap {boot.stat().st_size} bytes')
