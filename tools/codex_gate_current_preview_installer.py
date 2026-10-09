"""Clean embedded installation and source/default parity; never launch Play."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path(__file__).resolve().parent;base=root/'installer'
setup=base/'output/BT3-TagTeam-Preview-0.1-Setup.exe'
label='preview-check-'+time.strftime('%Y%m%d-%H%M%S')
app=base/(label+'-app');data=base/(label+'-data')
assert not app.exists() and not data.exists()
env=dict(os.environ,BT3_TAGTEAM_DATA=str(data))
subprocess.run([str(setup),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={app}',f'/LOG={base/(label+".log")}'],env=env,check=True,timeout=180)
subprocess.run([sys.executable,str(root/'codex_installer_package_check.py'),str(app),str(data)],check=True,timeout=120)
source=app/'resources/native-port'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source/'repo/build/ps2xRuntime/ps2EntryRunner-standalone.exe')==digest(root/'repo/build/ps2xRuntime/ps2EntryRunner-reviewed-cpu-forms.exe')
for name in ('cpu_transform_form_tiers.json','cpu_tactics.py','native_menu_loading.py','native_menu_services.py'):
 assert digest(source/'power-scale-trial/controller/game/tools'/name)==digest(root/'power-scale-trial/controller/game/tools'/name)
values=json.loads((source/'power-scale-trial/controller/game/mod-settings-defaults.json').read_text(encoding='utf-8'))
assert not values['native_mode_cover'] and not values['fusion_time_by_form']
result=dict(setup=str(setup),sha256=digest(setup),bytes=setup.stat().st_size,clean_install='PASS',embedded_runtime='PASS',source_parity='PASS',safe_defaults='PASS',game_launched=False,live_dialog_vulkan_readback='PENDING; cover OFF',app=str(app),data=str(data))
(base/'preview-current-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result),flush=True)
