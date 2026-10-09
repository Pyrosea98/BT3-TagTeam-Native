"""Developer importer: read the player's ISO; cache RGBA UI assets locally."""
from pathlib import Path
import json, shutil, struct, hashlib, re
HERE=Path(__file__).resolve().parent
DEFAULT=HERE/'power-scale-trial/app-data/native-ui'

def brand_asset(destination):
    """Shared original branding, independent of the player's disc art cache."""
    from PIL import Image
    with Image.open(HERE/'ui-assets/branding/tag-team-real-power-scale-v1.png') as source:
        logo=source.convert('RGBA')
        bounds=logo.getchannel('A').getbbox()
        if not bounds:raise ValueError('Brand logo is empty')
        logo=logo.crop(bounds)
        logo.thumbnail((768,256),Image.Resampling.LANCZOS)
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    (out/'brand-logo.rgba').write_bytes(struct.pack('<II',*logo.size)+logo.tobytes())
    return logo

def display_name(name):
    # Display only: keep audited IDs, file keys and original roster unchanged.
    name=re.sub(r'\[\d+\]', '', name)
    name=re.sub(r'\s*-\s*\d[\d.,]*(?:\s*[MKmk])?(?:\s*\([^)]*\))?', '', name)
    return re.sub(r'\s+', ' ', name).strip(' -')

