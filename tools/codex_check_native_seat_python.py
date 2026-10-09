"""Native input owns records without starting SDL or process-memory writers."""
from pathlib import Path
import os,sys,struct
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'power-scale-trial/controller/game/tools')]
os.environ['PS2X_NATIVE_SEAT_PADS']='1'
if '--roster' in sys.argv:
    from codex_roster_overlay import install
    install()
import quad_controller as pads,quad_menu_input as menu,controller_assignment as assignment,controller_mailbox as transport
class Memory:
    def __init__(self):self.mem={};self.writes=[]
    def read(self,at,size):return bytes(self.mem.get(at+i,0) for i in range(size))
    def write(self,at,data):
        self.mem.update((at+i,b) for i,b in enumerate(data));self.writes.append((at,len(data)))
    def read_u32(self,at):return struct.unpack('<I',self.read(at,4))[0]
    def write_u32(self,at,value):self.write(at,struct.pack('<I',value))
def forbidden(*a,**k):raise AssertionError('Native path invoked SDL/process-memory transport')
pads.ControllerCapture=forbidden
transport.Service=forbidden;transport.capability=forbidden
for cls in (pads.Bridge,menu.Bridge,assignment.Bridge):
    bridge=cls();assert bridge.capture is None and not bridge.poll(Memory());bridge.close()
p=Memory();owner=transport.Owner(1);assert owner.available(p)
owner.attach(p,'native-match');assert owner.service is None and not p.writes
scene=0x331DC8
p.write(menu.CODE,menu.payload());p.write_u32(menu.mode_menu.SCENE_MANAGER,scene)
p.write_u32(scene+0x18,40);p.write_u32(menu.guard.CONTROL,menu.guard.MAGIC)
p.writes.clear();owner=menu.Owner(1);owner.attach(p,'selection')
assert owner.service is None and p.read(menu.CONTROL,16)==struct.pack('<4I',menu.MAGIC,scene,2,1)
assert p.writes==[(menu.CONTROL,16)]
p.writes.clear();owner.attach(p,'selection');assert not p.writes
owner.close();p.write_u32(scene+0x18,39)
try:owner.attach(p,'wrong-scene')
except ValueError:pass
else:raise AssertionError('Native menu armed outside character selection')
assert not owner.capture
print('PASS native Python bridges skip SDL/transport; scoped menu arm once, invalid scene refused')
