from pathlib import Path
import tempfile,json,zipfile
import channel_updates as u
asset=dict(name='BT3-TagTeam-v0.5.alpha-Windows-Update.zip',digest='sha256:'+'a'*64,size=100,browser_download_url='https://github.com/'+u.REPO+'/releases/download/v0.5.alpha/update.zip')
stable=dict(tag_name='v0.4.1',published_at='2026-10-27',prerelease=False,draft=False,assets=[asset],html_url='stable')
nightly=dict(tag_name='v0.5.alpha',published_at='2026-11-07',prerelease=True,draft=False,assets=[asset],html_url='nightly',body='<!-- bt3-revision: new -->')
assert u.choose([stable,nightly],'nightly',{'version':'0.4.1'},{})['tag']=='v0.5.alpha'
assert u.choose([stable,nightly],'stable',{'version':'0.4.1'},{})['tag']=='v0.4.1'
assert u.choose([stable,nightly],'stable',{'version':'0.5.alpha'},{})is None
assert u.choose([nightly],'nightly',{'version':'0.5.alpha','revision':'new'},{})is None
assert u.choose([nightly],'nightly',{'version':'0.5.alpha','revision':'old'},{})is not None
assert u.choose([nightly],'nightly',{'version':'0.5.alpha'},{'asset_sha256':'a'*64})is None
for bad in ['http://github.com/'+u.REPO+'/releases/download/a/b','https://evil.example/a','https://github.com/other/repo/releases/download/a/b']:
 try:u.trusted_url(bad)
 except ValueError:pass
 else:raise AssertionError(bad)
with tempfile.TemporaryDirectory(dir=Path(__file__).parent)as d:
 p=Path(d);u.save_config(p,'stable',False);assert u.config(p)=={'channel':'stable','check_on_launch':False}
 for name in ['payload/../escape','/payload/update.json','payload/C:/escape','payload/a\\b']:
  with zipfile.ZipFile(p/'bad.zip','w')as z:z.writestr(name,b'bad')
  try:u.unpack(p/'bad.zip',p/'out')
  except ValueError:pass
  else:raise AssertionError(name)
 with zipfile.ZipFile(p/'good.zip','w')as z:
  z.writestr('update.py','raise Exception("must not execute")');z.writestr('payload/update.json','{}');z.writestr('payload/blobs/a.z',b'hello')
 u.unpack(p/'good.zip',p/'good');assert not(p/'good/update.py').exists()
print('PASS stable/nightly, no downgrade, revision/idempotence, channel persistence, trusted origin, safe archive, no downloaded script execution')

for p in Path(__file__).parent.iterdir():
 if p.is_file() and p.suffix in ('.py','.pyw','.iss','.md') and p.name!='test_channels.py':
  raw=p.read_text(encoding='utf-8');assert not any(x in raw for x in ('\u00c3','\u00c2','\ufffd')),p.name
assert u.version_key('v0.5.alpha')<u.version_key('v0.5.0')<u.version_key('v0.6.alpha')
print('PASS release ordering and installer UTF-8 audit')
