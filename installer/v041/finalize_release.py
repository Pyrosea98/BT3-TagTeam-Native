"""Freeze source archives and verify the compiled PC installer before publication."""
from pathlib import Path
import hashlib,json,subprocess,shutil,zipfile,os,sys
O=Path('F:/BT3-Builds/pc-release-v041');P=O/'payload';R=O/'release';D=O/'runtime-source'
HERE=Path(__file__).resolve().parent
W=HERE.parents[2]
FR=W/'repo-staging/BT3-TagTeam-Native'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
rev=json.loads((D/'SOURCE_REVISION.json').read_text())
for name in ('README.md','README.upstream.md'):rev['source_files'][name]=sha(D/name)
(D/'SOURCE_REVISION.json').write_text(json.dumps(rev,indent=2),encoding='utf-8')
run(['git','-C',D,'add','SOURCE_REVISION.json'])
if subprocess.run(['git','-C',str(D),'diff','--cached','--quiet']).returncode:
 run(['git','-C',D,'commit','-m','Correct release source manifest for branch documentation'])
# Hash blobs from one git archive rather than thousands of subprocesses.
nativezip=R/'BT3-TagTeam-v0.4.1-Native-Source.zip'
run(['git','-C',D,'archive','--format=zip','-o',nativezip,'HEAD'])
with zipfile.ZipFile(nativezip)as z:
 mismatches=[n for n,h in rev['source_files'].items()if hashlib.sha256(z.read(n)).hexdigest()!=h]
assert not mismatches,mismatches
tests=[]
for lang,mode in [('english','2x'),('spanish','normal')]:
 dst=O/'checks'/('install-en'if lang=='english'else'install-es')
 # Real user progress/settings must survive reinstall byte-for-byte.
 (dst/'data/saves').mkdir(parents=True,exist_ok=True)
 sentinel={'data/bt3_settings.txt':b'update_check=0\ncoop_fusion_swap_seconds=10\n# preservation check\n','data/saves/preservation-test.txt':b'existing player progress'}
 for n,b in sentinel.items():(dst/n).write_bytes(b)
 run([R/'BT3-TagTeam-v0.4.1-Windows-Setup.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',f'/DIR={dst}',f'/LANG={lang}',f'/MAPSIZE={mode}',f'/LOG={O}/checks/final-{lang}.log'])
 for n,b in sentinel.items():assert(dst/n).read_bytes()==b,n
 run([dst/'runtime/python.exe','-B',dst/'app.pyw','--check-package'])
 choices=json.loads((dst/'install-choices.json').read_text(encoding='utf-8-sig'))
 assert choices['expanded_maps']==(mode=='2x')
 for name in ('app.pyw','importer.py','Play.exe','release-profile.json'):
  assert sha(dst/name)==sha(P/name),name
 assert(dst/'manual/BT3-TagTeam-Manual-EN.html').exists()and(dst/'manual/BT3-TagTeam-Manual-ES.html').exists()
 tests.append(dict(language=lang,maps=mode,package_verified=True,settings_and_save_preserved=True))
run([sys.executable,'-B',HERE/'test_importer.py'])
F=FR/'installer/v041';F.mkdir(parents=True,exist_ok=True)
for p in HERE.iterdir():
 if p.is_file()and p.suffix in {'.py','.pyw','.cs','.iss','.md','.txt'}:shutil.copy2(p,F/p.name)
