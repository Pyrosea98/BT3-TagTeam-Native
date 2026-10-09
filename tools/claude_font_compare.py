"""Claude: side-by-side of the game's own label style against open-licence candidate fonts (reference render only)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claude_hud_sheet_lib as lib

FD = HERE / 'font-candidates'
CANDS = [
    ('Kanit Black Italic', FD / 'ofl_kanit_Kanit-BlackItalic.ttf', None),
    ('Barlow Condensed ExtraBold Italic', FD / 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf', None),
    ('Exo 2 Black Italic', FD / 'ofl_exo2_Exo2-Italic[wght].ttf', b'Black Italic'),
]
S = 2
W, H = 1100, 560


def font(path, size, var):
    f = ImageFont.truetype(str(path), size)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            try:
                f.set_variation_by_axes([900])
            except Exception:
                pass
    return f


def gold_text(img, xy, s, f, outline=(60, 24, 90, 255)):
    # vertical gold-to-orange gradient fill with a dark purple outline (the game's title look)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox(xy, s, font=f, stroke_width=3)
    w, h = bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((4 - (bbox[0] - xy[0]), 4 - (bbox[1] - xy[1])), s, font=f, fill=255)
    grad = Image.new('RGBA', (w, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        gd.line([(0, y), (w, y)], fill=(255, int(236 - 90 * t), int(120 - 90 * t), 255))
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ol = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ol).text((4 - (bbox[0] - xy[0]), 4 - (bbox[1] - xy[1])), s, font=f, fill=outline, stroke_width=4, stroke_fill=outline)
    base.alpha_composite(ol)
    base.paste(grad, (0, 0), mask)
    img.alpha_composite(base, (bbox[0] - 4, bbox[1] - 4))


def body_text(img, xy, s, f):
    ImageDraw.Draw(img).text(xy, s, font=f, fill=(238, 234, 255, 255), stroke_width=2, stroke_fill=(20, 16, 40, 255))


im = Image.new('RGBA', (W, H), (20, 28, 50, 255))
d = ImageDraw.Draw(im)
label = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 14)
d.text((20, 10), 'Game (decoded from the disc)', font=label, fill=(200, 210, 230, 255))
for k, path in enumerate(([452, 2, 37, 2], [453, 0, 24])):
    try:
        spr = lib.sprite(path)
        if path == [453, 0, 24]:
            spr = spr.crop((130, 0, 380, 128))
        if path == [452, 2, 37, 2]:
            spr = spr.crop((0, 0, spr.width, spr.height))
        im.alpha_composite(spr, (20 + k * 330, 34))
    except Exception as e:
        d.text((20 + k * 330, 40), 'sprite %s unavailable' % (path,), font=label, fill=(255, 120, 120, 255))
y = 200
for name, path, var in CANDS:
    d.text((20, y), name, font=label, fill=(200, 210, 230, 255))
    ft = font(path, 40, var)
    fb = font(path, 22, var)
    gold_text(im, (20, y + 22), 'MOD SETTINGS  Fusion', ft)
    body_text(im, (560, y + 26), 'Show fusion timer   Goku Blue Perfecto', fb)
    body_text(im, (560, y + 56), 'Contrasena  Quitar todos  Ñ é ü ¿?', fb)
    y += 120
im.convert('RGB').save(HERE / 'loading-mockups' / 'font-candidates.png')
print('saved')
