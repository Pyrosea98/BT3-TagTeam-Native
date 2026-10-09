"""Session-only physical controller assignment for all modded player seats.

Opt-in: native PCSX2 bindings remain untouched when no assignment is active.
P1/P2 receive the same standardized pad layout already used by P3/P4. The
authenticated mailbox has no executable writes and expires to neutral input.
"""
import struct
import threading
from collections import deque
from prototype import Assembler
from input_binding import ControllerCapture, SDL_BUTTONS
import controller_mailbox as transport
import quad_controller as pads
import mode_menu

CODE, CONTROL, MAILBOX, TOKEN = 0x06930000, 0x06933000, 0x06933100, 0x06933080
END, MAGIC = 0x06934000, 0x43415331


def order(value):
    value=tuple(value)
    if len(value) not in (2,3,4) or len(set(value))!=len(value) or any(type(i)is not int or not 0<=i<32 for i in value):
        raise ValueError('Choose a different connected controller for each player')
    return value


def private_devices(value):
    """Unused seats receive a disconnected index, never somebody else's pad."""
    selected=tuple(value[2:])
    return selected+tuple(range(32,34-len(selected)))


def payload():
    # Called after the native poll and before menu/actor input consumers.
    # The outer native-mode wrapper preserves registers and HI/LO.
    from quad_menu_input import MENU_BITS
    a=Assembler(CODE);a.li(8,CONTROL);a.lw(9,8);a.li(10,MAGIC)
    a.branch(5,9,10,'done');a.lw(9,8,12);a.branch(4,9,0,'done')
    a.addiu(29,29,-0x60)
    a.lw(9,8,28);a.branch(5,9,0,'stale')
    a.lw(9,8,16);a.lw(10,8,20);a.branch(4,9,10,'stale');a.sw(9,29,80)
    for seat in range(2):
        a.li(9,MAILBOX+32*seat)
        for field in range(5):a.lw(10,9,4*field);a.sw(10,29,seat*20+4*field)
    a.lw(9,8,28);a.branch(5,9,0,'stale')
    a.lw(9,8,16);a.lw(10,29,80);a.branch(5,9,10,'stale')
    a.sw(9,8,20);a.sw(0,8,24)
    for seat in range(2):
        for field in range(5):a.lw(10,29,seat*20+4*field);a.sw(10,8,0x180+seat*32+field*4)
    a.jump('publish')
    a.label('stale');a.lw(9,8,24);a.i(11,10,9,pads.LEASE)
    a.branch(4,10,0,'neutral');a.addiu(9,9,1);a.sw(9,8,24);a.jump('publish')
    a.label('neutral')
    for seat in range(2):
        for field in range(5):a.sw(0,8,0x180+seat*32+field*4)
    a.label('publish')
    for seat in range(2):
        # Use a private previous state; the native poll's previous word belongs
        # to PCSX2's original device, which may be another assigned player.
        a.li(12,mode_menu.PAD+seat*0x1C0);a.lw(10,8,0x180+seat*32)
        a.lw(11,8,0x40+seat*12);a.r(0x27,9,11,0);a.r(0x24,9,10,9)
        a.sw(10,12,328);a.sw(10,12,332);a.sw(9,12,336);a.sw(9,12,340)
        a.sw(10,8,0x40+seat*12)
        for offset in (348,384,388):a.sw(0,12,offset)
        for field,offset in enumerate((304,308,312,316),1):
            a.lw(9,8,0x180+seat*32+field*4);a.sw(9,12,offset)
        a.move(13,0)
        for mask,translated in MENU_BITS:
            tag=f's{seat}_{translated}';a.li(9,mask);a.r(0x24,9,10,9);a.branch(4,9,0,tag)
            a.li(9,translated);a.r(0x25,13,13,9);a.label(tag)
        a.lw(11,8,0x44+seat*12);a.r(0x27,9,11,0);a.r(0x24,9,13,9);a.sw(9,12,396)
        a.sw(13,8,0x44+seat*12);a.sw(13,12,400)
        a.branch(5,13,11,f'new{seat}');a.lw(9,8,0x48+seat*12);a.addiu(9,9,1);a.sw(9,8,0x48+seat*12)
        a.i(11,10,9,15);a.branch(5,10,0,f'norepeat{seat}');a.i(12,10,9,3)
        a.branch(4,10,0,f'next{seat}')
        a.label(f'norepeat{seat}');a.sw(0,12,400);a.jump(f'next{seat}')
        a.label(f'new{seat}');a.sw(0,8,0x48+seat*12)
        a.label(f'next{seat}')
    a.addiu(29,29,0x60);a.label('done');a.jr()
    code=a.finish();assert CODE+len(code)<CONTROL;return code


def code_pieces():return [(CODE,payload())]


