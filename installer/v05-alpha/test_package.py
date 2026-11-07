
from pathlib import Path
import json,gzip,zlib,hashlib,shutil,importlib.util,unittest.mock as mock
r=Path.cwd();a=r/'analysis/codex-alpha-audit-20261107';out=Path(r'F:\BT3-Builds\pc-release-v05-alpha');bundle=out/'update/payload';oldapp=Path(r'F:\BT3-Builds\pc-release-v041\payload');old=json.loads(gzip.decompress((oldapp/'import-data/content.json.gz').read_bytes()));source=Path(r'F:\BT3-Builds\Tag Team Mod Installer 2\experiments\ISO niveles de poder BETA 8.ISO');iso=source.open('rb');sha=lambda b:hashlib.sha256(b).hexdigest();new=json.loads((bundle/'update.json').read_text());lookup={}
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
(out/'update-validation.json').write_text(json.dumps(results,indent=2))
