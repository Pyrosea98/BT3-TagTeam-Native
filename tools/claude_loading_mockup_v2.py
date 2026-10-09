"""Claude: loading screen mockup v2 - mod logo, Shenron coil, Dragon Ball progress (offline art, not wired in).

Builds on claude_loading_mockup (portraits, frames, banners). 2x of the native 512x448 frame.
"""
from pathlib import Path
import math,random,sys
from PIL import Image,ImageDraw,ImageFilter
sys.path.insert(0,str(Path(__file__).resolve().parent))
import claude_loading_mockup as m

W,H=m.W,m.H
LOGO=Image.open(m.GAME/'Tag Team Mod Logo.png').convert('RGBA')

def catmull(points,steps=24):
    out=[]
    pts=[points[0]]+points+[points[-1]]
    for i in range(1,len(pts)-2):
        p0,p1,p2,p3=pts[i-1],pts[i],pts[i+1],pts[i+2]
        for s in range(steps):
            t=s/steps;t2,t3=t*t,t*t*t
            out.append(tuple(0.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t2+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t3) for k in (0,1)))
    out.append(points[-1]);return out

def dragon_layer(size):
    """A stylised Shenron: tapering green body with belly plates, dorsal spikes and a horned head."""
    S=2;w,h=size[0]*S,size[1]*S
    layer=Image.new('RGBA',(w,h),(0,0,0,0))
    ctrl=[(500,H+60),(380,810),(640,700),(400,590),(640,480),(430,400),(450,300),(410,215),(470,160),(560,140),(640,150)]
    path=catmull([(x*S,y*S) for x,y in ctrl],30)
    n=len(path)
    # unit tangents/normals
    tang=[];norm=[]
    for i in range(n):
        a=path[max(0,i-1)];b=path[min(n-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy) or 1
        tang.append((dx/l,dy/l));norm.append((-dy/l,dx/l))
    def radius(i):
        t=i/(n-1)                      # 0 tail ... 1 head
        return (10+54*min(1,t*1.6))*S if t<0.9 else (64-30*(t-0.9)/0.1)*S
    body=Image.new('RGBA',(w,h),(0,0,0,0));bd=ImageDraw.Draw(body)
    # dorsal spikes first (behind body)
    for i in range(6,n-12,9):
        r=radius(i);nx,ny=norm[i];tx,ty=tang[i]
        base=(path[i][0]-nx*r*0.9,path[i][1]-ny*r*0.9)
        tip=(base[0]-nx*r*0.75-tx*r*0.5,base[1]-ny*r*0.75-ty*r*0.5)
        a=(base[0]-tx*r*0.35,base[1]-ty*r*0.35);b=(base[0]+tx*r*0.35,base[1]+ty*r*0.35)
        bd.polygon([a,tip,b],fill=(214,64,46,255))
    # body discs: dark green, then belly stripe and scale arcs
    for i in range(n):
        r=radius(i);cx,cy=path[i]
        t=i/(n-1);g=int(120+70*(1-abs(0.5-t)*1.2))
        bd.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(26,max(110,g),60,255))
    for i in range(0,n,2):
        r=radius(i);cx,cy=path[i];nx,ny=norm[i]
        # belly: lighter strip on the inner side
        bx,by=cx+nx*r*0.55,cy+ny*r*0.55;br=r*0.42
        bd.ellipse((bx-br,by-br,bx+br,by+br),fill=(236,222,140,255))
    for i in range(4,n-4,5):
        r=radius(i);cx,cy=path[i];nx,ny=norm[i];tx,ty=tang[i]
        for k in (-0.35,0.1):
            px,py=cx-nx*r*0.15+tx*r*k,cy-ny*r*0.15+ty*r*k
            bd.arc((px-r*0.45,py-r*0.45,px+r*0.45,py+r*0.45),200,340,fill=(14,70,40,255),width=max(2,int(r*0.06)))
    # highlight rim
    rim=body.filter(ImageFilter.GaussianBlur(2*S))
    layer.alpha_composite(body)
    # head at the last point, oriented along the tangent
    hx,hy=path[-1];tx,ty=tang[-1];nx,ny=norm[-1]
    def P(u,v):return (hx+tx*u*S+nx*v*S,hy+ty*u*S+ny*v*S)
    hd=ImageDraw.Draw(layer)
    skull=[P(-30,-46),P(30,-52),P(110,-38),P(165,-24),P(172,-4),P(140,8),P(70,14),P(-10,40),P(-40,30)]
    hd.polygon(skull,fill=(30,150,72,255),outline=(10,60,30,255))
    jaw=[P(165,2),P(172,18),P(120,34),P(40,52),P(-20,50),P(0,24),P(70,16)]
    hd.polygon(jaw,fill=(24,128,62,255),outline=(10,60,30,255))
    hd.polygon([P(150,6),P(168,8),P(160,26),P(142,12)],fill=(255,248,224,255))      # fang
    for off in (-0.0,):
        pass
    # horns (swept back, ivory) and mane spikes
    hd.polygon([P(20,-48),P(-60,-96),P(-120,-110),P(-70,-70),P(0,-36)],fill=(240,226,170,255),outline=(120,100,60,255))
    hd.polygon([P(40,-50),P(-20,-120),P(-70,-140),P(-40,-90),P(20,-40)],fill=(240,226,170,255),outline=(120,100,60,255))
    for k,(u,v) in enumerate([(-30,-10),(-50,10),(-40,30),(-60,-30)]):
        hd.polygon([P(u,v),P(u-60,v+14*(k-1)),P(u-6,v+14)],fill=(214,64,46,255))
    # whiskers
    for sgn,ln in ((1,200),(-1,130)):
        pts=[P(150,-2+sgn*4),P(190,-20+sgn*30),P(250,-4+sgn*50),P(ln+100,-30+sgn*95)]
        hd.line(catmull([(p[0],p[1]) for p in pts],10),fill=(236,222,140,255),width=3*S)
    # eye
    ex,ey=P(86,-26);r=9*S
    hd.ellipse((ex-r,ey-r,ex+r,ey+r),fill=(255,40,30,255),outline=(255,255,200,255),width=2*S)
    hd.ellipse((ex-r*0.35,ey-r*0.5,ex+r*0.2,ey+r*0.1),fill=(255,255,255,255))
    out=layer.resize(size,Image.LANCZOS)
    return out

