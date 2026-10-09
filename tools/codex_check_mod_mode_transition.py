"""Check the actual mode-to-character-select GIF cover without a live game."""
import os,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'power-scale-trial/controller/game/tools'))
os.environ['PS2X_NATIVE_UI_SLICE']='1'
os.environ['PS2X_NATIVE_MODE_COVER']='1'
import native_menu_loading as m
import native_menu_texture as texture
from regional import DISPLAY_H,Y_ORIGIN

def decoded(packet):
    count=struct.unpack_from('<Q',packet,96)[0]&0x7fff
    return [struct.unpack_from('<3Q',packet,112+i*24) for i in range(count)]

def compressed_records(blob):
    count=struct.unpack_from('<Q',blob,96)[0]&0x7fff
    palette=struct.unpack_from('<16Q',blob,112)
    out=[]
    for i in range(count):
        v=int.from_bytes(blob[240+i*5:245+i*5],'little')
        x0=v&511;y0=(v>>9)&511;x1=((v>>18)&511)+1;y1=((v>>27)&511)+1
        out.append((palette[(v>>36)&15],((x0+1792)*16)|(((y0+Y_ORIGIN)*16)<<16),((x1+1792)*16)|(((y1+Y_ORIGIN)*16)<<16)))
    return out

out=root/'power-scale-trial/mod-mode-transition-captures';out.mkdir(exist_ok=True)
for lang in ('en','es'):
    base,frames=m.packets(lang)
    assert compressed_records(m.encode(base))==decoded(base)
    assert len({len(f) for f in frames})==1
    assert len(m.encode(base))+len(m.encode(m.packets('es' if lang=='en' else 'en')[0]))+sum(map(len,frames))<=m.END-m.DATA
    for index,frame in enumerate(frames):
        im=texture.picture().convert('RGB').resize((512,DISPLAY_H),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im)
        for color,p0,p1 in decoded(base)+decoded(frame):
            x0=(p0&65535)//16-1792;y0=((p0>>16)&65535)//16-Y_ORIGIN
            x1=(p1&65535)//16-1792;y1=((p1>>16)&65535)//16-Y_ORIGIN
            d.rectangle((x0,y0,x1-1,y1-1),fill=(color&255,(color>>8)&255,(color>>16)&255))
        im.resize((1024,896)).save(out/f'{lang}-{index}.png')
    print('PASS',lang,'textured cover + exact foreground decode, four bounded animation frames')
blocks=m.code_pieces();assert len(blocks[0][1])==1024 and len(blocks[-1][1])==m.END-m.DATA
print('PASS production mode fade payload and reserved code/data bounds; no game accessed')

assert len(texture.packet())+16<=texture.END-texture.DATA
assert texture.picture().size==(texture.WIDTH,texture.HEIGHT)
print('PASS styled texture fits existing immutable DMA/VRAM reservation')

os.environ['PS2X_NATIVE_MODE_COVER']='0'
assert m.payload()==struct.pack('<2I',0x03e00008,0)
print('PASS default-disabled native cover emits JR/NOP without drawing')
