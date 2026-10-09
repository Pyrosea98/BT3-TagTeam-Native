"""Captured production guest planning; no game boot or live PINE connection."""
from pathlib import Path
import json,os,struct,subprocess,sys
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import cpu_tactics as tactics,mod_settings as prefs,fresh_team_combat as core
import team_start_gate as start
from prototype import Assembler
ram=bytearray((HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-201319-d7ac1d61/16-ready-held.bin').read_bytes())
assert not tactics.build_memory(ram)['blocks']
for mode in ('training','training_coop'):
    assert not tactics.build_memory(ram,settings={'cpu_transform_allies':'more_often'},battle_mode=mode)['blocks']
for key in tactics.KEYS:
    try:prefs.validate_settings({key:'invalid'})
    except ValueError:pass
    else:raise AssertionError('Invalid preference accepted')
assert all(k in prefs.ui_fields() for k in tactics.KEYS)
import localization
assert localization.tr('CPU tactics',{'language':'es'})=='Tácticas de CPU'
original=bytes(ram)
import npc_transform_policy as npc
for block in npc.build_memory(ram,settings={'npc_transform_overrides':{'1':True}})['blocks']:
    at=block['address'];data=bytes.fromhex(block['data_hex']);ram[at:at+len(data)]=data
manifest=tactics.build_memory(ram,settings={'cpu_transform_allies':'more_often','cpu_transform_enemies':'outmatched'})
for b in manifest['blocks']:
    at=b['address'];before=bytes.fromhex(b['expected_hex']);data=bytes.fromhex(b['data_hex'])
    assert ram[at:at+len(before)]==before;ram[at:at+len(data)]=data
assert tactics.END-tactics.FRAME==65536
# A deterministic continuation increments a receipt, proving it runs once.
previous=manifest['previous'];a=Assembler(previous);a.li(8,0x06FE0400);a.lw(9,8,28);a.addiu(9,9,1);a.sw(9,8,28);a.jr()
ram[previous:previous+len(a.finish())]=a.finish()
# The planner program itself is unchanged except relocation of its two native
# calls to explicit boundary stubs. Actual native calls remain installed.
eligibility=struct.unpack_from('<I',ram,tactics.CONTROL+60)[0]
initiation=struct.unpack_from('<I',ram,tactics.CONTROL+64)[0]
real=tactics.apply_code(False,eligibility,initiation);stub=bytearray(real)
for at,target in ((0x06FE3000,eligibility),(0x06FE3200,initiation)):
    needle=struct.pack('<I',(3<<26)|(target>>2));replacement=struct.pack('<I',(3<<26)|(at>>2))
    assert needle in stub;stub=stub.replace(needle,replacement)
a=Assembler(0x06FE3000);a.li(8,0x06FE0400)
for reg in (6,7):
    a.addiu(9,0,1);a.branch(5,reg,9,'bad')
a.lw(9,8,20);a.branch(4,5,9,'deny');a.lw(9,8,24);a.branch(5,9,0,'deny')
a.addiu(2,0,1);a.jr();a.label('bad');a.lw(9,8,16);a.addiu(9,9,1);a.sw(9,8,16)
a.label('deny');a.move(2,0);a.jr()
ram[a.base:a.base+len(a.finish())]=a.finish()
a=Assembler(0x06FE3200);a.li(8,0x06FE0400);a.lw(9,8);a.addiu(9,9,1);a.sw(9,8)
a.sw(4,8,8);a.sw(5,8,12);a.addiu(9,0,236);a.sw(9,4,2376);a.addiu(2,0,1);a.jr()
ram[a.base:a.base+len(a.finish())]=a.finish()
ram[tactics.APPLY:tactics.APPLY+len(stub)]=stub
ram[0x06FE5000:0x06FE5000+len(real)]=real
struct.pack_into('<4I',ram,0x06FE0200,core.MODELS,len(real),eligibility,initiation)
fixture=HERE/'power-scale-trial/codex-cpu-tactics-fixture.bin';fixture.write_bytes(ram)
runner=HERE/'repo/build/ps2xRuntime'/os.environ.get('BT3_TEST_RUNNER','ps2EntryRunner-cpu-transform-tactics.exe')
p=subprocess.run([str(runner),'--native-cpu-transform-self-test',str(fixture)],capture_output=True,text=True,timeout=60,
                 env=dict(os.environ,PS2X_NATIVE_UI_SLICE='1'))
output=p.stdout+p.stderr+'\nEXIT '+str(p.returncode)+'\n'
(HERE/'power-scale-trial/codex-cpu-tactics-check.log').write_text(output,encoding='utf-8');print(output,end='')
assert p.returncode==0
assert "[cpu-tactics] actor=" in output and "reason=successful-start" in output
assert "starts_allies=1 starts_enemies=0" in output
# Existing rematch cleanup owns every byte in the new reservation.
import codex_native_rematch_rebuild as rebuild
assert any(lo<=tactics.FRAME and tactics.END<=hi for lo,hi in rebuild.cave_ranges())
class Client:
    def read(self,at,n):return bytes(ram[at:at+n])
    def write(self,at,data):ram[at:at+len(data)]=data
client=Client()
for at,data in rebuild.cave_restore_plan(client,original)[0]:client.write(at,data)
rebuild.verify_caves(client,original)
assert ram[tactics.FRAME:tactics.END]==original[tactics.FRAME:tactics.END]
print('PASS Native defaults, Training exclusion, setting validation, EN/ES page, manifest guards and actual production rematch cleanup')
