"""Claude: offline mockups of a game-style Tag Team loading screen (not wired into the game).

Uses only the real character-select face portraits extracted from the user's ISO
(power-scale-trial/controller/game/assets/portraits) and names from characters.json.
Draws at 2x (1024x896) of the native 512x448 frame.
"""
from pathlib import Path
import json,math,sys
from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageChops

HERE=Path(__file__).resolve().parent
GAME=HERE/'power-scale-trial/controller/game'
OUT=HERE/'loading-mockups'
W,H=1024,896
CHARS={c['character_id']:c for c in json.loads((GAME/'assets/characters.json').read_text(encoding='utf-8'))['characters']}

def font(name,size):
    for candidate in (f'C:/Windows/Fonts/{name}',):
        try:return ImageFont.truetype(candidate,size)
        except OSError:pass
    return ImageFont.load_default()

BLACK_FONT='ariblk.ttf';BOLD='arialbd.ttf';ITALIC='arialbi.ttf'

ART_BOX=(8,10,56,53)          # the opaque face area shared by the 161 icons (48x43)
ASPECT=(ART_BOX[3]-ART_BOX[1])/(ART_BOX[2]-ART_BOX[0])
BANNER=58

def portrait(cid,w,h,tint):
    im=Image.open(GAME/f'assets/portraits/{cid:03d}.png').convert('RGBA').crop(ART_BOX)
    im=im.resize((w,h),Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2,percent=60,threshold=2))
    back=Image.new('RGBA',(w,h));bd=ImageDraw.Draw(back)
    for y in range(h):
        k=y/max(1,h-1)
        bd.line([(0,y),(w,y)],fill=(int(tint[0]*(0.30-0.18*k)),int(tint[1]*(0.30-0.18*k)),int(tint[2]*(0.38-0.20*k)),255))
    back.alpha_composite(im);return back

def italic(img,shear=0.22):
    w,h=img.size
    return img.transform((w+int(h*shear),h),Image.AFFINE,(1,shear,-h*shear,0,1,0),Image.BICUBIC)

def text_layer(text,fnt,fill,outline=None,outline_w=0,shadow=None,shear=0.0):
    probe=ImageDraw.Draw(Image.new('RGBA',(1,1)))
    box=probe.textbbox((0,0),text,font=fnt,stroke_width=outline_w)
    pad=outline_w+6
    layer=Image.new('RGBA',(box[2]-box[0]+pad*2+10,box[3]-box[1]+pad*2+10),(0,0,0,0))
    d=ImageDraw.Draw(layer)
    xy=(pad-box[0],pad-box[1])
    if shadow:d.text((xy[0]+shadow[0],xy[1]+shadow[1]),text,font=fnt,fill=shadow[2],stroke_width=outline_w,stroke_fill=shadow[2])
    d.text(xy,text,font=fnt,fill=fill,stroke_width=outline_w,stroke_fill=outline or fill)
    return italic(layer,shear) if shear else layer

def paste_center(canvas,layer,cx,cy):
    canvas.alpha_composite(layer,(int(cx-layer.width/2),int(cy-layer.height/2)))

def glow(canvas,box,color,blur,alpha=140):
    g=Image.new('RGBA',canvas.size,(0,0,0,0));d=ImageDraw.Draw(g)
    d.rounded_rectangle(box,radius=12,fill=color+(alpha,))
    canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))

