"""Compile actual PadConfig against offline host devices; syntax-check owned UI.

Separate test output only; no CMake build, runner or guest process.
"""
from pathlib import Path
import json,os,re,subprocess,tempfile
root=Path(__file__).resolve().parent
runtime=root/'repo/ps2xRuntime'
entries=json.loads((root/'repo/build/compile_commands.json').read_text())
entry=next(e for e in entries if e['file'].replace('\\','/').endswith('/pad_config.cpp'))
compiler=Path(entry['command'].split('"')[1]).with_name('clang++.exe')
out=root/'analysis/native-pad-profile-check'
out.mkdir(parents=True,exist_ok=True)
exe=out/'pad-profiles-test.exe'
args=[str(compiler),'-std=c++20','-Wno-deprecated-declarations',
      '-I'+str(runtime/'include'),'-I'+str(runtime/'src'),'-I'+str(runtime/'third_party/bt3gl/src'),
      str(runtime/'src/lib/pad_config.cpp'),str(root/'codex_check_native_pad_profiles.cpp'),'-o',str(exe)]
vc=Path('C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
env=dict(os.environ)
batch=out/'test-env.cmd';batch.write_text(f'@echo off\ncall "{vc}" >nul\nif errorlevel 1 exit /b 1\nset\n')
result=subprocess.run(f'"{os.environ.get("COMSPEC","cmd.exe")}" /d /c "{batch}"',
                      check=True,capture_output=True,text=True)
for line in result.stdout.splitlines():
    if '=' in line:
        key,value=line.split('=',1)
        if key:env[key]=value
env['TMP']=str(out);env['TEMP']=str(out)
subprocess.run(args,check=True,env=env)
with tempfile.TemporaryDirectory(prefix='profiles-',dir=out) as tmp:
    subprocess.run([str(exe),tmp],check=True)
for suffix in ('/pad_config.cpp','/ps2_settings_overlay.cpp','/fe_pages.cpp','/ps2_debug_panel.cpp'):
    e=next((e for e in entries if e['file'].replace('\\','/').endswith(suffix)),entry)
    command=e['command']
    source=runtime/('src/frontend'+suffix if suffix=='/fe_pages.cpp' else 'src/lib'+suffix)
    command=command.replace('"'+e['file']+'"','"'+str(source)+'"')
    for pattern in (r' /Fo[^ ]+',r' /Fd[^ ]+',r' /clang:-MD',r' -clang:-MD',r' -clang:-MT[^ ]+',r' -clang:-MF[^ ]+'):
        command=re.sub(pattern,'',command)
    command=command.replace(' -c -- ',' /clang:-fsyntax-only -- ')
    subprocess.run(command,cwd=e['directory'],check=True,env=env)
    print('PASS native syntax:',suffix)
