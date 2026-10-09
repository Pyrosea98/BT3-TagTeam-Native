"""Claude: automatic audit of the game's own character name table (read-only, PINE 28012).

While the user sits on a character-select screen (scene 0x26..0x29) the names/forms table of the
UI package is resident in RAM. This reads RAM once per select-screen visit, finds each ISO-extracted
name (roster-assets/ui-characters.json, UTF-16 with the 0xFFFE marker) in the live image, infers
the slot stride from the hits and reports, for every index 0..252, whether the game's own table
holds that name at base + index*stride. Any index where the game disagrees with the ISO order is
listed. Writes power-scale-trial/menu-names-audit.json. Never writes game memory.
"""
from pathlib import Path
import collections,json,struct,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine,native_preparation as native,extract_loading_assets as ex

ROWS=json.loads((HERE/'roster-assets/ui-characters.json').read_text(encoding='utf-8'))['ui_entries']
OUT=TRIAL/'menu-names-audit.json'
SELECT_SCENES={0x26,0x27,0x28,0x29}

def scene(p):
    mgr=p.read_u32(0x2FF10C)
    return p.read_u32(mgr+0x18) if 0x100000<=mgr<=0x7ff0000 else None

def audit(ram):
    needles=[b'\xff\xfe'+r['base_name'].encode('utf-16-le') for r in ROWS]
    hits=[]
    for i,n in enumerate(needles):
        found=[];start=0x100000
        while True:
            at=ram.find(n,start,0x2000000)
            if at<0:break
            found.append(at);start=at+2
            if len(found)>8:break
        hits.append(found)
    # stride from consecutive first hits that are close together
    diffs=collections.Counter()
    for i in range(len(hits)-1):
        for a in hits[i]:
            for b in hits[i+1]:
                if 0<b-a<4096:diffs[b-a]+=1
    if not diffs:return dict(found=sum(1 for h in hits if h),stride=None,error='no consecutive name hits')
    stride=diffs.most_common(1)[0][0]
    # base: most common (address - index*stride)
    bases=collections.Counter(a-i*stride for i,h in enumerate(hits) for a in h)
    base,votes=bases.most_common(1)[0]
    result=dict(stride=stride,base=hex(base),votes=votes,found=sum(1 for h in hits if h))
    ok=[];missing=[];moved=[]
    for i,h in enumerate(hits):
        expected=base+i*stride
        if expected in h:ok.append(i)
        elif h:moved.append(dict(index=i,name=ROWS[i]['base_name'],at=[hex(a) for a in h[:3]],expected=hex(expected)))
        else:missing.append(dict(index=i,name=ROWS[i]['base_name']))
    result.update(match=len(ok),mismatch_moved=moved,not_found=missing)
    return result


ISO_PATH=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'

def iso_portraits():
    import pycdlib
    iso=pycdlib.PyCdlib();iso.open(str(ISO_PATH))
    with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as s:
        magic,cnt=struct.unpack('<4sI',s.read(8));tab=s.read(cnt*8);off,size=struct.unpack_from('<II',tab,450*8)
        s.seek(off);raw=s.read(size)
    ui=ex.package(ex.unpack_bpe(ex.package(raw)[1]))
    return ex.package(ui[31])

def portrait_order(ram):
    """Find every ISO portrait in the live RAM by three pixel windows and report the runtime slot order."""
    portraits=iso_portraits();starts={}
    for j,pb in enumerate(portraits):
        if len(pb)<=0x900:continue
        cand=[]
        for off in (0xC0,0x400,0x800):
            a=ram.find(pb[off:off+64],0x100000,0x8000000)
            cand.append(a-off if a>=0 else None)
        if None not in cand and len(set(cand))==1:starts[j]=cand[0]
    result=dict(located=len(starts),total=len(portraits))
    if len(starts)>=8:
        items=sorted(starts.items(),key=lambda kv:kv[1])
        diffs=collections.Counter(b[1]-a[1] for a,b in zip(items,items[1:]))
        stride=diffs.most_common(1)[0][0]
        base=collections.Counter(a-j*stride for j,a in starts.items()).most_common(1)[0][0]
        perm={str(j):(a-base)//stride for j,a in starts.items() if (a-base)%stride==0}
        result.update(base=hex(base),stride=stride,iso_to_runtime_slot=perm,same=sum(1 for j,s in perm.items() if int(j)==s))
    return result

def main():
    done=set();print('menu names audit waiting for a character-select screen',flush=True)
    while True:
        try:
            with pine.PineClient(port=28012,timeout=10) as p:
                s=scene(p)
            if s in SELECT_SCENES and s not in done:
                time.sleep(3)   # let the screen finish loading its tables; the bridge drops idle connections after 2 s
                with pine.PineClient(port=28012,timeout=90) as p:
                    ram=native.read_ram(p)
                dump=TRIAL/('select-screen-ram-scene%02X.bin'%s)
                if not dump.exists():dump.write_bytes(ram)   # kept for offline portrait-table analysis
                r=audit(ram);r['scene']=hex(s);r['time']=time.strftime('%H:%M:%S')
                try:r['portraits']=portrait_order(ram)
                except Exception as error:r['portraits']=dict(error=str(error))
                OUT.write_text(json.dumps(r,indent=1),encoding='utf-8')
                print(time.strftime('%H:%M:%S'),'portraits located',r.get('portraits',{}).get('located'),'same slot',r.get('portraits',{}).get('same'),'| scene',hex(s),'matched',r.get('match'),'of 253; moved',len(r.get('mismatch_moved',[])),'not found',len(r.get('not_found',[])),'stride',r.get('stride'),flush=True)
                if r.get('match',0)>200:done.add(s)
                else:time.sleep(5)
        except (OSError,pine.PineError,struct.error) as error:
            print(time.strftime('%H:%M:%S'),'retry:',type(error).__name__,error,flush=True);time.sleep(3)
        time.sleep(2)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