def background(accent_left,accent_right,warm=False):
    base=Image.new('RGBA',(W,H),(8,10,18,255))
    px=base.load()
    # vertical gradient: slightly lighter toward the middle band
    d=ImageDraw.Draw(base)
    for y in range(H):
        t=1-abs((y-H*0.5)/(H*0.5))
        c=(int(8+14*t),int(10+16*t),int(18+30*t),255)
        d.line([(0,y),(W,y)],fill=c)
    # side energy washes, kept soft so the portraits stay the focus
    for cx,col in ((0,accent_left),(W,accent_right)):
        wash=Image.new('RGBA',(W,H),(0,0,0,0));wd=ImageDraw.Draw(wash)
        wd.ellipse((cx-520,H*0.5-420,cx+520,H*0.5+420),fill=col+(85,))
        base.alpha_composite(wash.filter(ImageFilter.GaussianBlur(120)))
    # diagonal speed lines
    lines=Image.new('RGBA',(W,H),(0,0,0,0));ld=ImageDraw.Draw(lines)
    for i in range(-10,34):
        x=i*48
        ld.polygon([(x,0),(x+18,0),(x+18-260,H),(x-260,H)],fill=(255,255,255,7))
    base.alpha_composite(lines)
    # letterbox bars like the in-game cinematics
    bars=ImageDraw.Draw(base)
    bars.rectangle((0,0,W,72),fill=(0,0,0,255));bars.rectangle((0,H-72,W,H),fill=(0,0,0,255))
    return base

def frame(canvas,x,y,w,h,col):
    pad=8
    box=(x-pad,y-pad,x+w+pad,y+h+pad)
    glow(canvas,box,col,16,150)
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle(box,radius=8,fill=(10,14,26,255),outline=(255,255,255,255),width=3)
    d.rounded_rectangle((box[0]+5,box[1]+5,box[2]-5,box[3]-5),radius=5,outline=col+(255,),width=3)

def clean_name(name):
    return name.split('[')[0].strip()

def name_banner(canvas,x,y,w,name,form,col,align):
    h=BANNER
    d=ImageDraw.Draw(canvas)
    if align=='L':pts=[(x-8,y),(x+w+8,y),(x+w+8-14,y+h),(x-8,y+h)]
    else:pts=[(x-8+14,y),(x+w+8,y),(x+w+8,y+h),(x-8,y+h)]
    d.polygon(pts,fill=(0,0,0,228))
    d.rectangle((x-8,y,x+w+8,y+4),fill=col+(255,))
    size=21 if w>=200 else (18 if w>=160 else 15)
    t=text_layer(clean_name(name).upper(),font(ITALIC,size),(255,255,255,255),outline=(0,0,0,255),outline_w=2)
    room=w-14-(14 if align=='R' else 0)
    if t.width>room:t=t.resize((room,int(t.height*room/t.width)),Image.LANCZOS)
    off=(2 if align=='L' else 16)
    canvas.alpha_composite(t,(int(x+off-4),int(y+3)))
    if form:
        t2=text_layer(form,font(BOLD,13 if w>=160 else 11),(255,206,92,255))
        if t2.width>room:t2=t2.resize((room,int(t2.height*room/t2.width)),Image.LANCZOS)
        canvas.alpha_composite(t2,(int(x+off-4),int(y+h-t2.height-1)))

def side_layout(n,side):
    """(x, y, w, h) per fighter for one side; the cards stay inside y 96..716."""
    if n<=1:w=290
    elif n==2:w=226
    elif n==3:w=150
    elif n==4:w=150
    else:w=134
    h=int(w*ASPECT)
    cols=1 if n<=3 else 2
    rows=math.ceil(n/cols)
    banner=BANNER;gap_x=18;gap_y=16 if n<=3 else 12
    total_w=cols*w+(cols-1)*gap_x
    total_h=rows*(h+banner)+(rows-1)*gap_y
    x0=44 if side==0 else W-44-total_w
    y0=96+(620-total_h)//2
    spots=[]
    for i in range(n):
        r,c=divmod(i,cols)
        spots.append((x0+c*(w+gap_x),y0+r*(h+banner+gap_y),w,h))
    return spots

