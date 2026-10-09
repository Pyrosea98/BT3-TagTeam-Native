"""Offline PINE-memory regression for setup-screen bootstrap replacements.

No runner, sockets or live guest are used. Run with --roster for staged emitters.
"""
from pathlib import Path
import contextlib,io,os,struct,sys
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'power-scale-trial/controller/game/tools')]
os.environ.update(PS2X_NATIVE_UI_SLICE='1',PS2X_NATIVE_MODE_COVER='0')
if '--roster' in sys.argv:
    from codex_roster_overlay import install
    install()
import guest_loading_screen as g,native_mode_menu as menu,pine,mod_settings
from codex_native_menu_credits import install as credits

class Memory:
    def __init__(self):self.mem={};self.writes=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,address,size):return bytes(self.mem.get(address+i,0) for i in range(size))
    def write(self,address,data):
        self.mem.update((address+i,b) for i,b in enumerate(data));self.writes.append((address,len(data)))
    def read_u32(self,address):return struct.unpack('<I',self.read(address,4))[0]
    def write_u32(self,address,value):self.write(address,struct.pack('<I',value))

m=Memory()
boot=g.code_pieces()  # launcher caches this before the adapter installs About
for address,data in boot:m.write(address,data)
assert g.render_mismatch(m) is None
old=menu.payload()
pine.PineClient=lambda *args,**kwargs:m
credits(menu,mod_settings)
assert menu.payload()!=old
assert any(m.read(a,len(b))!=b for a,b in boot), 'must reproduce the stale boot aggregate'
assert all(m.read(a,len(b))==b for a,b in menu.code_pieces())
assert g.render_mismatch(m) is None, 'verified About replacement must not disable setup'

def screen():
    s=g.GuestLoadingScreen(speed=100)
    s.visible=True;s.surface=1;s.packet=bytes(16);s.packet_id='offline';return s

s=screen()
assert s.sync(force=True,client=m) and m.read_u32(g.CONTROL)==g.MAGIC
print('PASS exact launcher -> About installer order: stale bootstrap, intact published setup')

# Runtime owners may replace combat/menu entries after boot. Decorative cover
# settings also have no call edge from the setup renderer. No repair is allowed.
essential={a for a,b in g.render_code_pieces()}
unrelated=[(a,b) for a,b in boot if a not in essential]
assert unrelated
for address,data in unrelated:m.write(address,bytes(len(data)))
before=dict(m.mem)
assert g.render_mismatch(m) is None
assert screen().sync(force=True,client=m)
for address,data in unrelated:assert m.read(address,len(data))==bytes(len(data))
print('PASS unrelated runtime replacements remain untouched and setup stays available')

# Each required piece is checked in full, not just the dispatch JAL. A failure
# never writes a buffer/control word and a corrected source retries normally.
for owner,(address,data) in enumerate(g.render_code_pieces()):
    offset=min(12,len(data)-1);bad=bytearray(data);bad[offset]^=1
    m.write(address,bad);m.writes.clear()
    output=io.StringIO();s=screen()
    with contextlib.redirect_stdout(output):assert not s.sync(force=True,client=m)
    assert not m.writes and not s.available
    message=output.getvalue()
    assert f'{address+(offset&~3):#010x}' in message and 'expected LE' in message
    m.write(address,data)
    assert s.sync(force=True,client=m), 'repaired owner must be retried, without a permanent latch'
print('PASS full required-piece integrity, precise diagnostics, no repair writes, recoverable retry')
print('PASS profile:', 'roster' if '--roster' in sys.argv else 'base')
