"""Make a developer contact sheet from the native indexed-texture capture."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    args=parser.parse_args()
    root=args.capture.resolve()
    rows=[json.loads(line) for line in (root/'textures.jsonl').read_text().splitlines() if line.strip()]
    if not rows: raise SystemExit('No decoded textures were captured; check trigger and diagnostic log.')
    for page in range(0,len(rows),24):
        batch=rows[page:page+24]
        sheet=Image.new('RGB',(4*280,((len(batch)+3)//4)*240),(32,32,38))
        draw=ImageDraw.Draw(sheet)
        font=ImageFont.load_default()
        for i,row in enumerate(batch):
            file=(root/row['file']).resolve()
            if file.parent!=root: raise ValueError('Image path escapes capture')
            x,y=(i%4)*280,(i//4)*240
            with Image.open(file) as texture:
                texture=texture.convert('RGBA'); texture.thumbnail((264,170))
                for cy in range(y,y+176,16):
                    for cx in range(x,x+272,16):
                        draw.rectangle((cx,cy,cx+15,cy+15),fill=(70,70,78) if ((cx-x)//16+(cy-y)//16)%2 else (110,110,118))
                sheet.paste(texture,(x+(272-texture.width)//2,y+(176-texture.height)//2),texture)
            ee=row.get('ee_address')
            label=f"EE {hex(ee) if ee is not None else 'unknown'}  TBP {row['tbp']}\nPSM {row['psm']:#x}  {row['width']}x{row['height']}\nCLUT {row['clut']} CPSM {row['cpsm']:#x} CSA {row['csa']}"
            draw.multiline_text((x+6,y+181),label,font=font,fill='white',spacing=3)
        output=root/f'contact-sheet-{page//24:02d}.png'
        sheet.save(output); print(output)

if __name__=='__main__': main()
