"""Check final patch composition against a retained native preparation image."""
from pathlib import Path
import json,sys,struct
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
import fresh_team_trainer as trainer, fresh_team_ai as ai
import fusion_partner_lifecycle as fusion
from relocate_power_scale import CONTROL
run=HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261005-115724-a9f8162c'
path=run/'current-ee.bin';ram=path.read_bytes()
base=struct.unpack_from('<I',ram,CONTROL+4)[0]
fusion.POWER_SCALE_SIDE_TARGET=base+0x2264
installation=json.loads((run/'ai-installation.json').read_text())
support=json.loads((run/'support.json').read_text())
session=json.loads((run/'session.json').read_text())
selection=json.loads((run/'selection.json').read_text())
activation=ai.build_activation(path,installation,support)
manifest=trainer.final_team_manifest(ram,activation,path,play_intro=True,
    pause_mode=session['settings']['special_pause_mode'],present_mask=selection['participation_mask'],
    settings=session['settings'],battle_mode='teams',humans=1)
print(f"Final patch composition passed: {len(manifest['blocks'])} guarded blocks")
