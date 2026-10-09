"""Exercise the actual release loop with scripted guest memory, no sockets/game."""
import sys, struct, contextlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import fresh_team_trainer as f

class Guest:
    def __init__(self,session,step,changed=False):self.session=session;self.step=step;self.changed=changed
    def status(self):return 'running'
    def read_u32(self,at):
        if at==f.A(0x2FEB14):return 0x180000+(4 if self.changed else 0)
        effects=(f.extra_ground_effects,f.extra_generic_effects,f.extra_extended_auras,f.extra_charge_aura,
                 f.extra_special_pools,f.spawn_placement,f.team_participation)
        for mod in effects:
            if at==mod.CONTROL:return 5
            if at==mod.CONTROL+4:return 0x180000
        if at==f.team_start_gate.CONTROL:return int(not self.session.no_ack or self.step<3)
        if at==f.team_intro.CONTROL:return 1
        if at in (f.team_start_gate.CONTROL+8,f.team_intro.CONTROL+8):return 0x180000
        if at==f.team_start_gate.CONTROL+12:return 4
        if at==f.team_start_gate.CONTROL+20:return int(self.step>=3 and not self.session.no_ack)
        if at==f.team_start_gate.CONTROL+24:return int(self.step>=1)
        if at==f.team_intro.CONTROL+20:return int(self.step>=2)
        if at==f.team_intro.BATTLE:return 0x190000
        if at==0x190000:return 3
        if at==f.fresh_memory.CONTROL+80:return int(self.step<3)
        for i in range(4):
            if at in (f.combat.POINTERS+4*i,f.team_start_gate.CONTROL+0x80+4*i):return 0x200000+i*0x2000
            if at==0x200000+i*0x2000:return i
            if at in (0x200000+i*0x2000+0x1278,f.team_start_gate.CONTROL+0x40+4*i):return int(i>0)
        return 0
    def read(self,at,n):
        if at==f.ACK_ADDRESS:return b'M'*16
        if at==f.combat.MODE:return struct.pack('<4I',1,4,0x180000,4)
        return b'\0'*n
    def write(self,at,data):self.session.requests.append((at,data))
    def write_u32(self,at,value):raise AssertionError('Unexpected guest write')

def trial(intro,changed=False,mode='teams',humans=1,no_ack=False,native=False):
    s=f.Session.__new__(f.Session);s.play_intro=intro;s.requests=[];s.step=-1;s.accepted=[]
    s.battle_mode=mode;s.humans=humans;s.no_ack=no_ack;s.native_runtime=native
    @contextlib.contextmanager
    def client(*args):
        s.step+=1;yield Guest(s,s.step,changed and s.step>=2)
    s.client=client;s.running_client=client
    s.start_accepted_callback=lambda p:s.accepted.append((s.step,p.read_u32(f.team_start_gate.CONTROL+20)))
    f.Session.release_start.__wrapped__(s)
    return s

old=f.time.sleep;f.time.sleep=lambda _:None
try:
    s=trial(True);assert s.accepted==[(2,0)] and s.step==3
    assert s.requests[0][0]==f.team_intro.REQUEST
    s=trial(False);assert s.accepted==[(3,1)]
    for mode,humans in [('teams',0),('teams',2),('ffa',0),('ffa',1),('ffa',2),('coop',2),('training',1),('training_coop',2)]:
        s=trial(False,mode=mode,humans=humans);assert s.requests[0][0]==f.team_start_gate.REQUEST
        s=trial(False,mode=mode,humans=humans,no_ack=True);assert s.accepted==[(3,0)]
    for mode,humans in [('ffa',1),('ffa',4),('coop',2),('training',1),('training_coop',2)]:
        s=trial(False,mode=mode,humans=humans,native=True)
        assert s.requests[0]==(f.team_start_gate.REQUEST,struct.pack('<I',2)) and s.accepted==[(1,0)] and s.step==3
    try:trial(True,True)
    except ValueError as error:assert 'changed before start' in str(error)
    else:raise AssertionError('Identity change was accepted')
finally:f.time.sleep=old
print('PASS actual start loop: intro acceptance before release, no-intro ACK, identity rejection')
