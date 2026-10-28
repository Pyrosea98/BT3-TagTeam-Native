from pathlib import Path
import subprocess,shutil,json,hashlib,zipfile
B=Path('F:/BT3-Builds');S=B/'Tenkaichi3Decomp-tagteam';O=B/'pc-release-v041';D=O/'runtime-source';D.mkdir(exist_ok=True);HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tracked=subprocess.check_output(['git','-C',str(S),'ls-files','-z']).decode().split('\0');files=set(n for n in tracked if n)
extensions={'.c','.cpp','.cc','.h','.hpp','.inc','.py','.sh','.md','.txt','.json','.yaml','.yml','.toml','.ico','.png','.rc','.s','.S','.tsv','.ttf','.patch'}
for folder in ['src','include','port/src','port/include','port/tests','port/tools','port/release','port/setup','port/assets']:
 for p in (S/folder).rglob('*'):
  if p.is_file()and p.suffix in extensions and '__pycache__'not in p.parts:files.add(p.relative_to(S).as_posix())
banned={'.iso','.afs','.elf','.exe','.dll','.mem','.dat','.bin','.ps2','.pyd','.o','.ll','.i','.log','.zip'};records={}
for name in sorted(files):
 p=S/name
 if not p.is_file()or p.suffix.lower()in banned or any(x in ('build','build_release','gamedata','analysis','.git')for x in p.relative_to(S).parts):continue
 out=D/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out);records[name]=sha(out)
assert all(n in records for n in ['port/src/gs/mod_credits_data.inc','port/src/mod_assists_native.inc','port/include/mod_fusion_native.inc','src/battle/btl_char_flag_clash.c'])
(D/'README.upstream.md').write_bytes((S/'README.md').read_bytes())
(D/'README.md').write_text('''# BT3 Tag Team + Real Power Scale — native PC source

This branch contains the Tenkaichi3Decomp-based v0.4.1 port. The older `tagteam-native` branch retains the previous BT3-Recomp implementation; do not mix their installers or data.

- Windows installer and instructions: https://github.com/Pyrosea98/BT3-TagTeam-Native/releases
- Engine upstream: https://github.com/z3xox/Tenkaichi3Decomp
- Original Tag Team mod: https://github.com/tehmufti/Budokai-Tenkaichi-3-Tag-Team-Mod-PCSX2-
- Power Scale: LetsPlayBt3; special thanks to RidJuampa for helping me understand the code: https://www.youtube.com/@RidJuampa

Includes the current native gameplay, fusion/defusion/revival, CPU behavior, team input, assists and clash QTE, HUD/menu/localization and startup-credit implementations. The installer repository owns disc import, normal/2x map selection, save/settings seeding and Windows packaging. Android packaging is separate and maintained by Claude.

See `README.upstream.md`, `docs/port/README.md`, `port/release/Dockerfile` and `port/release/inside.sh` for the engine build. Supply your own supported game data for runtime tests. No ISO, BIOS, AFS archives or extracted game data is included in this source tree. Release binaries fetch game data from the user's authenticated import.

Preserve the AGPL-3.0 license and all upstream notices. The installer includes attribution and component licenses. See `SOURCE_REVISION.json` for the exact upstream base and modified-source manifest.
''',encoding='utf-8')
rev=dict(version='0.4.1',upstream='https://github.com/z3xox/Tenkaichi3Decomp',base_commit=subprocess.check_output(['git','-C',str(S),'rev-parse','HEAD'],text=True).strip(),build_receipt=json.loads((S/'analysis/codex-pc-release041/build-receipt.json').read_text()),source_files=records,game_files_included=False)
(D/'SOURCE_REVISION.json').write_text(json.dumps(rev,indent=2));F=O/'frontend-source';F.mkdir(exist_ok=True)
for p in HERE.iterdir():
 if p.is_file()and p.suffix in {'.py','.pyw','.cs','.iss','.md','.txt'}:shutil.copy2(p,F/p.name)
print('Prepared',len(records),'native source/dependency files and frontend sources without game inputs')