def dragon_balls(canvas,pct,x0,x1,y):
    """Seven Dragon Balls spaced along the bar; each lights once the fill passes it."""
    d=ImageDraw.Draw(canvas)
    for i in range(7):
        cx=x0+(x1-x0)*(i+0.5)/7;r=20
        lit=pct>=(i+0.5)/7-0.04
        if lit:
            g=Image.new('RGBA',canvas.size,(0,0,0,0));gd=ImageDraw.Draw(g)
            gd.ellipse((cx-r*1.9,y-r*1.9,cx+r*1.9,y+r*1.9),fill=(255,170,40,170))
            canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
        base=(255,170,30) if lit else (70,56,40)
        edge=(255,236,160) if lit else (110,96,70)
        d.ellipse((cx-r,y-r,cx+r,y+r),fill=base+(255,),outline=(0,0,0,255),width=3)
        d.ellipse((cx-r+4,y-r+4,cx+r-4,y+r-4),outline=edge+(255,),width=2)
        d.ellipse((cx-r*0.55,y-r*0.7,cx-r*0.05,y-r*0.2),fill=(255,255,255,150 if lit else 40))   # shine
        # stars
        k=i+1;sr=5
        spots=[(0,0)] if k==1 else [(math.cos(a)*9,math.sin(a)*9) for a in [2*math.pi*j/k+math.pi/2 for j in range(k)]]
        for sx,sy in spots:
            pts=[]
            for j in range(10):
                rr=sr if j%2==0 else sr*0.45;a=math.pi*j/5-math.pi/2
                pts.append((cx+sx+math.cos(a)*rr,y+sy+math.sin(a)*rr))
            d.polygon(pts,fill=(210,30,30,255) if lit else (120,40,40,255))

