"""Claude: import every module of a tools directory in its own subprocess; print the failures (used to compare trees).
Usage: python claude_import_matrix.py <tools_dir> <out.json>
"""
import json
import subprocess
import sys
from pathlib import Path

tools = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
fails = {}
names = sorted(p.stem for p in tools.glob('*.py') if not p.stem.startswith('test_') and p.stem not in ('modder_gui',))
for i, name in enumerate(names):
    code = f"import sys,os;sys.path.insert(0,r'{tools}');os.environ.setdefault('PS2X_NATIVE_UI_SLICE','1');import {name}"
    try:
        r = subprocess.run([sys.executable, '-I', '-c', code], capture_output=True, text=True, timeout=40, cwd=str(tools))
    except subprocess.TimeoutExpired:
        fails[name] = 'TIMEOUT'
        continue
    if r.returncode:
        last = (r.stderr.strip().splitlines() or ['?'])[-1][:200]
        fails[name] = last
out.write_text(json.dumps({'count': len(names), 'fails': fails}, indent=1), encoding='utf-8')
print('modules', len(names), 'failures', len(fails))
