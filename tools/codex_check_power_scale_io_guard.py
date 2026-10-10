"""Power Scale lookup-hook admission and tamper rejection, without a game."""
from pathlib import Path
import struct
import sys
from unittest.mock import patch

sandbox=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(sandbox),str(sandbox/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import extra_reload_preload as preload
from fusion_partner_lifecycle import POWER_SCALE_SIDE_TARGET
from native_map import A
import game_profile

address=A(0x2654D8);size=0x58
target=POWER_SCALE_SIDE_TARGET+(0x008C9398-0x008C8C24)
expected=bytes(range(size));native=lambda p,n:expected[:n]
ram=bytearray(max(address+size,target+16));ram[address:address+size]=expected
assert preload.native_io_helper_matches(ram,native,address,size)
ram[address:address+8]=struct.pack('<2I',(2<<26)|(target>>2),0)
ram[target:target+16]=bytes.fromhex('ff00033c00ff023cf0ffbd27ffff6334')
profile={'runtime_variant':'BT3 Power Scale BETA 1.5.1 (experimental)'}
with patch.object(game_profile,'installed',return_value=profile):
    assert preload.native_io_helper_matches(ram,native,address,size)
    for at in (address,address+4,address+8,address+size-1,target,target+15):
        ram[at]^=1
        assert not preload.native_io_helper_matches(ram,native,address,size),hex(at)
        ram[at]^=1
    assert not preload.native_io_helper_matches(ram,native,address,size-4)
with patch.object(game_profile,'installed',return_value=None):
    assert not preload.native_io_helper_matches(ram,native,address,size)
print('PASS: original helper and authenticated Power Scale hook admitted; wrong profile/size, target/header/tail tampering rejected')
