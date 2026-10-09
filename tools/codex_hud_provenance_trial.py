"""Development HUD upload provenance trial; one controller-free game."""
import os
import sys
from pathlib import Path
if __name__=='__main__':
    import run_power_scale_native as launch
    name='ps2EntryRunner-native-hud-provenance.exe'
    launch.RUNNER_FEATURES[name]=frozenset(('rematch','roster'))
    if '--runner' in sys.argv: raise ValueError('Provenance trial uses its dedicated runner')
    root=Path(__file__).resolve().parent/'power-scale-trial'
    uploads=root/'hud-upload-capture'
    capture=root/'hud-native-capture'
    if (uploads/'uploads.jsonl').exists() or any(capture.glob('capture-*')) or (capture/'capture.trigger').exists():
        raise RuntimeError('Archive previous upload and HUD capture outputs before launching.')
    capture.mkdir(exist_ok=True)
    os.environ['PS2X_HUD_UPLOAD_TRACE']=str(uploads)
    os.environ['PS2X_KICKPROBE']='2' # existing light builder attribution, no GIF census
    os.environ['PS2X_DRAW_TRACE']='1'
    os.environ['PS2X_DUMP_TEX']=str(capture)
    os.environ['PS2X_GS_DIAG_TRIGGER']=str(capture/'capture.trigger')
    os.environ['PS2X_NATIVE_REMATCH']='0'
    os.environ['PS2X_POWER_SCALE_ROSTER']='0'
    sys.argv.extend(('--runner',name,'--no-controller'))
    raise SystemExit(launch.main())
