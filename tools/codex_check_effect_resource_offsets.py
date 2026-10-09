"""Regression for actual expanded Goku Black resource table; no game boot."""
import json,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path[:0]=[str(root),str(root/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import extra_generic_effects as effects
capture=root/'power-scale-trial/controller/game/analysis/prepared-states/20261008-143656-2f99719d'
ram=(capture/'current-ee.bin').read_bytes()
u=lambda at:struct.unpack_from('<I',ram,at)[0]
actors=json.loads((capture/'ai-installation.json').read_text(encoding='utf-8'))['config']['actors']
backwards=[]
for actor in actors:
    model=actor['model'];resource=u(model+88)
    assert u(resource)==11
    for k in range(1,12):
        offset=u(resource+4*k)
        target=effects.effect_resource_target(resource,offset,len(ram))
        if offset&0x80000000:
            backwards.append((u(model+12),k,target))
            assert target==resource-0x2600
assert backwards==[(67,10,0xF961C0),(67,11,0xF961C0),(67,10,0xF961C0),(67,11,0xF961C0)]
# The real leaf clears2 low tag bits and performs ADDU in its return delay slot.
assert effects.NATIVE(effects.A(0x12CD64),20)==struct.pack('<5I',0x8CA30000,0x00031882,0x00031880,0x03E00008,0x00431021)
for resource,offset in [(0x100000,0xFFF00000),(0x7FFFFF0,16),(0xF987C0,0x80000000)]:
    try:effects.effect_resource_target(resource,offset,len(ram))
    except ValueError:pass
    else:raise AssertionError('Out-of-RAM target admitted')
assert effects.effect_resource_target(0xF987C0,0xFFFFDA03,len(ram))==0xF961C0
print('PASS all66 captured roster effect targets; Goku Black backward/tagged offsets; actual native ADDU opcodes; corrupt targets still rejected')

# Failure cleanup reverted the core ownership flag/count. Reapply the saved
# install journals and restore those explicit held-state words for an offline
# manifest replay; do not claim this is an untouched AI-ready capture.
held=bytearray(ram)
for filename in ('11-combat-engine.json','ai-installation.json'):
    for block in json.loads((capture/filename).read_text(encoding='utf-8'))['blocks']:
        at=block['address'];data=bytes.fromhex(block['data_hex'])
        held[at:at+len(data)]=data
struct.pack_into('<4I',held,effects.core.MODE,1,6,u(effects.core.ACTORS),6)
manifest=effects.build_memory(held)
assert len(manifest['blocks'])==64
print('PASS generic-effect pool manifest for recovered held failed3v2 capture (64 blocks); ownership reconstructed from install journals')
