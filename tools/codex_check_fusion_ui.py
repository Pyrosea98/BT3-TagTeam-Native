"""Offscreen Vulkan captures and independent defeat/scene/exit exporters."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
RUNNER = HERE/'repo/build/ps2xRuntime'/os.environ.get('BT3_TEST_RUNNER','ps2EntryRunner-coop-fusion-release.exe')
env = os.environ.copy()
env.update(PS2X_FUSION_HUD_TEST_ONLY='1', PS2X_NATIVE_UI_SLICE='1')
output = HERE/'power-scale-trial/fusion-native-captures'
p = subprocess.run([str(RUNNER), '--native-ui-vulkan-self-test', str(HERE/'power-scale-trial/app-data/native-ui'), str(output)], env=env, capture_output=True, text=True, timeout=45)
(HERE/'power-scale-trial/codex-fusion-visual-check.log').write_text(p.stdout+p.stderr, encoding='utf-8')
assert p.returncode == 0, p.stderr
assert len(list(output.glob('*.png'))) == 12
print('PASS 12 Vulkan captures: EN/ES, 16:9/21:9, Hexagon/Ring/Off')
env.update(PS2X_SCENE_CAPTURE_SELF_TEST='1', PS2X_DEFEAT_CAPTURE_SELF_TEST='1')
with tempfile.TemporaryDirectory(dir=HERE/'power-scale-trial') as temp:
    p = subprocess.run([str(RUNNER), '--native-exit-capture-self-test', temp], env=env, capture_output=True, text=True, timeout=45)
    assert p.returncode == 0, p.stderr
    snapshots = [json.loads(x.read_text()) for x in Path(temp).glob('*/state.json')]
    assert len(snapshots) == 3
    assert {s['reason'] for s in snapshots} == {'team-defeat-not-resolved', 'cinematic-gs-packet-collapse', 'unsupported-interpreted-path'}
    assert all('actors' in s and 'participation' in s and len(s['history'])==200 for s in snapshots)
    assert all(x.stat().st_size == 0x8000000 for x in Path(temp).glob('*/ram.bin'))
    (HERE/'power-scale-trial/codex-fusion-defeat-capture-check.log').write_text(p.stdout+p.stderr, encoding='utf-8')
    print('PASS independent defeat/scene/exit snapshots: RAM128MiB, metadata/history, duplicate suppression, no stop')
