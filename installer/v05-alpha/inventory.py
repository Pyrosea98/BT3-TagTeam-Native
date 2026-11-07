from pathlib import Path
import json,gzip,hashlib,time
p=Path('analysis/codex-alpha-audit-20261107');start=time.time();g=Path(r'F:\BT3-Builds\v05-select\preview\gamedata');old=json.loads(gzip.decompress(Path(r'F:\BT3-Builds\pc-release-v041\payload\import-data\content.json.gz').read_bytes()));baseline={}
for x in old['files']:baseline.setdefault(x['path'],[]).append(x)
files={};exclude=[]
for folder in ['pzs3us1','pzs3us2','pak3us3','pak3us4','disc','beta8','game-text','tagteam-ui','mods']:
 for f in (g/folder).rglob('*'):
  if not f.is_file():continue
  rel=f.relative_to(g).as_posix()
  if any(('backup' in a.lower() or a.endswith(('.bak','.log','.before'))) for a in f.relative_to(g).parts):continue
  if rel.startswith('mods/pak3us1/'):rel=rel.replace('mods/pak3us1/','mods/pzs3us1/',1)
  if rel.startswith('mods/pak3us2/'):rel=rel.replace('mods/pak3us2/','mods/pzs3us2/',1)
  files[rel]=dict(path=rel,source=str(f),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
changed=[];same=0;mapchanges=[]
for rel,x in files.items():
 rows=baseline.get(rel,[])
 if any(z['sha256']==x['sha256'] for z in rows):same+=1;continue
 x['before']=[dict(sha256=z['sha256'],variants=z['variants'],bytes=z['bytes'])for z in rows];changed.append(x)
 if len(rows)>1 and len({z['sha256']for z in rows})>1:mapchanges.append(rel)
result=dict(files=len(files),unchanged=same,changed=len(changed),changed_bytes=sum(x['bytes']for x in changed),changed_variant_maps=mapchanges,seconds=time.time()-start,records=changed)
(p/'update-inventory.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='records'},indent=2))
