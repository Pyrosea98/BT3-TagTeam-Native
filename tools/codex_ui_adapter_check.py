"""Offline test of the real settings model/native publisher, no game/socket."""
import sys,tempfile,struct,json,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install as roster
roster()
from codex_dependency_check import check_dependencies
check_dependencies()
import codex_native_ui_adapter as ui
ui.install()
import ingame_settings as menu,mod_settings,webbrowser

class Client:
    packet=None
    revision=0
    writes={}
    acknowledge=True
    def _exchange(self,command,expected):
        if command[0]==17:
            assert len(command)==2177
            self.packet=command[1:];self.revision+=1
            return struct.pack('<I',1)
        words=ui.WORDS.unpack(self.packet[:128])
        return struct.pack('<8I',1,1,words[2],words[3],self.revision if self.acknowledge else 0,0,self.revision,2)
    def read(self,address,length):
        if address==menu.CONTROL:return struct.pack('<3I',menu.MAGIC,1,180)
        return b'\0'*length
    def read_u32(self,address):
        return menu.CROSS if address==menu.CONTROL+12 else 0
    def write_u32(self,address,value):self.writes[address]=value

with tempfile.TemporaryDirectory(dir=HERE/'power-scale-trial') as temp:
    mod_settings.SETTINGS_PATH=Path(temp)/'settings.json'
    c=Client();model=menu.Controller();model.open()
    model.publish(c)
    assert b'ABOUT / CREDITS' in c.packet[128:384]
    assert ui.WORDS.unpack(c.packet[:128])[19]==0
    model.press(menu.DOWN);assert model.index_row==0
    model.press(menu.CROSS);assert model.view=='page' and model.group==0
    model.press(menu.TRIANGLE);assert model.view=='index'
    model.publish(c);assert ui.WORDS.unpack(c.packet[:128])[19]==1
    model.press(menu.UP);model.press(menu.CROSS);assert model.view=='about'
    model.publish(c);assert ui.UI_BUILD.encode() in c.packet
    assert b'RidJuampa' in c.packet
    model.press(menu.TRIANGLE);assert model.view=='index'
    model.values['language']='es';model.save(exit=False)
    assert mod_settings.load_settings()['show_credits_at_startup'] is True
    model.values['show_credits_at_startup']=False;model.save(exit=False)
    assert mod_settings.load_settings()['show_credits_at_startup'] is False
    assert mod_settings.load_settings()['language']=='es'
    assert json.loads(mod_settings.SETTINGS_PATH.read_text(encoding='utf-8'))['language']=='es'
    model.open();assert model.values['language']=='es'
    pages=0
    for group in range(len(model.groups)):
        model.group=group;model.view='page'
        for row in range(0,len(model.fields()),7):
            model.row=row;model.publish(c);pages+=1
            assert ui.WORDS.unpack(c.packet[:128])[18]==1
    model.view='index';model.index_row=len(model.groups)+2
    model.press(menu.CROSS);assert model.view=='about'
    opened=[];webbrowser.open=lambda link:opened.append(link)
    model.publish(c);assert not opened
    assert ui.LINKS[0].encode() in c.packet and ui.LINKS[1].encode() in c.packet
    model.press(menu.CROSS);assert opened==[ui.LINKS[0]]
    model.press(menu.DOWN);model.press(menu.CROSS);assert opened[-1]==ui.LINKS[1]
    # The existing modal's visibility gate discards Cross until this exact
    # native revision has returned through GPU readback.
    c.acknowledge=False;model._poll(c);assert len(opened)==2
    assert c.writes[menu.CONTROL+8]==180
    model.press(menu.TRIANGLE);assert model.view=='index'
    print('PASS real settings pages:',pages,'language persistence, explicit links and input acknowledgement gate')
    surface=ui.Surface();surface.set_teams([dict(side=0,fighters=[dict(character_id=i)for i in range(4)]),dict(side=1,fighters=[dict(character_id=10+i)for i in range(3)])])
    for mode,humans in (('teams',4),('coop',4),('ffa',4),('training',1),('training_coop',2),('teams',0)):
        surface.set_mode(mode,humans);surface.send(1,c);words=ui.WORDS.unpack(c.packet[:128])
        seats=[(words[22]>>(3*i))&7 for i in range(7)]
        assert sorted(seat for seat in seats if seat)==list(range(1,humans+1))
        if mode in ('coop','training_coop'):assert seats[:humans]==list(range(1,humans+1)) and not any(seats[4:])
    print('PASS mode/physical-seat publication and startup credit preference persistence')
    surface.phase='ready';surface.accepted=True;surface.visible=True
    packet=c.packet;generation=surface.generation
    surface.show('FAIL: late start timeout; close and reopen',100)
    assert surface.phase=='ready' and surface.generation==generation and c.packet==packet
    surface.phase='released';surface.accepted=False
    surface.show('FAIL: late diagnostic',100)
    assert surface.phase=='released' and surface.generation==generation and c.packet==packet
    print('PASS late diagnostics never create a new failure generation over an accepted/released match')
    for shape,index in (('off',0),('hexagon',1),('ring',2),('plate',3)):
        model.values.update(hud_overhead_shape=shape,hud_overhead_names='tiny',hud_style='overhead_only',hud_overhead_detail='everyone')
        model.save(exit=False)
        selected=ui.Surface();selected.set_teams([dict(side=side,fighters=[dict(character_id=side)])for side in (0,1)])
        ui._ACTIVE.client=c
        try:selected.begin()
        finally:del ui._ACTIVE.client
        words=ui.WORDS.unpack(c.packet[:128]);assert words[28]&3==index and words[25]&3==1 and words[24]&1==0 and (words[25]>>2)&3==3
    print('PASS actual settings->native publisher: four shapes, Tiny names and Overhead-only game HUD OFF')

