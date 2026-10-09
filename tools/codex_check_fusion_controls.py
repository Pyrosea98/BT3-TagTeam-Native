"""Replay current fusion MIPS code with captured resources; never launch a game."""
from pathlib import Path
import struct
import subprocess
import os
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import multiplayer_fusion as fusion
import quad_controller as pads
import guest_killfeed as feed

capture = HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/16-ready-held.bin'
ram = bytearray(capture.read_bytes())
sentinel = 0x06FE0000
for address, data in fusion.program(sentinel, pads.PAD):
    ram[address:address+len(data)] = data
# The captured solo match did not install the compact 3/4-seat text helper.
for compact in (False,True):
    address=feed.SMALL_TEXT if compact else feed.TEXT
    data=feed.text_code(compact)
    ram[address:address+len(data)]=data
data = pads.pad(sentinel)
ram[pads.PAD:pads.PAD+len(data)] = data
ram[sentinel:sentinel+8] = struct.pack('<2I', 0x03E00008, 0)
ports = [pads.RECORDS+i*pads.RECORD_STRIDE if i<2 else pads.PADS+(i-2)*pads.RECORD_STRIDE for i in range(4)]
ram[sentinel+0x100:sentinel+0x110] = struct.pack('<4I', *ports)
fixture = HERE/'power-scale-trial/codex-fusion-controls-fixture.bin'
fixture.write_bytes(ram)
runner = HERE/'repo/build/ps2xRuntime'/os.environ.get('BT3_TEST_RUNNER','ps2EntryRunner-coop-fusion-release.exe')
result = subprocess.run([str(runner), '--native-fusion-controls-self-test', str(fixture)], env=dict(os.environ,PS2X_NATIVE_UI_SLICE='1'), capture_output=True, text=True, timeout=45)
output = result.stdout+result.stderr+'\nEXIT '+str(result.returncode)+'\n'
(HERE/'power-scale-trial/codex-fusion-controls-check.log').write_text(output, encoding='utf-8')
print(output, end='')
assert result.returncode == 0

# Exercise production match teardown with the new prompt/interval/role fields.
import codex_native_rematch_rebuild as rebuild
class Client:
    def __init__(self, data): self.ram=data
    def read(self, at, size): return bytes(self.ram[at:at+size])
    def write(self, at, data): self.ram[at:at+len(data)]=data
baseline = (capture.parent/'00-original-selected-match.bin').read_bytes()
ram[fusion.CONTROL:fusion.CONTROL+32]=struct.pack('<8I',0x4D465531,0x1880000,10,3,1800,0,1800,1)
ram[fusion.ROWS:fusion.ROWS+640]=b'\x03'*640
client=Client(ram)
writes, receipt=rebuild.cave_restore_plan(client, baseline)
for address, data in writes: client.write(address, data)
rebuild.verify_caves(client, baseline)
assert client.ram[fusion.BASE:fusion.END]==baseline[fusion.BASE:fusion.END]
cleanup='PASS production cleanup restores fusion code/rows/interval/prompt/clock; preserves live services\n'
print(cleanup,end='')
with (HERE/'power-scale-trial/codex-fusion-controls-check.log').open('a',encoding='utf-8') as log: log.write(cleanup)
