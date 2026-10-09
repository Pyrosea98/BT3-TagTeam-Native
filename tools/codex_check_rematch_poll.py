"""Offline bridge-busy recovery checks; never opens a socket."""
import sys
from types import SimpleNamespace
from unittest.mock import patch
import codex_native_rematch_rebuild as rebuild

class Watcher:
    state='MENU'
    def observe(self):return None
    def report(self,*args,**kwargs):pass

class Client:
    def __init__(self,mode,writes):self.mode,self.writes=mode,writes
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read_u32(self,address):
        if self.mode=='timeout':raise TimeoutError('timed out')
        return rebuild.MAGIC if address==rebuild.CONTROL else 2
    def write_u32(self,address,value):self.writes.append((address,value))

logs=[];writes=[];modes=['timeout','inert','inert']
def client(**kwargs):
    mode=modes.pop(0)
    instance=Client(mode,writes)
    if mode=='inert':instance.read_u32=lambda _:0
    return instance
pine=SimpleNamespace(PineClient=client,require_runtime=lambda:None)
autopilot=SimpleNamespace(Autopilot=Watcher,log=logs.append)
native=SimpleNamespace(encode=lambda manifest:(b'',0))
class Closed(RuntimeError):pass
with patch.dict(sys.modules,{'native_preparation':native,'runtime_owner':SimpleNamespace(EmulatorClosed=Closed)}):
    rebuild.install(autopilot,pine)
    watcher=Watcher()
    assert watcher.observe() is None
    assert watcher.state=='MENU' and not writes and len(logs)==1
    assert watcher.observe() is None and not writes and not modes
    modes[:]=['teardown','teardown']
    watcher.playable='unused';watcher.native_cleanup_plan='unused'
    with patch.object(rebuild,'restore_detached',side_effect=TimeoutError('uncertain cleanup')):
        try:watcher.observe()
        except RuntimeError as error:assert 'uncertain cleanup' in str(error)
        else:raise AssertionError('Uncertain cleanup was silently retried')
    assert writes==[(rebuild.CONTROL+4,5)]
    writes.clear();modes[:]=['timeout']
    pine.require_runtime=lambda:(_ for _ in ()).throw(Closed('closed during read'))
    try:watcher.observe()
    except Closed:pass
    else:raise AssertionError('Runner shutdown wrapped as rematch failure')
    assert not writes
print('PASS: busy read retries without writes; uncertain cleanup remains an explicit failure')
