"""Dedicated graphics discovery runner. Arm capture via its trigger file."""
import os
import sys
from pathlib import Path

if __name__=='__main__':
    import run_power_scale_native as launch
    name='ps2EntryRunner-native-hud-rearm.exe'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster'))
    if '--runner' in sys.argv: raise ValueError('HUD diagnostic uses its dedicated runner')
    capture=Path(__file__).resolve().parent/'power-scale-trial/hud-native-capture'
    capture.mkdir(exist_ok=True)
    trigger=capture/'capture.trigger'
    if (capture/'textures.jsonl').exists() or (capture/'draws.jsonl').exists() or any(capture.glob('capture-*')):
        raise RuntimeError('Archive the previous hud-native-capture directory before launching again.')
    if trigger.exists(): raise RuntimeError('Remove previous capture.trigger before launching; archive previous output first.')
    os.environ['PS2X_DUMP_TEX']=str(capture)
    os.environ['PS2X_DRAW_TRACE']='1'
    os.environ['PS2X_GS_DIAG_TRIGGER']=str(trigger)
    sys.argv.extend(('--runner',name))
    raise SystemExit(launch.main())
