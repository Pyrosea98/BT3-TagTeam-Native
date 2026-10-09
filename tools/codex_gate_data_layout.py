"""Real alternate-drive install/import/upgrade/uninstall; never launch a game."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path(__file__).resolve().parent
base=root/'installer';setup=base/'output/BT3-TagTeam-Preview-0.1-Setup.exe'
resume=len(sys.argv)>1
work=Path(sys.argv[1] if resume else 'D:/BT3TagTeam-gate-'+time.strftime('%Y%m%d-%H%M%S')).resolve()
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-gate-')
assert work.exists() if resume else not work.exists()
app=work/'app';data=app/'data'
env=dict(os.environ);env.pop('BT3_TAGTEAM_DATA',None)
def run(args):
    subprocess.run(list(map(str,args)),env=env,check=True,timeout=600)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def install(label):
    run([setup,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={app}',f'/LOG={base/(label+".log")}'])
    assert Path((app/'data-root.txt').read_text(encoding='utf-8')).resolve()==data
    run([app/'runtime/python.exe','-I',app/'app.pyw','--check-runtime'])
    assert not json.loads((data/'runtime-check.json').read_text())['missing']
def uninstall(label,*switches):
    log=base/(label+'.log')
    run([app/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/LOG={log}',*switches])
    end=time.monotonic()+40
    while time.monotonic()<end:
        if log.exists() and 'Log closed.' in log.read_text(errors='replace'):break
        time.sleep(.2)
    assert 'Uninstallation process succeeded.' in log.read_text(errors='replace')
    assert 'Log closed.' in log.read_text(errors='replace')
    assert not (app/'Play.exe').exists()
install('data-layout-install')
assert digest(app/'app.pyw')==digest(base/'app.pyw')
assert digest(app/'resources/native-port/repo/build/ps2xRuntime/ps2EntryRunner-standalone.exe')==digest(root/'repo/build/ps2xRuntime/ps2EntryRunner-reviewed-cpu-forms.exe')
defaults=json.loads((app/'resources/native-port/power-scale-trial/controller/game/mod-settings-defaults.json').read_text())
assert not defaults['native_mode_cover'] and not defaults['fusion_time_by_form']
if resume:
    assert 'PASS installed original/expanded import' in (base/'data-layout-gate-first.log').read_text(errors='replace')
    run([app/'runtime/python.exe','-I','-c',
        "import runpy; m=runpy.run_path("+repr(str(app/'app.pyw'))+",run_name='gate'); assert m['imported'](); print('PASS retained real import receipt and art verification')"])
else:
    run([app/'runtime/python.exe','-I',root/'codex_installer_import_check.py',app,
         root.parent/'experiments/Dragon Ball Z Bt3 niveles de poder BETA 1.5.1.ISO',data,'--stored-root'])
print('PASS alternate-drive install, stored root, embedded runtime and real disc import',flush=True)
save=data/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
# The runtime check seeds the save without invoking the game.
settings=data/'native-port/power-scale-trial/controller/game/mod-settings.json'
values=json.loads(settings.read_text());values['language']='es';settings.write_text(json.dumps(values))
save.write_bytes(save.read_bytes()+b'isolated-upgrade-proof')
paths=[settings,save,data/'import/import-receipt.json',app/'data-root.txt']
before=[digest(p) for p in paths]
install('data-layout-upgrade')
assert before==[digest(p) for p in paths]
print('PASS upgrade preserves import, settings, save and location',flush=True)
uninstall('data-layout-keep-all')
assert before==[digest(p) for p in paths]
print('PASS default uninstall preserves all game data and saves',flush=True)
install('data-layout-reinstall')
uninstall('data-layout-delete-data','/DELETEGAMEDATA')
assert not (data/'import').exists() and not (data/'native-port').exists()
assert digest(save)==before[1]
print('PASS explicit data removal preserves saves',flush=True)
install('data-layout-final-install')
uninstall('data-layout-delete-all','/DELETEGAMEDATA','/DELETESAVES')
assert not save.exists() and not data.exists()
# Remove only this exact fresh gate tree; leave logs/evidence in the workspace.
import shutil
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-gate-')
shutil.rmtree(work)
result=dict(setup=str(setup),sha256=digest(setup),bytes=setup.stat().st_size,
    alternate_drive='D:',install='PASS',real_import='PASS',upgrade='PASS',
    uninstall_keep_all='PASS',uninstall_keep_saves='PASS',uninstall_delete_all='PASS',
    temporary_profile_cleaned=True,game_launched=False)
(base/'data-layout-gate.json').write_text(json.dumps(result,indent=2)+'\n')
setup.with_suffix('.exe.sha256').write_text(result['sha256']+'  '+setup.name+'\n')
print(json.dumps(result),flush=True)
