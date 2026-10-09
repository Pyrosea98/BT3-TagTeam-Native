"""High-resolution menu transition logo in an immutable DMA-referenced texture.

The 768px picture occupies a separate read-only EE reservation, outside heap1,
the loading double buffers and injected programs. GS scratch is shared with
the battle loading cover only while the menu is completely black. Re-upload
each frame because the native menu also uses this VRAM between our draws.
"""
import os
import math
from functools import lru_cache
from prototype import ROOT
from PIL import Image
import struct
import loading_texture_probe as gs
import loading_protocol as protocol
from regional import tbp

DATA, END = 0x06B00000, 0x06B80000
WIDTH, HEIGHT, TBP, CBP, TBW = 768, 576, tbp(0x2D00), tbp(0x3408), 12
MAGIC=0x54455831


def native_picture():
    """Restrained game UI artwork: navy depth, ki trails and glass Dragon Balls."""
    from PIL import ImageDraw,ImageFilter
    scale=3;w,h=512*scale,448*scale
    im=Image.new('RGB',(w,h));px=im.load()
    # Soft lighting instead of full-scene illustration. Centre stays readable.
    for y in range(h):
        yy=y/scale
        for x in range(w):
            xx=x/scale
            blue=math.exp(-((xx-80)/180)**2-((yy-155)/145)**2)
            amber=math.exp(-((xx-460)/115)**2-((yy-285)/130)**2)
            px[x,y]=(int(8+10*blue+8*amber),int(17+20*blue+6*amber),int(29+30*blue+4*amber))
    glow=Image.new('RGB',(w,h));g=ImageDraw.Draw(glow)
    # Quiet crossing trails borrow the cyan/gold accents of the native plates.
    curves=[([(0,287),(100,316),(236,328),(400,303),(512,246)],(15,63,89)),
            ([(0,311),(114,335),(284,332),(432,284),(512,240)],(28,68,91)),
            ([(0,335),(142,351),(304,338),(440,300),(512,283)],(67,48,22))]
    for pts,color in curves:g.line([(x*scale,y*scale) for x,y in pts],fill=color,width=5*scale)
    glow=glow.filter(ImageFilter.GaussianBlur(7*scale))
    from PIL import ImageChops
    im=ImageChops.add(im,glow);d=ImageDraw.Draw(im)
    def ellipse(cx,cy,r,fill,outline=None,width=1):
        d.ellipse(((cx-r)*scale,(cy-r)*scale,(cx+r)*scale,(cy+r)*scale),fill=fill,outline=outline,width=width*scale)
    def stars(cx,cy,count,radius=8,size=3,color=(171,50,13)):
        for index in range(count):
            angle=2*math.pi*index/count-math.pi/2
            x,y=(cx,cy) if count==1 else (cx+radius*math.cos(angle),cy+radius*math.sin(angle))
            points=[]
            for tip in range(10):
                angle=tip*math.pi/5-math.pi/2;rr=size if tip%2==0 else size*.43
                points.append(((x+rr*math.cos(angle))*scale,(y+rr*math.sin(angle))*scale))
            d.polygon(points,fill=color)
    # Shared project mark, kept separate from the player's franchise artwork.
    # Resolve from controller/game/assets in both developer and installed layouts.
    with Image.open(ROOT/'assets/tag-team-real-power-scale-v1.png') as source:
        logo=source.convert('RGBA');bounds=logo.getchannel('A').getbbox()
        if not bounds:raise ValueError('Project branding is empty')
        logo=logo.crop(bounds);logo.thumbnail((420*scale,132*scale),Image.Resampling.LANCZOS)
        im.paste(logo,((w-logo.width)//2,45*scale),logo)
    d=ImageDraw.Draw(im)
    for i in range(7):
        cx,cy,r=112+48*i,272,17
        ellipse(cx,cy,r+4,(18,36,46),(48,58,56))
        ellipse(cx,cy,r,(97,48,13),(210,135,35))
        # Nested highlights produce a smooth warm glass sphere, not flat pixels.
        for step in range(16):
            radius=16-step*.4
            ellipse(cx-step*.18,cy-step*.28,radius,(min(255,213+step*2),min(222,128+step*5),min(106,23+step*5)))
        d.ellipse(((cx-9)*scale,(cy-12)*scale,(cx-2)*scale,(cy-8)*scale),fill=(255,238,176))
        stars(cx,cy,i+1,8,2.7)
    # Fine sparks and small accent rails: sparse enough to retain the old UI tone.
    for x,y in ((49,205),(457,136),(414,337),(86,342),(151,103),(365,104)):
        d.ellipse((x*scale,y*scale,(x+1)*scale,(y+1)*scale),fill=(106,126,136))
    d.line((216*scale,225*scale,296*scale,225*scale),fill=(141,112,55),width=scale)
    return im.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)


@lru_cache(maxsize=1)
def picture():
    if os.environ.get('PS2X_NATIVE_UI_SLICE') is not None:
        result=native_picture()
        return result.quantize(256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    with Image.open(ROOT/'Tag Team Mod Logo.png') as source:
        logo=source.convert('RGB')
    h=round(WIDTH*logo.height/logo.width)
    result=Image.new('RGB',(WIDTH,HEIGHT))
    result.paste(logo.resize((WIDTH,h),Image.Resampling.LANCZOS),(0,(HEIGHT-h)//2))
    return result.quantize(256,method=Image.Quantize.MEDIANCUT,
                           dither=Image.Dither.NONE)


@lru_cache(maxsize=1)
def packet():
    pic=picture();pal=pic.getpalette()
    colours=[(*pal[i:i+3],255) for i in range(0,768,3)]
    blocks=protocol.vram_blocks(gs.PSMT8,TBP,TBW,WIDTH,HEIGHT)
    palette=protocol.vram_blocks(gs.PSMCT32,CBP,1,16,16)
    assert not blocks & palette and max(blocks|palette)<tbp(0x3480)
    out=bytearray(gs.ad_block(protocol.SETUP))
    out+=gs.upload_image(TBP,TBW,gs.PSMT8,WIDTH,HEIGHT,pic.tobytes())
    out+=gs.upload_image(CBP,1,gs.PSMCT32,16,16,gs.clut_image(colours))
    out+=gs.ad_block([(0,gs.TEXFLUSH),
        (gs.tex0(TBP,TBW,gs.PSMT8,10,10,1,1,CBP,0,0,0,1),gs.TEX0_1),
        (gs.LINEAR_TEX1,gs.TEX1_1),
        (gs.clamp1(2,2,0,WIDTH-1,0,HEIGHT-1),gs.CLAMP_1),
        (protocol.BG_SPRITE,gs.PRIM)])
    if os.environ.get('PS2X_NATIVE_UI_SLICE') is not None:
        out+=gs.textured_sprite(0,0,512,448,0,0,WIDTH*16,HEIGHT*16)
    else:
        out+=gs.textured_sprite(128,128,384,320,0,0,WIDTH*16,HEIGHT*16)
    out+=gs.ad_block([(5,gs.CLAMP_1),(0,gs.TEX1_1)],eop=True)
    result=protocol.referenced(bytes(out))
    assert len(result)<END-DATA
    return result


def ready_address():
    return DATA+len(packet())


def plan(ram):
    """Publish once before arming a menu, never rewrite 444 KB every frame."""
    blob=packet()+struct.pack('<4I',MAGIC,0,0,0)
    current=bytes(ram[DATA:DATA+len(blob)])
    if current==blob:return []
    if any(current):raise ValueError('Menu logo texture reservation has a different owner')
    return [(DATA,blob)]
