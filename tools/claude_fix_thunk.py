"""EXPERIMENT (Claude): repoint the one unrelocated Power Scale call to the relocated module entry.

relocate_power_scale.relocate() leaves exactly one j/jal into the old link range:
module+0x27c8 `jal 0x8c6bc0` (the link-time module entry, base 0x8c69c0 + 0x200).
With the module relocated to BASE, that call must target BASE+0x200.
This script waits for the native runner's bridge, checks the word, rewrites it
over PINE and reads it back. It touches nothing else. Run it after the game starts.
"""
from pathlib import Path
import struct,sys,time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
import pine

LINK_BASE=0x8c69c0
THUNK_OFFSET=0x27c8
ENTRY_OFFSET=0x200
BASE=int(sys.argv[1],16) if len(sys.argv)>1 else 0x8ca9c0

def jal(target):return (3<<26)|((target&0x0fffffff)>>2)

def main():
    address=BASE+THUNK_OFFSET
    old=jal(LINK_BASE+ENTRY_OFFSET);new=jal(BASE+ENTRY_OFFSET)
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        try:
            with pine.PineClient(port=28012,timeout=5) as p:
                # The module is relocated after boot; wait until the thunk holds the expected word.
                current=p.read_u32(address)
                if current==new:
                    print(f'{address:08x} already {new:08x}');return 0
                if current==old:
                    p.write_u32(address,new)
                    ok=p.read_u32(address)==new
                    print(f'{address:08x}: {old:08x} -> {new:08x} readback={"ok" if ok else "FAILED"}',flush=True)
                    return 0 if ok else 1
        except (OSError,pine.PineError):pass
        time.sleep(.5)
    print('Timed out waiting for the expected thunk word');return 2

if __name__=='__main__':raise SystemExit(main())
