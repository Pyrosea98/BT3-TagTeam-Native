"""Bounded, read-only model receipts for the reported Black/Zamasu cinematic."""
import struct
import time
from atomic_files import write_json
import fresh_team_combat as core
from native_map import A

def valid(pointer,size):
    return pointer%4==0 and 0x100000<=pointer<=0x8000000-size

def arm(client,owner,physical,row,count):
    if row[1] not in (192,194) or row[7]!=1 or row[8]>=5:return
    partner=2*row[8]+(physical&1)
    if partner>=count or partner==physical:return
    manager=client.read_u32(A(0x2FEB14))
    actors=[client.read_u32(core.POINTERS+4*i) for i in (physical,partner)]
    if any(not valid(p,0x1600) for p in actors):return
    owner.fusion_cinematic_capture=dict(manager=manager,count=count,seats=[physical,partner],
        actors=actors,request=row[0],started=time.monotonic(),last=0,samples=[])

def poll(client,owner):
    receipt=getattr(owner,'fusion_cinematic_capture',None)
    if not receipt:return
    now=time.monotonic()
    if now-receipt['started']>20 or len(receipt['samples'])>=8:
        owner.fusion_cinematic_capture=None;return
    if now-receipt['last']<.25:return
    if client.read_u32(A(0x2FEB14))!=receipt['manager'] or client.read_u32(core.MODE+4)!=receipt['count']:
        owner.fusion_cinematic_capture=None;return
    records=[]
    for seat,actor in zip(receipt['seats'],receipt['actors']):
        if client.read_u32(core.POINTERS+4*seat)!=actor or client.read_u32(actor)!=seat:
            owner.fusion_cinematic_capture=None;return
        mid=client.read_u32(actor+12)
        model=client.read_u32(core.MODELS+4*mid) if mid<12 else 0
        records.append(dict(seat=seat,actor=actor,action=client.read_u32(actor+2376),
            model_slot=mid,model=model,model_words=list(struct.unpack('<8I',client.read(model,32))) if valid(model,32) else None,
            fusion_words=list(struct.unpack('<12I',client.read(actor+0x12CC,48)))))
    if not any(r['action'] in (241,242) for r in records):return
    camera=client.read_u32(0x304270-22180)
    sample=dict(seconds=round(now-receipt['started'],3),actors=records,camera=camera,
        camera_models=list(struct.unpack('<2I',client.read(camera+768,8))) if valid(camera,776) else None)
    receipt['last']=now;receipt['samples'].append(sample)
    write_json(owner.freeze_folder()/'black-zamasu-cinematic.json',receipt)