def main(destination=DEFAULT,disc=None):
    if disc is None:import claude_hud_sheet_lib as disc
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    brand_asset(out)
    def save(name,image):
        image=image.convert('RGBA')
        (out/(name+'.rgba')).write_bytes(struct.pack('<II',*image.size)+image.tobytes())
    for name,path in [('balls',[449,1,9]),('wave',[449,1,10]),('vs',[455,11]),('banner',[450,0,9])]:
        save(name,disc.sprite(path))
    from PIL import Image, ImageDraw
    # HUD panels need a flat lower cap: stretching menu plate corners creates
    # grey blocks that resemble buttons. This plain plate has no corner ribs.
    flat=Image.new('RGBA',(250,100),(0,0,0,0));edge=ImageDraw.Draw(flat)
    edge.polygon([(3,0),(249,0),(244,99),(0,99)],fill=(7,11,16,245))
    edge.line([(3,0),(249,0)],fill=(122,136,148,255),width=1)
    edge.line([(249,0),(244,99)],fill=(50,62,73,255),width=1)
    edge.line([(0,99),(244,99)],fill=(35,44,54,255),width=1)
    save('hud-flat-plate',flat)
    original=disc.sprite([449,1,10]).convert('RGBA')
    frame=original.crop((3,13,195,55))
    # This compatibility asset must not contain the original gold scroll cap
    # or black tail, even with a runner that still samples wave-interior.
    interior=Image.new('RGBA',(148,15))
    for y in range(15):
        light=1-abs(y-6)/9
        for x in range(148):interior.putpixel((x,y),(int(18+35*light),int(82+110*light),int(119+112*light),255))
    # Erase only the blue interior in a bounded window. Gold scroll cap and
    # wavy frame remain a separate, stationary overlay at full brightness.
    for y in range(10,32):
        for x in range(29,182):
            r,g,b,a=frame.getpixel((x,y))
            if b>r and b>g*.85:frame.putpixel((x,y),(0,0,0,0))
    save('wave-frame',frame);save('wave-interior',interior)
    seats=disc.sprite([448,1,21]).convert('RGBA');tabs=disc.sprite([448,1,33]).convert('RGBA')
    for i,im in enumerate((seats.crop((0,32,64,64)),seats.crop((0,0,64,32)),seats.crop((64,0,128,32)),tabs.crop((128,0,192,20)),tabs.crop((192,0,256,20)))):
        bounds=im.getchannel('A').getbbox();save(f'seat-{i}',im.crop(bounds) if bounds else im)
    sheet=disc.sprite([449,1,9]);cw,ch=sheet.width//4,sheet.height//2
    for i in range(7):
        ball=sheet.crop(((i%4)*cw,(i//4)*ch,(i%4+1)*cw,(i//4+1)*ch))
        bounds=ball.getchannel('A').getbbox()
        if bounds:ball=ball.crop(bounds)
        save(f'ball-{i}',ball)
    for name,accent in [('team-cyan',(55,206,255,255)),('team-orange',(255,150,44,255))]:
        plate=Image.new('RGBA',(272,180));d=ImageDraw.Draw(plate)
        points=[(20,0),(271,0),(251,179),(0,179)]
        d.polygon(points,fill=(24,28,40,235));d.line(points+[points[0]],fill=accent,width=1)
        inner=[(21,2),(269,2),(250,177),(2,177)]
        d.line(inner+[inner[0]],fill=(190,198,215,255),width=2);save(name,plate)
    plate=Image.new('RGBA',(575,31));d=ImageDraw.Draw(plate)
    points=[(10,0),(574,0),(564,30),(0,30)]
    d.polygon(points,fill=(46,29,64,250));d.line(points+[points[0]],fill=(244,188,76,255),width=1);save('selected-row',plate)
    diamond=Image.new('RGBA',(9,9));ImageDraw.Draw(diamond).polygon([(4,0),(8,4),(4,8),(0,4)],fill=(255,255,255,255));save('spark',diamond)
    with Image.open(HERE/'power-scale-trial/hud-entry5-extracted/plate.png') as plate:save('title-plate',plate)
    for colour in ('green','blue','grey','red'):
        with Image.open(HERE/'power-scale-trial/hud-entry5-extracted'/f'bars-{colour}.png') as im:
            save(f'hud-bar-{colour}',im.crop((64,1,155,11)))
    for colour in ('grey','yellow','red'):
        with Image.open(HERE/'power-scale-trial/hud-entry5-extracted'/f'timer-{colour}.png') as im:
            for digit in range(10):
                x=(digit%4)*32;y=(digit//4)*32;cell=im.crop((x,y,x+32,y+32));save(f'timer-{colour}-{digit}',cell.crop(cell.getchannel('A').getbbox()))
    save('hud-gold',Image.new('RGBA',(2,2),(245,185,53,255)))
    marker=Image.new('RGBA',(20,20));draw=ImageDraw.Draw(marker)
    draw.line([(10,1),(18,10),(10,18),(1,10),(10,1)],fill=(60,220,255,255),width=2);save('lock-marker',marker)
    rows=json.loads((HERE/'roster-assets/characters.json').read_text(encoding='utf-8'))['characters']
    if len(rows)!=253:raise ValueError('Expected audited 253-slot roster')
    names=[]
    for row in rows:
        cid=row['character_id'];idx=row['portrait_iso_index']
        raw=disc.PORTRAITS[idx];w,h=disc._found[(450,1,31,idx)]
        pix=raw[0xC0:0xC0+w*h];pal=raw[0xC0+w*h+0x80:0xC0+w*h+0x480]
        colors=[]
        for index in range(256):
            entry=(index&0xE7)|((index&8)<<1)|((index&16)>>1)
            r,g,b,a=pal[entry*4:entry*4+4];colors.append(bytes((r,g,b,min(255,a*2))))
        pixels=bytearray()
        for y in range(h):
            for x in range(w):
                block=(y&~15)*w+(x&~15)*2;swap=(((y+2)>>2)&1)*4
                line=(((y&~3)>>1)+(y&1))&7
                source=block+line*w*2+((x+swap)&7)*4+((y>>1)&1)+((x>>2)&2)
                pixels.extend(colors[pix[source]])
        save(f'portrait-{cid:03}',Image.frombytes('RGBA',(w,h),bytes(pixels)))
        name=display_name(row['base_name']).encode('utf-8')
        if len(name)>255:raise ValueError('Unbounded character name')
        names.append(struct.pack('<H',len(name))+name)
    (out/'names.bin').write_bytes(b''.join(names))
    for path in (HERE/'ui-assets/glyph-atlas-v2').iterdir():
        if path.suffix in ('.gatl','.indices','.rgba'):shutil.copy2(path,out/path.name)
    # Approved row template, derived from the player's entry-5 plate.
    for stem in ('row-plate-9slice','help-plate-9slice','value-chip'):
        from PIL import Image
        with Image.open(HERE/'ui-assets/glyph-atlas-v2'/f'{stem}.png') as image:save(stem,image)
    (out/'manifest.json').write_text(json.dumps(dict(version=7,portraits=253,source_size=disc.ISO.stat().st_size,source_mtime_ns=disc.ISO.stat().st_mtime_ns,
        source_iso=str(disc.ISO),slot_map_sha256=hashlib.sha256((HERE/'roster-assets/characters.json').read_bytes()).hexdigest(),
        redistribution='Local player-disc cache; do not distribute game art'),indent=2),encoding='utf-8')
    print(out)
    return out
if __name__=='__main__':main()
