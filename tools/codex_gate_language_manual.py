"""Real isolated EN/ES installs and upgrade. Does not import or launch a game."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,ctypes
HERE=Path(__file__).resolve().parent
BASE=HERE/'installer'
setup=BASE/'output/BT3-Language-Manual-Gate.exe'
work=Path('D:/BT3TagTeam-language-gate-'+time.strftime('%Y%m%d-%H%M%S')).resolve()
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-language-gate-') and not work.exists()
app=work/'app';data=app/'data'
env=dict(os.environ);env.pop('BT3_TAGTEAM_DATA',None)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):subprocess.run(list(map(str,args)),env=env,check=True,timeout=180)
def install(label,lang,tasks=''):
    run([setup,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={app}',f'/LANG={lang}',f'/TASKS={tasks}',f'/LOG={BASE/(label+".log")}'])
    run([app/'runtime/python.exe','-I',app/'app.pyw','--check-runtime'])
    assert not json.loads((data/'runtime-check.json').read_text())['missing']
    for language in ('EN','ES'):
        for suffix in ('html','pdf'):
            name=f'BT3-TagTeam-Manual-{language}.{suffix}'
            assert digest(app/'manual'/name)==digest(BASE/'payload/manual'/name)
    return data/'native-port/power-scale-trial/controller/game/mod-settings.json'
def remove(label):
    log=BASE/(label+'.log')
    run([app/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/DELETEGAMEDATA','/DELETESAVES',f'/LOG={log}'])
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        if log.exists() and 'Log closed.' in log.read_text(errors='replace'):break
        time.sleep(.2)
    assert 'Uninstallation process succeeded.' in log.read_text(errors='replace') and not data.exists()
    assert not (app/'install-language.txt').exists()
buffer=ctypes.create_unicode_buffer(32768)
assert ctypes.windll.shell32.SHGetFolderPathW(None,2,None,0,buffer)==0
group=Path(buffer.value)/'BT3 Codex Language Gate'
assert not group.exists()
settings=install('language-manual-spanish','spanish','startmenuicon')
assert (app/'install-language.txt').read_text()=='es'
assert json.loads(settings.read_text())['language']=='es'
manual=group/'Manual de BT3 Tag Team.lnk'
assert manual.exists()
import comtypes.client
link=comtypes.client.CreateObject('WScript.Shell',dynamic=True).CreateShortcut(str(manual))
assert Path(link.TargetPath).name in ('BT3-TagTeam-Manual-ES.pdf','BT3-TagTeam-Manual-ES.html')
assert Path(link.TargetPath).parent==(app/'manual')
before=digest(settings)
install('language-manual-upgrade','english')
assert (app/'install-language.txt').read_text()=='en' and digest(settings)==before
remove('language-manual-spanish-uninstall')
assert not manual.exists()
settings=install('language-manual-english','english')
assert json.loads(settings.read_text())['language']=='en'
remove('language-manual-english-uninstall')
assert work.parent==Path('D:/') and work.name.startswith('BT3TagTeam-language-gate-')
shutil.rmtree(work)
if group.exists() and not any(group.iterdir()):group.rmdir()
receipt=dict(artifact_sha256=digest(BASE/'output/BT3-TagTeam-Preview-0.1-Setup.exe'),
    gate_setup_sha256=digest(setup),spanish_first_run='PASS',english_first_run='PASS',
    upgrade_language_preserved='PASS',localized_manual_shortcut='PASS',manual_content_parity='PASS',
    uninstall_language_file_and_data='PASS',game_launched=False,temporary_profile_cleaned=True)
(BASE/'language-manual-gate.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
