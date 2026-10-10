"""Execute emitted CPU ASSIST/REGISTER; test bounded read-only trace lifecycle.

ELIGIBLE is a controlled boundary here (including rejected/busy cases).
This tests scheduling and registration, not live range/ownership admission.
"""
from pathlib import Path
import struct
import copy
import sys
from unittest.mock import patch

sandbox = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(sandbox), str(sandbox/'power-scale-trial/controller/game/tools')]
from codex_roster_overlay import install
install()
import beam_struggle as b
import beam_assist_diagnostics as trace

MASK=(1<<64)-1
def signed(n): return n-(1<<64) if n & (1<<63) else n

class Machine:
    def __init__(self, eligible=1, stock=b.STOCK, side_word=0, due=True):
        self.mem={};self.regs=[0]*32;self.calls=[];self.accepted=eligible
        self.manager=0x1800000;self.actors=[0x1900000+i*0x10000 for i in range(4)]
        self.regs[4]=1;self.regs[29]=0x7FFE000;self.regs[31]=0x6000000
        for at,data in [(b.ASSIST,b.assist_code()),(b.REGISTER,b.register_code()),
                        (b.FREE,b.free_code()),(b.SYNC,b.sync_code())]:self.put(at,data)
        self.word(b.core.ACTORS,self.manager);self.word(b.CONTROL+b.C['count'],4)
        self.word(b.CONTROL+b.C['intro'],60);self.word(b.CONTROL+b.C['serial'],1)
        self.word(b.CONTROL+b.C['assist'],1);self.word(b.CONTROL+b.C['assist_cpu'],1)
        self.put(b.CONTROL+b.C['range2'],struct.pack('<f',150**2))
        self.word(self.manager+64,2);self.word(b.participation.CONTROL+12,15)
        self.word(b.beam.CONTROL+24,1);self.word(b.beam.CONTROL+16,2)
        self.word(self.manager+80,72 if due else 73) # CPU physical 2: intro+8+4
        self.word(self.manager+88,side_word);self.word(b.CONTROL+b.C['trans_action'],11)
        self.word(b.beam.CONTROL+64,self.actors[0]);self.word(self.actors[0]+2376,304)
        self.word(b.beam.CONTROL+68,self.actors[1]);self.word(self.actors[1]+2376,304)
        self.word(b.beam.CONTROL+80,0);self.word(b.beam.CONTROL+84,1)
        for i,actor in enumerate(self.actors):
            self.word(b.core.POINTERS+i*4,actor);self.word(actor+0x1278,1)
            self.word(actor+12,i);self.word(b.core.MODELS+i*4,0x1A00000+i*0x10000)
            self.word(0x1A00000+i*0x10000+16,i);self.word(0x1A00000+i*0x10000+4,1)
            self.word(actor+0x9E4+20,stock)
            self.word(actor+0x9E4,100000)
    def put(self,at,data):self.mem.update((at+i,v) for i,v in enumerate(data))
    def word(self,at,value):self.put(at,struct.pack('<I',value&0xFFFFFFFF))
    def get(self,at,size=4):return int.from_bytes(bytes(self.mem.get(at+i,0) for i in range(size)),'little')
    def run(self):
        pc=b.ASSIST;pending=None
        for _ in range(10000):
            if pc==0x6000000: return
            if pc in (b.ELIGIBLE,b.SET_ACTION):
                if pc==b.ELIGIBLE:self.regs[2]=(self.accepted if self.regs[4]==2 else 0)&MASK
                else:self.calls.append(tuple(self.regs[r] for r in (4,5)))
                pc=self.regs[31];pending=None;continue
            ins=self.get(pc);op=ins>>26;rs=ins>>21&31;rt=ins>>16&31;rd=ins>>11&31;sh=ins>>6&31;fn=ins&63
            imm=ins&65535;si=imm if imm<32768 else imm-65536;target=None
            x,y=self.regs[rs],self.regs[rt];addr=(x+si)&0xFFFFFFFF
            if op==0:
                if fn in (0x21,0x2D):self.regs[rd]=x+y
                elif fn==0x23:self.regs[rd]=(x-y)&0xFFFFFFFF;self.regs[rd]=self.regs[rd] if self.regs[rd]<0x80000000 else self.regs[rd]|0xFFFFFFFF00000000
                elif fn==0:self.regs[rd]=(y&0xFFFFFFFF)<<sh
                elif fn==2:self.regs[rd]=(y&0xFFFFFFFF)>>sh
                elif fn==4:self.regs[rd]=y<<(x&31)
                elif fn==0x25:self.regs[rd]=x|y
                elif fn==0x2A:self.regs[rd]=int(signed(x)<signed(y))
                elif fn==0x2B:self.regs[rd]=int(x<y)
                elif fn==8:target=x&0xFFFFFFFF
                else:raise AssertionError((hex(pc),hex(ins)))
            elif op==9:
                value=(x+si)&0xFFFFFFFF;self.regs[rt]=value if value<0x80000000 else value|0xFFFFFFFF00000000
            elif op==15:self.regs[rt]=imm<<16
            elif op==13:self.regs[rt]=x|imm
            elif op==12:self.regs[rt]=x&imm
            elif op==11:self.regs[rt]=int(x<(si&MASK))
            elif op in (35,55):
                value=self.get(addr,4 if op==35 else 8)
                self.regs[rt]=value if op==55 or value<0x80000000 else value|0xFFFFFFFF00000000
            elif op in (43,63):self.put(addr,(y&((1<<(32 if op==43 else 64))-1)).to_bytes(4 if op==43 else 8,'little'))
            elif op in (4,5):
                if (x==y)==(op==4):target=pc+4+si*4
            elif op==1:
                if (signed(x)<0 if rt==0 else signed(x)>=0):target=pc+4+si*4
            elif op in (6,7):
                if (signed(x)<=0 if op==6 else signed(x)>0):target=pc+4+si*4
            elif op in (2,3):
                target=((pc+4)&0xF0000000)|((ins&0x3FFFFFF)<<2)
                if op==3:self.regs[31]=pc+8
            else:raise AssertionError((hex(pc),hex(ins)))
            self.regs=[r&MASK for r in self.regs];self.regs[0]=0
            pc,pending=(pc+4 if pending is None else pending),target
        raise AssertionError('CPU assist did not return')

