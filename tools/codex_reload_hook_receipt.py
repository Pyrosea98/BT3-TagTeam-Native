"""Authenticate one transformation-owned scratch hook at native teardown."""
import struct

def capture(worker,source):
    import extra_reload_stage as stage
    if worker is None or source is None:return None
    manifest=worker.owned.get('stage')
    if manifest is None:return None
    blocks={b['address']:b for b in manifest['blocks']}
    hook=blocks.get(stage.creator.EXT_ENTRY)
    expected=struct.pack('<2I',(2<<26)|(stage.EXTENSION>>2),0)
    if hook is None or bytes.fromhex(hook['data_hex'])!=expected:return None
    immutable=[]
    for address in (stage.ENTRY,stage.EXTENSION,stage.OLD_EXTENSION):
        block=blocks.get(address)
        if block is None:raise ValueError('Transformation hook receipt lacks its code chain')
        immutable.append((address,bytes.fromhex(block['data_hex'])))
    original=struct.pack('<2I',(2<<26)|(stage.creator.EXT_CODE>>2),0)
    if immutable[-1][1]!=original:raise ValueError('Transformation hook receipt has an unexpected parent')
    return dict(source=str(source),manager=manifest['world']['manager'],
        address=stage.creator.EXT_ENTRY,data=expected,immutable=immutable)

def validate(p,source,prepared,receipt):
    import extra_reload_stage as stage
    if receipt is None or receipt['source']!=str(source):
        raise ValueError('Transformation scratch hook has no receipt for this match')
    manager=struct.unpack_from('<I',prepared,0x2FEB14)[0]
    if receipt['manager']!=manager or p.read_u32(stage.CONTROL+8)!=manager:
        raise ValueError('Transformation scratch hook receipt belongs to another manager')
    for address,data in receipt['immutable']:
        if p.read(address,len(data))!=data:
            raise ValueError(f'Transformation scratch code changed at {address:08X}')
    return receipt['address'],receipt['data']

def accepted_span(p,source,baseline,prepared,at,end,current,receipt):
    if current in (prepared[at:end],baseline[at:end]):return True
    import extra_reload_stage as stage
    hook=stage.creator.EXT_ENTRY
    if not at<=hook or hook+8>end:return False
    expected=struct.pack('<2I',(2<<26)|(stage.EXTENSION>>2),0)
    if current[hook-at:hook-at+8]!=expected:return False
    # Every non-hook byte must still match one complete registered image.
    candidates=[]
    for image in (prepared,baseline):
        candidate=bytearray(image[at:end]);candidate[hook-at:hook-at+8]=expected
        candidates.append(bytes(candidate))
    if current not in candidates:return False
    address,data=validate(p,source,prepared,receipt)
    return address==hook and data==expected
