"""Claude: read-only lock-on / target probe for the ki-blast bug (workstream: targeting).

For every HUMAN fighter in a captured team match, every ~0.1 s, record only on change:
 - the physical index and character the pair-local target table (0xD8000 + 4*physical) points at,
   with that target's HP, present flag and action id;
 - the human's own action id and the three delayed-damage words (actor+3480/3500/3512) that make
   the manual switch defer;
 - lock-on queue counters (CONTROL 0x073D6800: frames+12, switches+16, queued+20, expired+24,
   cancelled+28, pending[i]+0x100+4*i, held[i]+0x100+48+4*i).
Layout: lockon_switch.py / lockon_queue.py / fresh_team_combat.py. Small reads only (no RAM dump), so
the controller session is never starved. Writes JSON lines to power-scale-trial/probe-target/.
Never writes game memory.
"""
from pathlib import Path
import json,struct,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import pine

OUT=TRIAL/'probe-target'
PORT=int(sys.argv[1]) if len(sys.argv)>1 else 28012
TABLE,POINTERS,MODE=0xD8000,0xD8040,0xD8080
CONTROL=0x073D6800
ROW_BASE,ROW_BYTES,SLOT=0x9A4,0xA4,0x994
NAMES={}
try:
    for c in json.loads((TRIAL/'controller/game/assets/characters.json').read_text(encoding='utf-8'))['characters']:NAMES[c['character_id']]=c['name']
except OSError:pass

def fighter(p,physical):
    actor=p.read_u32(POINTERS+4*physical)
    if not 0x100000<=actor<=0x7ff0000:return None
    slot=p.read_u32(actor+SLOT)
    if slot>=5:return None
    row=actor+ROW_BASE+slot*ROW_BYTES
    c,costume,present=struct.unpack('<3I',p.read(row,12))
    return dict(actor=actor,character=c,name=NAMES.get(c,'?'),present=present,hp=p.read_u32(row+64),
                action=p.read_u32(actor+0x948),human=p.read_u32(actor+0x1278))

def snapshot(p):
    if p.read_u32(MODE)!=1:return None
    count=p.read_u32(MODE+4)
    if not 2<=count<=12:return None
    fighters=[fighter(p,i) for i in range(count)]
    control=struct.unpack('<8I',p.read(CONTROL,32))
    out=[]
    for i,f in enumerate(fighters):
        if f is None or not f['human']:continue
        t=p.read_u32(TABLE+4*i)
        target=fighters[t] if t<count else None
        pending=[p.read_u32(f['actor']+o) for o in (3480,3500,3512)]
        out.append(dict(physical=i,name=f['name'],action=f['action'],hp=f['hp'],pending=pending,
            target_physical=t,target=None if target is None else dict(name=target['name'],hp=target['hp'],present=target['present'],action=target['action']),
            queue=dict(pending=p.read_u32(CONTROL+0x100+4*i),held=p.read_u32(CONTROL+0x100+48+4*i))))
    return dict(count=count,switches=control[4],queued=control[5],expired=control[6],cancelled=control[7],humans=out)

def main():
    OUT.mkdir(exist_ok=True)
    path=OUT/(time.strftime('%Y%m%d-%H%M%S')+'.jsonl')
    print('target probe writing',path,flush=True)
    last=None;start=time.monotonic()
    while True:
        try:
            with pine.PineClient(port=PORT,timeout=2) as p:
                while True:
                    s=snapshot(p)
                    key=json.dumps(s,sort_keys=True)
                    if s is not None and key!=last:
                        with path.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(t=round(time.monotonic()-start,2),**s))+'\n')
                        for h in s['humans']:
                            t=h['target'] or {}
                            print(time.strftime('%H:%M:%S'),h['name'],'-> target',h['target_physical'],t.get('name'),'hp',t.get('hp'),'pending',h['pending'],'sw',s['switches'],flush=True)
                    last=key;time.sleep(.1)
        except (OSError,pine.PineError,struct.error):time.sleep(1)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