class Mailbox(transport.Mailbox):
    TOKEN_ADDRESS=TOKEN
    READS={CONTROL:16}
    WRITES={MAILBOX:64,CONTROL+16:4,CONTROL+28:4}

    @classmethod
    def identity(cls,p):
        if p.read(CODE,len(payload()))!=payload():raise ValueError('Controller assignment hook is not installed; restart Play')
        return {CONTROL:p.read(CONTROL,16),CODE:p.read(CODE,16)}


class Bridge(pads.Bridge):
    def poll(self,p):
        if pads.native_seat_pads():return False
        if struct.unpack_from('<I',p.read(CONTROL,16))[0]!=MAGIC:return False
        self.capture.update();available=dict(self.capture.controllers);parts=[]
        for device in self.devices:
            handle=available.get(device)
            if handle:
                buttons=[n for i,n in enumerate(SDL_BUTTONS) if self.capture.dll.SDL_GameControllerGetButton(handle,i)]
                axes=[self.capture.dll.SDL_GameControllerGetAxis(handle,i) for i in range(6)]
                parts.append(pads.encode_pad(buttons,axes))
            else:parts.append(bytes(32))
        p.write_u32(CONTROL+28,1);p.write(MAILBOX,b''.join(parts))
        self.sequence=(self.sequence+1)&0xFFFFFFFF or 1
        p.write_u32(CONTROL+16,self.sequence);p.write_u32(CONTROL+28,0);return True


class Owner:
    def __init__(self,pid):self.pid=pid;self.order=None;self.service=None;self.capture=None

    def assign(self,devices):
        self.close();self.order=order(devices) if devices is not None else None

    def attach(self,p,capture):
        if pads.native_seat_pads():
            self.disable(p) # PadConfig owns P1/P2 directly; no physical SDL remapping.
            return
        if self.order is None:return
        if self.service is not None:
            if self.service.failure:raise RuntimeError(self.service.failure)
            if self.capture==capture and self.service.active:return
        self.close()
        # Disarm before staging data; arm only after the input thread is ready.
        p.write_u32(CONTROL+12,0)
        p.write(CONTROL,struct.pack('<8I',MAGIC,0,0,0,0,0,pads.LEASE,0)+bytes(0x1E0))
        try:
            self.service=transport.Service(Mailbox.attach(p,self.pid),devices=self.order[:2],bridge_factory=Bridge)
            p.write_u32(CONTROL+12,1);self.capture=capture
        except BaseException:self.close();raise

    def disable(self,p):
        self.close();p.write_u32(CONTROL+12,0)

    def close(self):
        if self.service is not None:self.service.close()
        self.service=None;self.capture=None


class CapturePump:
    """Keep short press/release transitions between the watcher's menu ticks."""
    def __init__(self):
        self.lock=threading.Lock();self.stop=threading.Event();self.ready=threading.Event()
        self.events=deque(maxlen=128);self.current=set();self.controllers=[];self.error=None
        self.thread=threading.Thread(target=self._run,name='Controller assignment capture',daemon=True)
        self.thread.start()
        if not self.ready.wait(5):self.close();raise OSError('Controller capture timed out')
        if self.error:self.close();raise OSError(self.error)

    def _run(self):
        capture=None
        try:
            capture=ControllerCapture(background=True);previous=None
            while not self.stop.is_set():
                current=capture.pressed()
                with self.lock:
                    self.controllers=list(capture.controllers);self.current=current
                    if current!=previous:self.events.append(current.copy())
                previous=current;self.ready.set();self.stop.wait(.01)
        except Exception as error:self.error=str(error)
        finally:
            if capture is not None:capture.close()
            self.ready.set()

    def pressed(self):
        if self.error:raise OSError(self.error)
        with self.lock:return self.events.popleft() if self.events else self.current.copy()

    def update(self):pass

    def close(self):
        self.stop.set();self.thread.join(timeout=5)
        if self.thread.is_alive():raise RuntimeError('Controller capture did not stop')


class Wizard:
    """Fresh Cross/A presses, one unclaimed controller per human seat."""
    def __init__(self,humans,capture=None):
        self.humans=humans;self.capture=capture or ControllerCapture(background=True)
        self.devices=[];self.ready=False;self.message='Release all controller buttons.'

    def poll(self):
        pressed=self.capture.pressed()
        self.capture.update();connected={i for i,_ in self.capture.controllers}
        if any(i not in connected for i in self.devices):
            self.devices=[];self.ready=False;self.message='A controller disconnected. Start again with Player 1.';return None
        if not self.ready:
            if not pressed:self.ready=True;self.message='Press Cross / A on this player\u2019s controller.'
            return None
        candidates={int(s.split('/')[0][4:]) for s in pressed if s.endswith('/FaceSouth')}
        if not candidates:return None
        self.ready=False
        if len(candidates)>1:self.message='One controller at a time. Release and try again.';return None
        device=next(iter(candidates))
        if device in self.devices:self.message='That controller already belongs to another player.';return None
        self.devices.append(device);self.message='Release all controller buttons.'
        if len(self.devices)==self.humans:return order(self.devices)
        return None

    def close(self):self.capture.close()
