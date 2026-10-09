"""Offline production clock execution; no game launch."""
from pathlib import Path
import os,struct,subprocess,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import fusion_duration as timer
import guest_killfeed as feed
import fresh_team_combat as core
import body_swap as body
ram=bytearray((HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/16-ready-held.bin').read_bytes())
for address,data in ((timer.TICK,timer.tick()),(feed.ROW,feed.row_code())):
    ram[address:address+len(data)]=data
struct.pack_into('<3I',ram,0x06FE0100,core.MODELS,body.FINISHED,core.PAIR+4)
fixture=HERE/'power-scale-trial/codex-fusion-form-fixture.bin'
fixture.write_bytes(ram)
runner=HERE/'repo/build/ps2xRuntime'/os.environ.get('BT3_TEST_RUNNER','ps2EntryRunner-fusion-form-life.exe')
p=subprocess.run([str(runner),'--native-fusion-form-self-test',str(fixture)],capture_output=True,text=True,timeout=45,env=dict(os.environ,PS2X_NATIVE_UI_SLICE='1'))
output=p.stdout+p.stderr+'\nEXIT '+str(p.returncode)+'\n'
(HERE/'power-scale-trial/codex-fusion-form-check.log').write_text(output,encoding='utf-8')
print(output,end='');assert p.returncode==0

import codex_native_rematch_rebuild as rebuild
class Client:
    def __init__(self,data):self.ram=data
    def read(self,at,n):return bytes(self.ram[at:at+n])
    def write(self,at,data):self.ram[at:at+len(data)]=data
baseline=(HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/00-original-selected-match.bin').read_bytes()
struct.pack_into('<6I',ram,timer.RECORDS+104,241,123456,219,131072,30,0x464F5231)
client=Client(ram)
for at,data in rebuild.cave_restore_plan(client,baseline)[0]:client.write(at,data)
rebuild.verify_caves(client,baseline)
assert ram[timer.RECORDS:timer.RECORDS+10*timer.STRIDE]==baseline[timer.RECORDS:timer.RECORDS+10*timer.STRIDE]
assert ram[timer.CAPTURE:timer.END]==baseline[timer.CAPTURE:timer.END]
line='PASS production match cleanup clears form life/rate/grace/mapping code before next match\n'
print(line,end='')
with (HERE/'power-scale-trial/codex-fusion-form-check.log').open('a',encoding='utf-8') as log:log.write(line)