def progress_v2(canvas,pct,message):
    x0,x1,y0,y1=170,W-170,752,776
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((x0-6,y0-6,x1+6,y1+6),radius=10,fill=(0,0,0,235),outline=(255,255,255,255),width=3)
    d.rounded_rectangle((x0,y0,x1,y1),radius=6,fill=(26,30,46,255))
    fw=int((x1-x0)*pct)
    if fw>6:
        bar=Image.new('RGBA',(fw,y1-y0),(0,0,0,0));bd=ImageDraw.Draw(bar)
        for xx in range(fw):
            t=xx/max(1,fw-1);bd.line([(xx,0),(xx,y1-y0)],fill=(int(255-0*t),int(196-86*t),int(52-32*t),255))
        sh=Image.new('RGBA',bar.size,(255,255,255,0));ImageDraw.Draw(sh).rectangle((0,0,fw,(y1-y0)//2),fill=(255,255,255,60));bar.alpha_composite(sh)
        mk=Image.new('L',bar.size,0);ImageDraw.Draw(mk).rounded_rectangle((0,0,fw-1,y1-y0-1),radius=6,fill=255)
        canvas.paste(bar,(x0,y0),mk)
    t=m.text_layer(f'{int(pct*100)}%',m.font(m.BLACK_FONT,24),(255,255,255,255),outline=(0,0,0,255),outline_w=3,shear=0.15)
    canvas.alpha_composite(t,(x1+18,(y0+y1)//2-t.height//2))
    dragon_balls(canvas,pct,x0,x1,y0-34)
    lab=m.text_layer(message.upper(),m.font(m.BOLD,22),(235,240,250,255),outline=(0,0,0,255),outline_w=2)
    m.paste_center(canvas,lab,W//2,H-36)

def render(team0,team1,pct,message,mode_text='TEAM BATTLE'):
    blue=(60,140,255);red=(255,86,60)
    canvas=m.background(blue,red)
    bars0=ImageDraw.Draw(canvas)
    # dragon behind everything, with a soft green aura
    dr=dragon_layer((W,H))
    aura=Image.new('RGBA',(W,H),(0,0,0,0));aura.alpha_composite(dr)
    aura=aura.filter(ImageFilter.GaussianBlur(26));
    green=Image.new('RGBA',(W,H),(60,230,120,0));green.putalpha(aura.getchannel('A').point(lambda a:int(a*0.55)))
    canvas.alpha_composite(green);canvas.alpha_composite(dr)
    bars=ImageDraw.Draw(canvas);bars.rectangle((0,H-72,W,H),fill=(0,0,0,255))   # bottom bar only; the head may cross the top bar
    for side,(team,col) in enumerate(((team0,blue),(team1,red))):
        for i,(cid,(x,y,w,h)) in enumerate(zip(team,m.side_layout(len(team),side))):
            m.frame(canvas,x,y,w,h,col)
            canvas.alpha_composite(m.portrait(cid,w,h,col),(x,y))
            info=m.CHARS[cid]
            m.name_banner(canvas,x,y+h+10,w,info['base_name'],info['form'],col,'L' if side==0 else 'R')
    # logo (centre top) over a soft dark plate so it reads on the art
    lw=300;lh=int(LOGO.height*lw/LOGO.width);logo=LOGO.resize((lw,lh),Image.LANCZOS)
    plate=Image.new('RGBA',(W,H),(0,0,0,0));pd=ImageDraw.Draw(plate);pd.ellipse((W//2-215,214-10,W//2+215,214+lh+30),fill=(0,0,0,150))
    canvas.alpha_composite(plate.filter(ImageFilter.GaussianBlur(26)))
    canvas.alpha_composite(logo,(W//2-lw//2,214))
    m.vs_emblem(canvas,W//2,H//2+140,0.72 if max(len(team0),len(team1))<=3 else 0.62)
    t=m.text_layer(mode_text,m.font(m.ITALIC,30),(255,255,255,255),outline=(0,0,0,255),outline_w=3);m.paste_center(canvas,t,W//2,36)
    progress_v2(canvas,pct,message)
    return canvas.convert('RGB')

if __name__=='__main__':
    m.OUT.mkdir(exist_ok=True)
    render([10,38],[117,112],0.58,'Loading selected fighters').save(m.OUT/'v2_2v2.png')
    render([4],[53,112,86],0.31,'Creating independent fighters').save(m.OUT/'v2_1v3.png')
    print('saved v2')
