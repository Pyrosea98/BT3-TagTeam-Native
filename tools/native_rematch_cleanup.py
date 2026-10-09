"""Capture a held rematch and inventory allocations before enabling cleanup."""
import json
from pathlib import Path
import struct


def hud_inventory(ram):
    """Bound the native renderer's child traversal without executing callbacks."""
    u=lambda address:struct.unpack_from('<I',ram,address)[0]
    valid=lambda address,size:0x100000<=address<=len(ram)-size and address%4==0
    owner=u(0x2feb3c)
    result=dict(owner=owner,roots=[],nodes=[],issues=[])
    if not valid(owner,28):return result
    result['roots']=[u(owner+offset) for offset in range(0,28,4)]
    visited=set();active=set()
    def visit(node,depth):
        if node in active:
            result['issues'].append(dict(kind='cycle',node=node));return
        if node in visited:return
        if depth>128 or len(visited)>=4096:
            result['issues'].append(dict(kind='traversal_bound',node=node));return
        if not valid(node,48):
            result['issues'].append(dict(kind='invalid_node',node=node));return
        visited.add(node);active.add(node)
        flags,count,children=u(node),u(node+40),u(node+44)
        result['nodes'].append(dict(address=node,flags=flags,children=count,child_array=children))
        # Native 2188B8 returns immediately for disabled nodes.
        if not flags&1 and count:
            if count>4096 or not valid(children,count*4):
                result['issues'].append(dict(kind='invalid_children',node=node))
            else:
                for index in range(count):visit(u(children+index*4),depth+1)
        active.remove(node)
    for root in result['roots']:
        if root:visit(root,0)
    return result


def inventory(ram):
    u=lambda address:struct.unpack_from('<I',ram,address)[0]
    valid=lambda address,size:0x100000<=address<=len(ram)-size and address%4==0
    manager=u(0x2feb14)
    result=dict(manager=manager,mode=u(0xd8080),heap_bounds=[u(0x2ff084),u(0x2ff08c)],models=[])
    if valid(manager,32):result['manager_words']=list(struct.unpack_from('<8I',ram,manager))
    for slot in range(12):
        model=u(0x31c640+slot*4)
        if not valid(model,0x1670) or u(model+16)!=slot:continue
        result['models'].append(dict(slot=slot,address=model,visible=u(model+8),character=u(model+12),
            resource=u(model+20),backing=u(model+5728),fx_node=u(model+5732),shader_node=u(model+5736)))
    start,end=result['heap_bounds']
    blocks=[]
    if (start,end)==(0x2000000,0x6000000):
        at=start
        for _ in range(4096):
            if at==end:break
            if at>end-32 or u(at)!=0x53484254:
                raise ValueError(f'Heap block signature changed at {at:08x}')
            size=u(at+16)
            if size<32 or size%4 or at+size>end or u(at+size-4)!=size:
                raise ValueError(f'Heap block bounds changed at {at:08x}')
            blocks.append(dict(header=at,size=size,used=u(at+4),data=u(at+20),payload_size=u(at+24)))
            at+=size
        if at!=end:raise ValueError('Heap chain exceeds the bounded inventory')
    result['heap_blocks']=blocks
    result['used_blocks']=sum(bool(b['used']) for b in blocks)
    result['used_bytes']=sum(b['size'] for b in blocks if b['used'])
    result['hud']=hud_inventory(ram)
    pool=u(0x2fec44)
    result['graphics_pool']=pool
    result['model_lists']=[]
    if valid(pool,439084):
        for name,offset in (('fx',397776),('shader',439072)):
            head,tail,count=struct.unpack_from('<3I',ram,pool+offset)
            record=dict(kind=name,head=head,tail=tail,count=count,nodes=[],issues=[])
            node=head;seen=set()
            while node:
                if node in seen or not valid(node,4) or len(seen)>=4096:
                    record['issues'].append(dict(kind='invalid_chain',node=node));break
                seen.add(node);record['nodes'].append(node);node=u(node)
            if len(seen)!=count or (record['nodes'] and record['nodes'][-1]!=tail):
                record['issues'].append(dict(kind='list_metadata_mismatch'))
            record['extended_nodes']=[p for p in record['nodes'] if start<=p<end]
            result['model_lists'].append(record)
    return result


def restore_patches(report, pine):
    """Return preparation code hooks to the clean selected-match bytes.

    Only ranges whose current bytes still equal the audited post-reset bytes are
    written, under the preparation hold. Anything else is left alone and reported.
    """
    import native_preparation as native
    restored=skipped=0
    with pine.PineClient(timeout=10) as p:
        native.quiet(p,timeout=5)
        try:
            for item in report['low_memory_restore_candidates']:
                at=item['address'];expected=bytes.fromhex(item['expected_hex']);original=bytes.fromhex(item['original_hex'])
                if p.read(at,len(expected))!=expected:
                    skipped+=1;continue
                p.write(at,original)
                if p.read(at,len(original))!=original:
                    raise RuntimeError(f'Hook restore readback failed at {at:08x}')
                restored+=1
        finally:
            native.resume(p)
    return restored,skipped


def audit(watcher, pine):
    import native_preparation as native
    source=Path(watcher.playable)
    destination=source.parent/'native-rematch-audit'
    destination.mkdir(exist_ok=True)
    with pine.PineClient(timeout=10) as p:
        try:
            native.quiet(p,timeout=5)
            manager=p.read_u32(0x2feb14)
            if (not 0x100000<=manager<=0x7ffffe0 or manager%4 or
                    p.read_u32(0xd8080)!=0 or manager!=p.read_u32(native.CONTROL+24) or
                    p.read_u32(manager)!=2):
                raise ValueError('Native rematch ownership changed during capture')
            ram=native.read_ram(p)
        finally:
            native.resume(p)
    (destination/'after-native-reset.bin').write_bytes(ram)
    report=dict(status='AUDIT ONLY: no allocations freed or heap reset',after=inventory(ram),
                before=inventory(source.read_bytes()),low_memory_restore_candidates=[],untouched_game_data=True)
    baseline=next(source.parent.glob('*original-selected-match.bin')).read_bytes()
    # Deduplicate code ranges across stages. Expected bytes come from the
    # observed reset, original bytes from this match's own clean capture.
    ranges=set()
    for path in source.parent.glob('*.json'):
        document=json.loads(path.read_text())
        for block in document.get('blocks',[]):
            at=block.get('address');data=block.get('data_hex')
            if isinstance(at,int) and isinstance(data,str) and 0x100000<=at<0x400000:
                ranges.add((at,len(bytes.fromhex(data))))
    for at,size in sorted(ranges):
        if ram[at:at+size]!=baseline[at:at+size]:
            report['low_memory_restore_candidates'].append(dict(address=at,size=size,
                expected_hex=ram[at:at+size].hex(),original_hex=baseline[at:at+size].hex()))
    (destination/'ownership.json').write_text(json.dumps(report,indent=2)+'\n')
    return destination,report
