"""Check the installed embedded app without launching a game or changing a save."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

app = Path(sys.argv[1]).resolve()
data = Path(sys.argv[2]).resolve()
env = dict(os.environ, BT3_TAGTEAM_DATA=str(data), PATH=os.environ['SystemRoot']+'\\System32')
env.pop('PYTHONPATH', None)
env.pop('VIRTUAL_ENV', None)
save = data/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
before = hashlib.sha256(save.read_bytes()).hexdigest() if save.exists() else None
run = subprocess.run([str(app/'runtime/python.exe'), '-I', str(app/'app.pyw'), '--check-runtime'], env=env, capture_output=True, text=True, timeout=90)
if run.returncode:
    raise RuntimeError('Installed runtime check failed.')
dependencies = json.loads((data/'runtime-check.json').read_text(encoding='utf-8'))
assert not dependencies['missing'], 'Missing embedded dependencies'
after = hashlib.sha256(save.read_bytes()).hexdigest()
expected = before or hashlib.sha256((app/'default-save.bin').read_bytes()).hexdigest()
assert after == expected, 'Starting save was not seeded/preserved'
result = {'runtime': 'PASS', 'modules': dependencies['controller_modules'], 'save': 'preserved' if before else 'seeded', 'save_sha256': after, 'game_launched': False}
(data/'package-check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
