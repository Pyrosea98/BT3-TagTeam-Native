"""Watch a native trial for a guest freeze and save the loader/hold state when it happens.

Read-only: it only reads guest RAM over the loopback PINE bridge (28012).
Detects a freeze when the runner's `[fps] gframe=` counter stops advancing.
Run from the workspace root with the experiments venv python while the trial runs.
"""
from pathlib import Path
import json,re,struct,sys,time

HERE=Path(__file__).resolve().parent
TRIAL=HERE/'power-scale-trial'
TOOLS=TRIAL/'controller/game/tools'
LOG=TRIAL/'runner.log'
STALL_SECONDS=8
sys.path.insert(0,str(TOOLS))
import pine
import native_preparation as native

def last_gframe():
    size=LOG.stat().st_size
    with LOG.open('rb') as stream:
        stream.seek(max(0,size-262144))
        text=stream.read().decode('utf-8',errors='replace')
    found=re.findall(r'\[fps\] GAME=[0-9.]+ gframe=(\d+)',text)
    return int(found[-1]) if found else None

def capture(folder):
    folder.mkdir(parents=True,exist_ok=True)
    with pine.PineClient(port=28012,timeout=10) as p:
        u=p.read_u32
        words=lambda base,count:[u(base+4*i) for i in range(count)]
        state=dict(time=time.strftime('%H:%M:%S'),
            transport=dict(magic=u(native.CONTROL),hold_request=u(native.CONTROL+16),hold_ack=u(native.CONTROL+20),
                manager=u(native.CONTROL+24),words=words(native.CONTROL,16)),
            native_manager=u(0x2feb14),battle_mode=u(0xd8080),
            hooks={hex(a):[u(a),u(a+4)] for a in (0x1c2a28,0x12bc9c,0x203830,0x2654d8,0x1d61f8,0x1d6360,0x203ba0)},
            disc_job_state=u(0x31e760),disc_words=words(0x31e760,64),
            loader_manager=u(0x2feb14) and words(u(0x2feb14),160),
            heap_bounds=[u(0x2ff084),u(0x2ff08c)])
        (folder/'state.json').write_text(json.dumps(state,indent=1,default=hex)+'\n')
        (folder/'ram.bin').write_bytes(native.read_ram(p))
    # Keep the runner/controller log tails: a continuous trace can grow very large.
    for name,keep in (('runner.log',4<<20),('controller.log',1<<20)):
        source=TRIAL/name
        if source.is_file():
            with source.open('rb') as stream:
                stream.seek(max(0,source.stat().st_size-keep))
                (folder/(name+'.tail')).write_bytes(stream.read())

def main():
    print('Watching',LOG,'for a freeze (gframe stalled %ds). Close the game to stop.'%STALL_SECONDS,flush=True)
    value=None;since=time.monotonic();done=False
    while True:
        try:
            now=last_gframe()
        except OSError:
            time.sleep(1);continue
        if now!=value:value,since,done=now,time.monotonic(),False
        elif value and not done and time.monotonic()-since>=STALL_SECONDS:
            folder=TRIAL/'freeze-captures'/time.strftime('%Y%m%d-%H%M%S')
            try:
                capture(folder);print('Freeze at gframe',value,'-> saved',folder,flush=True)
            except Exception as error:
                print('Freeze detected but capture failed:',error,flush=True)
            done=True
        time.sleep(1)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