for kwargs,works in (({},True),({'side_word':-1},True),({'side_word':1},False),
                     ({'due':False},False),({'stock':b.STOCK-1},False),
                     ({'eligible':0},False),({'eligible':-1},False)):
    machine=Machine(**kwargs);machine.run()
    assert bool(machine.calls)==works,(kwargs,machine.calls)
    if works:
        assert machine.calls==[(machine.actors[2],11)]
        assert machine.get(b.CONTROL+b.TELEMETRY['triggers'])==1
        assert machine.get(b.CONTROL+b.SLOTS+b.S['state'])==b.P_MOVING
    if kwargs.get('stock')==b.STOCK-1:
        assert machine.get(b.CONTROL+b.TELEMETRY['assist_no_stock'])==1

machine=Machine()
machine.word(machine.actors[0]+0x1278,0)
for at,value in ((b.CONTROL,b.MAGIC),(b.CONTROL+0x10,b.VERSION),
                 (b.CONTROL+4,machine.manager),(b.beam.CONTROL,b.beam.MAGIC),
                 (b.beam.CONTROL+4,machine.manager),(b.beam.CONTROL+8,4)):
    machine.word(at,value)
class ReadOnlyClient:
    def read(self,at,size):return machine.get(at,size).to_bytes(size,'little')
    def read_u32(self,at):return machine.get(at)
value=trace.snapshot(ReadOnlyClient())
assert value['active']==2 and value['actors'][2]['stock']==b.STOCK
assert value['actors'][2]['schedule_due'] and len(value['slots'])==8
assert value['counters']['assists_cpu']==0
assert value['human_struggle_sides']==[0]
assert value['actors'][2]['sample_gate']=='ready-at-sample'
def case(mutate, expected):
    sample=copy.deepcopy(value);actor=sample['actors'][2];mutate(sample,actor)
    actual=trace.classify(sample,actor)
    assert actual['sample_gate']==expected,(expected,actual)
    return actual
case(lambda v,a:v.update(assist=0),'assist-disabled')
case(lambda v,a:v.update(cpu=0),'cpu-assist-disabled')
case(lambda v,a:v.update(phase=4),'coordinator-not-push-phase')
case(lambda v,a:v['slots'][0].update(actor=a['address']),'eligible-pending-or-releasing')
case(lambda v,a:v.update(participation=[3,0]),'eligible-not-participating')
case(lambda v,a:a.update(hp=0),'eligible-dead')
case(lambda v,a:a.update(hp=None),'eligible-invalid-hp-row')
case(lambda v,a:a['actions'].__setitem__(1,264),'eligible-busy-requested-or-queued')
case(lambda v,a:a['actions'].__setitem__(0,264),'eligible-busy-current')
case(lambda v,a:v.update(ffa=True),'eligible-no-unique-allied-side')
case(lambda v,a:[slot.update(actor=123) for slot in v['slots'][:4]],'eligible-slot-full')
case(lambda v,a:a.update(model_valid=False),'eligible-invalid-model')
case(lambda v,a:a.update(model_position=(150.,0.,0.)),'eligible-out-of-range')
case(lambda v,a:a.update(schedule_due=False),'schedule-not-due')
case(lambda v,a:v.update(side_word=1),'lead-rule')
case(lambda v,a:a.update(stock=b.STOCK-1),'insufficient-stock')
case(lambda v,a:v['actors'][0]['actions'].__setitem__(0,11),'register-ally-not-in-struggle-action')
case(lambda v,a:v.update(side_word=-1),'ready-at-sample')
for margin,expected in ((-1,'lead-rule'),(0,'ready-at-sample'),(1,'ready-at-sample')):
    def side1(v,a):
        a['physical']=3;v['side_word']=margin
    actual=case(side1,expected)
    assert actual['assist_side']==1
machine.word(b.beam.CONTROL+4,machine.manager+4)
assert trace.snapshot(ReadOnlyClient()) is None

recorder=trace.Recorder();messages=[]
value=dict(manager=1,count=4,serial=1,active=2,counters={'triggers':0})
with patch.object(trace,'snapshot',return_value=value):
    recorder.tick(None,messages.append,lambda:0)
    recorder.tick(None,messages.append,lambda:.1)
assert len(messages)==1 and 'struggle started' in messages[0]
ended=dict(value,active=0,counters={'triggers':1,'assists_cpu':1})
with patch.object(trace,'snapshot',return_value=ended):recorder.tick(None,messages.append,lambda:1)
assert 'struggle ended' in messages[-1] and 'assists_cpu' in messages[-1]
recorder.finish(messages.append);size=len(messages);recorder.finish(messages.append)
assert len(messages)==size
print('PASS: emitted CPU schedule/REGISTER, sampled gate reasons for both sides, range/busy/pending/slot/stock/phase, bounded start/end/counter trace')
