"""Read a PS2 card and import its BT3 files into the native trial's folder card."""
from pathlib import Path
import hashlib, shutil, struct, time

HERE=Path(__file__).resolve().parent
CARD=HERE.parent/'experiments/.full-install/game/runtime28/memcards/Mcd001.ps2'
NAME='BASLUS-21678DBZT3'

def extract(path):
    raw=path.read_bytes()
    if not raw.startswith(b'Sony PS2 Memory Card Format '):raise ValueError('Not a PS2 card')
    page,pages,_,_,count,allocation,end,root=struct.unpack_from('<4H4I',raw,40)
    stride=len(raw)//(count*pages)
    if page!=512 or pages!=2 or stride not in (512,528):raise ValueError('Unsupported card geometry')
    size=page*pages
    ifc=struct.unpack_from('<32I',raw,80)
    def cluster(n):
        if not 0<=n<count:raise ValueError('Invalid card cluster')
        return b''.join(raw[(n*pages+i)*stride:(n*pages+i)*stride+page] for i in range(pages))
    def following(n):
        entries=size//4; fat_index=n//entries
        table=struct.unpack_from('<I',cluster(ifc[fat_index//entries]),4*(fat_index%entries))[0]
        return struct.unpack_from('<I',cluster(table),4*(n%entries))[0]
    def chain(n):
        seen=set(); result=bytearray()
        while True:
            if n in seen or not 0<=n<end:raise ValueError('Invalid card chain')
            seen.add(n);result.extend(cluster(allocation+n))
            nxt=following(n)
            if nxt==0xffffffff:return bytes(result)
            if not nxt&0x80000000:raise ValueError('Unallocated card chain')
            n=nxt&0x7fffffff
    def directory(n,entry_count=None):
        data=chain(n);rows=[]
        if entry_count is None:entry_count=struct.unpack_from('<I',data,4)[0]
        if entry_count>len(data)//512:raise ValueError('Directory length exceeds chain')
        for offset in range(0,entry_count*512,512):
            mode=struct.unpack_from('<H',data,offset)[0]
            if not mode&0x8000:continue
            length=struct.unpack_from('<I',data,offset+4)[0]
            start=struct.unpack_from('<I',data,offset+16)[0]
            name=data[offset+64:offset+96].split(b'\0',1)[0].decode('ascii')
            rows.append((name,mode,length,start))
        return rows
    matches=[row for row in directory(root) if row[0]==NAME and row[1]&0x20]
    if len(matches)!=1:raise ValueError('BT3 USA save not found on card')
    files={}
    for name,mode,length,start in directory(matches[0][3],matches[0][2]):
        if name in ('.','..') or mode&0x20:continue
        if Path(name).name!=name:raise ValueError('Unsafe card filename')
        files[name]=chain(start)[:length]
    if len(files.get(NAME,b''))!=16384:raise ValueError(f'BT3 save is not 16 KiB: {[(k,len(v)) for k,v in files.items()]}')
    return files

if __name__=='__main__':
    files=extract(CARD)
    target=HERE/'savedata'/NAME
    if target.exists():
        backup=HERE/'power-scale-trial/save-backups'/time.strftime('%Y%m%d-%H%M%S')/NAME
        shutil.copytree(target,backup)
        print('Previous native save backed up:',backup)
    target.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        (target/name).write_bytes(data)
        print(name,len(data),hashlib.sha256(data).hexdigest())
    print('Imported from',CARD,'to',target)