# Exercise simultaneous heartbeat and intro callback through their real Surface
# methods. PINE calls own the transport lock before invoking start_accepted.
class OwnedClient(Client):
    def _exchange(self,command,expected):
        with ui.TRANSPORT_LOCK:return super()._exchange(command,expected)
surface=ui.Surface();surface.phase='ready';surface.visible=True;surface.transport_version=2
client=OwnedClient();attempt=threading.Event();finished=threading.Event();errors=[]
def heartbeat():
    attempt.set()
    try:surface.sync(client=client)
    except BaseException as error:errors.append(error)
def intro():
    try:
        with ui.TRANSPORT_LOCK:
            worker=threading.Thread(target=heartbeat,daemon=True);worker.start()
            assert attempt.wait(1)
            time.sleep(.03) # let heartbeat contend while the PINE poll is owned
            surface.start_accepted(client)
        worker.join(1);assert not worker.is_alive()
    except BaseException as error:errors.append(error)
    finally:finished.set()
threading.Thread(target=intro,daemon=True).start()
assert finished.wait(2), 'Heartbeat/intro PINE-to-UI lock inversion'
assert not errors,errors
assert surface.accepted
print('PASS concurrent PINE-owned intro acknowledgement and UI heartbeat complete')
import feature_preferences as preferences
assert preferences.grid('hud_panel_scale_percent')==[50,65,80,100,120]
assert preferences.grid('hud_panel_opacity_percent')==[30,50,70,100]
assert preferences.step_value('hud_panel_scale_percent',65,1)==80
assert preferences.step_value('hud_panel_scale_percent',100,-1)==80
values={};preferences.validate_into(values)
assert values['hud_panel_scale_percent']==65 and values['hud_panel_opacity_percent']==50
assert values['hud_overhead_shape']=='hexagon' and values['hud_overhead_names']=='off'
assert preferences.step_value('hud_overhead_names','off',1)=='tiny'
values.update(hud_panel_scale_percent=130,hud_panel_opacity_percent=20)
preferences.validate_into(values)
assert values['hud_panel_scale_percent']==130 and values['hud_panel_opacity_percent']==20
print('PASS compact defaults, size/opacity presets and older saved values remain valid')
