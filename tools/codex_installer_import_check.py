"""Use the installed embedded app to import a real disc without starting Play."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys

app_dir=Path(sys.argv[1]).resolve()
source=Path(sys.argv[2]).resolve()
data=Path(sys.argv[3]).resolve()
if '--stored-root' in sys.argv:os.environ.pop('BT3_TAGTEAM_DATA',None)
else:os.environ['BT3_TAGTEAM_DATA']=str(data)
loader=importlib.machinery.SourceFileLoader('installed_app',str(app_dir/'app.pyw'))
spec=importlib.util.spec_from_loader(loader.name,loader)
app=importlib.util.module_from_spec(spec)
loader.exec_module(app)
assert app.DATA.resolve()==data
app.initialize()
assert not app.imported(), 'Fresh profile required'
last=[None]
def progress(percent,label):
    if percent!=last[0]:print(percent,label,flush=True);last[0]=percent
app.import_disc(source,progress)
assert app.imported()
sys.path[:0]=[str(app.HERE),str(app.HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import fresh_team_combat
assert fresh_team_combat.program()
receipt=json.loads((data/'import/import-receipt.json').read_text(encoding='utf-8'))
print('PASS installed original/expanded import, full receipt/art verification and actual fresh combat code generation',flush=True)
print(json.dumps({'original':receipt['original_disc_sha256'],'expanded':receipt['prepared_disc_sha256'],'game_launched':False}),flush=True)
