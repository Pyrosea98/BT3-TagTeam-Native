"""Claude: reference mock of the proposed 'overhead HUD' on the user's own 21:9 screenshot (reference only, not shipped)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SRC = Path(r'C:\Users\JUAN\AppData\Local\Temp\claude\C--Users-JUAN-Downloads-Tag-Team-Mod-Installer-2\7f42cf6d-7c12-4e13-9929-fad92cc76793\images\9.webp')
FONT = HERE / 'font-candidates' / 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf'
im = Image.open(SRC).convert('RGBA')
W, H = im.size
# hide the original HUD bands to show the "native HUD off" case: darken/blur the top 175 px region
top = im.crop((0, 0, W, 175)).resize((W // 8, 22), Image.BILINEAR).resize((W, 175), Image.BILINEAR)
im.paste(top, (0, 0))
for box in ((20, 160, 500, 290), (1520, 160, 1995, 290)):
    reg = im.crop(box)
    reg = reg.resize((max(2, reg.width // 12), max(2, reg.height // 12)), Image.BILINEAR).resize(reg.size, Image.BILINEAR)
    im.paste(reg, box[:2])
d = ImageDraw.Draw(im, 'RGBA')


def f(sz):
    return ImageFont.truetype(str(FONT), sz)


def slant_bar(x, y, w, h, fill, back=(20, 24, 34, 200), k=None, frac=1.0):
    k = k if k is not None else h
    d.polygon([(x + k, y), (x + w, y), (x + w - k, y + h), (x, y + h)], fill=back)
    ww = int(w * frac)
    d.polygon([(x + k, y), (x + ww, y), (x + ww - k, y + h), (x, y + h)], fill=fill)
    d.line([(x + k, y), (x + w, y)], fill=(255, 255, 255, 90), width=1)


def detailed(cx, y, name, hp, ki, tag=None, accent=(90, 208, 255, 255)):
    w, h = 190, 56
    x = cx - w // 2
    # plate
    d.polygon([(x + 14, y), (x + w, y), (x + w - 14, y + h), (x, y + h)], fill=(18, 22, 32, 215))
    d.line([(x + 14, y), (x + w, y), (x + w - 14, y + h), (x, y + h), (x + 14, y)], fill=(190, 198, 215, 230), width=2)
    d.rectangle([x + 18, y + 7, x + 18 + 36, y + 7 + 36], fill=(5, 5, 8, 255), outline=accent)
    d.text((x + 62, y + 4), name, font=f(17), fill=(238, 234, 255, 255), stroke_width=2, stroke_fill=(20, 16, 40, 255))
    slant_bar(x + 62, y + 24, 112, 9, (60, 220, 70, 255), frac=hp)
    slant_bar(x + 62, y + 36, 112, 6, (60, 140, 255, 255), frac=ki)
    for i in range(6):
        d.polygon([(x + 62 + i * 14 + 3, y + 46), (x + 62 + i * 14 + 12, y + 46), (x + 62 + i * 14 + 9, y + 51), (x + 62 + i * 14, y + 51)],
                  fill=(240, 200, 60, 255) if i < 4 else (70, 70, 80, 200))
    if tag:
        d.text((x + 20, y + 40), tag, font=f(15), fill=(235, 230, 120, 255), stroke_width=2, stroke_fill=(30, 24, 10, 255))
    # pointer to the head
    d.polygon([(cx - 7, y + h), (cx + 7, y + h), (cx, y + h + 9)], fill=(190, 198, 215, 230))


def simple(cx, y, hp):
    w, h = 64, 7
    slant_bar(cx - w // 2, y, w, h, (60, 220, 70, 255) if hp > 0.3 else (230, 70, 60, 255), frac=hp)


detailed(795, 395, 'Goku (Super)', 0.92, 0.75, tag='1P')
detailed(1313, 262, 'Nappa', 0.62, 0.40, accent=(240, 162, 74, 255))
for cx, y, hp in ((165, 296, 0.85), (552, 372, 0.55), (1526, 344, 0.9), (1568, 326, 0.2), (1530, 395, 0.7)):
    simple(cx, y, hp)
d.text((28, 12), 'Native game HUD OFF (blurred here) | detailed mini-HUD over 1P and the target | simple bars over everyone else',
       font=f(26), fill=(255, 214, 90, 255), stroke_width=3, stroke_fill=(30, 20, 50, 255))
out = HERE / 'loading-mockups' / 'overhead-hud-mock.png'
im.convert('RGB').save(out)
print('saved', out)
