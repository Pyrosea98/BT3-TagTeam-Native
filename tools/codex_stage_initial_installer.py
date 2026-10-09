"""Build-time staging only: explicit sources, no player discs/art/saves/logs."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'installer/payload';OUT.mkdir(parents=True,exist_ok=True)
RESOURCE=OUT/'resources/native-port'
# This builder creates the preview package; public staging must write 'public'.
(OUT/'release-channel.txt').write_text('preview\n',encoding='utf-8')
def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
def scripts(source,destination):
    for path in source.rglob('*.py'):
        if '__pycache__' not in path.parts:copy(path,destination/path.relative_to(source))
scripts(HERE/'power-scale-trial/controller/game/tools',RESOURCE/'power-scale-trial/controller/game/tools')
for table in ('fusion_form_tiers.json','cpu_transform_form_tiers.json'):
    copy(HERE/'power-scale-trial/controller/game/tools'/table,RESOURCE/'power-scale-trial/controller/game/tools'/table)
scripts(HERE/'power-scale-trial/controller/iso_compatibility',RESOURCE/'power-scale-trial/controller/iso_compatibility')
scripts(HERE/'roster-tools',RESOURCE/'roster-tools')
for wheel in (HERE/'power-scale-trial/controller/vendor-wheels').glob('*.whl'):
    copy(wheel,RESOURCE/'power-scale-trial/controller/vendor-wheels'/wheel.name)
# Native glue is temporarily frozen as source; developer tests/diagnostics are
# excluded. The runtime dependency checker verifies the actual lazy graph.
for path in HERE.glob('*.py'):
    if path.name.startswith(('codex_','native_','relocate_','run_power_scale_')) and not path.name.startswith('codex_build_') and not any(word in path.stem for word in ('check','audit','capture','benchmark','review','self_test','preview','compare','diagnostic','boot_')):
        copy(path,RESOURCE/path.name)
copy(HERE/'codex_dependency_check.py',RESOURCE/'codex_dependency_check.py')
copy(HERE/'codex_extract_battle_hud.py',RESOURCE/'codex_extract_battle_hud.py')
for path in (HERE/'power-scale-trial/controller/game/analysis').iterdir():
    if path.is_file() and path.suffix in ('.json','.bin'):copy(path,RESOURCE/'power-scale-trial/controller/game/analysis'/path.name)
for name in ('characters.json','native-menu-pre-settings.json'):
    copy(HERE/'power-scale-trial/controller/game/assets'/name,RESOURCE/'power-scale-trial/controller/game/assets'/name)
    if name == 'characters.json':
        # Labels need the character rows, not the developer's source-disc path.
        metadata=RESOURCE/'power-scale-trial/controller/game/assets'/name
        labels=json.loads(metadata.read_text(encoding='utf-8'));labels.pop('source',None)
        metadata.write_text(json.dumps(labels,ensure_ascii=False,indent=2),encoding='utf-8')
copy(HERE/'roster-assets/characters.json',RESOURCE/'roster-assets/characters.json')
for name in ('psmt8-textures-afs1.json','tagteam-bootstrap.pnach','codex_decode_disc_indices.exe'):
    copy(HERE/'power-scale-trial'/name,RESOURCE/'power-scale-trial'/name)
copy(HERE/'power-scale-trial/controller/game/Tag Team Mod Logo.png',RESOURCE/'power-scale-trial/controller/game/Tag Team Mod Logo.png')
defaults=json.loads((HERE/'power-scale-trial/controller/game/mod-settings-defaults.json').read_text(encoding='utf-8'))
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import mod_settings
defaults=mod_settings.validate_settings(defaults)
defaults.update(expanded_maps=True,native_mode_menu_enabled=True,show_credits_at_startup=True,language='en',fusion_time_by_form=False,native_mode_cover=False)
for name in ('mod-settings.json','mod-settings-defaults.json'):
    p=RESOURCE/'power-scale-trial/controller/game'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(defaults,indent=2),encoding='utf-8')
for path in (HERE/'ui-assets/glyph-atlas-v2').iterdir():
    if path.suffix in ('.gatl','.indices','.rgba') and path.name.startswith(('title-','body-','numeric-')):copy(path,RESOURCE/'ui-assets/glyph-atlas-v2'/path.name)
copy(HERE/'ui-assets/ui_strings.json',RESOURCE/'ui-assets/ui_strings.json')
copy(HERE/'power-scale-trial/controller/game/assets/tag-team-real-power-scale-v1.png',RESOURCE/'power-scale-trial/controller/game/assets/tag-team-real-power-scale-v1.png')
branding=HERE/'ui-assets/branding'
if branding.is_dir():
    shutil.copytree(branding,RESOURCE/'ui-assets/branding',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
runner=RESOURCE/'repo/build/ps2xRuntime'
copy(Path(os.environ.get('BT3_PACKAGE_RUNNER',str(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-four-seat-fusion-review.exe'))),runner/'ps2EntryRunner-standalone.exe')
for path in (HERE/'repo/build/ps2xRuntime').glob('*.dll'):copy(path,runner/path.name)
for path in (HERE/'stock-deploy').glob('*.dll'):
    if path.name.startswith(('msvcp','vcruntime')):
        copy(path,runner/path.name);copy(path,RESOURCE/'power-scale-trial'/path.name)
for name in ('app.pyw','package_ui.py','disc-import.exe'):
    copy(HERE/'installer'/name,OUT/name)
copy(HERE/'installer/Play.exe',OUT/'Play.exe')
copy(HERE/'installer/assets/BT3TagTeam.ico',OUT/'assets/BT3TagTeam.ico')
copy(HERE/'savedata/BASLUS-21678DBZT3/BASLUS-21678DBZT3',OUT/'default-save.bin')
for name in ('icon.sys','dbzsm.ico'):
    copy(HERE/'savedata/BASLUS-21678DBZT3'/name,OUT/'save-card'/name)
copy(HERE/'power-scale-trial/save-backups/20261005-104334/BASLUS-21678DBZT3/BASLUS-21678DBZT3',OUT/'fresh-save.bin')
for name in ('supported-discs.json','map-recipe.json','map-fields.bin'):
    copy(HERE/'installer'/name,OUT/'import-data'/name)
base=Path(sys.base_prefix);runtime=OUT/'runtime'
for name in ('python.exe','pythonw.exe','python3.dll','python311.dll','vcruntime140.dll','vcruntime140_1.dll'):
    copy(base/name,runtime/name)
for directory in ('DLLs','tcl'):
    shutil.copytree(base/directory,runtime/directory,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(base/'Lib',runtime/'Lib',dirs_exist_ok=True,ignore=shutil.ignore_patterns('site-packages','__pycache__','test','tests','idlelib','ensurepip','*.pyc'))
site=Path(sys.prefix)/'Lib/site-packages'
for name in ('PIL','pycdlib','psutil','numpy','capstone','elftools','zstandard','comtypes'):
    shutil.copytree(site/name,runtime/'Lib/site-packages'/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','tests','*.pyc'))
for path in site.iterdir():
    if path.name.endswith('.libs'):shutil.copytree(path,runtime/'Lib/site-packages'/path.name,dirs_exist_ok=True)
    if path.name.endswith('.dist-info') and path.name.lower().startswith(('pillow-','pycdlib-','psutil-','numpy-','capstone-','pyelftools-','zstandard-','comtypes-','pycaw-')):
        shutil.copytree(path,runtime/'Lib/site-packages'/path.name,dirs_exist_ok=True)
notices=OUT/'notices'
for name in ('LICENSE.txt',):copy(base/name,notices/('Python-'+name))
for path in (HERE/'font-candidates').glob('*OFL.txt'):copy(path,notices/path.name)
copy(HERE/'repo/LICENSE',notices/'BT3-Recomp-LICENSE')
for path in sorted((HERE/'installer/notices-extra').glob('*.txt')):
    copy(path,notices/path.name)
copy(HERE/'repo/build/ps2xRuntime/fps60_sites.txt',RESOURCE/'runtime-data/fps60_sites.txt')
for name in ('RussoOne-Regular.ttf','OFL.txt'):
    copy(HERE/'repo/ps2xRuntime/assets/fonts'/name,RESOURCE/'runtime-data/assets/fonts'/name)
copy(HERE/'installer/assets/BT3TagTeam-icon-1024.png',RESOURCE/'runtime-data/assets/icon.png')
revision=hashlib.sha256()
for path in sorted(RESOURCE.rglob('*')):
    if path.is_file() and 'repo' not in path.relative_to(RESOURCE).parts and path.name!='source-build.json':
        revision.update(path.relative_to(RESOURCE).as_posix().encode('utf-8'))
        revision.update(hashlib.sha256(path.read_bytes()).digest())
(RESOURCE/'source-build.json').write_text(json.dumps({'revision':revision.hexdigest()}),encoding='utf-8')
subprocess.run([sys.executable,str(HERE/'codex_prepare_player_manual.py')],check=True)
inventory=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size} for p in OUT.rglob('*') if p.is_file()]
(HERE/'installer/package-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print('Staged files:',len(inventory),'size:',sum(p['bytes'] for p in inventory))
