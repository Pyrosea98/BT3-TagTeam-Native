"""Offline real-sprite cover compositor. No game hooks or controller edits.

Review surface for the native draw layer; animation time is explicit. Current
labels reuse the existing project font, not an extracted native glyph atlas.
The preview asset provider is Claude's read-only local disc decoder.
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

HERE = Path(__file__).resolve().parent
KIT = json.loads((HERE/'codex_design_kit.json').read_text())
S = KIT['scale']
SIZE = tuple(v*S for v in KIT['canvas'])


@lru_cache(None)
def sprite(name):
    import claude_hud_sheet_lib as disc
    return disc.sprite(KIT['sprites'][name])


@lru_cache(None)
def roster():
    return {r['character_id']: r for r in json.loads((HERE/'roster-assets/characters.json').read_text())['characters']}


def put(image, tile, x, y):
    image.alpha_composite(tile, (round(x*S), round(y*S)))


def trim(image):
    return image.crop(image.getchannel('A').getbbox())


def pop(age, duration, start=1.0, peak=1.25):
    if age >= duration:return 1.0
    if age < 0:return 1.0
    t=age/duration
    return start+(peak-start)*t/.45 if t<.45 else peak-(peak-1)* (t-.45)/.55


def label(image, text, x, y, width, height):
    sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
    import fonts
    font=fonts.truetype(fonts.path('heading'), round(height*S))
    tile=Image.new('RGBA',(round(width*S),round(height*S*1.8)))
    d=ImageDraw.Draw(tile)
    # Secondary text remains restrained: white with the kit's dark shadow.
    text=text.upper();bounds=d.textbbox((0,0),text,font=font,stroke_width=1*S)
    d.text((2*S,-bounds[1]+2*S),text,font=font,fill=(234,239,244),stroke_width=S,stroke_fill=(4,8,12))
    length=bounds[2]-bounds[0]+4*S
    if length>width*S:
        wide=Image.new('RGBA',(length,tile.height));wd=ImageDraw.Draw(wide)
        wd.text((2*S,-bounds[1]+2*S),text,font=font,fill=(234,239,244),stroke_width=S,stroke_fill=(4,8,12))
        tile=wide.resize(tile.size,Image.Resampling.LANCZOS)
    put(image,tile,x,y)


def card(image, cid, x, y, w, h, side):
    row=roster()[cid];slant=min(KIT['plate_slant'],w*.1)*S
    x0,y0,w0,h0=[v*S for v in (x,y,w,h)]
    pts=[(x0+slant,y0),(x0+w0,y0),(x0+w0-slant,y0+h0),(x0,y0+h0)]
    mask=Image.new('L',SIZE);ImageDraw.Draw(mask).polygon(pts,fill=255)
    edge=Image.new('RGBA',SIZE);ed=ImageDraw.Draw(edge)
    accent=tuple(KIT['energy'] if side==0 else KIT['fusion'])
    ed.line(pts+[pts[0]],fill=accent+(160,),width=3*S)
    image.alpha_composite(edge.filter(ImageFilter.GaussianBlur(5*S)))
    plate=Image.new('RGBA',SIZE);pd=ImageDraw.Draw(plate);pd.polygon(pts,fill=tuple(KIT['plate']))
    with Image.open(HERE/'roster-assets'/row['portrait']) as original:
        face=trim(original.convert('RGBA'))
    face.thumbnail((round(w0-14*S),round(h0-8*S)),Image.Resampling.LANCZOS)
    # Upscale from native portrait resolution, preserving the sprite silhouette.
    factor=min((w0-14*S)/face.width,(h0-8*S)/face.height)
    face=face.resize((round(face.width*factor),round(face.height*factor)),Image.Resampling.LANCZOS)
    plate.alpha_composite(face,(round(x0+(w0-face.width)/2),round(y0+(h0-face.height)/2)))
    plate.putalpha(ImageChops.multiply(plate.getchannel('A'),mask));image.alpha_composite(plate)
    pd=ImageDraw.Draw(image);pd.line(pts+[pts[0]],fill=tuple(KIT['metal']),width=2*S)
    pd.line([pts[0],pts[1]],fill=(238,244,251,255),width=S)
    label(image,row['base_name'],x+3,y+h+4,w-6,10 if w<120 else 13)


def compose(teams,progress,*,frame=40,stage_age=12,vs_age=12,match_ready=False,
            preparation_complete=False,native_load_complete=True):
    if preparation_complete and not native_load_complete:return None
    if len(teams)!=2 or any(not 1<=len(t)<=6 for t in teams):raise ValueError('Requires two teams of one to six fighters')
    if any(type(cid)is not int or cid not in roster() for t in teams for cid in t):raise ValueError('Invalid engine slot')
    progress=max(0,min(100,progress));image=Image.new('RGBA',SIZE,tuple(KIT['background']))
    band=sprite('band').copy().resize((SIZE[0]+80*S,160*S),Image.Resampling.LANCZOS)
    band.putalpha(band.getchannel('A').point(lambda a:round(a*.13)))
    put(image,band,-40+6*math.sin(frame/180),145)
    logo=HERE/'power-scale-trial/controller/game/Tag Team Mod Logo.png'
    with Image.open(logo) as original:
        tile=trim(original.convert('RGBA'));tile.thumbnail((150*S,48*S),Image.Resampling.LANCZOS)
    put(image,tile,KIT['margin'],10)
    for side,team in enumerate(teams):
        n=len(team);left=32 if side==0 else 410
        if n==1:positions=[(left,88,198,198)]
        elif n==2:positions=[(left+27,68+i*120,144,92) for i in range(2)]
        elif n==3:positions=[(left+32,66+i*80,134,59) for i in range(3)]
        else:
            positions=[(left+(i%2)*104,64+(i//2)*81,94,60) for i in range(n)]
            if n%2:positions[-1]=(left+52,positions[-1][1],94,60)
        for cid,box in zip(team,positions):card(image,cid,*box,side)
    if match_ready:
        size=round(KIT['vs']['size']*pop(vs_age,KIT['vs']['pop_frames'],.6,1.1))
        tile=trim(sprite('vs'));factor=size*S/max(tile.size)
        tile=tile.resize((round(tile.width*factor),round(tile.height*factor)),Image.Resampling.LANCZOS)
        cx,cy=KIT['vs']['center'];put(image,tile,cx-tile.width/S/2,cy-tile.height/S/2)
    balls=sprite('balls');cw,ch=balls.width//4,balls.height//2
    lit=int(progress*7/100);spec=KIT['balls'];total=7*spec['size']+6*spec['gap'];x=(640-total)/2
    for i in range(7):
        col,row=i%4,i//4;ball=trim(balls.crop((col*cw,row*ch,(col+1)*cw,(row+1)*ch)))
        scale=pop(stage_age,spec['pop_frames']) if i==lit-1 else 1
        size=round(spec['size']*scale);ball=ball.resize((size*S,size*S),Image.Resampling.LANCZOS)
        if i>=lit:
            ball=ImageEnhance.Color(ball).enhance(.15);ball=ImageEnhance.Brightness(ball).enhance(.3)
        put(image,ball,x+i*(spec['size']+spec['gap'])+(spec['size']-size)/2,spec['y']+(spec['size']-size)/2)
        if i==lit-1 and 0<=stage_age<spec['pop_frames']:
            cx=(x+i*(spec['size']+spec['gap'])+spec['size']+5)*S;cy=(spec['y']+7)*S
            radius=max(1,round(5*S*(1-stage_age/spec['pop_frames'])))
            spark=ImageDraw.Draw(image)
            spark.line((cx-radius,cy,cx+radius,cy),fill=(255,237,179),width=S)
            spark.line((cx,cy-radius,cx,cy+radius),fill=(255,237,179),width=S)
    # Split the actual gold frame from its blue interior. Scroll only the wave.
    bar=trim(sprite('bar'));box=KIT['bar']['box'];w,h=box[2]-box[0],box[3]-box[1]
    bar=bar.resize((w*S,h*S),Image.Resampling.LANCZOS)
    blue=Image.new('L',bar.size);blue.putdata([a if b>r*1.1 and b>g*.8 else 0 for r,g,b,a in bar.getdata()])
    empty=ImageEnhance.Brightness(bar).enhance(.32)
    wave=bar.copy();wave.putalpha(blue)
    moving=ImageChops.offset(wave,round(frame*.15*S),0)
    extent=Image.new('L',bar.size);ImageDraw.Draw(extent).rectangle((0,0,round(w*S*progress/100),h*S),fill=255)
    filled=empty.copy();filled.alpha_composite(moving)
    filled=Image.composite(filled,empty,extent)
    interior=Image.composite(filled,bar,blue);put(image,interior,box[0],box[1])
    return image.convert('RGB')


if __name__=='__main__':
    destination=HERE/'loading-mockups/codex-real-sprites';destination.mkdir(exist_ok=True)
    for name,teams in [('1v1',[[0],[29]]),('1v3',[[0],[89,88,87]]),('5v5',[[0,24,65,212,239],[29,177,168,233,213]])]:
        compose(teams,60,match_ready=True).save(destination/(name+'.png'))
    assert compose([[0],[29]],100,preparation_complete=True,native_load_complete=False) is None
    print(destination)
