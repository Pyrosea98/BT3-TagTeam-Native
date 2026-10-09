"""Compile actual menu route and validate replacement against fake bridge RAM."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
import native_mode_menu as menu,ingame_settings,pine
from codex_native_menu_credits import install as credits
old=menu.payload()
class Client:
    memory=old+bytes(256)
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read_u32(self,at):return 0
    def read(self,at,n):assert at==menu.CODE;return self.memory[:n]
    def write(self,at,data):assert at==menu.CODE;Client.memory=data
original=pine.PineClient;pine.PineClient=Client
try:credits(menu,ingame_settings)
finally:pine.PineClient=original
assert menu.PAGES[0]==(0,7,1,3,6)
assert menu.assets.LABELS[0]=='Team Battle' and menu.assets.LABELS[7]=='About / Credits'
assert Client.memory[:len(menu.payload())]==menu.payload()
assert len(menu.payload())<menu.OFF-menu.CODE
print('PASS actual menu About route: default Team Battle, second About, audited replacement/readback, code bounds')
