from pathlib import Path
import tempfile,json,gzip,hashlib,zlib,sys
from importer import import_game
def sha(b):return hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory()as d:
    root=Path(d);iso=root/'input.iso';before=b'original-resource'+b'\x00'*120;iso.write_bytes(before)
    bundle=root/'bundle';(bundle/'import-data/deltas').mkdir(parents=True)
    target=b'updated-resource'+b'\x01'*110+b'longer-data'
    delta=(int.from_bytes(before[:len(target)],'little')^int.from_bytes(target,'little')).to_bytes(len(target),'little');compressed=zlib.compress(delta)
    patch=bundle/'import-data/deltas/one.xor.z';patch.write_bytes(compressed)
    copy=dict(path='pzs3us1/00000.bin',variants=['normal','2x'],bytes=len(before),sha256=sha(before),sources={'test':dict(offset=0,bytes=len(before))})
    changed=dict(path='mods/pzs3us1/00000.bin',variants=['2x'],bytes=len(target),sha256=sha(target),sources={'test':dict(offset=0,bytes=len(before),base_sha256=sha(before),patch=dict(file=patch.name,bytes=len(compressed),sha256=sha(compressed)))})
    manifest=dict(schema=1,sources=[dict(id='test',sha256=sha(before),bytes=len(before))],files=[copy,changed])
    def store():
        with gzip.open(bundle/'import-data/content.json.gz','wt')as f:json.dump(manifest,f)
        (bundle/'release-profile.json').write_text(json.dumps(dict(content_manifest_sha256=sha((bundle/'import-data/content.json.gz').read_bytes()))))
    store();a=import_game(iso,root/'normal',bundle,'normal');assert a['files']==1 and not(root/'normal/mods').exists()
    assert(root/'normal/pak3us1/00000.bin').read_bytes()==before,'archive alias broke on atomic final rename'
    b=import_game(iso,root/'twice',bundle,'2x');assert(root/'twice/mods/pzs3us1/00000.bin').read_bytes()==target
    try:import_game(iso,root/'normal',bundle)
    except ValueError:pass
    else:raise AssertionError('overwrote existing data')
    try:import_game(iso,root/'cancelled',bundle,cancel=lambda:True)
    except InterruptedError:pass
    else:raise AssertionError('ignored cancellation')
    assert not list(root.glob('cancelled*'))
    copy['path']='../escape';store()
    try:import_game(iso,root/'unsafe',bundle)
    except ValueError:pass
    else:raise AssertionError('accepted traversal')
    assert not(root/'escape').exists();copy['path']='pzs3us1/00000.bin';copy['sources']['test']['bytes']=9999;store()
    try:import_game(iso,root/'bad-bounds',bundle)
    except ValueError:pass
    else:raise AssertionError('accepted out-of-bounds read')
    assert not list(root.glob('bad-bounds*'))
print('PASS real importer: normal/2x variant separation, changed-length binary patch, existing data protection, cancellation cleanup, traversal and bounds rejection')
