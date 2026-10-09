"""Read back actual Vulkan UI without booting the game, then check the strip.

Usage: python codex_check_branding_loading.py path/to/new/runner.exe
Uses the production native UI self-test; never changes guest RAM or saves.
"""
import argparse,json,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser();parser.add_argument('runner',type=Path)
    args=parser.parse_args()
    out=HERE/'power-scale-trial/branding-loading-captures';out.mkdir(exist_ok=True)
    assets=HERE/'power-scale-trial/app-data/native-ui'
    env=os.environ.copy()
    for key in ('PS2X_NATIVE_UI_TEST_MENUS_ONLY','PS2X_NATIVE_UI_TEST_HUD_ONLY','PS2X_FUSION_HUD_TEST_ONLY','PS2X_REVIVE_HUD_TEST_ONLY','PS2X_UI_MENU_FIXTURES'):
        env.pop(key,None)
    env.update(PS2X_NATIVE_UI_SLICE='1')
    with (out/'vulkan-check.log').open('wb') as log:
        result=subprocess.run([str(args.runner.resolve()),'--native-ui-vulkan-self-test',str(assets),str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if result.returncode:raise RuntimeError(f'Vulkan self-test exit {result.returncode}: {out / "vulkan-check.log"}')
    rows=[]
    for language in ('en','es'):
        for match in ('1v1','2v1','3v2','5v5'):
            name=f'loading-{language}-{match}'
            image=Image.open(out/(name+'.png')).convert('RGB')
            # At 78% progress this area must be uniformly blue energy. The
            # legacy crop leaks a yellow notch and black tail into this area.
            pixels=list(image.crop((52,349,466,359)).getdata())
            cyan=sum(b>r+60 and g>r+35 for r,g,b in pixels)/len(pixels)
            assert cyan>.97,(name,'sprite border/black tail in energy fill',cyan)
            logo=list(image.crop((226,2,414,62)).getdata())
            gold=sum(r>160 and g>90 and b<r*.75 for r,g,b in logo)
            assert gold>100,(name,'brand logo missing',gold)
            rows.append(dict(name=name,cyan_fill_fraction=cyan,logo_gold_pixels=gold))
        for kind,box in (('credits-full',(100,28,540,176)),('about',(442,5,608,60)),('settings',(442,5,608,60))):
            image=Image.open(out/f'{kind}-{language}.png').convert('RGB')
            pixels=list(image.crop(box).getdata())
            gold=sum(r>160 and g>90 and b<r*.75 for r,g,b in pixels)
            assert gold>100,(kind,language,'branding missing')
    names=['credits-full-en','about-en','loading-en-3v2','loading-es-5v5']
    sheet=Image.new('RGB',(1280,944),(12,21,35));draw=ImageDraw.Draw(sheet)
    for index,name in enumerate(names):
        x=index%2*640;y=index//2*472
        with Image.open(out/(name+'.png')) as image:sheet.paste(image,(x,y))
        draw.text((x+10,y+454),name,fill=(230,230,230))
    sheet.save(out/'contact-sheet.png')
    (out/'acceptance.json').write_text(json.dumps(dict(renderer=str(args.runner.resolve()),game_booted=False,strip_readback='PASS',branding_readback='PASS',cases=rows),indent=2),encoding='utf-8')
    print('PASS actual Vulkan EN/ES branding and borderless energy strip readback; no game boot')
if __name__=='__main__':main()
