"""Offline native bulk transport/framing and import bootstrap checks."""
import importlib
from pathlib import Path
import struct
import sys
from codex_native_bulk_snapshot import read_ranges,CHUNK,RAM_BYTES

class Client:
    calls=[]
    def _exchange(self,command,expected):
        assert len(command)==9 and command[0]==16
        address,length=struct.unpack('<2I',command[1:])
        assert length==expected and 0<length<=CHUNK and address+length<=RAM_BYTES
        self.calls.append((address,length))
        return bytes([address//CHUNK])*length

p=Client();result=read_ranges(p,CHUNK+23)
assert type(result) is bytes and result==bytes(CHUNK)+bytes([1])*23
assert p.calls==[(0,CHUNK),(CHUNK,23)]
for bad in (0,-1,True,RAM_BYTES+1):
    try:read_ranges(p,bad)
    except ValueError:pass
    else:raise AssertionError('Invalid capture accepted')
class Short:
    def _exchange(self,*args):return b''
try:read_ranges(Short(),1)
except ValueError:pass
else:raise AssertionError('Short reply accepted')

# Verify actual original module keeps its source path and all hold/apply logic.
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here/'power-scale-trial/controller/game/tools'))
from codex_bulk_snapshot_trial import Finder
sys.meta_path.insert(0,Finder())
native=importlib.import_module('native_preparation')
from codex_native_bulk_snapshot import read_ram
assert native.read_ram is read_ram
assert Path(native.__file__).resolve()==(here/'power-scale-trial/controller/game/tools/native_preparation.py').resolve()
assert callable(native.quiet) and callable(native.apply) and callable(native.resume)
print('PASS: bounded chunks, byte parity, short reply rejection, original module hold/apply preserved')
