"""Claude: concept mock of a compact frame whose BORDER is the life and ki gauge (hexagon / ring), translucent, on the user's own screenshot."""
import math
import sys
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'power-scale-trial/controller/game/tools'))
import claude_hud_sheet_lib as lib
import extract_loading_assets as ex
pm = json.load(open(HERE / 'power-scale-trial/portrait-slot-map.json'))['map']
SRC = Path(r'C:\Users\JUAN\AppData\Local\Temp\claude\C--Users-JUAN-Downloads-Tag-Team-Mod-Installer-2\7f42cf6d-7c12-4e13-9929-fad92cc76793\images\9.webp')
FONT = HERE / 'font-candidates' / 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf'
SS = 3  # supersample


def portrait(slot, size):
    j = pm[str(slot)]['iso_index']
    p = Image.frombytes('RGBA', (64, 64), ex.portrait_rgba(lib.PORTRAITS[j]))
    return p.resize((size, size), Image.LANCZOS)


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (180, 240, 300, 0, 60, 120)]


def along(points, frac):
    """points of a polyline up to the fraction of its total length"""
    segs = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(segs)
    target = total * max(0.0, min(1.0, frac))
    out = [points[0]]
    acc = 0.0
    for i, s in enumerate(segs):
        if acc + s >= target:
            t = (target - acc) / s if s else 0
            out.append((points[i][0] + (points[i + 1][0] - points[i][0]) * t, points[i][1] + (points[i + 1][1] - points[i][1]) * t))
            return out
        acc += s
        out.append(points[i + 1])
    return out


def line(d, pts, color, width):
    if len(pts) > 1:
        d.line(pts, fill=color, width=width, joint='curve')
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2], fill=color)


def variant_a(size, slot, hp, ki, name=None, alpha=0.6):
    """flat-top hexagon: top three edges = life (green->red), bottom three edges = ki (blue)"""
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = W / 2
    r = W * 0.46
    pts = hexagon(cx, cy, r)
    d.polygon(pts, fill=(14, 18, 28, int(255 * 0.45 * alpha / 0.6)))
    # portrait masked to a slightly smaller hexagon
    pr = portrait(slot, int(W * 0.62))
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).polygon(hexagon(cx, cy, r * 0.80), fill=255)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    layer.paste(pr, (int(cx - pr.width / 2), int(cy - pr.height / 2)))
    layer.putalpha(Image.composite(layer.getchannel('A'), Image.new('L', (W, W), 0), mask))
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    track = (230, 236, 250, int(150 * alpha / 0.6))
    top = [pts[0], pts[1], pts[2], pts[3]]
    bottom = [pts[0], pts[5], pts[4], pts[3]]
    bw = max(2, int(W * 0.055))
    line(d, top, (20, 24, 34, 170), bw)
    line(d, bottom, (20, 24, 34, 170), bw)
    hpcol = (70, 225, 90, 255) if hp > 0.3 else (235, 70, 60, 255)
    line(d, along(top, hp), hpcol, bw)
    line(d, along(bottom, ki), (70, 150, 255, 255), bw)
    d.line(pts + [pts[0]], fill=track, width=max(1, SS))
    return im


def variant_b(size, slot, hp, ki, alpha=0.6):
    """double hexagon ring: outer = life, inner = ki"""
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = W / 2
    ro, ri = W * 0.47, W * 0.37
    d.polygon(hexagon(cx, cy, ro), fill=(14, 18, 28, int(255 * 0.40 * alpha / 0.6)))
    pr = portrait(slot, int(W * 0.50))
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).polygon(hexagon(cx, cy, ri * 0.86), fill=255)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    layer.paste(pr, (int(cx - pr.width / 2), int(cy - pr.height / 2)))
    layer.putalpha(Image.composite(layer.getchannel('A'), Image.new('L', (W, W), 0), mask))
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    bw = max(2, int(W * 0.05))
    po = hexagon(cx, cy, ro)
    pi = hexagon(cx, cy, ri)
    for pts, frac, col in ((po, hp, (70, 225, 90, 255) if hp > 0.3 else (235, 70, 60, 255)), (pi, ki, (70, 150, 255, 255))):
        loop = pts[3:] + pts[:3]
        loop = loop + [loop[0]]
        line(d, loop, (20, 24, 34, 170), bw)
        line(d, along(loop, frac), col, bw)
    return im


