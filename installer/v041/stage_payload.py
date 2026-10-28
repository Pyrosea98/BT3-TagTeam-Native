from pathlib import Path
import shutil,hashlib,json,struct,zipfile,sys
W=Path('F:/BT3-Builds/Tag Team Mod Installer 2');B=Path('F:/BT3-Builds');S=B/'Tenkaichi3Decomp-tagteam';O=B/'pc-release-v041';P=O/'payload';HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((S/'analysis/codex-pc-release041/build-receipt.json').read_text())['source_guard']
for name in ('app.pyw','importer.py'):shutil.copy2(HERE/name,P/name)
shutil.copy2(W/'native-port/installer/credits_splash.py',P/'credits_splash.py')
for folder in ('assets','manual','save-seed','import-data'): (P/folder).mkdir(exist_ok=True)
shutil.copy2(W/'native-port/installer/assets/BT3TagTeam.ico',P/'assets/BT3TagTeam.ico')
shutil.copytree(W/'native-port/startup/credits-v04',P/'assets/credits-v04',dirs_exist_ok=True)
runtime=W/'native-port/installer/v04/payload/runtime'
def ignore(path,names):
    skip={'__pycache__'}
    if Path(path).name=='site-packages':skip|={n for n in names if n not in ('PIL','pillow-12.3.0.dist-info','pillow.libs')}
    return [n for n in names if n in skip]
shutil.copytree(runtime,P/'runtime',dirs_exist_ok=True,ignore=ignore)
release=S/'port/build_release/release-win'
for p in release.iterdir():
    if p.name in ('gamedata','saves','Tenkaichi3Decomp-setup.exe'):continue
    if p.is_dir():shutil.copytree(p,P/p.name,dirs_exist_ok=True)
    elif p.name!='Tenkaichi3Decomp.dat':shutil.copy2(p,P/p.name)
raw=(release/'Tenkaichi3Decomp.dat').read_bytes()
sys.path.insert(0,str(W/'native-port'))
from finalize_beta8_decomp_content import stock_sources,flat,fnv
magic,count,want=struct.unpack_from('<4sIQ',raw);assert magic==b'BT3D'and len(raw)==16+count*16
stock=stock_sources(B/'Tenkaichi3Decomp-tagteam-release/Tenkaichi3Decomp')
game=B/'Tenkaichi3Decomp-content/beta8-native-profile/gamedata'
source=[flat((game/'disc/SLUS_219.99').read_bytes()),(game/'disc/BIN/DBZP.BIN').read_bytes()];old=[];new=[]
for i in range(count):
    host,which,off,n=struct.unpack_from('<4I',raw,16+i*16)
    assert which<2 and off+n<=len(stock[which])and off+n<=len(source[which])
    old.append(stock[which][off:off+n]);new.append(source[which][off:off+n])
assert fnv(old)==want,'Raw initializer does not authenticate against stock reference programs'
adapted=bytearray(raw);struct.pack_into('<Q',adapted,8,fnv(new))
(P/'Tenkaichi3Decomp.dat').write_bytes(adapted)
accepted=(B/'Tenkaichi3Decomp-tagteam-release/Tenkaichi3Decomp/bt3_settings.txt').read_text()
settings=[]
for line in accepted.splitlines():
    key=line.partition('=')[0]
    if not key or '"'in line or key in ('scale','aspect_milli','display','fullscreen','window_w','window_h')or key.startswith(('padslot_','pad_guid_','net_','online_')):continue
    if key in ('coop_fusion_controls','coop_fusion_swap_seconds','skip_logos','skip_copyright','skip_intro','update_check','show_credits_at_startup'):continue
    settings.append(line)
settings+=['coop_fusion_controls=0','coop_fusion_swap_seconds=10','skip_logos=0','skip_copyright=0','skip_intro=0','update_check=0','show_credits_at_startup=1']
(P/'recommended-settings.txt').write_text('\n'.join(settings)+'\n')
seed=B/'Tenkaichi3Decomp-content/native-round2-integration/pc-signoff-apk-handoff-20261027/save-seed/BASLUS-21678DBZT3'
assert (seed/'BASLUS-21678DBZT3').is_file();shutil.copytree(seed,P/'save-seed/BASLUS-21678DBZT3',dirs_exist_ok=True)
files={n:sha(P/n)for n in ('Tenkaichi3Decomp.exe','Tenkaichi3Decomp.exe.mem','Tenkaichi3Decomp.dat')}
manifest=P/'import-data/content.json.gz'
if manifest.exists():
    profile=dict(version='0.4.1',engine='Tenkaichi3Decomp Tag Team / Real Power Scale',runtime=files,content_manifest_sha256=sha(manifest),source_build_receipt_sha256=sha(S/'analysis/codex-pc-release041/build-receipt.json'),android='Separate artifact maintained by Claude; not bundled in this Windows setup')
    (P/'release-profile.json').write_text(json.dumps(profile,indent=2))
    (O/'payload-stage-receipt.json').write_text(json.dumps(profile,indent=2))
shutil.copy2(HERE/'installer.iss',O/'installer.iss');print('Staged current native runtime, portable embedded Python, credit assets, accepted settings and save seed')