def vs_emblem(canvas,cx,cy,scale=1.0):
    f=font(BLACK_FONT,int(170*scale))
    shadow=text_layer('VS',f,(0,0,0,255),outline=(0,0,0,255),outline_w=14,shear=0.2)
    body=text_layer('VS',f,(255,236,120,255),outline=(255,120,20,255),outline_w=9,shear=0.2)
    # glow
    g=Image.new('RGBA',canvas.size,(0,0,0,0))
    gl=text_layer('VS',f,(255,170,40,255),outline=(255,170,40,255),outline_w=22,shear=0.2)
    g.alpha_composite(gl,(int(cx-gl.width/2),int(cy-gl.height/2)))
    canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
    paste_center(canvas,shadow,cx+7,cy+8)
    paste_center(canvas,body,cx,cy)

def progress(canvas,pct,message,col_a=(255,196,52),col_b=(255,110,20)):
    x0,x1,y0,y1=170,W-170,748,778
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((x0-6,y0-6,x1+6,y1+6),radius=10,fill=(0,0,0,235),outline=(255,255,255,255),width=3)
    d.rounded_rectangle((x0,y0,x1,y1),radius=6,fill=(26,30,46,255))
    fill_w=int((x1-x0)*pct)
    if fill_w>6:
        bar=Image.new('RGBA',(fill_w,y1-y0),(0,0,0,0));bd=ImageDraw.Draw(bar)
        for xx in range(fill_w):
            t=xx/max(1,fill_w-1)
            bd.line([(xx,0),(xx,y1-y0)],fill=tuple(int(col_a[i]+(col_b[i]-col_a[i])*t) for i in range(3))+(255,))
        shine=Image.new('RGBA',bar.size,(255,255,255,0));sd=ImageDraw.Draw(shine);sd.rectangle((0,0,fill_w,(y1-y0)//2),fill=(255,255,255,55))
        bar.alpha_composite(shine)
        mask=Image.new('L',bar.size,0);ImageDraw.Draw(mask).rounded_rectangle((0,0,fill_w-1,y1-y0-1),radius=6,fill=255)
        canvas.paste(bar,(x0,y0),mask)
    t=text_layer(f'{int(pct*100)}%',font(BLACK_FONT,24),(255,255,255,255),outline=(0,0,0,255),outline_w=3,shear=0.15)
    canvas.alpha_composite(t,(x1+18,y0+15-t.height//2))
    lab=text_layer(message.upper(),font(BOLD,22),(235,240,250,255),outline=(0,0,0,255),outline_w=2)
    paste_center(canvas,lab,W//2,H-36)

def title(canvas,mode_text):
    t=text_layer(mode_text,font(ITALIC,30),(255,255,255,255),outline=(0,0,0,255),outline_w=3)
    paste_center(canvas,t,W//2,36)

def render(team0,team1,pct,message,mode_text='TEAM BATTLE',style='gold'):
    blue=(60,140,255);red=(255,86,60)
    if style=='classic':blue=(70,170,255);red=(255,120,50)
    canvas=background(blue,red)
    for side,(team,col) in enumerate(((team0,blue),(team1,red))):
        for i,(cid,(x,y,w,h)) in enumerate(zip(team,side_layout(len(team),side))):
            frame(canvas,x,y,w,h,col)
            canvas.alpha_composite(portrait(cid,w,h,col),(x,y))
            info=CHARS[cid]
            name_banner(canvas,x,y+h+10,w,info['base_name'],info['form'],col,'L' if side==0 else 'R')
    vs_emblem(canvas,W//2,H//2-14,1.0 if max(len(team0),len(team1))<=3 else 0.8)
    title(canvas,mode_text)
    progress(canvas,pct,message)
    return canvas.convert('RGB')

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    cases={
        '1_2v2':([10,38],[117,112],0.58,'Loading selected fighters','TEAM BATTLE'),
        '2_1v3':([4],[53,112,86],0.31,'Creating independent fighters','TEAM BATTLE'),
        '3_5v5':([0,10,38,53,54],[117,112,86,97,111],0.82,'Preparing special effects','TEAM BATTLE'),
    }
    for name,(a,b,pct,msg,mode) in cases.items():
        render(a,b,pct,msg,mode).save(OUT/f'{name}.png')
        print('saved',OUT/f'{name}.png')
