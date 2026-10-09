"""Compile/test only the platform-neutral native seat service, no shared runner."""
from pathlib import Path
import os,subprocess
here=Path(__file__).resolve().parent
build=here/'seat-pads-test-build';build.mkdir(exist_ok=True)
source=build/'main.cpp';source.write_text('#include "runtime/ps2_native_seat_pads_test.h"\nint main(){return ps2_native_seats::selfTest();}\n')
vc=Path('C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
include=here/'repo/ps2xRuntime/include'
batch=build/'build.cmd';batch.write_text(f'@echo off\ncall "{vc}" && cl /nologo /EHsc /std:c++17 /W4 /I"{include}" /Fe:"{build / "test.exe"}" /Fo:"{build / "test.obj"}" "{source}"\n')
subprocess.run(f'"{os.environ.get("COMSPEC","cmd.exe")}" /d /c "{batch}"',check=True,cwd=build)
subprocess.run([str(build/'test.exe')],check=True)
