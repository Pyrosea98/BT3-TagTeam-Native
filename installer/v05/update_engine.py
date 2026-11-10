"""Verified 0.4.1 / earlier 0.5.alpha.1 -> current 0.5.alpha.1 update. Never writes saves/settings or changes ISO files."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,shutil,zlib,uuid,sys
VERSION='0.5.alpha.1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def child(root,name):
 q=PurePosixPath(name)
 if q.is_absolute() or not q.parts or any(x in ('..','.') or ':' in x or '\\' in x for x in q.parts):raise ValueError('Unsafe update path: '+name)
 p=root.joinpath(*q.parts)
 if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Path leaves installation: '+name)
 return p

def _apply(app,bundle,check=False):
 app=Path(app).resolve();bundle=Path(bundle).resolve()
 # Recover interrupted updates before reading a potentially half-updated release profile.
 for journal in (app/'.updates').glob('v05-alpha-*/journal.json'):
  work=journal.parent
  if (work/'COMPLETED').exists() or (work/'ROLLED_BACK').exists():continue
  for e in reversed(json.loads(journal.read_text())):
   dst=Path(e['destination']);backup=Path(e['backup'])
   if e.get('started'):
    if e['existed'] and backup.is_file():os.replace(backup,dst)
    elif not e['existed'] and dst.is_file():dst.unlink()
  (work/'ROLLED_BACK').write_text('Recovered interrupted update')
 manifest=json.loads((bundle/'update.json').read_text());version=manifest['version'];assert manifest.get('schema')==1;profile=json.loads((app/'release-profile.json').read_text())
 data=(app/'data-root.txt').read_text(encoding='utf-8-sig').strip() if (app/'data-root.txt').exists() else str(app/'data');data=Path(data).expanduser().resolve()
 if profile['version']==version and not (app/'alpha-update-receipt.json').exists() and not (app/'bootstrap/payload/update.json').exists():raise ValueError('Alpha profile without completed update receipt')
 if profile['version'] not in manifest['from_versions']:raise ValueError('This updater requires a supported 0.4.1 or completed 0.5.alpha.1 installation; different versions need their own recipe')
 receipt=json.loads((data/'gamedata/import-receipt.json').read_text())
 roots={'app':app,'data':data};records=manifest['files'];plans=[]
 # Verify every touched input before replacing a single file. Custom changes fail closed.
 for i,r in enumerate(records):
  
  if r['root']=='data' and not r['path'].startswith('gamedata/'):raise ValueError('Personal data may not be updated')
  if r['root']=='app' and (r['path'].startswith(('data/','saves/','settings/')) or r['path'] in ('bt3_settings.txt','install-choices.json','data-root.txt')):raise ValueError('Personal app configuration may not be updated')
  dest=child(roots[r['root']],r['path']);before=sha(dest) if dest.is_file() else None
  if before==r['sha256']:continue
  if before not in r['before']:raise ValueError('Modified or unsupported input: '+str(dest))
  patch=r['plans'][str(before)];blob=child(bundle,patch['file']);assert sha(blob)==patch['sha256'],'Corrupt update blob'
  raw=zlib.decompress(blob.read_bytes())
  if patch['kind']=='xor':raw=(int.from_bytes(raw,'little')^int.from_bytes(dest.read_bytes()[:r['bytes']],'little')).to_bytes(r['bytes'],'little')
  assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'Reconstructed file failed verification'
  plans.append((r,dest,raw))
  if i%1000==0:print('Verified',i,'/',len(records),flush=True)
 if check:print('PASS preflight;',len(plans),'files ready; no files modified');return
 if not plans:print('Already running this 0.5.alpha.1 revision; verified all package files');return
 # Reject a running game, including processes whose cwd is outside the installation.
 if os.name=='nt':
  import subprocess
  if 'Tenkaichi3Decomp.exe' in subprocess.check_output(['tasklist','/FI','IMAGENAME eq Tenkaichi3Decomp.exe','/NH'],text=True):raise ValueError('Close the game before updating')
 work=app/'.updates'/('v05-alpha-'+uuid.uuid4().hex);work.mkdir(parents=True);journal=[]
 try:
  for i,(r,dest,raw) in enumerate(plans):
   temp=work/('new-'+str(i));temp.write_bytes(raw);journal.append(dict(destination=str(dest),backup=str(work/('old-'+str(i))),new=str(temp),existed=dest.exists(),done=False))
  (work/'journal.json').write_text(json.dumps(journal))
  for e in journal:
   dest=Path(e['destination']);dest.parent.mkdir(parents=True,exist_ok=True)
   if e['existed']:shutil.copy2(dest,e['backup'])
   e['started']=True;(work/'journal.json').write_text(json.dumps(journal))
   os.replace(e['new'],dest);e['done']=True;(work/'journal.json').write_text(json.dumps(journal))
  (app/'alpha-update-receipt.json').write_text(json.dumps(dict(version=version,revision=manifest.get('revision'),files=len(plans),backup=str(work),source_import=receipt),indent=2))
  (work/'COMPLETED').write_text(version)
 except BaseException:
  for e in reversed(journal):
   if e.get('started'):
    dst=Path(e['destination'])
    if e['existed'] and Path(e['backup']).exists():os.replace(e['backup'],dst)
    elif not e['existed'] and dst.exists():dst.unlink()
  (work/'ROLLED_BACK').write_text('Rolled back failed update')
  raise
 print('Updated to '+version+'. Saves, achievements, settings and map choice preserved. Backup: '+str(work))
def apply(app,bundle,check=False):
 lockdir=Path(app)/'.updates';lockdir.mkdir(parents=True,exist_ok=True)
 with (lockdir/'update.lock').open('a+b') as lock:
  lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
  if os.name=='nt':
   import msvcrt
   try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:raise ValueError('Another update is running; wait until it finishes')
  else:
   import fcntl
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:return _apply(app,bundle,check)
  finally:
   lock.seek(0)
   if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
   else:fcntl.flock(lock,fcntl.LOCK_UN)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('installation');parser.add_argument('--bundle',default=str(Path(__file__).parent/'payload'));parser.add_argument('--check',action='store_true');args=parser.parse_args()
 try:apply(args.installation,args.bundle,args.check)
 except Exception as e:print('Update stopped safely:',str(e));sys.exit(1)
