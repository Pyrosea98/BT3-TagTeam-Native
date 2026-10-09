"""Ownership, cursor wrapping and surface handoff checks, without PINE."""
import struct
from types import SimpleNamespace as NS
from codex_native_mode_style import snapshot,install
OWNER=0x300000;CONTROL=0x7600000
class Memory:
    control=(123,2,0,0,180,OWNER,4)
    rows=(0,7,1,3,6)
    last=0xffffffff
    changed=False
    def read(self,address,length):
        if address==CONTROL:
            self.changed=not self.changed
            values=list(self.control);values[4]-=int(self.changed)
            return struct.pack('<7I',*values)
        data=bytearray(64);struct.pack_into('<5I',data,12,*self.rows);struct.pack_into('<2I',data,56,5,self.last)
        return bytes(data)
    def read_u32(self,address):return OWNER if address==44 else 0
menu=NS(CONTROL=CONTROL,MAGIC=123,PAGES=((0,7,1,3,6),),old=NS(MAIN_OBJECT=44),ready=lambda p:True)
p=Memory()
assert snapshot(menu,p)==(0,0),'signed -1 cursor must select first row'
p.last=3;assert snapshot(menu,p)==(0,4)
p.rows=(0,1,2,3,4);assert snapshot(menu,p) is None
p.rows=(0,7,1,3,6);p.control=(123,4,0,0,180,OWNER,4);assert snapshot(menu,p) is None
events=[]
class Surface:
    visible=True
    def hide(self,p):events.append('close');self.visible=False
class Controller:
    def tick(self,p,**kwargs):events.append('open-settings');self.settings_menu.active=True
menu.Controller=Controller;menu.localization=NS(ES={});menu.team_assignment=NS(STATE=0xa0)
install(menu,NS(CONTROL=80),Surface)
c=Controller();c._dbz_menu_surface=Surface();c.settings_menu=NS(active=True);c.team_menu=NS(active=False)
c.tick(p)
assert events==['close','open-settings'],'close must precede new native owner'
events.clear();c._dbz_menu_surface.visible=True;c.settings_menu.active=False
c.tick(p)
assert events==['open-settings'] and not c._dbz_menu_surface.visible,'never close a newly opened settings owner'
print('PASS actual mode snapshot: row ownership, unsigned cursor, lease changes, original menu exclusion')
print('PASS native mode/settings handoff: close-before-open and no late close of new owner')
