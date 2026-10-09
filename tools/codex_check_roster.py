"""Offline roster checks using the actual DLC files; never connects to a game."""
from pathlib import Path
import importlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install, STAGED
install()
from codex_roster_resources import pak_extent, allocation_capacity
import selected_team_prepare as prepare
import extra_reload_preload as preload
import character_names
import guest_killfeed as feed
import npc_transform_policy as npc
import mod_settings as settings
import loading_presentation as cover


def afs_entry(stream, index):
    stream.seek(8+index*8)
    start, size = struct.unpack('<2I', stream.read(8))
    stream.seek(start)
    return stream.read(size)


def main():
    from codex_dependency_check import check_dependencies
    dependencies=check_dependencies()
    for source in STAGED.glob('*.py'):
        compile(source.read_text(encoding='utf-8'), str(source), 'exec')
        importlib.import_module(source.stem)
    ram = bytearray(0x2000000)
    capacities = (843776,1443840,845824)
    pointers = (0x400000,0x600000,0x800000)
    pool = 0x200000
    resource = pool+439276+672
    pack = lambda p, v: struct.pack_into('<I', ram, p, v)
    results = []
    with (HERE/'power-scale-input/DATA/DLC.AFS').open('rb') as stream:
        assert stream.read(4) == b'AFS\0'
        for cid, entries in ((212,(1222,1230,1234)), (192,(703,710,714)), (187,(572,580,584)),
                             (202,(962,970,974)), (204,(1014,1022,1026)), (226,(1586,1594,1598))):
            extents = []
            for i,(index,p,capacity) in enumerate(zip(entries,pointers,capacities)):
                data = afs_entry(stream,index)
                assert len(data)<=capacity
                ram[p:p+capacity] = bytes(capacity)
                ram[p:p+len(data)] = data
                header = p-64
                for offset,value in ((0,0x53484254),(4,1),(16,capacity+100),(20,p),(24,capacity)):
                    pack(header+offset,value)
                # Deliberately reproduce the extended leader's wrong size fields.
                for offset,value in ((0,p),(4,2048),(8,preload.request_files(cid,0,False)[i]),(12,0)):
                    pack(resource+16*i+offset,value)
                extents.append(pak_extent(ram,p))
                assert allocation_capacity(ram,p)==capacity
            pack(resource+48,1);pack(resource+52,0)
            row = prepare.resource_info(ram,resource,0,cid,0,pool)
            assert 0<row['draw_nodes']<=512 and row['collision_size']<=0x3800
            results.append(dict(character=cid,extents=extents,draw_nodes=row['draw_nodes']))
    # Reject an out-of-allocation terminal offset and an unowned buffer.
    p=pointers[2]; count=struct.unpack_from('<I',ram,p)[0]
    terminal=p+4*(count+1); saved=struct.unpack_from('<I',ram,terminal)[0]
    pack(terminal,capacities[2]+4)
    try: pak_extent(ram,p)
    except ValueError: pass
    else: raise AssertionError('Out-of-allocation PAK accepted')
    pack(terminal,saved);pack(p-64+4,0)
    try: pak_extent(ram,p)
    except ValueError: pass
    else: raise AssertionError('Unowned PAK accepted')
    assert len(character_names.character_table())==253
    for cid,label in ((24,'Nail[5]'),(65,'Granola[160]'),(212,'Goku Instinto Dominado[160]'),(239,'Black Freezer[160]')):
        assert character_names.character_name(cid)==label
    assert character_names.character_name(14)==character_names.character_name(17)
    assert character_names.character_info(14)['character_id']!=character_names.character_info(17)['character_id']
    assert character_names.character_info(24)['portrait_path'].endswith('199.png')
    assert character_names.character_info(202)['portrait_path'] is not None
    # Candidate-address validation and engine-keyed updates, with shuffled JSON rows.
    import tempfile
    from types import SimpleNamespace
    from unittest.mock import patch
    import codex_runtime_labels as labels
    cached=json.loads((HERE/'roster-assets/runtime-names.json').read_text(encoding='utf-8'))
    table=json.loads((HERE/'roster-assets/characters.json').read_text(encoding='utf-8'))
    captured=b''.join((b'\xff\xfe'+name.encode('utf-16-le')).ljust(64,b'\0')[:64] for name in cached['names'])
    with tempfile.TemporaryDirectory(dir=HERE/'power-scale-trial',prefix='codex-label-check-') as temporary:
        root=Path(temporary);assets=root/'roster-assets';assets.mkdir()
        (assets/'runtime-names.json').write_text(json.dumps(cached),encoding='utf-8')
        table['characters'].reverse()
        for row in table['characters']:row['name']='stale'
        manifest=assets/'characters.json';manifest.write_text(json.dumps(table),encoding='utf-8')
        with patch.object(labels,'HERE',root),patch.object(labels,'SEEN',set()):
            labels.refresh(SimpleNamespace(read=lambda *_:bytes(253*64)),SimpleNamespace(kind='character_select',manager=1,object=1))
            assert all(row['name']=='stale' for row in json.loads(manifest.read_text())['characters'])
            labels.refresh(SimpleNamespace(read=lambda *_:captured),SimpleNamespace(kind='character_select',manager=1,object=2))
            updated={row['character_id']:row['name'] for row in json.loads(manifest.read_text())['characters']}
            assert updated[24]=='Nail[5]' and updated[65]=='Granola[160]'
    synthetic=[]
    for index in range(8):
        synthetic.append(dict(source_model=0x300000,source_resource=0x310000,source_character=3,
            native_row_address=0x320000+index*164,native_row_hex=bytes(164).hex(),
            resource=0x330000+index*64,resource_flags=1,resource_handle=1,file_ids=[2000,2001,2002],
            collision=0x340000,collision_size=128,character=65,source_actor=0x350000,
            physical_id=index+2,side=index%2,slot=index//2+1,x_offset=90.0,draw_nodes=74))
    creation_bytes=len(prepare.create_code(0x1C2A30,synthetic,[0x350000,0x352000],0x360000,pool,[0,1],grow=320))
    assert creation_bytes<prepare.NATIVE_FRAME-prepare.CODE
    names,_=feed.name_data({i:character_names.character_name(i) for i in range(253)})
    assert len(names)==253*128 and feed.NAMES+len(names)<=feed.UNKNOWN<feed.END
    options=settings.validate_settings({settings.NPC_OVERRIDES_KEY:{'252':True}})
    blocks=dict(npc.configured_data(options,0x123000,4))
    assert len(blocks[npc.OVERRIDES])==253 and blocks[npc.OVERRIDES][252]==1
    assert len(blocks[npc.GIANT_TABLE])==253
    assert npc.predicate() and feed.row_code() and feed.draw_code()
    import selected_resource_queue as queue
    import extra_reload_service as io
    from codex_roster_io import transport_file_id
    assert [transport_file_id(n) for n in (3464,3472,3473)] == [0x040003F6,0x040003FE,0x04000402]
    requests=[dict(character=204,costume=0,damaged=False,file_ids=[3464,3472,3473])]
    assert len(queue.payload(requests,hold_idle=True,fast_pump=True))<queue.CONTROL-queue.CODE
    assert len(io.queue_code())<0x800
    assert len(cover.normalize_teams([dict(side=0,fighters=[212,252])])[0]['fighters'])==2
    for invalid in (-1,253,True):
        try: preload.request_files(invalid,0,False)
        except ValueError: pass
        else: raise AssertionError('Invalid roster ID accepted')
    report=dict(status='OFFLINE PASS; Claude reports tested extended matches and original 5v5 pass; mixed-roster 5v5 status173 unresolved',resources=results,
                staged_modules=len(list(STAGED.glob('*.py'))),character_labels=253,
                dlc_read_volume=4, logical_ids_preserved=True,
                dependencies=dependencies,
                creation_code_8_extras_bytes=creation_bytes,
                extended_identity_mapping='Runtime labels keyed by engine slot; reviewed 253-slot portrait permutation applied')
    (HERE/'roster-offline-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