def variant_c(size, slot, hp, ki, alpha=0.6):
    """round: outer arc = life (270 deg), inner arc = ki"""
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = W / 2
    ro, ri = W * 0.46, W * 0.36
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=(14, 18, 28, int(255 * 0.40 * alpha / 0.6)))
    pr = portrait(slot, int(W * 0.58))
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).ellipse([cx - ri * 0.9, cy - ri * 0.9, cx + ri * 0.9, cy + ri * 0.9], fill=255)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    layer.paste(pr, (int(cx - pr.width / 2), int(cy - pr.height / 2)))
    layer.putalpha(Image.composite(layer.getchannel('A'), Image.new('L', (W, W), 0), mask))
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    bw = max(2, int(W * 0.05))
    for rad, frac, col in ((ro - bw / 2, hp, (70, 225, 90, 255) if hp > 0.3 else (235, 70, 60, 255)), (ri - bw / 2, ki, (70, 150, 255, 255))):
        box = [cx - rad, cy - rad, cx + rad, cy + rad]
        d.arc(box, 135, 135 + 270, fill=(20, 24, 34, 170), width=bw)
        d.arc(box, 135, 135 + 270 * max(0.01, frac), fill=col, width=bw)
    return im


def shrink(im, size):
    return im.resize((size, size), Image.LANCZOS)


def label(img, xy, text, size=18):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FONT), size)
    d.text(xy, text, font=f, fill=(255, 214, 90, 255), stroke_width=2, stroke_fill=(30, 20, 50, 255))


base = Image.open(SRC).convert('RGBA')
W, H = base.size
canvas = Image.new('RGBA', (W, 534 + 190), (14, 20, 34, 255))
# background strip: stretch a piece of the game screenshot for the sheet
canvas.paste(base, (0, 0))
canvas.paste(base.crop((0, 300, W, 534)).resize((W, 190), Image.LANCZOS), (0, 534))
overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
# sheet row (large)
specs = [(variant_a, 'A: hexagon, border = life (top) + ki (bottom)'), (variant_b, 'B: double hexagon ring, outer life / inner ki'), (variant_c, 'C: round ring, outer life / inner ki')]
for i, (fn, name) in enumerate(specs):
    x = 90 + i * 640
    big = fn(150, 0, 0.72, 0.55)
    big = shrink(big, 150)
    overlay.alpha_composite(big, (x, 548))
    label(overlay, (x + 160, 590), name, 22)
# in-situ small ones (real size ~46 px): own fighter bottom centre and the target
for fn, (x, y) in ((variant_a, (772, 410)),):
    small = shrink(fn(46, 0, 0.72, 0.55), 46)
    overlay.alpha_composite(small, (x, y))
tgt = shrink(variant_a(40, 80, 0.55, 0.35), 40)
overlay.alpha_composite(tgt, (1292, 280))
for cx, y, hp in ((165, 296, 0.85), (552, 372, 0.55), (1526, 344, 0.9)):
    d = ImageDraw.Draw(overlay, 'RGBA')
    d.polygon([(cx - 28, y), (cx + 28, y), (cx + 25, y + 5), (cx - 31, y + 5)], fill=(20, 24, 34, 150))
    d.polygon([(cx - 28, y), (cx - 28 + 56 * hp, y), (cx - 31 + 56 * hp, y + 5), (cx - 31, y + 5)], fill=(60, 220, 70, 230))
canvas.alpha_composite(overlay)
d = ImageDraw.Draw(canvas)
label(canvas, (20, 8), 'In the fight: variant A at about 46 px (you) and 40 px (target), thin bars over the others', 24)
out = HERE / 'loading-mockups' / 'hex-hud-mock.png'
canvas.convert('RGB').save(out)
print('saved', out)
