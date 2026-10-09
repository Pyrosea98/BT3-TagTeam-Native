"""Diagnostic stage labels; payload bytes and supplied purposes stay intact."""
def label_manifest(manifest,stage):
    for block in manifest.get('blocks',[]):
        if not block.get('purpose'):
            address=block.get('address',0)
            length=len(block.get('data_hex',''))//2
            block['purpose']=f'{stage}: guest write at 0x{address:08X}, {length} bytes'
