"""Controller-owned team setup before the native character selector.

The chosen physical seats are a single receipt shared by selection, roster
validation and preparation. No choice changes the fighters' parity identities.
"""
import struct
from localization import tr
from prototype import Assembler
import fonts

CODE, RESOLVE, END = 0x06911000, 0x06911800, 0x06912000
MENU, MAGIC = 0x076FF000, 0x324D4E42
STATE, CHOICE, BUTTONS, PREVIOUS, LEASE, HUMANS, VALID = range(0xA0,0xBC,4)
SEATS=0xC0
TEAM_CHOICES={7:2,10:2,12:4,17:3,15:4,20:3}
CHOICES={**TEAM_CHOICES,3:2,13:4,18:3}


def physical_seats(teams):
    if len(teams) not in (2,3,4) or any(type(t)is not int or t not in (0,1) for t in teams):
        raise ValueError('Assign each of the two to four players to Team 1 or Team 2')
    counts=[0,0];result=[]
    for team in teams:
        result.append(2*counts[team]+team);counts[team]+=1
    return tuple(result)


def selected(ram,mode,humans):
    if mode not in ('teams','training') or humans<2:return None
    u=lambda p:struct.unpack('<I',ram[p:p+4])[0]
    if u(MENU)!=MAGIC or u(MENU+VALID)!=1:return None
    choice=u(MENU+60)
    if CHOICES.get(choice)!=humans:return None
    result=tuple(u(MENU+SEATS+4*i) for i in range(humans))
    if result!=physical_seats(tuple(i&1 for i in result)):
        raise ValueError('Player team assignment is corrupt or stale')
    return result


def input_code():
    import mode_menu as menu
    a=Assembler(CODE);a.li(8,MENU);a.lw(9,8);a.li(10,MAGIC);a.branch(5,9,10,'no')
    a.lw(9,8,STATE);a.addiu(10,0,1);a.branch(5,9,10,'no')
    a.lw(9,8,LEASE);a.branch(4,9,0,'expire');a.addiu(9,9,-1);a.sw(9,8,LEASE)
    a.li(9,menu.MAIN_CALLER);a.branch(5,4,9,'no')
    a.li(9,menu.SCENE_MANAGER);a.lw(9,9);a.li(10,0x100000);a.r(0x2B,10,9,10);a.branch(5,10,0,'expire')
    a.li(10,0x1FFF000);a.r(0x2B,10,9,10);a.branch(4,10,0,'expire')
    a.lw(9,9,0x18);a.addiu(10,0,4);a.branch(5,9,10,'expire')
    a.lw(9,8,4);a.addiu(10,0,2);a.branch(5,9,10,'expire')
    a.li(9,menu.PAD);a.lw(10,9,0x150);a.lw(11,8,PREVIOUS);a.sw(10,8,PREVIOUS)
    a.i(14,11,11,0xFFFF);a.r(0x24,10,10,11);a.lw(11,8,BUTTONS);a.r(0x25,10,10,11);a.sw(10,8,BUTTONS)
    a.sw(0,9,0x18C);a.sw(0,9,0x190);a.addiu(2,0,1);a.jr()
    a.label('expire');a.sw(0,8,STATE);a.sw(0,8,BUTTONS);a.sw(0,8,VALID)
    a.label('no');a.move(2,0);a.jr();return a.finish()


def resolve_code():
    # Input t5=selection side, t6=slot; preserve both and t3=selector owner.
    a=Assembler(RESOLVE);a.li(8,MENU);a.lw(10,8,VALID);a.addiu(24,0,1)
    a.branch(5,10,24,'legacy');a.lw(9,8,60)
    for choice in TEAM_CHOICES:
        a.addiu(10,0,choice);a.branch(4,9,10,'assigned')
    a.jump('legacy');a.label('assigned')
    a.r(0,24,0,14,1);a.r(0x21,24,24,13)
    for seat in range(4):
        a.lw(10,8,SEATS+4*seat);a.branch(5,10,24,f'next{seat}')
        a.addiu(2,0,seat+1);a.jr();a.label(f'next{seat}')
    a.addiu(2,0,1);a.jr();a.label('legacy');a.move(2,0);a.jr();return a.finish()


def code_pieces():return [(CODE,input_code())]


