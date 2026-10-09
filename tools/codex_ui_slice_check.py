"""Run the dedicated native GPU acceptance without ISO/game/window/PINE."""
import os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'power-scale-trial/native-ui-slice-capture'
def main():
    env=os.environ.copy();env['PS2X_NATIVE_UI_SLICE']='1';env['PS2X_NATIVE_UI_BENCH']='1'
    with (HERE/'power-scale-trial/codex-ui-slice-self-test.log').open('wb') as log:
        result=subprocess.run([str(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-native-ui-slice.exe'),
          '--native-ui-vulkan-self-test',str(HERE/'power-scale-trial/app-data/native-ui'),str(OUT)],
          env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if result.returncode:raise RuntimeError(f'Native GPU acceptance exit {result.returncode}')
    from PIL import Image
    for lang in ('en','es'):
        sheet=Image.new('RGB',(640*5,448*5))
        for one in range(1,6):
            for two in range(1,6):
                with Image.open(OUT/f'loading-{lang}-{one}v{two}.png') as image:sheet.paste(image,((two-1)*640,(one-1)*448))
        sheet.save(OUT/f'contact-sheet-{lang}.png')
    with Image.open(OUT/'aspect-en.png') as image:image.resize((2560,1080),Image.Resampling.BILINEAR).save(OUT/'aspect-en-presented.png')
    print('Native GPU acceptance and both all25 contact sheets PASS:',OUT)
if __name__=='__main__':main()
