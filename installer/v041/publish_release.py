"""Publish the user-approved PC release; credentials stay in child-process memory."""
from pathlib import Path
import subprocess,os,json,hashlib
O=Path('F:/BT3-Builds/pc-release-v041');R=O/'release';D=O/'runtime-source'
W=Path(__file__).resolve().parents[3];F=W/'repo-staging/BT3-TagTeam-Native'
credential=subprocess.run(['git','-C',str(F),'credential','fill'],input='protocol=https\nhost=github.com\npath=Pyrosea98/BT3-TagTeam-Native.git\n\n',capture_output=True,text=True)
fields=dict(s.split('=',1)for s in credential.stdout.splitlines()if '='in s)
if credential.returncode or not fields.get('password'):raise SystemExit('Repository credential unavailable')
env=os.environ.copy();env['GH_TOKEN']=fields['password']
def gh(*args):
 p=subprocess.run(['gh',*map(str,args)],env=env,capture_output=True,text=True,encoding='utf-8')
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
repos={'runtime':'Pyrosea98/BT3-TagTeam-Runtime','installer':'Pyrosea98/BT3-TagTeam-Native'}
tag='v0.4.1';statepath=O/'publication-work.json'
state=json.loads(statepath.read_text())if statepath.exists()else{}
for repo in repos.values():
 releases=json.loads(gh('api',f'repos/{repo}/releases?per_page=100'))
 existing=next((r for r in releases if r['tag_name']==tag),None)
 if existing:
  assert repo in state and state[repo]['id']==existing['id'],'Refusing to replace an existing release'
verification=json.loads((R/'RELEASE_VERIFICATION.json').read_text())
for folder,branch,key in [(D,'decomp-native','native_commit'),(F,'main','installer_commit')]:
 assert subprocess.check_output(['git','-C',str(folder),'rev-parse','HEAD'],text=True).strip()==verification[key]
 subprocess.run(['git','-C',str(folder),'push','origin',f'HEAD:refs/heads/{branch}'],check=True,env=env)
groups={repos['runtime']:[R/'BT3-TagTeam-v0.4.1-Native-Source.zip',R/'RELEASE_VERIFICATION.json',R/'SHA256SUMS.txt'],repos['installer']:[R/n for n in ('BT3-TagTeam-v0.4.1-Windows-Setup.exe','BT3-TagTeam-v0.4.1-Installer-Source.zip','BT3-TagTeam-v0.4.1-ImportRecipes.zip','README.txt','RELEASE_VERIFICATION.json','SHA256SUMS.txt')]}
checks={}
for repo,assets in groups.items():
 branch='decomp-native'if repo==repos['runtime']else'main'
 if repo not in state:
  gh('release','create',tag,'--repo',repo,'--target',branch,'--title','v0.4.1 — Tag Team + Real Power Scale (PC)','--notes-file',R/'RELEASE_NOTES.md','--draft')
  value=json.loads(gh('api',f'repos/{repo}/releases/tags/{tag}'));state[repo]={'id':value['id']};statepath.write_text(json.dumps(state,indent=2))
 current=json.loads(gh('api',f'repos/{repo}/releases/{state[repo]["id"]}'))
 remote={a['name']:a for a in current['assets']}
 for p in assets:
  if p.name not in remote:
   print('Uploading',repo,p.name,flush=True);gh('release','upload',tag,p,'--repo',repo)
 current=json.loads(gh('api',f'repos/{repo}/releases/{state[repo]["id"]}'));remote={a['name']:a for a in current['assets']};checks[repo]=[]
 for p in assets:
  a=remote[p.name];h=sha(p)
  assert a['state']=='uploaded'and a['size']==p.stat().st_size and a.get('digest')=='sha256:'+h,(repo,p.name,'remote identity mismatch')
  checks[repo].append(dict(name=p.name,sha256=h,bytes=a['size'],url=a['browser_download_url']))
# Publish only after both complete draft releases have verified uploaded bytes.
for repo in groups:
 gh('release','edit',tag,'--repo',repo,'--draft=false','--latest')
 value=json.loads(gh('api',f'repos/{repo}/releases/tags/{tag}'));assert not value['draft']and not value['prerelease']
 state[repo].update(url=value['html_url'],published=True,assets=checks[repo])
(R/'publication.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
print('PUBLISHED AND VERIFIED',json.dumps({repo:s['url']for repo,s in state.items()}),flush=True)