shutil.copy2(P/'credits_splash.py',F/'credits_splash.py')
shutil.copytree(P/'assets',F/'assets',dirs_exist_ok=True)
shutil.copytree(P/'manual',F/'manual',dirs_exist_ok=True)
shutil.copytree(P/'licenses',F/'licenses',dirs_exist_ok=True)
for n in ('release-profile.json','recommended-settings.txt'):shutil.copy2(P/n,F/n)
(F/'BUILD.md').write_text('''# v0.4.1 Windows packaging

Current native source: https://github.com/Pyrosea98/BT3-TagTeam-Runtime/tree/decomp-native

The earlier installer folders target the older runtime; use this folder for v0.4.1.
Build the engine using its release Dockerfile and inside.sh. The scripts here document the exact maintainer staging layout under F:/BT3-Builds; adjust these paths for another machine. stage_payload.py authenticates the initializer against the stock reference before adapting it to the supported profile.

ImportRecipes.zip in the v0.4.1 release supplies import-data/ (compressed authenticated file deltas and content manifest). Place that directory in payload/ beside the native Windows release, embedded CPython 3.11.9 with Tk and Pillow 12.3.0, app.pyw, importer.py, credits_splash.py, assets/, manual/, recommended-settings.txt and release-profile.json. Compile Play.cs with the Windows .NET Framework C# compiler and the supplied icon. Supply your own completed save seed if desired; no disc image or extracted game archives belong in Git.

Run test_importer.py, then app.pyw --check-package using the embedded Python. Compile installer.iss with Inno Setup 6.7.3. The issuer's build_content.py creates authenticated copy/XOR recipes from their locally owned supported ISO and approved loose-data profile; it never modifies the input ISO. Use the release verification and SHA256SUMS for the exact published artifacts.

The installed app defaults to Vulkan. Existing saves/settings are preserved. Both normal and optional 2x maps use the same gameplay fixes. Android packaging is separate.
''',encoding='utf-8')
readme=FR/'README.md';old=readme.read_text(encoding='utf-8')
if not old.startswith('# BT3 Tag Team + Real Power Scale — v0.4.1'):
 readme.write_text('''# BT3 Tag Team + Real Power Scale — v0.4.1

[Download the PC installer](https://github.com/Pyrosea98/BT3-TagTeam-Native/releases/tag/v0.4.1) · [Current native source](https://github.com/Pyrosea98/BT3-TagTeam-Runtime/tree/decomp-native) · [Installer source/build instructions](installer/v041/BUILD.md)

The current release uses Tenkaichi3Decomp and Power Scale BETA 8. Choose normal or optional 2× maps during setup; both retain the current fixes. Import your own supported ISO. English/Spanish manuals, recommended settings and an unlocked-save option are included; existing progress and settings are preserved. Android is released separately.

The installer shows the shared credits and thank-you pages while preparing the game, at startup and in mod settings. Special thanks to [RidJuampa](https://www.youtube.com/@RidJuampa) for helping me understand the code. See the release notes and included upstream/component notices for full credits.

The sections below document the previous runtime and releases, retained for existing users. Do not combine their data or installers with v0.4.1.

---

'''+old,encoding='utf-8')
run(['git','-C',FR,'add','README.md','installer/v041'])
run(['git','-C',FR,'commit','-m','Release v0.4.1 installer for the current native Power Scale port'])
frontzip=R/'BT3-TagTeam-v0.4.1-Installer-Source.zip'
run(['git','-C',FR,'archive','--format=zip','-o',frontzip,'HEAD'])
with zipfile.ZipFile(R/'BT3-TagTeam-v0.4.1-ImportRecipes.zip','w',compression=zipfile.ZIP_STORED)as z:
 for p in sorted((P/'import-data').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(P).as_posix())
verification=dict(version='0.4.1',installer_tests=tests,source_manifest_files_verified=len(rev['source_files']),native_commit=subprocess.check_output(['git','-C',str(D),'rev-parse','HEAD'],text=True).strip(),installer_commit=subprocess.check_output(['git','-C',str(FR),'rev-parse','HEAD'],text=True).strip(),content=json.loads((O/'content-build-receipt.json').read_text()),asset_parity=json.loads((O/'approved-assets-parity.json').read_text()),native_smoke=json.loads((O/'native-smoke-receipt.json').read_text()),profile=json.loads((P/'release-profile.json').read_text()),limitations='Automated native smoke and regression checks; no new physical 3/4-controller acceptance claimed. APK separate.')
(R/'RELEASE_VERIFICATION.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
assets=[p for p in sorted(R.iterdir())if p.suffix in ('.exe','.zip')or p.name in ('README.txt','RELEASE_VERIFICATION.json')]
(R/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n'for p in assets),encoding='utf-8')
print('FINAL RELEASE CHECKS PASSED',json.dumps(verification['installer_tests']),flush=True)
