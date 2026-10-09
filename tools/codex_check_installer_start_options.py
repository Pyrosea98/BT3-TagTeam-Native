"""Exercise actual app save-seeding entry point without imports or gameplay."""
import hashlib,json,os,runpy,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
APP=HERE/'installer'
with tempfile.TemporaryDirectory(prefix='bt3-save-choice-') as temporary:
    root=Path(temporary);old=os.environ.get('BT3_TAGTEAM_DATA');os.environ['BT3_TAGTEAM_DATA']=str(root/'data')
    try:app=runpy.run_path(str(APP/'app.pyw'),run_name='installer_save_test')
    finally:
        if old is None:os.environ.pop('BT3_TAGTEAM_DATA',None)
        else:os.environ['BT3_TAGTEAM_DATA']=old
    seed=app['seed_progression'];scope=seed.__globals__;scope['APP']=root
    unlocked=(HERE/'savedata/BASLUS-21678DBZT3/BASLUS-21678DBZT3').read_bytes()
    fresh=(HERE/'power-scale-trial/save-backups/20261005-104334/BASLUS-21678DBZT3/BASLUS-21678DBZT3').read_bytes()
    assert len(fresh)==16384 and fresh!=unlocked
    (root/'default-save.bin').write_bytes(unlocked);(root/'fresh-save.bin').write_bytes(fresh)
    (root/'save-card').mkdir()
    for name in ('icon.sys','dbzsm.ico'):(root/'save-card'/name).write_bytes((HERE/'savedata/BASLUS-21678DBZT3'/name).read_bytes())
    for choice in (True,False):
        data=root/('unlocked' if choice else 'fresh');data.mkdir();scope['DATA']=data
        (data/'save-start-choice.json').write_text(json.dumps({'schema':1,'all_unlocked':choice}))
        seed();save=data/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
        assert save.read_bytes()==(unlocked if choice else fresh)
        save.write_bytes(b'existing player progress');seed();assert save.read_bytes()==b'existing player progress'
    data=root/'legacy';data.mkdir();scope['DATA']=data;seed()
    assert json.loads((data/'save-start-choice.json').read_text())['all_unlocked'] is True
for name in ('initial.iss','preview-current.iss'):
    source=(APP/name).read_text(encoding='utf-8')
    for task in ('desktopicon','startmenuicon'):
        task_line=next(line for line in source.splitlines() if line.startswith(f'Name: "{task}";'))
        assert 'unchecked' not in task_line
        assert f'Tasks: {task}' in source
    assert 'english.SaveChoice=' in source and 'spanish.SaveChoice=' in source
    assert "if not FileExists(ResolvedDataRoot+'\\save-start-choice.json')" in source
    assert 'SetupIconFile=assets\\BT3TagTeam.ico' in source
print('PASS: both seeds, existing saves, legacy default, task wiring/defaults, EN/ES, icon setup.')
print('Fresh seed bytes:',len(fresh),'SHA256:',hashlib.sha256(fresh).hexdigest())
