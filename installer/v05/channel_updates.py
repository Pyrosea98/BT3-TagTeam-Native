"""Consent-driven official release updates. Downloaded scripts are never executed."""
from pathlib import Path, PurePosixPath
import hashlib,json,urllib.request,zipfile,os,tempfile
REPO='Pyrosea98/BT3-TagTeam-Native'
ASSET='BT3-TagTeam-v0.5.alpha-Windows-Update.zip'
MAX_DOWNLOAD=1024*1024*1024

def fetch_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'BT3-TagTeam-Updater','Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=8) as r:
  raw=r.read(4*1024*1024+1)
  if len(raw)>4*1024*1024:raise ValueError('Release metadata too large')
  return json.loads(raw)

def config(app):
 p=Path(app)/'update-preferences.json'
 return json.loads(p.read_text()) if p.exists() else {'channel':'nightly','check_on_launch':True}

def save_config(app,channel,automatic):
 if channel not in ('stable','nightly'):raise ValueError('Invalid channel')
 p=Path(app)/'update-preferences.json';tmp=p.with_suffix('.tmp')
 tmp.write_text(json.dumps({'channel':channel,'check_on_launch':bool(automatic)},indent=2));os.replace(tmp,p)

def version_key(value):
 import re
 text=value.lstrip('v');nums=re.match(r'(\d+)\.(\d+)(?:\.(\d+))?',text)
 if not nums:return (-1,)
 return tuple(int(x or 0)for x in nums.groups())+(0 if any(s in text.lower()for s in ('alpha','beta','nightly','rc'))else 1,)

def choose(releases,channel,profile,receipt):
 if channel not in ('stable','nightly'):raise ValueError('Invalid channel')
 current=profile.get('version','0.0');installed=receipt.get('asset_sha256')
 for r in sorted(releases,key=lambda x:x.get('published_at',''),reverse=True):
  if r.get('draft') or (channel=='stable' and r.get('prerelease')):continue
  if version_key(r['tag_name'])<version_key(current):continue
  # A stable feed must never silently downgrade an alpha installation.
  if channel=='stable' and current=='0.5.alpha' and r['tag_name'].lstrip('v')=='0.4.1':continue
  assets=[a for a in r.get('assets',[]) if a['name'].startswith('BT3-TagTeam-') and a['name'].endswith('-Windows-Update.zip')]
  if not assets:continue
  a=assets[0];digest=a.get('digest','')
  import re
  marker=re.search(r'<!-- bt3-revision: ([a-zA-Z0-9._-]+) -->',r.get('body',''))
  if marker and profile.get('revision')==marker.group(1):return None
  if not digest.startswith('sha256:') or len(digest)!=71:continue
  if installed==digest[7:]:return None
  return {'tag':r['tag_name'],'title':r.get('name') or r['tag_name'],'notes':r.get('body',''),'url':a['browser_download_url'],'bytes':a['size'],'sha256':digest[7:],'page':r['html_url']}
 return None

def available(app):
 app=Path(app);p=app/'online-update-receipt.json'
 receipt=json.loads(p.read_text()) if p.exists() else {}
 profile=json.loads((app/'release-profile.json').read_text())
 return choose(fetch_json('https://api.github.com/repos/'+REPO+'/releases?per_page=30'),config(app)['channel'],profile,receipt)

def trusted_url(url):
 from urllib.parse import urlparse
 p=urlparse(url)
 if p.scheme!='https' or p.netloc!='github.com' or not p.path.startswith('/'+REPO+'/releases/download/'):raise ValueError('Unexpected update location')

def unpack(archive,destination):
 destination=Path(destination);seen=set();total=0
 with zipfile.ZipFile(archive) as z:
  for item in z.infolist():
   p=PurePosixPath(item.filename)
   if p.is_absolute() or any(v in ('..','.') or ':' in v or '\\' in v for v in p.parts):raise ValueError('Unsafe update archive')
   if item.is_dir():continue
   # Only authenticated data used by the installed update engine is extracted.
   if p.parts[0]!='payload':continue
   if len(p.parts)<2 or not (p.as_posix()=='payload/update.json' or p.parts[1]=='blobs'):raise ValueError('Unexpected update payload')
   key=p.as_posix().casefold()
   if key in seen:raise ValueError('Duplicate update entry')
   seen.add(key);total+=item.file_size
   if total>MAX_DOWNLOAD*3 or item.file_size>MAX_DOWNLOAD:raise ValueError('Update archive exceeds limit')
   target=destination.joinpath(*p.parts);target.parent.mkdir(parents=True,exist_ok=True)
   with z.open(item) as src,target.open('xb') as dst:
    import shutil
    shutil.copyfileobj(src,dst,1024*1024)
 if not (destination/'payload/update.json').is_file():raise ValueError('Missing update manifest')

def install(app,release,report=lambda x:None):
 from update_engine import apply
 app=Path(app);trusted_url(release['url'])
 if not 0<release['bytes']<=MAX_DOWNLOAD:raise ValueError('Invalid download size')
 cache=app/'.updates/downloads';cache.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='download-',dir=cache) as d:
  root=Path(d);archive=root/'update.zip';h=hashlib.sha256();done=0
  req=urllib.request.Request(release['url'],headers={'User-Agent':'BT3-TagTeam-Updater'})
  with urllib.request.urlopen(req,timeout=30) as src,archive.open('xb') as dst:
   while True:
    b=src.read(1024*1024)
    if not b:break
    done+=len(b)
    if done>release['bytes']:raise ValueError('Download exceeded expected size')
    dst.write(b);h.update(b);report(int(90*done/release['bytes']))
  if done!=release['bytes'] or h.hexdigest()!=release['sha256']:raise ValueError('Download verification failed')
  unpack(archive,root/'unpacked');apply(app,root/'unpacked/payload')
  p=app/'online-update-receipt.json';tmp=p.with_suffix('.tmp')
  tmp.write_text(json.dumps({'tag':release['tag'],'asset_sha256':release['sha256']},indent=2));os.replace(tmp,p)
 report(100)
