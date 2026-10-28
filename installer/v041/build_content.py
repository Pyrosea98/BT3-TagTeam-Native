"""Build authenticated file-level COPY/bsdiff recipes, never bundle an ISO/AFS."""
from pathlib import Path
import sys,hashlib,json,gzip,struct,bisect,os,time,zlib
W=Path('F:/BT3-Builds/Tag Team Mod Installer 2');B=Path('F:/BT3-Builds');OUT=B/'pc-release-v041';P=OUT/'payload'
sys.path[:0]=[str(OUT/'builder-deps'),str(W/'native-port')]

from qwen_iso_identity_diff import parse_volume
G=B/'Tenkaichi3Decomp-content/beta8-native-profile/gamedata';P.mkdir(parents=True,exist_ok=True);R=P/'import-data';R.mkdir(exist_ok=True);(R/'deltas').mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def canon(path):
 for i in (1,2):path=path.replace('pak3us'+str(i)+'/', 'pzs3us'+str(i)+'/')
 return path
sources=[('original',W/'experiments/ISO niveles de poder BETA 8.ISO','f4afdfd366e376e0e8b813729aa7a8b103fca4e7b88a338ee3ad32cca16639f1'),('r4-2x',W/'native-port/random-select-patch/BETA8-native-r4-2x-random-38-stages-r4-gokugohan.iso','258d8b943c9e2b646ce87c77c26534bf6a22339d2727a1b8dd59c99b449a0a92'),('r4-normal',W/'native-port/random-select-patch/BETA8-native-r4-normal-random-38-stages-r4-gokugohan.iso','3039ac351ad07079d78d17dca6e6aa3a4aec40c60d3aeb47bda8cbb1520cb8f1')]
indices={};streams={};meta=[]
for sid,path,digest in sources:
 assert hashfile(path)==digest,('source identity',path);_,vol=parse_volume(path);idx={};f=path.open('rb');streams[sid]=f
 dirs={v['path']for v in vol if v.get('is_dir')}
 for entry in vol:
  name=entry['path'];at=entry['lba']*2048;n=entry['size']
  if name in dirs:continue
  if name.endswith('.AFS'):
   f.seek(at);magic,count=struct.unpack('<4sI',f.read(8));assert magic==b'AFS\0'and 0<count<100000
   rows=f.read(count*8)
   for i in range(count):
    offset,size=struct.unpack_from('<II',rows,i*8);assert offset+size<=n
    idx[canon(Path(name).stem.lower()+'/'+f'{i:05d}.bin')]=(at+offset,size)
  else:idx['disc/'+name]=(at,n)
 indices[sid]=idx;meta.append(dict(id=sid,sha256=digest,bytes=path.stat().st_size))
 print('Indexed',sid,len(idx),flush=True)
catalog=json.loads((G.parent/'extraction-catalog.json').read_text());baseline={canon(row['path']):row for row in catalog['records']}
orig=streams['original'];originalIndex=indices['original'];byhash={};sizes=[]
for path,(at,n) in originalIndex.items():
 orig.seek(at);data=orig.read(n);assert len(data)==n;byhash.setdefault((n,sha(data)),(at,n));sizes.append((n,at))
sizes.sort();print('Original resources indexed by digest',len(byhash),flush=True)
maps=json.loads((G.parent/'maps-v4-installation.json').read_text());mapOverrides={row['path'].replace('\\','/')for row in maps['files']}
oldMaps=json.loads((W/'native-port/installer/v04/import-data/beta8-maps.json').read_text());normalMap={}
for row in oldMaps['patches']:
 orig.seek(row['source_offset']);a=orig.read(row['length']);assert sha(a)==row['before_sha256']
 for key,(at,n) in originalIndex.items():
  if at==row['source_offset']and n==row['length']:normalMap[key]=a;break
assert len(normalMap)==56
targets=[]
for folder in ['pak3us1','pak3us2','pak3us3','pak3us4','disc','beta8','game-text','tagteam-ui','mods']:
 for path in sorted((G/folder).rglob('*')):
  if not path.is_file()or any('backup'in x.lower()for x in path.relative_to(G).parts):continue
  rel=canon(path.relative_to(G).as_posix())
  targets.append((rel,path,['2x']if rel in mapOverrides else['normal','2x'],None))
  if rel in normalMap:targets[-1]=(rel,path,['2x'],None);targets.append((rel,path,['normal'],normalMap[rel]))
