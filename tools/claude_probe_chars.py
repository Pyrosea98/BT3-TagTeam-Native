"""Claude (workstream C): read-only live probe of how the game loads a character.

Run next to the native trial while the user plays an ordinary 1v1 with an extended
character (IDs 161-252). Polls the game's model table over PINE (port 28012) and,
for every new (slot, character, resource ids) combination, records:
- the 56-byte resource record: three (buffer, size, file id) entries plus state words;
- the first words of each buffer and whether it parses as a native PAK (count,
  ascending offsets), with the largest offset as the real size evidence;
- the heap block that owns each buffer (payload size actually allocated);
- which disc volume/index the Power Scale lookup hook maps each file id to.
Writes JSON lines to power-scale-trial/probe-chars/<time>.jsonl. Never writes game memory.
"""
from pathlib import Path
import json,struct,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine

MODELS=0x31C640
OUT=TRIAL/'probe-chars'

def lookup(file_id):
    """Power Scale hook at link 0x8C9398: ids >= 3402 -> volume 2 index id-3402, others volume 1 index id-1."""
    return dict(volume=2,index=file_id-3402) if file_id>=3402 else dict(volume=1,index=file_id-1)

def afs_entry(path,index):
    try:
        with open(path,'rb') as f:
            magic,n=struct.unpack('<4sI',f.read(8))
            if magic!=b'AFS\0' or not 0<=index<n:return None
            f.seek(8+8*index);offset,size=struct.unpack('<II',f.read(8))
            f.seek(offset);head=f.read(16)
            return dict(offset=offset,size=size,head=head.hex())
    except OSError:return None

def pak_info(p,address,limit=0x4000):
    try:data=p.read(address,min(limit,0x2000))
    except Exception:return None
    count=struct.unpack_from('<I',data)[0]
    info=dict(first_words=[hex(w) for w in struct.unpack_from('<8I',data)])
    if 0<count<=4096 and 4*(count+2)<=len(data):
        offsets=struct.unpack_from('<%dI'%(count+1),data,4)
        ok=offsets[0]>=4*(count+2) and all(a<b for a,b in zip(offsets,offsets[1:]))
        info.update(pak_count=count,pak_valid=ok,pak_end=offsets[-1],first_offsets=list(offsets[:4]))
    return info

def owner_block(p,address):
    """Walk back to an 'SHBT' heap header whose data pointer (+20) is this buffer."""
    try:data=p.read(max(0,address-0x100),0x100)
    except Exception:return None
    for off in range(0,0x100-28,4):
        if struct.unpack_from('<I',data,off)==(0x53484254,):pass
        if struct.unpack_from('<I',data,off)[0]==0x53484254:
            head=address-0x100+off
            fields=struct.unpack_from('<7I',data,off)
            if fields[5]==address:return dict(header=hex(head),used=fields[1],block_size=fields[4],payload_size=fields[6])
    return None

def snapshot(p):
    u=p.read_u32;rows=[]
    for slot in range(12):
        model=u(MODELS+4*slot)
        if not 0x100000<=model<=0x7ffe000 or u(model+16)!=slot:continue
        resource=u(model+20)
        row=dict(slot=slot,model=hex(model),character=u(model+12),visible=u(model+8),resource=hex(resource))
        if 0x100000<=resource<=0x7fffc00:
            words=struct.unpack('<14I',p.read(resource,56))
            row['record_words']=[hex(w) for w in words]
            files=[]
            for i in (0,4,8):
                ptr,size,fid=words[i],words[i+1],words[i+2]
                entry=dict(buffer=hex(ptr),size_field=size,file_id=fid,lookup=lookup(fid) if fid not in (0,0xFFFFFFFF) else None)
                if 0x100000<=ptr<=0x7fff000:
                    entry['content']=pak_info(p,ptr);entry['owner']=owner_block(p,ptr)
                files.append(entry)
            row['files']=files
        rows.append(row)
    return rows

def main():
    OUT.mkdir(exist_ok=True)
    path=OUT/(time.strftime('%Y%m%d-%H%M%S')+'.jsonl')
    seen=set();print('probing; writing',path,flush=True)
    afs={name:TRIAL.parent/'power-scale-input/DATA'/name for name in ('MOD.AFS','DLC.AFS')}
    while True:
        try:
            with pine.PineClient(port=28012,timeout=3) as p:
                for row in snapshot(p):
                    key=(row['slot'],row['character'],tuple(f['file_id'] for f in row.get('files',[])))
                    if key in seen:continue
                    seen.add(key)
                    for f in row.get('files',[]):
                        look=f.get('lookup')
                        if look and look['volume']==2:
                            f['mod_afs']=afs_entry(afs['MOD.AFS'],look['index'])
                            f['dlc_afs']=afs_entry(afs['DLC.AFS'],look['index'])
                    row['time']=time.strftime('%H:%M:%S')
                    with path.open('a',encoding='utf-8') as out:out.write(json.dumps(row)+'\n')
                    print(row['time'],'slot',row['slot'],'character',row['character'],flush=True)
        except (OSError,pine.PineError):
            time.sleep(1)
        time.sleep(.5)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
