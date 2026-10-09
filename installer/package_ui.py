"""Temporary embedded import-time UI derivation; no pre-extracted game art."""
import hashlib,json,struct,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import pycdlib

def derive(here,iso_path):
    sys.path.insert(0,str(here));sys.path.insert(0,str(here/'power-scale-trial/controller/game/tools'))
    import extract_loading_assets as ex
    import codex_extract_battle_hud as hud
    import codex_import_native_ui as importer
    trial=here/'power-scale-trial';extracted=trial/'hud-entry5-extracted';extracted.mkdir(exist_ok=True)
    blob=hud.entry5(iso_path)
    if hashlib.sha256(blob).hexdigest()!=hud.ENTRY_SHA256:raise ValueError('Unsupported interface art.')
    for name,off,psm,w,h,bw,uw,uh,paloff,count,tbp,clut in hud.ASSETS:
        source=extracted/(name+'.ct32');source.write_bytes(blob[off:off+uw*uh*4]);target=extracted/(name+'.indices')
        subprocess.run([str(trial/'codex_decode_disc_indices.exe'),str(source),str(target),*map(str,(psm,w,h,bw,uw,uh))],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        palette=blob[paloff:paloff+count*4];colours=[]
        for index in target.read_bytes():
            entry=index if count==16 else (index&0xe7)|((index&8)<<1)|((index&16)>>1)
            r,g,b,a=palette[entry*4:entry*4+4];colours.append((r,g,b,min(255,a*255//128)))
        image=Image.new('RGBA',(w,h));image.putdata(colours);image.save(extracted/(name+'.png'))
    atlas=here/'ui-assets/glyph-atlas-v2'
    plate=Image.open(extracted/'plate.png').convert('RGBA').crop((0,16,78,36))
    def nine_slice(width,height):
        result=Image.new('RGBA',(width,height));sx=(0,20,plate.width-12,plate.width);sy=(0,4,plate.height-4,plate.height)
        dx=(0,20,width-12,width);dy=(0,4,height-4,height)
        for y in range(3):
            for x in range(3):result.paste(plate.crop((sx[x],sy[y],sx[x+1],sy[y+1])).resize((dx[x+1]-dx[x],dy[y+1]-dy[y])),(dx[x],dy[y]))
        d=ImageDraw.Draw(result);d.rectangle((width-20,0,width-1,height-1),fill=(0,0,0,0));d.polygon([(width-21,0),(width-1,0),(width-13,height-1),(width-21,height-1)],fill=(9,12,17,255));d.line((20,0,width-2,0),fill=(95,107,123,255));d.line((width-2,0,width-13,height-1),fill=(95,107,123,255));return result
    nine_slice(575,48).save(atlas/'row-plate-9slice.png');nine_slice(575,34).save(atlas/'help-plate-9slice.png')
    chip=Image.new('RGBA',(172,36));ImageDraw.Draw(chip).polygon([(10,0),(171,0),(161,35),(0,35)],fill=(15,20,30,255),outline=(183,194,208,255));chip.save(atlas/'value-chip.png')
    iso=pycdlib.PyCdlib();iso.open(str(iso_path))
    sizes={tuple(p):(w,h) for p,w,h,_ in json.loads((trial/'psmt8-textures-afs1.json').read_text(encoding='utf-8'))}
    def fetch(path):
        with iso.open_file_from_iso(iso_path='/DATA/PZS3US1.AFS;1') as stream:
            stream.seek(8+path[0]*8);offset,size=struct.unpack('<II',stream.read(8));stream.seek(offset);data=stream.read(size)
        for index in path[1:]:
            try:package=ex.package(data)
            except Exception:package=ex.package(ex.unpack_bpe(data))
            data=package[index]
        return data
    def sprite(path):
        w,h=sizes[tuple(path)];data=fetch(path);pixels=data[0xc0:0xc0+w*h];pal=data[0xc0+w*h+0x80:0xc0+w*h+0x480];rgba=[]
        for y in range(h):
            for x in range(w):
                block=(y&~15)*w+(x&~15)*2;swap=(((y+2)>>2)&1)*4;line=(((y&~3)>>1)+(y&1))&7
                index=pixels[block+line*w*2+((x+swap)&7)*4+((y>>1)&1)+((x>>2)&2)]
                entry=(index&0xe7)|((index&8)<<1)|((index&16)>>1);r,g,b,a=pal[entry*4:entry*4+4];rgba.append((r,g,b,min(255,a*2)))
        image=Image.new('RGBA',(w,h));image.putdata(rgba);return image
    try:
        portraits=ex.package(ex.package(ex.unpack_bpe(ex.package(fetch([450]))[1]))[31])
        importer.main(trial/'app-data/native-ui',disc=SimpleNamespace(ISO=iso_path,sprite=sprite,_found=sizes,PORTRAITS=portraits))
    finally:iso.close()
