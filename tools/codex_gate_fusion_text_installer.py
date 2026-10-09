"""Actual isolated clean install/import/upgrade/uninstall. Never start Play."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent
BASE=HERE/'installer';PY=HERE.parent/'experiments/.full-install/.venv/Scripts/python.exe'
setup=BASE/'output/BT3-TagTeam-Fusion-0.1-Setup.exe'
old=BASE/'output/BT3-TagTeam-Initial-0.1-Setup.exe'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runner_sha=digest(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-fusion-text-release.exe')
def finish_gate():
    result={'setup_sha256':digest(setup),'setup_bytes':setup.stat().st_size,'runner_sha256':runner_sha,
            'clean_install':'PASS','original_expanded_import':'PASS','upgrade':'PASS','uninstall_preserves_save':'PASS','game_launched':False}
    (BASE/'fusion-text-gate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
if '--finish-uninstall' in sys.argv:
    # Inno's temporary uninstaller can finish after its original process exits.
    log=(BASE/'fusion-text-gate.log').read_text(encoding='utf-8',errors='replace')
    assert 'PASS actual prior-version upgrade retains distinct settings/save' in log
    checks=[json.loads(line) for line in log.splitlines() if line.startswith('{"runtime"')]
    expected=checks[-1]['save_sha256'];assert checks[-1]['save']=='preserved'
    assert not (BASE/'fusion-text-upgrade-installed/Play.exe').exists()
    assert not (BASE/'fusion-text-upgrade-profile/native-port').exists()
    assert digest(BASE/'fusion-text-upgrade-profile/saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3')==expected
    assert 'Uninstallation process succeeded.' in (BASE/'fusion-text-uninstall.log').read_text(encoding='utf-8')
    print('PASS actual completed uninstall removes app/private sources and retains save',flush=True)
    finish_gate();raise SystemExit(0)
def run(args,env=None):
    p=subprocess.run(list(map(str,args)),env=env,timeout=600)
    assert p.returncode==0,(args[0],p.returncode)
def install(exe,app,data,label):
    assert app.resolve().is_relative_to(BASE.resolve()) and data.resolve().is_relative_to(BASE.resolve())
    env=dict(os.environ,BT3_TAGTEAM_DATA=str(data))
    run([exe,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={app}',f'/LOG={BASE/(label+".log")}'],env)
    run([PY,HERE/'codex_installer_package_check.py',app,data])
    return env
def save(data):return data/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
def runner(app):return app/'resources/native-port/repo/build/ps2xRuntime/ps2EntryRunner-standalone.exe'
app=BASE/'fusion-text-installed';data=BASE/'fusion-text-profile'
assert not app.exists() and not data.exists(),'Fresh gate paths already exist'
install(setup,app,data,'fusion-text-install')
assert digest(runner(app))==runner_sha
run([app/'runtime/python.exe','-I',HERE/'codex_installer_import_check.py',app,
     HERE.parent/'experiments/Dragon Ball Z Bt3 niveles de poder BETA 1.5.1.ISO',data])
print('PASS clean final install + actual installed original/expanded import',flush=True)
upgrade=BASE/'fusion-text-upgrade-installed';profile=BASE/'fusion-text-upgrade-profile'
assert not upgrade.exists() and not profile.exists()
install(old,upgrade,profile,'fusion-text-prior-install')
settings=profile/'native-port/power-scale-trial/controller/game/mod-settings.json'
values=json.loads(settings.read_text(encoding='utf-8'));values.update(language='es',expanded_maps=False,coop_fusion_swap_seconds=45)
settings.write_text(json.dumps(values,indent=2),encoding='utf-8')
save(profile).write_bytes(save(profile).read_bytes()+b'isolated-upgrade-proof')
before={'settings':digest(settings),'save':digest(save(profile))}
env=install(setup,upgrade,profile,'fusion-text-upgrade')
assert digest(settings)==before['settings'] and digest(save(profile))==before['save']
assert digest(runner(upgrade))==runner_sha
print('PASS actual prior-version upgrade retains distinct settings/save',flush=True)
run([upgrade/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/LOG={BASE/"fusion-text-uninstall.log"}'],env)
deadline=time.monotonic()+30
while ((upgrade/'Play.exe').exists() or (profile/'native-port').exists()) and time.monotonic()<deadline:time.sleep(.1)
assert not (upgrade/'Play.exe').exists() and not (profile/'native-port').exists()
assert digest(save(profile))==before['save']
print('PASS actual uninstall removes app/private sources and retains save',flush=True)
finish_gate()
