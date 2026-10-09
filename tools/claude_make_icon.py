"""Claude: original app icon for BT3 Tag Team (own drawing, no game art): two overlapping orange balls = "tag team",
on a dark navy rounded square with a gold edge. Writes installer/assets/BT3TagTeam.ico (multi-size) and a preview PNG."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / 'installer' / 'assets'
OUT.mkdir(parents=True, exist_ok=True)
S = 1024  # master canvas


def star(d, cx, cy, r, fill, points=5):
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + i * math.pi / points
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def ball(im, cx, cy, r, stars):
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=(40, 16, 6, 255))  # dark rim
    # radial orange gradient
    for i in range(r, 0, -3):
        t = i / r
        u = 1 - t
        col = (int(215 + 40 * u), int(92 + 118 * u), int(14 + 70 * u * u), 255)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)
    # highlight
    hl = Image.new('RGBA', im.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r * 0.60, cy - r * 0.74, cx - r * 0.10, cy - r * 0.34], fill=(255, 240, 190, 120))
    hl = hl.filter(ImageFilter.GaussianBlur(r * 0.06))
    layer.alpha_composite(hl)
    d = ImageDraw.Draw(layer)
    n = len(stars)
    for (sx, sy) in stars:
        star(d, cx + sx * r, cy + sy * r, r * 0.20, (200, 20, 20, 255))
    im.alpha_composite(layer)


def make():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # rounded navy tile with vertical gradient
    tile = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    for y in range(S):
        t = y / S
        td.line([(0, y), (S, y)], fill=(int(14 + 12 * t), int(22 + 40 * t), int(48 + 42 * t), 255))
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([24, 24, S - 24, S - 24], radius=210, fill=255)
    im.paste(tile, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 24, S - 24, S - 24], radius=210, outline=(240, 190, 70, 255), width=22)
    d.rounded_rectangle([58, 58, S - 58, S - 58], radius=180, outline=(255, 255, 255, 40), width=6)
    # two overlapping balls (back-left smaller, front-right larger) = tag team
    ball(im, 395, 560, 270, [(-0.42, 0.02), (-0.20, 0.42)])           # 2 stars
    ball(im, 640, 470, 300, [(-0.05, -0.28), (-0.38, 0.12), (0.30, 0.05), (-0.18, 0.46), (0.22, 0.48)])  # 5 stars
    return im


master = make()
master.save(OUT / 'BT3TagTeam-icon-1024.png')
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
master.resize((256, 256), Image.LANCZOS).save(OUT / 'BT3TagTeam.ico', sizes=sizes)
# contact preview
sheet = Image.new('RGBA', (780, 300), (30, 30, 36, 255))
x = 20
for s in (256, 128, 64, 48, 32, 24, 16):
    sheet.alpha_composite(master.resize((s, s), Image.LANCZOS), (x, 20))
    x += s + 14
sheet.convert('RGB').save(OUT / 'BT3TagTeam-icon-preview.png')
print('wrote', OUT / 'BT3TagTeam.ico')
