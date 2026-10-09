"""Replay actual co-op ownership metadata; no socket, runner or state load."""
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import codex_native_rematch_rebuild as rebuild

source=HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261007-212806-5d5a93ff/16-ready-held.bin'
plan=rebuild.ownership_plan(source)
layout=(rebuild.SCENE_LAYOUT,rebuild.SCENE_LAYOUT+4,False)
assert layout in plan[2]
assert struct.unpack_from('<I',plan[0],layout[0])[0]==0
assert struct.unpack_from('<I',plan[1],layout[0])[0]==1
class Boundary:
    def __init__(self,state=2,attached=False):
        self.state,self.attached=state,attached
        self.memory={rebuild.SCENE_LAYOUT:struct.pack('<I',1)}
        self.writes=[]
    def read_u32(self,address):
        if address==rebuild.CONTROL:return rebuild.MAGIC
        if address==rebuild.CONTROL+4:return self.state
        return int(self.attached) if address in rebuild.PARENTS else 0
    def read(self,address,length):return self.memory.get(address,bytes(length))
    def write(self,address,data):self.memory[address]=data;self.writes.append(address)
    def write_u32(self,address,value):self.write(address,struct.pack('<I',value))
with tempfile.TemporaryDirectory(prefix='coop-detach-',dir=HERE/'power-scale-trial') as temp:
    native=SimpleNamespace(CONTROL=0x0768F000,MAGIC=0x12345678)
    with patch.dict(sys.modules,{'native_preparation':native}), \
            patch.object(rebuild,'packet_arena_restore',return_value=(0x400000,bytes(28),{})), \
            patch.object(rebuild,'cave_restore_plan',return_value=([],{})), \
            patch.object(rebuild,'verify_caves'):
        for state,attached in ((1,False),(2,True)):
            client=Boundary(state,attached)
            try:rebuild.restore_detached(client,Path(temp)/source.name,(plan[0],plan[1],[layout]))
            except ValueError:pass
            else:raise AssertionError('Layout restored before acknowledged native detach')
            assert not client.writes
        client=Boundary()
        rebuild.restore_detached(client,Path(temp)/source.name,(plan[0],plan[1],[layout]))
        assert client.read(rebuild.SCENE_LAYOUT,4)==bytes(4)
print('PASS: actual 2-human 2v3 checkpoint classifies exact split-layout word; production cleanup restores baseline 0 only after detach')
del plan

logs=[];writes=[]
obs=SimpleNamespace(manager=0x123456,loop=1,team_mode=1,result_flags=0,return_flags=0)
class Watcher:
    state='ACTIVE'
    def observe(self):return obs
    def report(self,*args,**kwargs):pass
class Client:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read_u32(self,address):return 0
    def read(self,address,length):return bytes(length)
    def write(self,address,data):writes.append((address,data))
    def write_u32(self,address,value):writes.append((address,value))
pine=SimpleNamespace(PineClient=lambda **kw:Client(),require_runtime=lambda:None)
autopilot=SimpleNamespace(Autopilot=Watcher,log=logs.append,
                        menu_return=SimpleNamespace(return_destination=lambda *args:None))
with patch.dict(sys.modules,{'native_preparation':SimpleNamespace(encode=lambda manifest:(b'',0))}):
    rebuild.install(autopilot,pine)
    watcher=Watcher();watcher.playable=source
    assert watcher.observe() is obs
    assert writes[-1]==(rebuild.CONTROL+4,1) and watcher.native_armed_source==source
    assert layout in watcher.native_cleanup_plan[2]
    print('PASS: actual controller observation arms clean rematch for the reproduced co-op checkpoint')
    del watcher.native_cleanup_plan

    # Hard links are read-only fixtures here; only copied JSON is changed.
    with tempfile.TemporaryDirectory(prefix='coop-ownership-',dir=HERE/'power-scale-trial') as temp:
        root=Path(temp)
        for name in ('00-original-selected-match.bin','16-ready-held.bin'):
            try:os.link(source.parent/name,root/name)
            except PermissionError:shutil.copy2(source.parent/name,root/name)
        for path in source.parent.glob('*.json'):shutil.copy2(path,root/path.name)
        (root/'unknown.json').write_text(json.dumps({'blocks':[{'address':0x331DF0,'data_hex':'00000000'}]}),encoding='utf-8')
        unknown_source=root/source.name
        try:rebuild.ownership_plan(unknown_source)
        except ValueError as error:assert '00331DF0..00331DF4' in str(error)
        else:raise AssertionError('Offline classifier accepted an unknown scene word')
        writes.clear();logs.clear()
        watcher=Watcher();watcher.playable=unknown_source
        assert watcher.observe() is obs and watcher.state=='ACTIVE' and not writes
        receipt=json.loads((root/'native-rematch-unclassified.json').read_text(encoding='utf-8'))
        assert receipt['unclassified'][0]['address']==0x331DF0
        assert receipt['unclassified'][0]['observed_hex']=='00000000'
        assert 'checkpoint' in receipt
        assert watcher.observe() is obs and len(logs)==1 and not writes
        print('PASS: unknown live write keeps match ACTIVE, captures state once, never arms partial cleanup; offline remains strict')
        watcher=Watcher();watcher.playable=unknown_source
        with patch.object(rebuild,'record_unclassified',side_effect=OSError('fixture')):
            assert watcher.observe() is obs and watcher.state=='ACTIVE' and not writes
        print('PASS: diagnostic file failure also leaves the current match running')
