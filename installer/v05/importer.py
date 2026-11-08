"""Portable, authenticated ISO-to-loose-data import for Tag Team v0.4.1."""
from pathlib import Path,PurePosixPath
import argparse,gzip,hashlib,json,os,shutil,time,uuid,zlib


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def child(root,name):
    p=PurePosixPath(name)
    if p.is_absolute()or not p.parts or any(s in ('..','.')or':'in s or'\\'in s for s in p.parts):raise ValueError('Unsafe content path')
    out=root.joinpath(*p.parts)
    if root.resolve()not in out.resolve().parents:raise ValueError('Content escapes its destination')
    return out

def archive_aliases(stage,final_root):
    """Preserve both archive names without duplicating game files on NTFS."""
    aliases=[]
    for alias,target in [('pak3us1','pzs3us1'),('pak3us2','pzs3us2'),('pzs3us3','pak3us3'),('pzs3us4','pak3us4')]:
        current=stage/target;link=stage/alias
        if not current.is_dir()or link.exists():continue
        try:
            if os.name=='nt':
                import _winapi
                _winapi.CreateJunction(str((final_root/target).resolve()),str(link.resolve()))
            else:os.symlink(target,link,target_is_directory=True)
            aliases.append(dict(path=alias,target=target,method='directory-alias'))
        except (OSError,AttributeError):
            shutil.copytree(current,link);aliases.append(dict(path=alias,target=target,method='copy-fallback'))
    return aliases

def import_game(iso,output,bundle,maps='2x',report=lambda *a:None,cancel=lambda:False):
    iso=Path(iso);output=Path(output);bundle=Path(bundle)
    if maps not in ('normal','2x'):raise ValueError('Choose normal or 2x maps')
    if output.exists():raise ValueError('Game data already exists; existing progress is preserved')
    profile=json.loads((bundle/'release-profile.json').read_text())
    manifest_file=bundle/'import-data/content.json.gz'
    if digest(manifest_file)!=profile['content_manifest_sha256']:raise ValueError('Installer content manifest failed verification')
    with gzip.open(manifest_file,'rt',encoding='utf-8')as f:manifest=json.load(f)
    if manifest.get('schema')!=1 or not 1<=len(manifest['files'])<=120000:raise ValueError('Invalid content manifest')
    report(0,'Checking your ISO')
    source_hash=digest(iso);source=next((s for s in manifest['sources']if s['sha256']==source_hash and s['bytes']==iso.stat().st_size),None)
    if not source:raise ValueError('Unsupported ISO. Use original Power Scale BETA 8, or the compatible R4 normal/2x image listed in the manual.')
    selected=[r for r in manifest['files']if maps in r['variants']];names=[r['path'].casefold()for r in selected]
    if len(names)!=len(set(names)):raise ValueError('Duplicate content path')
    output.parent.mkdir(parents=True,exist_ok=True)
    needed=sum(r['bytes']for r in selected)+(1<<30)
    if shutil.disk_usage(output.parent).free<needed:raise ValueError('Not enough free disk space for the selected game data')
    temp=output.with_name(output.name+'.partial-'+uuid.uuid4().hex);temp.mkdir(exist_ok=False)
    started=time.time();total=sum(r['bytes']for r in selected);done=0;validated=set()
    try:
        with iso.open('rb')as src:
            for i,row in enumerate(selected):
                if cancel():raise InterruptedError('Import cancelled')
                dst=child(temp,row['path']);dst.parent.mkdir(parents=True,exist_ok=True);plan=row['sources'][source['id']]
                at=plan['offset'];size=plan['bytes']
                if not isinstance(at,int)or not isinstance(size,int)or at<0 or size<0 or at+size>source['bytes']:raise ValueError('Invalid ISO read bounds')
                src.seek(at);h=hashlib.sha256()
                if 'patch'in plan:
                    if size>128<<20 or row['bytes']>128<<20:raise ValueError('Patch exceeds bounded resource size')
                    before=src.read(size)
                    if len(before)!=size or hashlib.sha256(before).hexdigest()!=plan['base_sha256']:raise ValueError('Source resource changed')
                    patch=plan['patch'];p=child(bundle/'import-data/deltas',patch['file'])
                    if patch['bytes']>64<<20 or p.stat().st_size!=patch['bytes']:raise ValueError('Invalid patch size')
                    if p.name not in validated:
                        if digest(p)!=patch['sha256']:raise ValueError('Resource patch failed verification')
                        validated.add(p.name)
                    decoder=zlib.decompressobj();delta=decoder.decompress(p.read_bytes(),row['bytes']+1)
                    if len(delta)!=row['bytes']or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:raise ValueError('Invalid resource delta length')
                    result=(int.from_bytes(delta,'little')^int.from_bytes(before[:len(delta)],'little')).to_bytes(len(delta),'little')
                    if len(result)!=row['bytes']:raise ValueError('Patched resource size mismatch')
                    h.update(result);dst.write_bytes(result)
                else:
                    if size!=row['bytes']:raise ValueError('Copy size mismatch')
                    with dst.open('xb')as f:
                        left=size
                        while left:
                            if cancel():raise InterruptedError('Import cancelled')
                            block=src.read(min(left,8<<20))
                            if not block:raise ValueError('Truncated ISO')
                            f.write(block);h.update(block);left-=len(block)
                if h.hexdigest()!=row['sha256']:raise ValueError('Reconstructed resource failed verification: '+row['path'])
                done+=row['bytes']
                if i%150==0 or i+1==len(selected):report(5+int(94*done/max(1,total)),'Preparing game data: '+str(i+1)+' / '+str(len(selected)))
        aliases=archive_aliases(temp,output)
        receipt=dict(version='0.4.1',source_iso_sha256=source_hash,map_size=maps,files=len(selected),bytes=done,manifest_sha256=profile['content_manifest_sha256'],archive_aliases=aliases,verified=True,seconds=time.time()-started)
        (temp/'import-receipt.json').write_text(json.dumps(receipt,indent=2));os.rename(temp,output);report(100,'Ready');return receipt
    except BaseException:
        assert temp.resolve().parent==output.resolve().parent and temp.name.startswith(output.name+'.partial-')
        if temp.exists():shutil.rmtree(temp)
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--iso',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--maps',choices=['normal','2x'],default='2x');a=p.parse_args()
    print(json.dumps(import_game(a.iso,a.output,a.bundle,a.maps,lambda percent,label:print(json.dumps(dict(percent=percent,label=label)),flush=True)),indent=2))
