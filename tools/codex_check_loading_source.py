"""Compile the changed UI sources without linking or touching a live runner."""
import json, re, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
entries=json.loads((root/'repo/build/compile_commands.json').read_text(encoding='utf-8'))
files=[root/'repo/ps2xRuntime/src/lib/ps2_settings_overlay.cpp',root/'repo/ps2xRuntime/src/lib/ps2_ui_vulkan.cpp']
base=next(e for e in entries if e['file'].replace('\\','/').endswith('/ps2_ui_vulkan.cpp'))
for source in files:
    command=base['command']
    command=command.replace('"'+base['file']+'"','"'+str(source)+'"')
    for pattern in (r' /Fo[^ ]+',r' /Fd[^ ]+',r' /clang:-MD',r' -clang:-MD',r' -clang:-MT[^ ]+',r' -clang:-MF[^ ]+'):
        command=re.sub(pattern,'',command)
    command=command.replace(' -c -- ', ' /clang:-fsyntax-only -- ')
    print('Syntax check: '+source.name,flush=True)
    result=subprocess.run(command,cwd=base['directory'])
    if result.returncode:raise SystemExit(result.returncode)
