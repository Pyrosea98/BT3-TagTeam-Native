
from pathlib import Path
import importlib.util,tempfile,json,zlib,hashlib,unittest.mock as mock,shutil
spec=importlib.util.spec_from_file_location('update',Path(__file__).with_name('update_engine.py'));u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
process_check=mock.patch('subprocess.check_output',return_value='');process_check.start()
sha=lambda b:hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory(dir=Path(__file__).parent)as tmp:
 root=Path(tmp);bundle=root/'payload';bundle.mkdir();app=root/'game';app.mkdir();(app/'data/gamedata').mkdir(parents=True)
 profile={'version':'0.4.1'};(app/'release-profile.json').write_text(json.dumps(profile));(app/'data/gamedata/import-receipt.json').write_text('{"maps":"normal"}')
 personal={'data/bt3_settings.txt':b'keyboard_player=2\n','data/saves/progress.bin':b'earned progress','data/saves/achievements-0.dat':b'trophy record'}
 for rel,b in personal.items():f=app/rel;f.parent.mkdir(exist_ok=True,parents=True);f.write_bytes(b)
 records=[]
 for i in range(2):
  before=b'original'+bytes([i]);after=b'updated asset'+bytes([i]);(app/f'data/gamedata/f{i}').write_bytes(before);blob=zlib.compress(after);(bundle/f'b{i}').write_bytes(blob)
  records.append(dict(root='data',path=f'gamedata/f{i}',bytes=len(after),sha256=sha(after),before=[sha(before)],plans={sha(before):dict(file=f'b{i}',sha256=sha(blob),kind='full')}))
 manifest=dict(schema=1,version='0.5.alpha',from_versions=['0.4.1'],files=records);(bundle/'update.json').write_text(json.dumps(manifest))
 u.apply(app,bundle,True);assert(app/'data/gamedata/f0').read_bytes()==b'original\0'
 (bundle/'b1').write_bytes(b'corrupt')
 try:u.apply(app,bundle)
 except AssertionError:pass
 else:raise AssertionError('corrupt payload accepted')
 assert(app/'data/gamedata/f0').read_bytes()==b'original\0'
 (bundle/'b1').write_bytes(zlib.compress(b'updated asset\1'))
 # An interrupted replace rolls the first file back too.
 original=u.os.replace;counter=[0]
 def fail_second(src,dst):
  if Path(src).name.startswith('new-'):
   counter[0]+=1
   if counter[0]==2:raise OSError('simulated write failure')
  return original(src,dst)
 with mock.patch.object(u.os,'replace',fail_second):
  try:u.apply(app,bundle)
  except OSError:pass
  else:raise AssertionError('failure not injected')
 for i in range(2):assert(app/f'data/gamedata/f{i}').read_bytes()==b'original'+bytes([i])
 u.apply(app,bundle)
 for i in range(2):assert(app/f'data/gamedata/f{i}').read_bytes()==b'updated asset'+bytes([i])
 for rel,b in personal.items():assert(app/rel).read_bytes()==b
 # Reject path traversal even on hostile package metadata.
 for bad in ['../saves/x','C:/x','/x','gamedata/../../x']:
  try:u.child(app,bad)
  except ValueError:pass
  else:raise AssertionError(bad)
 print('PASS updater preflight/corrupt-payload rejection before writes, rollback after second replacement, exact files, personal data and normal map receipt preservation, path confinement')