class Controller:
    def __init__(self):
        self.active=False;self.screen=None;self.row=0;self.teams=[];self.choice=None;self.input_ready=False
        self.inputs=None;self.wizard=None;self.notice=''

    def picture(self):
        from PIL import Image,ImageDraw
        im=Image.new('RGB',(512,448),(10,16,28));d=ImageDraw.Draw(im)
        title=fonts.truetype('sans-bold',25)
        font=fonts.truetype('sans-bold',17)
        small=fonts.truetype('sans',13)
        d.rectangle((0,0,511,4),fill=(245,184,63))
        d.text((24,22),tr('ASSIGN CONTROLLERS' if self.wizard else 'PLAYER SETUP' if self.choice not in TEAM_CHOICES else 'CHOOSE YOUR TEAMS'),font=title,fill=(249,197,90))
        def line(text,y,color=(203,216,234)):
            # Keep translated instructions inside the actual 512-pixel surface.
            words=tr(text).split();row=''
            for word in words:
                trial=(row+' '+word).strip()
                if row and d.textlength(trial,font=small)>460:
                    d.text((25,y),row,font=small,fill=color);y+=18;row=word
                else:row=trial
            d.text((25,y),row,font=small,fill=color)
        if self.wizard:
            d.text((25,98),tr(f'PLAYER {len(self.wizard.devices)+1}'),font=title,fill=(249,197,90))
            line(self.wizard.message,148)
            for i,device in enumerate(self.wizard.devices):
                d.text((25,211+i*28),tr('Player {player} — Controller {controller}',player=i+1,controller=device+1),font=font,fill=(117,227,161))
            line('Triangle: cancel assignment',402)
            return im.quantize(16,dither=Image.Dither.NONE).convert('RGB')
        line('Choose teams and optionally assign controllers.',60)
        seats=physical_seats(self.teams)
        for i,team in enumerate(self.teams):
            y=92+i*44;selected=i==self.row
            d.rounded_rectangle((20,y-5,491,y+35),radius=7,fill=(31,46,66),outline=(247,192,75) if selected else (64,80,102),width=2)
            color=((71,184,241),(246,120,102))[team]
            d.text((33,y),tr(f'PLAYER {i+1}'),font=font,fill=(242,244,249))
            if self.choice in TEAM_CHOICES:
                d.text((214,y),tr(f'<  TEAM {team+1}  >'),font=font,fill=color)
                d.text((399,y+3),tr(f'SLOT {seats[i]//2+1}'),font=small,fill=(219,228,240))
            assigned=self.inputs.order if self.inputs is not None else None
            label=tr('Controller {controller}',controller=assigned[i]+1) if assigned is not None and i<len(assigned) else tr('Default input')
            d.text((34,y+19),label,font=small,fill=(188,202,222))
        import quad_controller
        labels=('Configure controllers (Shift+Tab)','Use configured controllers','Continue') if quad_controller.native_seat_pads() else ('Assign controllers…','Restore default controller order','Continue')
        for i,label in enumerate(labels):
            y=279+i*35
            d.rounded_rectangle((20,y,491,y+29),radius=6,fill=(31,46,66),outline=(247,192,75) if self.row==len(self.teams)+i else (64,80,102),width=2)
            d.text((33,y+4),tr(label),font=font,fill=(242,244,249))
        line(self.notice or 'Up/Down: select   Left/Right: team',389)
        line('Cross: select / continue    Triangle: back',424,(249,197,90))
        return im.quantize(16,dither=Image.Dither.NONE).convert('RGB')

    def tick(self,p):
        wanted=p.read_u32(MENU)==MAGIC and p.read_u32(MENU+STATE)==1
        if not wanted:
            if self.active:self.close(p)
            return False
        choice=p.read_u32(MENU+CHOICE)
        if choice not in CHOICES:raise ValueError('Unknown player assignment request')
        dirty=False
        if not self.active:
            from guest_loading_screen import GuestLoadingScreen
            self.screen=GuestLoadingScreen();self.active=True;self.choice=choice
            self.row=0;self.teams=[i&1 for i in range(CHOICES[choice])];self.input_ready=False;self.notice='';dirty=True
        p.write_u32(MENU+LEASE,180);p.write_u32(MENU+16,180)
        buttons=p.read_u32(MENU+BUTTONS)
        if buttons:p.write_u32(MENU+BUTTONS,0)
        if buttons&0x1000:
            if self.wizard:
                self.wizard.close();self.wizard=None;self.input_ready=False
                self.screen.show_picture(self.picture(),surface='menu',client=p);return True
            p.write_u32(MENU+STATE,0);p.write_u32(MENU+VALID,0);self.close(p);return True
        if self.wizard:
            if self.screen.presented(p):
                before=(tuple(self.wizard.devices),self.wizard.message)
                try:result=self.wizard.poll()
                except (OSError,AttributeError):
                    self.wizard.close();self.wizard=None;self.notice='Cannot read controllers. Check connections and try again.'
                    self.screen.show_picture(self.picture(),surface='menu',client=p);return True
                if result is not None:
                    try:
                        self.inputs.assign(result);self.inputs.attach(p,('menu',))
                        self.notice='Assigned for this session. Standard gamepad controls.';self.row=len(self.teams)+2
                    except (OSError,ValueError,RuntimeError) as error:
                        self.inputs.assign(None);self.inputs.disable(p)
                        print(f'Controller assignment could not start: {error}',flush=True)
                        self.notice='Controller assignment failed. Default controls restored.'
                    self.wizard.close();self.wizard=None
                    self.input_ready=False;dirty=True
                else:dirty=before!=(tuple(self.wizard.devices),self.wizard.message)
            if dirty:self.screen.show_picture(self.picture(),surface='menu',client=p)
            else:self.screen.sync(client=p)
            return True
        if not self.screen.presented(p):buttons=0
        elif not self.input_ready:
            import mode_menu
            self.input_ready=p.read_u32(mode_menu.PAD+0x150)==0
            buttons=0
        if buttons&0x50:self.row=(self.row+(1 if buttons&0x40 else -1))%(len(self.teams)+3)
        if buttons&0xA0 and self.row<len(self.teams) and self.choice in TEAM_CHOICES:self.teams[self.row]^=1
        if buttons&0x4000:
            if self.row==len(self.teams):
                import quad_controller
                if quad_controller.native_seat_pads():self.notice='Configure Player 1-4 in Shift+Tab > Controllers.'
                elif self.inputs is None:self.notice='Controller assignment requires Play (any teams).'
                else:
                    try:
                        from controller_assignment import Wizard,CapturePump
                        self.wizard=Wizard(len(self.teams),capture=CapturePump())
                    except (OSError,AttributeError):self.notice='Cannot read controllers. Check connections and try again.'
                self.screen.show_picture(self.picture(),surface='menu',client=p);return True
            if self.row==len(self.teams)+1:
                if self.inputs is not None:self.inputs.assign(None);self.inputs.disable(p)
                self.notice='Using configured native controllers.' if quad_controller.native_seat_pads() else 'Default controller order restored.';self.input_ready=False
                self.screen.show_picture(self.picture(),surface='menu',client=p);return True
            if self.inputs is not None and self.inputs.order is not None and len(self.inputs.order)<len(self.teams):
                self.notice='Assign all players or restore the default order.'
                self.screen.show_picture(self.picture(),surface='menu',client=p);return True
            seats=physical_seats(self.teams)
            p.write(MENU+SEATS,struct.pack('<4I',*(seats+(0xFFFFFFFF,)*(4-len(seats)))))
            p.write_u32(MENU+HUMANS,len(seats));p.write_u32(MENU+VALID,int(self.choice in TEAM_CHOICES))
            self.close(p)
            # The guest performs the ordinary dispatch only after this receipt
            # has been published completely and the overlay has disappeared.
            p.write_u32(MENU+STATE,2);return True
        if dirty or buttons:self.screen.show_picture(self.picture(),surface='menu',client=p)
        else:self.screen.sync(client=p)
        return True

    def close(self,p):
        import mode_menu
        p.write_u32(MENU+28,p.read_u32(mode_menu.PAD+0x150))
        if self.screen:self.screen.hide(client=p)
        if self.wizard:self.wizard.close();self.wizard=None
        self.screen=None;self.active=False

    def shutdown(self):
        if self.wizard:self.wizard.close();self.wizard=None
