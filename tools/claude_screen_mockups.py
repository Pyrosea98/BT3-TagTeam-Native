"""Reference renders of the mod's screens in the unified look, built from sprites decoded from the user's own disc.
Text is a stand-in (Arial Black, gold fill, dark outline) for the game-style glyph atlas Codex will bake. Not shipped."""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
TRIAL = HERE / 'power-scale-trial'
sys.path.insert(0, str(HERE))
import claude_hud_sheet_lib as lib
import extract_loading_assets as ex
pm = json.load(open(TRIAL / 'portrait-slot-map.json'))['map']
S = 2
W, H = 640 * S, 448 * S
OUT = HERE / 'loading-mockups'
FB = 'C:/Windows/Fonts/ariblk.ttf'
FI = 'C:/Windows/Fonts/arialbi.ttf'
GOLD = (255, 214, 90, 255)
CYAN = (90, 208, 255, 255)
WHITE = (240, 236, 255, 255)
DARK = (20, 16, 40, 255)


def font(sz, path=FB):
    return ImageFont.truetype(path, sz * S)


def portrait(slot):
    j = pm[str(slot)]['iso_index']
    return Image.frombytes('RGBA', (64, 64), ex.portrait_rgba(lib.PORTRAITS[j]))


def background():
    bg = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(14 + 10 * t), int(20 + 34 * t), int(40 + 30 * t), 255))
    band = lib.sprite([450, 0, 9])
    band = band.resize((W, int(band.height * W / band.width)), Image.LANCZOS)
    band.putalpha(band.getchannel('A').point(lambda a: int(a * 0.30)))
    bg.alpha_composite(band, (0, int(H * 0.30)))
    return bg


def text(img, xy, s, sz, fill=GOLD, stroke=(60, 24, 90, 255), anchor='la', path=FB, sw=3):
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font(sz, path), fill=fill, stroke_width=max(1, sw * S // 2), stroke_fill=stroke, anchor=anchor)


def plate(img, pts, fill=(24, 28, 40, 235), edge=(190, 198, 215, 255), w=2):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=edge, width=w * S)
    img.alpha_composite(lay)


def sl(x, y, w, h, k=14):
    return [(x + k * S, y), (x + w, y), (x + w - k * S, y + h), (x, y + h)]


def paste(img, spr, xy, scale=1.0):
    s = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.LANCZOS)
    img.alpha_composite(s, xy)


def helpbar(im, s):
    plate(im, sl(60 * S, 388 * S, 520 * S, 34 * S, 14))
    text(im, (80 * S, 398 * S), s, 11, fill=(210, 216, 232, 255), stroke=(10, 10, 20, 255), path=FI, sw=1)


