"""Build the isolated no-console launcher, replace the distributable on success."""
from pathlib import Path
import os,shutil,subprocess
HERE=Path(__file__).resolve().parent
APP=HERE/'installer';BUILD=APP/'play-build';BUILD.mkdir(exist_ok=True)
vc=Path('C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
rc=Path('C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe')
command=f'call "{vc}" && "{rc}" /nologo /fo "{BUILD / "play.res"}" play.rc && cl /nologo /std:c++17 /O2 /MT /Fe:"{BUILD / "Play.exe"}" /Fo:"{BUILD / "play.obj"}" play.cpp "{BUILD / "play.res"}" user32.lib /link /SUBSYSTEM:WINDOWS'
batch=BUILD/'build-play.cmd';batch.write_text('@echo off\n'+command+'\n',encoding='utf-8')
subprocess.run(f'"{os.environ.get("COMSPEC","cmd.exe")}" /d /c "{batch}"',cwd=APP,check=True)
pending=APP/'Play.pending.exe';shutil.copy2(BUILD/'Play.exe',pending);pending.replace(APP/'Play.exe')
print('Built launcher with embedded original icon:',APP/'Play.exe')
