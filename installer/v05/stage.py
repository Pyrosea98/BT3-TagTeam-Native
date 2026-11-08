from pathlib import Path
import shutil,json,zlib,hashlib,subprocess,os
import argparse
cli=argparse.ArgumentParser();cli.add_argument('--stable-payload',type=Path,required=True);cli.add_argument('--alpha-update',type=Path,required=True);cli.add_argument('--output',type=Path,required=True);args=cli.parse_args()
S=Path(__file__).resolve().parent;O=args.output.resolve();O.mkdir(exist_ok=True)
P=O/'payload';P.mkdir(exist_ok=True)
B=args.stable_payload.resolve();U=O/'update'
p=S/'app.pyw';a=p.read_text(encoding='utf-8');a=a.replace("if bundle.is_dir():", "if bundle.is_dir() and not (APP/'alpha-update-receipt.json').exists():");p.write_text(a,encoding='utf-8')
# Stage the frozen authenticated import package without copying any player data.
for item in B.iterdir():
 if item.name=='data' or item.name=='__pycache__':continue
 dest=P/item.name
 if item.is_dir():shutil.copytree(item,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 else:shutil.copy2(item,dest)
for name in ['app.pyw','importer.py','credits_splash.py','update_engine.py','channel_updates.py','update_ui.py']:
 shutil.copy2(S/name,P/name)
csc=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe')
subprocess.run([str(csc),'/nologo','/target:winexe','/r:System.Windows.Forms.dll','/win32icon:'+str(P/'assets/BT3TagTeam.ico'),'/out:'+str(P/'Play.exe'),str(S/'Play.cs')],check=True)
old=args.alpha_update.resolve();shutil.copytree(old,U,dirs_exist_ok=True)
m=json.loads((U/'payload/update.json').read_text());m['revision']='installers-channels-20261107'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def add(name,raw):
 h=sha(raw);compressed=zlib.compress(raw,9);ch=sha(compressed);blob=U/'payload/blobs'/(ch+'.z');blob.write_bytes(compressed)
 row=next((r for r in m['files']if r['root']=='app' and r['path']==name),None)
 if row:
  prior=list(dict.fromkeys(row['before']+[row['sha256']]))
  row.update(bytes=len(raw),sha256=h,before=prior,plans={str(x):dict(file='blobs/'+blob.name,sha256=ch,kind='full')for x in prior})
 else:
  path=B/name;before=sha(path.read_bytes())if path.is_file()else None
  m['files'].append(dict(root='app',path=name,bytes=len(raw),sha256=h,before=[before],plans={str(before):dict(file='blobs/'+blob.name,sha256=ch,kind='full')}))
for name in ['app.pyw','Play.exe','update_engine.py','channel_updates.py','update_ui.py']:
 add(name,(P/name).read_bytes())
# The installed alpha profile needs the new packaging revision; base import profile stays frozen until bootstrap.
row=next(r for r in m['files']if r['root']=='app'and r['path']=='release-profile.json');plan=next(iter(row['plans'].values()));assert plan['kind']=='full';profile=json.loads(zlib.decompress((U/'payload'/plan['file']).read_bytes()));profile['revision']=m['revision'];add('release-profile.json',json.dumps(profile,indent=2).encode())
(U/'payload/update.json').write_text(json.dumps(m,separators=(',',':')))
shutil.copy2(S/'update_engine.py',U/'update.py')
shutil.copytree(U/'payload',P/'bootstrap/payload',dirs_exist_ok=True)
# Only manifest-referenced blobs; remove no source files, never remove the frozen base package.
needed={p['file']for r in m['files']for p in r['plans'].values()}
for root in [U/'payload',P/'bootstrap/payload']:
 for b in (root/'blobs').glob('*'):
  if 'blobs/'+b.name not in needed:b.unlink()
(O/'release').mkdir(exist_ok=True)
print('Staged full payload and update payload:',len(m['files']),'records')

for name in ('installer.iss','update-installer.iss'):shutil.copy2(S/name,O/name)
