
from pathlib import Path
import json,hashlib,zlib,shutil,os
r=Path.cwd();a=r/'analysis/codex-alpha-audit-20261107';out=Path(r'F:\BT3-Builds\pc-release-v05-alpha');pack=out/'update';payload=pack/'payload';blobs=payload/'blobs';blobs.mkdir(parents=True,exist_ok=True)
base=Path(r'F:\BT3-Builds\Tenkaichi3Decomp-content\beta8-native-profile\gamedata');oldapp=Path(r'F:\BT3-Builds\pc-release-v041\payload');preview=Path(r'F:\BT3-Builds\v05-select\preview');sha=lambda x:hashlib.sha256(x).hexdigest();records=[]
def add(root,path,raw,previous,oldbytes=None):
 want=sha(raw);plans={}
 for h in previous:
  kind='full';delta=zlib.compress(raw,6)
  if h and oldbytes is not None and sha(oldbytes)==h:
   x=(int.from_bytes(oldbytes[:len(raw)],'little')^int.from_bytes(raw,'little')).to_bytes(len(raw),'little');z=zlib.compress(x,6)
   if len(z)<len(delta):delta=z;kind='xor'
  digest=sha(delta);name='blobs/'+digest+'.z';dest=payload/name
  if not dest.exists():dest.write_bytes(delta)
  plans[str(h)]=dict(file=name,sha256=digest,kind=kind)
 records.append(dict(root=root,path=path,bytes=len(raw),sha256=want,before=previous,plans=plans))
inventory=json.loads((a/'update-inventory.json').read_text());assert not inventory['changed_variant_maps']
for x in inventory['records']:
 rel=x['path']
 if any(t in rel.lower()for t in ['.before','backup','.bak','.log']):continue
 raw=Path(x['source']).read_bytes()
 # Chime was added after inventory began; handle it explicitly below if absent.
 if sha(raw)!=x['sha256']:raise ValueError('Data changed during packaging: '+rel)
 old=base/rel;oldbytes=old.read_bytes()if old.is_file()else None
 previous=list(dict.fromkeys(z['sha256']for z in x['before']))or[None]
 add('data','gamedata/'+rel,raw,previous,oldbytes)
cue=preview/'gamedata/tagteam-ui/achievement-chime.wav'
if not any(x['path']=='gamedata/tagteam-ui/achievement-chime.wav'for x in records):add('data','gamedata/tagteam-ui/achievement-chime.wav',cue.read_bytes(),[None])
for folder in ['songs','stages','fonts','tbo','textures','licenses']:
 for f in (preview/folder).rglob('*'):
  if not f.is_file()or any(t in f.name.lower()for t in ['.before','.bak','.log']):continue
  rel=f.relative_to(preview).as_posix();old=oldapp/rel;raw=f.read_bytes();prior=old.read_bytes()if old.is_file()else None
  if prior==raw:continue
  add('app',rel,raw,[sha(prior)if prior is not None else None],prior)
candidate=a/'candidate';runtime={}
for name in ['Tenkaichi3Decomp.exe','Tenkaichi3Decomp.exe.mem','Tenkaichi3Decomp.dat','SDL3.dll']:
 raw=(candidate/name).read_bytes();prior=(oldapp/name).read_bytes();runtime[name]=sha(raw);add('app',name,raw,[sha(prior)],prior)
profile=json.loads((oldapp/'release-profile.json').read_text());profile.update(version='0.5.alpha',runtime={n:h for n,h in runtime.items()if n!='SDL3.dll'},alpha=True,update_base='0.4.1',source_build_receipt_sha256=sha((a/'production-receipt.json').read_bytes()))
add('app','release-profile.json',json.dumps(profile,indent=2).encode(),[sha((oldapp/'release-profile.json').read_bytes())],(oldapp/'release-profile.json').read_bytes())
launcher=(oldapp/'app.pyw').read_text(encoding='utf-8').replace('0.4.1','0.5.alpha');launcher=launcher.replace('env=os.environ.copy();env.update(',"env={k:v for k,v in os.environ.items() if not k.startswith('BT3_')};env.update(")
add('app','app.pyw',launcher.encode(),[sha((oldapp/'app.pyw').read_bytes())],(oldapp/'app.pyw').read_bytes())
manifest=dict(schema=1,version='0.5.alpha',from_versions=['0.4.1'],map_choice='preserved; normal and 2x map variants unchanged',files=records)
(payload/'update.json').write_text(json.dumps(manifest,separators=(',',':')));shutil.copy2(a/'update_player.py',pack/'update.py')
(pack/'Update.cmd').write_text('@echo off\nsetlocal\nset "GAME=%~1"\nif not defined GAME set /p "GAME=Existing BT3 Tag Team 0.4.1 installation folder: "\nif not exist "%GAME%\\runtime\\python.exe" (echo Supported installation not found.& pause& exit /b 1)\n"%GAME%\\runtime\\python.exe" -B "%~dp0update.py" "%GAME%"\nset "RESULT=%ERRORLEVEL%"\npause\nexit /b %RESULT%\n')
summary=dict(files=len(records),uncompressed_bytes=sum(x['bytes']for x in records),blob_bytes=sum(x.stat().st_size for x in blobs.iterdir()),normal_and_2x_preserved=True)
(out/'package-receipt.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