assert len({p for p,_,_,_ in targets})>81000
records=[];cached={};patchcount=0;copied=0;began=time.time()
cache=OUT/'content-build-cache.json'
if cache.exists():cached=json.loads(cache.read_text())
def read(sid,span):
 at,n=span;f=streams[sid];f.seek(at);data=f.read(n);assert len(data)==n;return data
for k,(rel,path,variants,override)in enumerate(targets):
 desired=override if override is not None else path.read_bytes();want=sha(desired);plans={}
 # JSON files here are provenance/metadata, not scripts. Replace developer
 # locations with a portable label, while preserving binary routing tables.
 if path.suffix=='.json':
  try:
   def portable(x):
    if isinstance(x,dict):return {a:portable(b)for a,b in x.items()}
    if isinstance(x,list):return [portable(y)for y in x]
    if isinstance(x,str)and('F:\\BT3-'in x or 'F:/BT3-'in x or 'C:\\Users\\JUAN'in x):return 'Imported user game data'
    return x
   desired=json.dumps(portable(json.loads(desired)),ensure_ascii=False,indent=2).encode('utf-8');want=sha(desired)
  except (ValueError,UnicodeError):pass
 for sid,source,digest in sources:
  basekey=rel[5:]if rel.startswith('mods/')else rel
  if basekey=='disc/SLUS_216.78':basekey='disc/SLUS_219.99'
  span=indices[sid].get(basekey)
  if span is None and sid=='original':span=byhash.get((len(desired),want))
  if span is None and basekey in originalIndex and sid!='original':span=indices[sid].get(basekey)
  if span is None:
   # New resource/art has no exact source; prefer a same-size original donor
   # only when its prefix agrees. Otherwise encode a bounded new-data patch.
   if sid=='original':
    pos=bisect.bisect_left(sizes,(len(desired),0));candidates=sizes[max(0,pos-4):pos+4]
    for n,at in candidates:
     candidate=read(sid,(at,n))
     if candidate[:32]==desired[:32]and abs(n-len(desired))<65536:span=(at,n);break
  before=read(sid,span)if span else b'';basehash=sha(before)
  if before==desired:plans[sid]=dict(offset=span[0],bytes=len(before));copied+=1;continue
  key='xor-'+basehash+'-'+want;entry=cached.get(key)
  if not entry or not(R/'deltas'/entry['file']).is_file():
   delta=(int.from_bytes(before[:len(desired)],'little')^int.from_bytes(desired,'little')).to_bytes(len(desired),'little');patch=zlib.compress(delta,6)
   assert (int.from_bytes(zlib.decompress(patch),'little')^int.from_bytes(before[:len(desired)],'little')).to_bytes(len(desired),'little')==desired
   name=sha(patch)+'.xor.z';(R/'deltas'/name).write_bytes(patch);entry=dict(file=name,sha256=sha(patch),bytes=len(patch));cached[key]=entry
  plans[sid]=dict(offset=span[0]if span else 0,bytes=len(before),base_sha256=basehash,patch=entry);patchcount+=1
 records.append(dict(path=rel,variants=variants,bytes=len(desired),sha256=want,sources=plans))
 if k%1000==0:
  print(k,'/',len(targets),'files;',patchcount,'patch plans;',round(time.time()-began,1),'s',flush=True);cache.write_text(json.dumps(cached))
manifest=dict(schema=1,version='0.4.1',sources=meta,files=records,approved_assets=196,normal_maps='Exact original map coordinates; omit 2x-specific map overlays',runtime='Tenkaichi3Decomp-tagteam native port; all fixes from signed-off current profile')
with gzip.open(R/'content.json.gz','wt',encoding='utf-8',compresslevel=6)as f:json.dump(manifest,f,separators=(',',':'))
cache.write_text(json.dumps(cached));receipt=dict(status='RECIPE_BUILT_PATCH_ROUNDTRIPS_PASSED',files=len(records),source_variants=len(sources),patch_plans=patchcount,copy_plans=copied,patch_payload_bytes=sum(p.stat().st_size for p in(R/'deltas').glob('*')),manifest_sha256=hashfile(R/'content.json.gz'),seconds=time.time()-began)
(OUT/'content-build-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
