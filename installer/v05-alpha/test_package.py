
from pathlib import Path
import json,gzip,zlib,hashlib,shutil,importlib.util,unittest.mock as mock
r=Path.cwd();a=r/'analysis/codex-ginyu-release-20261107';out=Path(r'F:\BT3-Builds\pc-release-v05-alpha-ginyu');bundle=out/'update/payload';oldapp=Path(r'F:\BT3-Builds\pc-release-v041\payload');old=json.loads(gzip.decompress((oldapp/'import-data/content.json.gz').read_bytes()));source=Path(r'F:\BT3-Builds\Tag Team Mod Installer 2\experiments\ISO niveles de poder BETA 8.ISO');iso=source.open('rb');sha=lambda b:hashlib.sha256(b).hexdigest();new=json.loads((bundle/'update.json').read_text());lookup={}
for rec in old['files']:lookup.setdefault(rec['path'],[]).append(rec)
spec=importlib.util.spec_from_file_location('update',a/'update_player.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
def olddata(rec):
 plan=rec['sources']['original'];iso.seek(plan['offset']);data=iso.read(plan['bytes'])
 if 'patch'in plan:
  assert sha(data)==plan['base_sha256'];delta=zlib.decompress((oldapp/'import-data/deltas'/plan['patch']['file']).read_bytes());data=(int.from_bytes(delta,'little')^int.from_bytes(data[:rec['bytes']],'little')).to_bytes(rec['bytes'],'little')
 assert len(data)==rec['bytes'] and sha(data)==rec['sha256'];return data
results=[]
for mode in ['normal','2x']:
 app=out/'checks'/('upgrade-'+sha((a/'candidate/Tenkaichi3Decomp.exe').read_bytes())[:8]+'-'+mode);assert not app.exists(),'Do not overwrite a prior fixture';(app/'data/gamedata').mkdir(parents=True)
 for rec in new['files']:
  dest=(app if rec['root']=='app'else app/'data')/rec['path']
  if rec['root']=='app':
   if not (oldapp/rec['path']).is_file():continue
   raw=(oldapp/rec['path']).read_bytes()
  else:
   candidates=[x for x in lookup.get(rec['path'][9:],[])if mode in x['variants']]
   if not candidates:continue
   raw=olddata(candidates[0])
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 shutil.copy2(oldapp/'release-profile.json',app/'release-profile.json')
 (app/'data/gamedata/import-receipt.json').write_text(json.dumps(dict(maps=mode,source='original',version='0.4.1')))
 personal={'data/bt3_settings.txt':b'keyboard_player=2\nstory_difficulty=2\n','data/saves/card1/progress.bin':b'earned progress','data/saves/achievements-1.dat':b'earned trophy'}
 for rel,raw in personal.items():f=app/rel;f.parent.mkdir(exist_ok=True,parents=True);f.write_bytes(raw)
 with mock.patch('subprocess.check_output',return_value=''):u.apply(app,bundle)
 for rec in new['files']:
  dest=(app if rec['root']=='app'else app/'data')/rec['path'];assert sha(dest.read_bytes())==rec['sha256'],rec['path']
 for rel,raw in personal.items():assert(app/rel).read_bytes()==raw
 assert json.loads((app/'data/gamedata/import-receipt.json').read_text())['maps']==mode
 assert json.loads((app/'release-profile.json').read_text())['version']=='0.5.alpha'
 results.append(dict(map_choice=mode,all_package_files_verified=True,settings_saves_trophies_preserved=True))
 print('PASS exact package upgrade',mode,flush=True)
# Earlier completed alpha -> this same-version revision, then idempotent reapply.
old=Path(r'F:\BT3-Builds\pc-release-v05-alpha');app=out/'checks/upgrade-published-alpha';assert not app.exists();shutil.copytree(old/'checks/upgrade-98f00de2-normal',app,ignore=shutil.ignore_patterns('.updates'))
personal={str(p.relative_to(app)):p.read_bytes()for p in (app/'data').rglob('*')if p.is_file()and ('saves'in p.parts or p.name=='bt3_settings.txt')}
with mock.patch('subprocess.check_output',return_value=''):u.apply(app,bundle)
for rec in new['files']:
 dest=(app if rec['root']=='app'else app/'data')/rec['path'];assert sha(dest.read_bytes())==rec['sha256'],rec['path']
for rel,raw in personal.items():assert(app/rel).read_bytes()==raw
assert json.loads((app/'release-profile.json').read_text())['revision']=='ginyu-language-20261107'
with mock.patch('subprocess.check_output',return_value=''):u.apply(app,bundle)
results.append(dict(from_version='0.5.alpha',map_choice='normal',all_package_files_verified=True,settings_saves_trophies_preserved=True,idempotent_reapply=True))
print('PASS earlier alpha upgrade and verified no-op reapply',flush=True)
(out/'update-validation.json').write_text(json.dumps(results,indent=2))
