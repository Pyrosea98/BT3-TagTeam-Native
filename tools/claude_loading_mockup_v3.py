"""Loading cover mockup built ONLY from sprites decoded from the user's own disc (reference render, not shipped)."""
import sys,struct,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageFont
HERE=Path(__file__).resolve().parent;TRIAL=HERE/'power-scale-trial'
sys.path.insert(0,str(TRIAL/'controller/game/tools'))
import extract_loading_assets as ex
import claude_hud_sheet_lib as lib
pm=json.load(open(TRIAL/'portrait-slot-map.json'))['map']
def portrait(slot):
    j=pm[str(slot)]['iso_index'];return ex.portrait_rgba(lib.PORTRAITS[j])
def img(rgba,w,h):
    return Image.frombytes('RGBA',(w,h),rgba)
W,H=640,448
S=2
bg=Image.new('RGBA',(W*S,H*S),(14,18,30,255))
d=ImageDraw.Draw(bg)
# subtle vertical gradient from the game's own colours (deep navy to teal)
for y in range(H*S):
    t=y/(H*S);c=(int(14+10*t),int(20+34*t),int(40+30*t),255);d.line([(0,y),(W*S,y)],fill=c)
# dragon banner texture (450.0.9) as a faint band
band=lib.sprite([450,0,9],512,128) if lib.has([450,0,9]) else None
if band:
    band=band.resize((W*S,int(band.height*W*S/band.width)));band.putalpha(band.getchannel('A').point(lambda a:int(a*0.35)))
    bg.alpha_composite(band,(0,int(H*S*0.40)))
def plate(pts,fill,edge):
    layer=Image.new('RGBA',bg.size,(0,0,0,0));ld=ImageDraw.Draw(layer)
    ld.polygon(pts,fill=fill);ld.line(pts+[pts[0]],fill=edge,width=3*S)
    return layer
def slanted_portrait(slot,x,y,flip=False):
    p=img(portrait(slot),64,64).resize((64*S*3//2*1,64*S*3//2*1),Image.NEAREST) if False else img(portrait(slot),64,64).resize((64*3*S//1,64*3*S//1),Image.LANCZOS)
    if flip:p=p.transpose(Image.FLIP_LEFT_RIGHT)
    return p
# portraits on slanted plates
pw=192*S
for slot,x,flip in ((0,40*S,False),(29,(W-40)*S-pw,True)):
    y=90*S
    pts=[(x+20*S,y),(x+pw,y),(x+pw-20*S,y+pw),(x,y+pw)] if not flip else [(x,y),(x+pw-20*S,y),(x+pw,y+pw),(x+20*S,y+pw)]
    bg.alpha_composite(plate(pts,(24,28,40,230),(180,190,210,255)))
    p=slanted_portrait(slot,x,y,flip)
    mask=Image.new('L',bg.size,0);ImageDraw.Draw(mask).polygon(pts,fill=255)
    tile=Image.new('RGBA',bg.size,(0,0,0,0));tile.alpha_composite(p,(x,y));tile.putalpha(Image.composite(tile.getchannel('A'),Image.new('L',bg.size,0),mask))
    bg.alpha_composite(tile)
    bg.alpha_composite(plate(pts,(0,0,0,0),(235,238,245,255)))
# VS burst
vs=lib.sprite([455,11],128,128) if lib.has([455,11]) else None
if vs:
    vs=vs.resize((vs.width*S*2,vs.height*S*2),Image.LANCZOS);bg.alpha_composite(vs,((W*S-vs.width)//2,(90*S+pw//2)-vs.height//2))
# dragon balls 449.1.9: 4+3 grid of cells
db=lib.sprite([449,1,9],256,128) if lib.has([449,1,9]) else None
if db:
    cell=db.width//4;balls=[]
    for k in range(7):
        r,cidx=divmod(k,4);balls.append(db.crop((cidx*cell,r*cell,cidx*cell+cell,r*cell+cell)))
    sz=56*S;gap=10*S;total=7*sz+6*gap;x0=(W*S-total)//2;y0=292*S
    for k,b in enumerate(balls):
        b=b.resize((sz,sz),Image.LANCZOS)
        if k>=4:  # not yet reached: dim them
            b=b.copy();a=b.getchannel('A').point(lambda v:int(v*0.35));b.putalpha(a)
        bg.alpha_composite(b,(x0+k*(sz+gap),y0))
# wavy progress frame 449.1.10
bar=lib.sprite([449,1,10],256,64) if lib.has([449,1,10]) else None
if bar:
    bar=bar.resize((bar.width*S*3//2,bar.height*S*3//2),Image.LANCZOS);bg.alpha_composite(bar,((W*S-bar.width)//2,348*S))
out=bg.resize((W*S//1,H*S//1),Image.LANCZOS).convert('RGB')
out.save(HERE/'loading-mockups'/'v3-real-sprites.png');print('saved')