def settings():
    im = background()
    text(im, (W // 2, 40 * S), 'MOD SETTINGS', 26, anchor='ma')
    fw = 500 * S
    fx = (W - fw) // 2
    fy = 78 * S
    rows = [('Fusion duration', 'slider', 0.55, '40 s'), ('Show fusion timer', 'toggle', True, 'ON'),
            ('Ultimate camera', 'toggle', False, 'OFF'), ('Kill feed', 'toggle', True, 'ON'),
            ('Lock-on button', 'choice', None, 'L3'), ('CPU transformations', 'slider', 0.30, 'Rare')]
    ry = fy + 30 * S
    rh = 34 * S
    track = lib.sprite([453, 0, 8])
    knob = lib.sprite([453, 0, 11])
    for i, (label, kind, val, shown) in enumerate(rows):
        y = ry + i * rh
        if i == 1:
            plate(im, sl(fx, y, fw, rh - 6 * S, 14), fill=(70, 40, 120, 235), edge=GOLD)
        else:
            plate(im, sl(fx, y, fw, rh - 6 * S, 14), fill=(24, 28, 40, 220), edge=(120, 128, 148, 255), w=1)
        text(im, (fx + 30 * S, y + 4 * S), label, 13, fill=WHITE, stroke=DARK, path=FI, sw=2)
        rx = fx + fw - 70 * S
        if kind == 'slider':
            tw = 130 * S
            tx = rx - tw - 10 * S
            ty = y + 10 * S
            d = ImageDraw.Draw(im)
            d.polygon([(tx + 5 * S, ty), (tx + tw, ty), (tx + tw - 5 * S, ty + 9 * S), (tx, ty + 9 * S)], fill=(43, 48, 59, 255))
            e = int(tw * val)
            d.polygon([(tx + 5 * S, ty), (tx + e, ty), (tx + e - 5 * S, ty + 9 * S), (tx, ty + 9 * S)], fill=(240, 162, 74, 255))
            k = knob.resize((14 * S, 14 * S), Image.LANCZOS)
            im.alpha_composite(k, (tx + e - 7 * S, ty - 2 * S))
            text(im, (rx + 6 * S, y + 4 * S), shown, 12, fill=(200, 230, 255, 255), stroke=DARK, path=FI, sw=2)
        else:
            col = GOLD if (kind == 'toggle' and val) else ((150, 156, 170, 255) if kind == 'toggle' else CYAN)
            plate(im, sl(rx - 40 * S, y + 3 * S, 64 * S, 22 * S, 8), fill=(30, 34, 48, 240), edge=col)
            text(im, (rx - 8 * S, y + 14 * S), shown, 11, fill=col, stroke=(10, 10, 20, 255), anchor='mm', sw=2)
    helpbar(im, 'Up/Down select    Left/Right change    X save    O back')
    return im


def digits(im, nums, n, x, y, scale):
    for ch in str(n):
        k = int(ch)
        r, c = divmod(k, 4)
        cell = nums.crop((c * 64, r * 64, c * 64 + 64, r * 64 + 64))
        paste(im, cell, (x, y), scale)
        x += int(46 * scale * S / 1)
    return x


def training():
    im = background()
    nums = lib.sprite([450, 0, 13])
    text(im, (W // 2, 26 * S), 'MODDED TRAINING', 20, anchor='ma')
    plate(im, sl(24 * S, 70 * S, 250 * S, 150 * S, 16))
    text(im, (46 * S, 80 * S), 'PRACTICE', 12, fill=GOLD, stroke=(40, 20, 10, 255), sw=2)
    items = [('Refill HP', 'ON', GOLD), ('Idle CPU', 'ON', GOLD), ('Show hit counter', 'ON', GOLD), ('Reset position', 'O', CYAN)]
    for i, (a, b, c) in enumerate(items):
        y = 104 * S + i * 26 * S
        text(im, (46 * S, y), a, 12, fill=WHITE, stroke=DARK, path=FI, sw=2)
        plate(im, sl(206 * S, y - 2 * S, 56 * S, 20 * S, 7), fill=(30, 34, 48, 240), edge=c)
        text(im, (238 * S, y + 8 * S), b, 10, fill=c, stroke=(10, 10, 20, 255), anchor='mm', sw=2)
    plate(im, sl(330 * S, 70 * S, 286 * S, 70 * S, 16))
    text(im, (352 * S, 78 * S), 'HITS', 11, fill=GOLD, stroke=(40, 20, 10, 255), sw=2)
    digits(im, nums, 12, 500 * S, 74 * S, 0.9 * 1)
    plate(im, sl(330 * S, 152 * S, 286 * S, 70 * S, 16))
    text(im, (352 * S, 160 * S), 'DAMAGE', 11, fill=GOLD, stroke=(40, 20, 10, 255), sw=2)
    digits(im, nums, 3480, 440 * S, 158 * S, 0.8)
    for i, (slot, name, fill, pct) in enumerate(((0, 'GOKU', (95, 199, 165), 0.85), (29, 'VEGETA', (240, 162, 74), 0.55))):
        x = (40 if i == 0 else 340) * S
        plate(im, sl(x, 300 * S, 260 * S, 60 * S, 14))
        p = portrait(slot).resize((46 * S, 46 * S), Image.LANCZOS)
        im.alpha_composite(p, (x + 22 * S, 307 * S))
        text(im, (x + 78 * S, 306 * S), name, 11, fill=WHITE, stroke=DARK, sw=2)
        d = ImageDraw.Draw(im)
        bx, by, bw = x + 78 * S, 326 * S, 164 * S
        d.polygon([(bx + 6 * S, by), (bx + bw, by), (bx + bw - 6 * S, by + 10 * S), (bx, by + 10 * S)], fill=(43, 48, 59, 255))
        e = int(bw * pct)
        d.polygon([(bx + 6 * S, by), (bx + e, by), (bx + e - 6 * S, by + 10 * S), (bx, by + 10 * S)], fill=fill + (255,))
    helpbar(im, 'Select: reset    Start: pause menu')
    return im


def standings():
    im = background()
    nums = lib.sprite([450, 0, 13])
    ban = lib.sprite([455, 31])
    b = ban.resize((int(ban.width * 0.8 * S), int(ban.height * 0.8 * S)), Image.LANCZOS)
    im.alpha_composite(b.crop((0, b.height // 2, b.width, b.height)), ((W - b.width) // 2, 6 * S))
    entries = [(0, 'GOKU', '5 KOs'), (29, 'VEGETA', '3 KOs'), (22, 'PICCOLO', '1 KO'), (13, 'GOHAN', '0 KOs')]
    for i, (slot, name, kos) in enumerate(entries):
        y = 118 * S + i * 66 * S
        gold = i == 0
        plate(im, sl(70 * S, y, 500 * S, 58 * S, 16), fill=(70, 40, 120, 235) if gold else (24, 28, 40, 235),
              edge=GOLD if gold else (190, 198, 215, 255))
        r, c = divmod(i + 1, 4)
        cell = nums.crop((c * 64, r * 64, c * 64 + 64, r * 64 + 64))
        paste(im, cell, (90 * S, y - 2 * S), 0.9 * S / 1)
        p = portrait(slot).resize((50 * S, 50 * S), Image.LANCZOS)
        im.alpha_composite(p, (170 * S, y + 4 * S))
        text(im, (238 * S, y + 10 * S), name, 16, fill=(255, 236, 170, 255) if gold else (230, 234, 246, 255), stroke=(30, 16, 50, 255), sw=3)
        text(im, (540 * S, y + 30 * S), kos, 12, fill=CYAN, stroke=(10, 10, 20, 255), anchor='rm', path=FI, sw=2)
    helpbar(im, 'X rematch    O character select')
    return im


if __name__ == '__main__':
    for name, fn in (('v3-settings', settings), ('v3-training', training), ('v3-standings', standings)):
        fn().convert('RGB').save(OUT / (name + '.png'))
        print('saved', name)
