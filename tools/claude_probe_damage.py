"""Claude: read-only damage logger for an ordinary 1v1 (workstream I, "damage mapping").

Polls the two leader actors over PINE (port 28012 native, or pass 28011 for PCSX2) at ~40 Hz and records, per side:
character, costume, current/max HP from the native roster row, and the action id.
Every HP change is logged with the delta and both sides' action ids, so we can see
how much damage each attack type really does and whether a fighter takes damage at all.
Layout (selected_team_capture.py): manager=[0x2FEB14], actor array=[manager+4],
actor side s = array + s*0x1600, row = actor + 0x9A4 + slot*0xA4 (character +0,
costume +4, present +8, hp +64, max_hp +68), slot=[actor+0x994], action=[actor+0x948].
Writes JSON lines to power-scale-trial/probe-damage/. Never writes game memory.
"""
from pathlib import Path
import json,struct,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine

OUT=TRIAL/'probe-damage'
PORT=int(sys.argv[1]) if len(sys.argv)>1 else 28012   # 28012 = native trial, 28011 = PCSX2
ACTOR_BYTES,ROW_BASE,ROW_BYTES,SLOT=0x1600,0x9A4,0xA4,0x994
NAMES={}
try:
    for c in json.loads((TRIAL/'controller/game/assets/characters.json').read_text(encoding='utf-8'))['characters']:NAMES[c['character_id']]=c['name']
except OSError:pass

def sides(p):
    manager=p.read_u32(0x2FEB14)
    if not 0x100000<=manager<=0x7ff0000 or p.read_u32(manager)!=2:return None
    array=p.read_u32(manager+4)
    if not 0x100000<=array<=0x7000000:return None
    out=[]
    for side in range(2):
        actor=array+side*ACTOR_BYTES
        if p.read_u32(actor)!=side:return None
        slot=p.read_u32(actor+SLOT)
        if slot>=5:return None
        row=actor+ROW_BASE+slot*ROW_BYTES
        c,costume,present=struct.unpack('<3I',p.read(row,12))
        hp,mx=struct.unpack('<2I',p.read(row+64,8))
        out.append(dict(side=side,character=c,name=NAMES.get(c,'?'),costume=costume,hp=hp,max_hp=mx,action=p.read_u32(actor+0x948)))
    return out

def main():
    OUT.mkdir(exist_ok=True)
    path=OUT/(time.strftime('%Y%m%d-%H%M%S')+'.jsonl')
    print('damage probe writing',path,flush=True)
    last=None;start=time.monotonic();match=0
    while True:
        try:
            with pine.PineClient(port=PORT,timeout=2) as p:
                while True:
                    s=sides(p)
                    if s is None:
                        if last is not None:print(time.strftime('%H:%M:%S'),'battle ended',flush=True)
                        last=None;time.sleep(.5);continue
                    now=round(time.monotonic()-start,2)
                    if last is None or [x['character'] for x in s]!=[x['character'] for x in last] or [x['costume'] for x in s]!=[x['costume'] for x in last]:
                        match+=1
                        rec=dict(t=now,event='start',match=match,fighters=s)
                        print(time.strftime('%H:%M:%S'),'START',[(x['name'],x['costume'],x['hp'],x['max_hp']) for x in s],flush=True)
                        with path.open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
                    else:
                        for a,b in zip(last,s):
                            if a['hp']!=b['hp']:
                                other=s[1-b['side']]
                                rec=dict(t=now,event='hp',match=match,side=b['side'],name=b['name'],costume=b['costume'],
                                    hp=b['hp'],max_hp=b['max_hp'],delta=b['hp']-a['hp'],own_action=b['action'],other_action=other['action'],other_name=other['name'])
                                with path.open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
                    last=s;time.sleep(.025)
        except (OSError,pine.PineError,struct.error):time.sleep(1)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
