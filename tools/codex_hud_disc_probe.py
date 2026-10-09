"""Read-only targeted disc texture header and source-body probe."""
import json
import struct
import subprocess
import hashlib
from PIL import Image
from pathlib import Path
import claude_hud_sheet_lib as disc

HERE=Path(__file__).resolve().parent
output=HERE/'power-scale-trial/hud-disc-probe'
output.mkdir(exist_ok=True)
inventory=json.loads((HERE/'power-scale-trial/textures-all-afs.json').read_text())['PZS3US1']
candidates=[r for r in inventory if (r[1]==20 and r[2:4]==[128,128]) or (r[1]==19 and r[2:4]==[256,64])]
captures=[]
archive=HERE/'power-scale-trial/log-archive/hud-native-capture-clock8-clock2-success'
for folder in (archive/'capture-1',archive/'capture-2'):
    for row in map(json.loads,(folder/'textures.jsonl').read_text().splitlines()):
        if row['tbp'] not in (10752,10880) or row['clut']==12992: continue
        with Image.open(folder/row['file']) as im:
            captures.append((row,list(im.convert('RGBA').getdata())))
def pattern(values):
    labels={}; result=[]
    for value in values:
        if value not in labels: labels[value]=len(labels)
        result.append(labels[value])
    return result
matches=[]
for path,psm,w,h,size in candidates:
    blob=disc.fetch(path)
    name='.'.join(map(str,path))
    (output/(name+'.bin')).write_bytes(blob)
    print(name,psm,w,h,len(blob))
    indices=output/(name+'.indices')
    run=subprocess.run([str(HERE/'power-scale-trial/codex_decode_disc_indices.exe'),str(output/(name+'.bin')),str(indices)],capture_output=True)
    if run.returncode: print('decode rejected',name,run.returncode); continue
    values=indices.read_bytes()
    palette_offset=0xc0+w*h//(2 if psm==20 else 1)+0x80
    palette=blob[palette_offset:palette_offset+(64 if psm==20 else 1024)]
    if len(palette)!=(64 if psm==20 else 1024): continue
    colours=[]
    for index in values:
        entry=index if psm==20 else (index&0xe7)|((index&8)<<1)|((index&16)>>1)
        r,g,b,a=palette[entry*4:entry*4+4]
        colours.append((r,g,b,min(255,a*255//128)))
    preview=Image.new('RGBA',(w,h)); preview.putdata(colours); preview.save(output/(name+'.png'))
    for row,rgba in captures:
        if (row['psm'],row['width'],row['height'])!=(psm,w,h): continue
        exact=colours==rgba
        equivalent=pattern(colours)==pattern(rgba)
        if exact or equivalent:
            hit={'disc_path':path,'tbp':row['tbp'],'psm':psm,'clut':row['clut'],'exact_rgba':exact,'palette_independent_pixel_partition':equivalent,'blob_sha256':hashlib.sha256(blob).hexdigest()}
            matches.append(hit);print('MATCH',hit)
(output/'matches.json').write_text(json.dumps(matches,indent=2)+'\n')

# Search the existing prepared RAM capture, not a live game/PINE connection.
# Only accept the same indexed TEX0 dimensions and complete native IMAGE header.
import numpy as np
ram_path=HERE/'power-scale-trial/controller/game/analysis/prepared-states/20261006-194551-a32ecc27/16-ready-held.bin'
ram=ram_path.read_bytes()
words=np.frombuffer(ram,dtype='<u8')
mask=(63<<20)|(15<<26)|(15<<30)
value=(20<<20)|(7<<26)|(7<<30)
hits=np.flatnonzero((words & np.uint64(mask))==np.uint64(value))
ram_matches=[]
for hit in hits:
    address=int(hit)*8-0x50
    if address<0 or address+8640>len(ram): continue
    if struct.unpack_from('<Q',ram,address+0x98)[0]!=0x52: continue
    if ((struct.unpack_from('<Q',ram,address+0xb0)[0]>>58)&3)!=2: continue
    name=f'ram-{address:08x}'
    binary=output/(name+'.bin'); binary.write_bytes(ram[address:address+8640])
    indices=output/(name+'.indices')
    run=subprocess.run([str(HERE/'power-scale-trial/codex_decode_disc_indices.exe'),str(binary),str(indices)],capture_output=True)
    if run.returncode: continue
    shape=pattern(indices.read_bytes())
    for row,rgba in captures:
        if (row['psm'],row['width'],row['height'])!=(20,128,128): continue
        if shape==pattern(rgba):
            match={'ram_capture':str(ram_path),'ee_header':f'{address:08X}','ee_pixels':f'{address+0xc0:08X}','tbp':row['tbp'],'clut':row['clut'],'evidence':'exact palette-independent pixel partition; not an observed upload event'}
            ram_matches.append(match); print('RAM MATCH',match)
print('RAM TEX0 candidates:',len(hits),'verified timer shape matches:',len(ram_matches))
(output/'ram-matches.json').write_text(json.dumps(ram_matches,indent=2)+'\n')
