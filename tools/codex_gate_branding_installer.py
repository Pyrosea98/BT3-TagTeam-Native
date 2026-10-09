"""Isolated installer identity, shortcuts and D: data; never launches Play."""
from pathlib import Path
import ctypes,hashlib,json,os,shutil,subprocess,time
HERE=Path(__file__).resolve().parent
BASE=HERE/'installer'
setup=BASE/'output/BT3-Branding-Options-Gate.exe'
work=Path('D:/BT3TagTeam-branding-gate-'+time.strftime('%Y%m%d-%H%M%S')).resolve()
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-branding-gate-') and not work.exists()
app=work/'app';data=app/'data'
env=dict(os.environ);env.pop('BT3_TAGTEAM_DATA',None)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def special(folder):
    buffer=ctypes.create_unicode_buffer(32768)
    assert ctypes.windll.shell32.SHGetFolderPathW(None,folder,None,0,buffer)==0
    return Path(buffer.value)
shortcuts=[special(0x10)/'BT3 Codex Branding Gate.lnk',special(2)/'BT3 Codex Branding Gate/BT3 Codex Branding Gate.lnk']
assert not any(p.exists() for p in shortcuts)
def run(args):subprocess.run(list(map(str,args)),env=env,check=True,timeout=600)
def install(label,unlocked,tasks):
    run([setup,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={app}',f'/UNLOCKED={unlocked}',f'/TASKS={tasks}',f'/LOG={BASE/(label+".log")}'])
    assert Path((app/'data-root.txt').read_text(encoding='utf-8')).resolve()==data
    run([app/'runtime/python.exe','-I',app/'app.pyw','--check-runtime'])
    assert not json.loads((data/'runtime-check.json').read_text())['missing']
def uninstall(label):
    log=BASE/(label+'.log')
    run([app/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/DELETEGAMEDATA','/DELETESAVES',f'/LOG={log}'])
    end=time.monotonic()+45
    while time.monotonic()<end:
        if log.exists() and 'Log closed.' in log.read_text(errors='replace'):break
        time.sleep(.2)
    assert 'Log closed.' in log.read_text(errors='replace') and 'Uninstallation process succeeded.' in log.read_text(errors='replace')
    assert not any(p.exists() for p in shortcuts) and not (app/'Play.exe').exists() and not data.exists()
install('branding-options-fresh','no','')
assert not any(p.exists() for p in shortcuts)
save=data/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
assert digest(save)==digest(app/'fresh-save.bin')
assert not json.loads((data/'save-start-choice.json').read_text())['all_unlocked']
runner=app/'resources/native-port/repo/build/ps2xRuntime/ps2EntryRunner-standalone.exe'
assert digest(runner)==digest(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-branding-fusion-review.exe')
run([app/'runtime/python.exe','-I',HERE/'codex_installer_import_check.py',app,
     HERE.parent/'experiments/Dragon Ball Z Bt3 niveles de poder BETA 1.5.1.ISO',data,'--stored-root'])
game=data/'native-port/power-scale-trial/controller/game'
assert json.loads((game/'game-profile.json').read_text())['runtime_variant']=='BT3 Power Scale BETA 1.5.1 (experimental)'
art=data/'native-port/power-scale-trial/app-data/native-ui'
assert json.loads((art/'manifest.json').read_text())['version']==7 and (art/'brand-logo.rgba').is_file()
assert (data/'native-port/runtime-data/assets/icon.png').is_file()
print('PASS real D: import, variant metadata, shared logo/cache/icon, fresh-save choice and tasks off',flush=True)
save.write_bytes(save.read_bytes()+b'gate-upgrade-proof')
settings=game/'mod-settings.json'
values=json.loads(settings.read_text());values['language']='es';settings.write_text(json.dumps(values))
paths=[save,settings,data/'import/import-receipt.json',data/'save-start-choice.json',app/'data-root.txt']
before=[digest(p) for p in paths]
install('branding-options-upgrade','yes','desktopicon,startmenuicon')
assert [digest(p) for p in paths]==before and all(p.is_file() for p in shortcuts)
import comtypes.client
shell=comtypes.client.CreateObject('WScript.Shell',dynamic=True)
for path in shortcuts:
    link=shell.CreateShortcut(str(path))
    assert Path(link.TargetPath).resolve()==(app/'Play.exe').resolve()
    assert Path(str(link.IconLocation).rsplit(',',1)[0]).resolve()==(app/'assets/BT3TagTeam.ico').resolve()
print('PASS upgrade preserves all player data; both optional shortcuts target Play and original icon',flush=True)
uninstall('branding-options-uninstall')
install('branding-options-unlocked','yes','')
assert digest(save)==digest(app/'default-save.bin')
assert json.loads((data/'save-start-choice.json').read_text())['all_unlocked']
uninstall('branding-options-unlocked-uninstall')
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-branding-gate-')
shutil.rmtree(work)
if shortcuts[1].parent.exists() and not any(shortcuts[1].parent.iterdir()):shortcuts[1].parent.rmdir()
result=dict(artifact_sha256=digest(BASE/'output/BT3-TagTeam-Preview-0.1-Setup.exe'),
    gate_setup_sha256=digest(setup),runner_sha256=digest(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-branding-fusion-review.exe'),
    real_import='PASS',metadata_and_branding='PASS',both_save_choices='PASS',upgrade_preservation='PASS',
    tasks_off_on_icons_and_removal='PASS',isolated_app_id=True,temporary_profile_cleaned=True,game_launched=False)
(BASE/'branding-options-gate.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
