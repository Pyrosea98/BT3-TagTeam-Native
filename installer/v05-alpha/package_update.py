from pathlib import Path
import json,shutil,zlib,hashlib
r=Path.cwd();a=r/'analysis/codex-ginyu-release-20261107';old=Path(r'F:\BT3-Builds\pc-release-v05-alpha');out=Path(r'F:\BT3-Builds\pc-release-v05-alpha-ginyu');pack=out/'update';pack.mkdir(parents=True,exist_ok=True)
assert json.loads((a/'native-validation.json').read_text())['passed']
shutil.copytree(old/'update',pack,dirs_exist_ok=True);payload=pack/'payload';manifest=json.loads((payload/'update.json').read_text());previous=json.loads((old/'update/payload/update.json').read_text());prior={x['root']+':'+x['path']:x for x in previous['files']};sha=lambda b:hashlib.sha256(b).hexdigest()
local=json.loads((r/'analysis/codex-language-audit-20261107/candidate-receipt.json').read_text())['files']
def replace(root,path,raw):
 rec=next(x for x in manifest['files']if x['root']==root and x['path']==path);before=list(dict.fromkeys(rec['before']+[prior[root+':'+path]['sha256']]+([local[path]]if path in local else [])))
 blob=zlib.compress(raw,6);h=sha(blob);name='blobs/'+h+'.z';(payload/name).write_bytes(blob)
 rec.update(bytes=len(raw),sha256=sha(raw),before=before,plans={str(x):dict(file=name,sha256=h,kind='full')for x in before})
for name in ['Tenkaichi3Decomp.exe','Tenkaichi3Decomp.exe.mem','Tenkaichi3Decomp.dat','SDL3.dll']:replace('app',name,(a/'candidate'/name).read_bytes())
profile=json.loads((old/'checks/upgrade-final-normal/release-profile.json').read_text());profile.update(version='0.5.alpha',revision='ginyu-language-20261107',runtime={n:sha((a/'candidate'/n).read_bytes())for n in ['Tenkaichi3Decomp.exe','Tenkaichi3Decomp.exe.mem','Tenkaichi3Decomp.dat']},source_build_receipt_sha256=sha((a/'production-receipt.json').read_bytes()))
replace('app','release-profile.json',json.dumps(profile,indent=2).encode())
manifest.update(from_versions=['0.4.1','0.5.alpha'],revision='ginyu-language-20261107')
(payload/'update.json').write_text(json.dumps(manifest,separators=(',',':')));shutil.copy2(a/'update_player.py',pack/'update.py')
(pack/'Update.cmd').write_text('@echo off\nsetlocal\nset "GAME=%~1"\nif not defined GAME set /p "GAME=Existing BT3 Tag Team 0.4.1 or 0.5.alpha installation folder: "\nif not exist "%GAME%\\runtime\\python.exe" (echo Supported installation not found.& pause& exit /b 1)\n"%GAME%\\runtime\\python.exe" -B "%~dp0update.py" "%GAME%"\nset "RESULT=%ERRORLEVEL%"\npause\nexit /b %RESULT%\n')
(pack/'README.txt').write_text('''BT3 TAG TEAM + REAL POWER SCALE — 0.5.alpha revision (2026-11-07)

Close the game, extract this ZIP, run Update.cmd, and choose the existing installation folder containing Play.exe. Supports 0.4.1 and earlier completed 0.5.alpha installs. Keep using the same launcher. No fresh extraction is needed for a compatible imported ISO.

This revision adds Ginyu's actual-hit body exchange and the English/Spanish text audit. Existing saves, achievements, settings, bindings and normal/2x map choice are preserved. Inputs and reconstructed files are verified before replacement; rollback copies are retained. Applying the same revision again verifies the package files and makes no changes.

Ginyu keeps the normal successful-hit cinematic. Bodies exchange costumes, remaining health, Ki, stocks and stats; players keep their controls and teams. Stolen-body special-technique restrictions remain as in the original move. Online/replays retain their original rules. In-fight fused bodies are not exchanged because they own a separate consumed-partner/timer lifecycle.

Experimental PC alpha. No new playable Namek chapters or APK is included. New installations: install 0.4.1 and import a supported ISO, then apply this update. New ISO revisions need a compatible import recipe; do not replace extracted data arbitrarily.

ESPAÑOL
Cierra el juego, extrae el ZIP, ejecuta Update.cmd e indica la carpeta de tu instalación 0.4.1 o 0.5.alpha. Se conservan partidas, logros, ajustes y mapas normales/2x. No necesitas reinstalar ni volver a extraer una ISO compatible. Esta revisión incluye el intercambio real de cuerpos de Ginyu y las correcciones de textos en inglés y español.
''',encoding='utf8')
(out/'package-receipt.json').write_text(json.dumps(dict(version='0.5.alpha',revision=manifest['revision'],files=len(manifest['files']),from_versions=manifest['from_versions'],normal_and_2x_preserved=True),indent=2));print('Prepared current alpha update; prior release package untouched')
