"""Check v11 settings and native input construction without a game or SDL."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
os.environ.update(PS2X_NATIVE_UI_SLICE='1',PS2X_NATIVE_SEAT_PADS='1')
if '--roster' in sys.argv:
    from codex_roster_overlay import install
    install()
import mod_settings,controller_hub,autopilot,quad_menu_input
values=mod_settings.validate_settings({})
fields=mod_settings.ui_fields()
assert set(fields)<=set(values),set(fields)-set(values)
assert values['fusion_enabled'] is True
assert values['tournament_ring_outs'] is False
import lockon_select,lockon_threat
assert not lockon_select.wanted(values) and not lockon_threat.wanted(values)
assert values['ground_running'] is False and values['beam_assist_enabled'] is False
with patch.object(controller_hub,'Hub',side_effect=AssertionError('Native input must not create an SDL hub')):
    watcher=autopilot.Autopilot(lifetime=SimpleNamespace(process=SimpleNamespace(pid=42)),menu_checkpoint=False)
assert watcher.controller_hub is None
assert isinstance(watcher.menu_input,quad_menu_input.Owner)
assert watcher.assigned_input.order is None
watcher.assigned_input.assign(None)
client=SimpleNamespace(write_u32=lambda address,value:None)
watcher.assigned_input.attach(client,('battle','fixture'),allow_arm=True,in_match=True,rewound=True)
assert watcher.assigned_input.service is None
if '--roster' in sys.argv:
    import character_names
    assert len(character_names.character_table())==253
print('PASS: v11 settings resolve, unverified features default off, native owners bypass SDL, roster labels retained')
