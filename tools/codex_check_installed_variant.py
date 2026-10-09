"""Replay the installed-profile regression against real preparation captures."""
import json
import runpy
import sys
import tempfile
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
import game_profile
original=game_profile.ROOT
if '--child' not in sys.argv:
    for option in ([],['--cpu-tactics']):
        subprocess.run([sys.executable,__file__,'--child',*option],check=True)
    raise SystemExit(0)
record=json.loads((original/'game-profile.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='installed-variant-',dir=HERE/'power-scale-trial') as temp:
    game_profile.ROOT=Path(temp)
    path=game_profile.ROOT/'game-profile.json'
    legacy=dict(record)
    legacy.pop('runtime_variant',None)
    path.write_text(json.dumps(legacy),encoding='utf-8')
    assert game_profile.installed()['runtime_variant']==game_profile.POWER_SCALE_VARIANT
    assert 'runtime_variant' not in json.loads(path.read_text())
    option=['--cpu-tactics'] if '--cpu-tactics' in sys.argv else []
    sys.argv=[str(HERE/'codex_check_quad_rematch_cleanup.py'),*option]
    runpy.run_path(sys.argv[0],run_name='__main__')
    print('PASS legacy installed profile: '+('CPU planner enabled' if option else 'native CPU settings'))
    unknown=dict(legacy,iso_sha256='0'*64)
    path.write_text(json.dumps(unknown),encoding='utf-8')
    assert 'runtime_variant' not in game_profile.installed()
    import fusion_partner_lifecycle
    assert not fusion_partner_lifecycle.power_scale_side_call()
    print('PASS unknown disc remains unrecognized; runtime opcode guards unchanged')
game_profile.ROOT=original
