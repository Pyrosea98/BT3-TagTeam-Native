"""Actual Vulkan render/readback plus mode-family review sheets, no game."""
import os,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
RUNNER=sys.argv[1] if len(sys.argv)>1 else 'ps2EntryRunner-modes-hud-credits.exe'
OUT=HERE/'power-scale-trial'/('native-ui-live-fixes-capture' if 'live-mode-fixes' in RUNNER else 'native-ui-modes-capture')
def main():
    env=os.environ.copy();env.update(PS2X_NATIVE_UI_SLICE='1',PS2X_NATIVE_UI_BENCH='1')
    with (HERE/'power-scale-trial'/('codex-live-mode-fixes-gpu.log' if 'live-mode-fixes' in RUNNER else 'codex-modes-hud-credits-gpu.log')).open('wb') as log:
        result=subprocess.run([str(HERE/'repo/build/ps2xRuntime'/RUNNER),
            '--native-ui-vulkan-self-test',str(HERE/'power-scale-trial/app-data/native-ui'),str(OUT)],
            env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if result.returncode:raise RuntimeError(f'Native GPU acceptance exit {result.returncode}')
    def sheet(paths,name,columns=5):
        rows=(len(paths)+columns-1)//columns
        image=Image.new('RGB',(640*columns,472*rows),(14,12,24));draw=ImageDraw.Draw(image)
        for i,path in enumerate(paths):
            with Image.open(path) as capture:image.paste(capture.resize((640,448)),((i%columns)*640,(i//columns)*472))
            draw.text(((i%columns)*640+8,(i//columns)*472+450),path.stem,fill='white')
        image.save(OUT/name)
    for lang in ('en','es'):
        sheet([OUT/f'loading-{lang}-{one}v{two}.png' for one in range(1,6) for two in range(1,6)],f'contact-teams-{lang}.png')
        sheet(sorted(OUT.glob(f'coop-{lang}-*.png')),f'contact-coop-{lang}.png',3)
        sheet([OUT/f'ffa-{lang}-{i}.png' for i in range(2,11)],f'contact-ffa-{lang}.png',3)
        sheet(sorted(OUT.glob(f'training*-{lang}-*.png'))+[OUT/f'exhibition-{lang}.png',OUT/f'credits-full-{lang}.png',OUT/f'credits-strip-{lang}.png'],f'contact-other-{lang}.png',3)
        sheet(sorted(OUT.glob(f'hud-{lang}-*.png')),f'contact-hud-{lang}.png',2)
        for capture in OUT.glob(f'hud-{lang}-*-21x9.png'):
            with Image.open(capture) as image:image.resize((2560,1080),Image.Resampling.BILINEAR).save(OUT/(capture.stem+'-presented.png'))
    print('PASS native GPU acceptance and EN/ES all-family contact sheets:',OUT)
if __name__=='__main__':main()
