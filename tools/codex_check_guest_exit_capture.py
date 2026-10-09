"""Exercise the production exit capture through a headless native fixture."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
runner=HERE/'repo/build/ps2xRuntime/ps2EntryRunner-coop-exit-capture.exe'
root=Path(tempfile.mkdtemp(prefix='guest-exit-check-',dir=HERE/'power-scale-trial'))
result=subprocess.run([str(runner),'--native-exit-capture-self-test',str(root)],capture_output=True,text=True,timeout=45)
print(result.stdout+result.stderr,end='')
assert result.returncode==0, f'Native fixture returned {result.returncode}'
folders=list(root.glob('guest-exit-*'));assert len(folders)==1
capture=folders[0]
state=json.loads((capture/'state.json').read_text(encoding='utf-8'))
assert len(state['history'])==200
assert state['history'][0]['pc']==0x100000+400*4
assert state['history'][-1]['pc']==0x100000+599*4
assert state['pc']==0x2F0 and state['caller_pc']==0x2BAAE8 and state['caller_ra']==0x123456
assert state['layout']==1 and state['reason']=='unsupported-interpreted-path'
assert (capture/'ram.bin').stat().st_size==0x8000000
with (capture/'ram.bin').open('rb') as stream:
    stream.seek(0x2F0);assert struct.unpack('<I',stream.read(4))[0]==0x8001
assert (capture/'context.bin').read_bytes()==(capture/'main-context.bin').read_bytes()
assert (capture/'context.bin').stat().st_size>0
print('PASS: production128MiB/context/metadata capture; chronological last200/source/RA/SP; caller/layout; duplicate suppressed; no game/runtime stop')
marker=root/'not-a-directory';marker.write_text('fixture',encoding='utf-8')
failed=subprocess.run([str(runner),'--native-exit-capture-self-test',str(marker)],capture_output=True,text=True,timeout=45)
assert failed.returncode==0 and '[guest-exit-capture] local capture failed' in failed.stderr
assert marker.read_text(encoding='utf-8')=='fixture'
print('PASS: capture I/O failure leaves runtime running and existing file unchanged')
print('Fixture:',root.name)
