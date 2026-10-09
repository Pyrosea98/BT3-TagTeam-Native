"""Audit actual refusal rows and captured native fusion recipes, read-only."""
import collections,json,re,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path[:0]=[str(root),str(root/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import cpu_tactics as cpu
labels={r['character_id']:r['name'] for r in json.loads((root/'roster-assets/characters.json').read_text(encoding='utf-8'))['characters']}
tiers,families=cpu.tables()
log=root/'power-scale-trial/log-archive/runner-revive-hud-live.log'
rows=collections.defaultdict(lambda:dict(count=0,forms=set()))
for line in log.read_text(encoding='utf-8').splitlines():
    if 'reason=unreviewed-zero-cost-or-revert' not in line:continue
    cid=int(re.search(r' cid=(\d+)',line)[1]);entry=rows[cid];entry['count']+=1
    entry['forms'].add(re.search(r' forms=([^ ]+)',line)[1])
report=[]
for cid,entry in sorted(rows.items()):
    zero=[]
    for forms in sorted(entry['forms']):
        for pair in forms.split(','):
            dst,cost=map(int,pair.split(':'))
            if dst>=253 or cost:continue
            upward=bool(families[cid] and families[cid]==families[dst] and tiers[dst]>tiers[cid])
            zero.append(dict(destination=dst,label=labels.get(dst),admitted_by_reviewed_table=upward))
    report.append(dict(character=cid,label=labels.get(cid),refusals=entry['count'],zero_cost_slots=zero))
for src,dst in [(67,190),(67,192),(190,192),(149,177),(149,122)]:
    assert families[src]==families[dst]!=0 and tiers[src]<tiers[dst]
for src,dst in [(192,67),(149,51),(122,177),(149,192)]:
    assert not(families[src]==families[dst]!=0 and tiers[src]<tiers[dst])
assert families[194]==families[195]==0
capture=root/'power-scale-trial/controller/game/analysis/prepared-states/20261008-152903-d77051ee/16-ready-held.bin'
ram=capture.read_bytes();u=lambda at:struct.unpack_from('<I',ram,at)[0]
recipes={}
for i in (1,3):
    model=u(0x31c640+4*i);cid=u(model+12);param=u(model+0x91c)
    recipes[cid]=dict(destinations=list(ram[param+0x98:param+0x9c]),costs=list(ram[param+0x9c:param+0xa0]),
        results=list(ram[param+0xb4:param+0xb7]),fusion_costs=list(ram[param+0xae:param+0xb1]),
        fusion_kinds=list(ram[param+0xb1:param+0xb4]),restoration_partners=list(ram[param+0xb7:param+0xba]),
        partners=[list(ram[param+0xba+4*j:param+0xbe+4*j]) for j in range(3)])
assert recipes[67]['destinations']==[190,192,255,255]
assert recipes[67]['results']==[255]*3
assert recipes[194]['destinations']==[255]*4
assert not any(cid in p for p in recipes[194]['partners'] for cid in (67,190,192))
# Native getters authenticate result B4, restoration partner B7, partners BA.
from prototype import ROOT,elf_reader
from native_map import elf_path
read=elf_reader(elf_path(ROOT))[2]
assert struct.unpack('<I',read(0x20e360,4))[0]==0x920200b4
assert struct.unpack('<I',read(0x20e390,4))[0]==0x920200b7
assert struct.unpack('<I',read(0x20e3d4,4))[0]==0x922200ba
out=dict(log=str(log),refusals=report,captured_recipes=recipes,
    limits='Captured base Black and Zamasu do not have a Black/Zamasu pair; transformed Black recipes not captured, no blanket ISO-wide no-fusion claim.')
(root/'power-scale-trial/cpu-free-form-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('PASS audit all',sum(r['refusals'] for r in report),'refusals across',len(report),'identities; reviewed upward/revert/cross-family checks; actual native recipe getters')
