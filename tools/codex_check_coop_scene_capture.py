"""Production scene/exit captures remain independent and never stop the guest."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
runner=HERE/'repo/build/ps2xRuntime/ps2EntryRunner-coop-scene-fusion.exe'
with tempfile.TemporaryDirectory(prefix='coop-scene-capture-',dir=HERE/'power-scale-trial') as temp:
    root=Path(temp);env=os.environ.copy();env['PS2X_SCENE_CAPTURE_SELF_TEST']='1'
    result=subprocess.run([str(runner),'--native-exit-capture-self-test',temp],env=env,capture_output=True,text=True,timeout=45)
    print(result.stdout+result.stderr,end='');assert result.returncode==0
    exits=list(root.glob('guest-exit-*'));scenes=list(root.glob('black-scene-*'))
    assert len(exits)==len(scenes)==1
    state=json.loads((scenes[0]/'state.json').read_text())
    assert state['reason']=='cinematic-gs-packet-collapse' and state['layout']==1
    assert 'cinematic_stop' in state and 'reload_retire' in state and len(state['history'])==200
    assert (scenes[0]/'ram.bin').stat().st_size==0x8000000
    assert (scenes[0]/'context.bin').read_bytes()==(exits[0]/'context.bin').read_bytes()
    marker=root/'not-a-directory';marker.write_text('preserved')
    failed=subprocess.run([str(runner),'--native-exit-capture-self-test',str(marker)],env=env,capture_output=True,text=True,timeout=45)
    assert failed.returncode==0 and marker.read_text()=='preserved'
    print('PASS scene capture:128MiB RAM/context/last200/scene/reload metadata; independent exit capture; duplicate suppressed; no stop; I/O failure nonfatal')
