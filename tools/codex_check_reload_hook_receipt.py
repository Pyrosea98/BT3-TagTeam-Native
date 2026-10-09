"""Offline hook ownership checks, including merged code spans and tampering."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import struct
import sys
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import extra_reload_stage as stage
from codex_reload_hook_receipt import capture,accepted_span

hook=stage.creator.EXT_ENTRY;source='same-match/ready.bin';manager=0x300000
parent=struct.pack('<2I',(2<<26)|(stage.creator.EXT_CODE>>2),0)
jump=struct.pack('<2I',(2<<26)|(stage.EXTENSION>>2),0)
blocks=[dict(address=at,data_hex=data.hex()) for at,data in (
    (hook,jump),(stage.ENTRY,b'payload'),(stage.EXTENSION,b'extension'),(stage.OLD_EXTENSION,parent))]
worker=SimpleNamespace(owned={'stage':dict(blocks=blocks,world={'manager':manager})})
receipt=capture(worker,source)
import autopilot
watcher=autopilot.Autopilot.__new__(autopilot.Autopilot)
watcher.reload_worker=worker;watcher.playable=source;watcher.controller_input=None
autopilot.Autopilot.reset_reload_worker(watcher)
assert watcher.reload_worker is None and watcher.native_reload_hook_receipt==receipt
baseline=bytearray(0x2FEB18);prepared=bytearray(baseline)
struct.pack_into('<I',prepared,0x2FEB14,manager)
prepared[hook:hook+8]=parent
class Client:
    def __init__(self):self.data=dict(receipt['immutable'])
    def read(self,at,length):return self.data[at][:length]
    def read_u32(self,at):assert at==stage.CONTROL+8;return manager
p=Client();at=hook-4;end=hook+12
current=bytes(prepared[at:hook])+jump+bytes(prepared[hook+8:end])
assert accepted_span(p,source,baseline,prepared,at,end,current,receipt)
assert accepted_span(p,source,baseline,prepared,at,end,bytes(prepared[at:end]),None)
assert not accepted_span(p,source,baseline,prepared,at,end,b'\xff'+current[1:],receipt)
for bad_receipt in (None,dict(receipt,source='another-match'),dict(receipt,manager=manager+4)):
    try:accepted_span(p,source,baseline,prepared,at,end,current,bad_receipt)
    except ValueError:pass
    else:raise AssertionError('Unauthenticated hook accepted')
p.data[stage.EXTENSION]=b'tampered'
try:accepted_span(p,source,baseline,prepared,at,end,current,receipt)
except ValueError:pass
else:raise AssertionError('Tampered code chain accepted')
print('PASS: exact owned hook accepted; wrong match/manager, code-chain and adjacent-byte tampering rejected')
