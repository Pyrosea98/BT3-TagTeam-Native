import sys,struct,collections,numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import claude_menu_names_audit as aud
ramb=(TRIAL/'select-screen-ram-scene26.bin').read_bytes()
por=aud.iso_portraits()
# portrait start addresses: use the 4th window (offset len//2) agreement with the 5th (len-0x80)
starts={}
for j,pb in enumerate(por):
    a=ramb.find(pb[len(pb)//2:len(pb)//2+48],0x100000,0x8000000)
    b=ramb.find(pb[len(pb)-0x80:len(pb)-0x80+48],0x100000,0x8000000)
    if a>=0 and b>=0 and a-len(pb)//2==b-(len(pb)-0x80):starts[j]=a-len(pb)//2
print('portrait starts located',len(starts))
vals=sorted(starts.items());print('first',[(j,hex(a)) for j,a in vals[:3]],'last',[(j,hex(a)) for j,a in vals[-2:]])
u32=np.frombuffer(ramb,dtype='<u4')
want=np.array([starts[j] for j,_ in vals],dtype=np.uint32)
hit_pos=collections.defaultdict(list)
mask=np.isin(u32,want)
pos=np.nonzero(mask)[0]
inv={a:j for j,a in starts.items()}
print('u32 words equal to a portrait start:',len(pos))
rows=[(int(p)*4,inv[int(u32[p])]) for p in pos]
# show clusters
rows.sort()
clusters=[];cur=[rows[0]] if rows else []
for r in rows[1:]:
    if r[0]-cur[-1][0]<=64:cur.append(r)
    else:
        clusters.append(cur);cur=[r]
if cur:clusters.append(cur)
clusters=[c for c in clusters if len(c)>=6]
print('clusters with >=6 pointers',len(clusters))
for c in clusters[:6]:print(hex(c[0][0]),'->',hex(c[-1][0]),'n',len(c),'iso idx',[x[1] for x in c[:14]])

import json
missing=[j for j in range(len(por)) if j not in starts]
print('unlocated portrait indices',len(missing),missing)
p=json.load(open(TRIAL/'menu-names-map-proposal.json'))
changed={int(k) for k,v in p.items() if v['iso_index']!=int(k)}
print('slots whose runtime name differs from ISO name:',len(changed))
print('unlocated AND changed',len(set(missing)&changed),'unlocated only',sorted(set(missing)-changed),'changed only',sorted(changed-set(missing))[:40])
# are RAM block positions consistent with ISO sizes?
prev=None;ok=0;bad=[]
for j in sorted(starts):
    if j-1 in starts:
        d=starts[j]-starts[j-1]
        if d==len(por[j-1]) or d==((len(por[j-1])+0xF)&~0xF) or d==((len(por[j-1])+0x3F)&~0x3F):ok+=1
        else:bad.append((j,d,len(por[j-1])))
print('consecutive neighbours consistent with ISO size (aligned):',ok,'inconsistent',len(bad),bad[:6])

print('=== RAM order of located portraits ===')
order=sorted(starts.items(),key=lambda kv:kv[1])
seq=[];prev=None
for j,a in order:
    if prev is not None and a-prev not in (5472,5504):seq.append(f'| gap {a-prev:+d} |')
    seq.append(str(j));prev=a
print(' '.join(seq))

print('=== slot assignment from RAM order ===')
slot_of={};dups=collections.defaultdict(list);slot=0;prev_addr=None;prev_j=None;unknown_slots=[]
for j,a in order:
    if prev_addr is not None:
        if a==prev_addr:
            dups[slot].append(j);continue
        gap=a-prev_addr-len(por[prev_j])
        # entries missing between = number of unknown-size entries filling gap (5472 or 5504 each)
        n=round(gap/5488) if gap>0 else 0
        for _ in range(n):slot+=1;unknown_slots.append(slot)
        slot+=1
    slot_of[j]=slot;prev_addr=a;prev_j=j
print('slots used',slot+1,'of 253; unknown-content slots',len(unknown_slots),unknown_slots[:70])
agree=0;dis=[]
for j,s in sorted(slot_of.items()):
    pr=p.get(str(s));prop=None if not pr else pr['iso_index']
    if prop==j:agree+=1
    else:dis.append((s,j,prop))
print('slot->iso agree with name-based proposal',agree,'disagree',len(dis),dis[:25])
out={str(s):dict(iso_index=j,ram_address=hex(starts[j]),source='pixel-match') for j,s in slot_of.items()}
for j,sl in dups.items():
    for x in sl:out.setdefault(str(j),{}).setdefault('also_identical_iso',[]).append(x)
json.dump(dict(base=hex(order[0][1]),slots=out,unknown_slots=unknown_slots,duplicates={str(k):v for k,v in dups.items()}),open(TRIAL/'portrait-slot-map.json','w'),indent=1)

print('=== final map ===')
final={};src={}
for j,s in slot_of.items():final[s]=j;src[s]='ram-order (portrait found verbatim in the game RAM at its slot position)'
for s in range(253):
    if s in final:continue
    pr=p.get(str(s))
    if pr and pr['iso_index'] is not None and pr['iso_index'] not in final.values():
        final[s]=pr['iso_index'];src[s]='name match, consistent with RAM order (slot position holds a non-verbatim image)'
claimed=set(final.values());free_iso=[j for j in range(253) if j not in claimed]
free_slots=[s for s in range(253) if s not in final]
print('resolved',len(final),'unresolved slots',free_slots,'unclaimed ISO portraits',free_iso)
res=dict(note='slot = engine character slot of the runtime table (0xFD8AD0); iso_index = index into the ISO UI portrait list (PZS3US1.AFS entry 450 -> ui[31]); derived from the order of the portrait block in a live character-select RAM dump (scene 0x26)',
         map={str(s):dict(iso_index=final[s],source=src[s]) for s in sorted(final)},unresolved_slots=free_slots,unclaimed_iso=free_iso)
json.dump(res,open(TRIAL/'portrait-slot-map.json','w'),indent=1)
