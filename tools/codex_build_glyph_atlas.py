"""Build portable indexed UI font assets. Python is used only at build time."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
W, H, SCALE = 512, 256, 4
VARIANTS = {'gold': ((255, 239, 145), (235, 128, 26)),
            'white': ((255, 255, 255), (200, 208, 241)),
            'grey': ((204, 210, 224), (120, 128, 146)),
            'cyan': ((190, 255, 255), (38, 156, 211)),
            'yellow': ((255, 255, 170), (247, 198, 20)),
            'red': ((255, 171, 148), (214, 39, 28)),
            'green': ((204, 255, 157), (53, 192, 48))}
PAIRS = ['AV', 'AW', 'AY', 'AT', 'FA', 'LT', 'LY', 'PA', 'TA', 'TO', 'VA', 'WA', 'YA',
         'Yo', 'To', 'Ta', 'Te', 'Tr', 'Tu', 'Ty', 'Va', 'Vo', 'Wa', 'Wo', 'Ya', 'Ye',
         'Fo', 'Fi', 'Fl', 'ry', 'rt', 'rv', 'ra', 'ro', 'we', 'wo', 'yo', 'ff', 'fi', 'fl']


def font_codepoints(path):
    """Read Unicode cmap formats 4/12 to reject missing source glyphs."""
    data = path.read_bytes()
    tables = {}
    for i in range(struct.unpack_from('>H', data, 4)[0]):
        tag, _, off, size = struct.unpack_from('>4sIII', data, 12 + i * 16)
        tables[tag] = (off, size)
    cmap, _ = tables[b'cmap']
    result = set()
    for i in range(struct.unpack_from('>H', data, cmap + 2)[0]):
        platform, encoding, rel = struct.unpack_from('>HHI', data, cmap + 4 + i * 8)
        if platform != 0 and (platform, encoding) not in ((3, 1), (3, 10)):
            continue
        off = cmap + rel
        fmt = struct.unpack_from('>H', data, off)[0]
        if fmt == 12:
            for j in range(struct.unpack_from('>I', data, off + 12)[0]):
                start, end, glyph = struct.unpack_from('>III', data, off + 16 + j * 12)
                result.update(range(start + (glyph == 0), end + 1))
        elif fmt == 4:
            n = struct.unpack_from('>H', data, off + 6)[0] // 2
            ends = off + 14
            starts = ends + n * 2 + 2
            deltas = starts + n * 2
            ranges = deltas + n * 2
            for j in range(n):
                end = struct.unpack_from('>H', data, ends + j * 2)[0]
                start = struct.unpack_from('>H', data, starts + j * 2)[0]
                delta = struct.unpack_from('>h', data, deltas + j * 2)[0]
                rel = struct.unpack_from('>H', data, ranges + j * 2)[0]
                for c in range(start, min(end, 0xfffe) + 1):
                    glyph = (c + delta) & 0xffff if not rel else struct.unpack_from('>H', data, ranges + j * 2 + rel + 2 * (c - start))[0]
                    if glyph:
                        result.add(c)
    return result


def palettes(style):
    result = {}
    for name, (top, bottom) in VARIANTS.items():
        pal = [(0, 0, 0, 0)] * 256
        # Straight RGBA host palettes. Native GS upload must convert alpha once.
        for c in range(1, 16):
            pal[c] = (12, 15, 31, c * 17)
            pal[16 + c] = (42, 33, 68, c * 6)  # subdued outer glow
            pal[32 + c] = (*top, c * 17)
        for g in range(13):
            rgb = tuple(round(a + (b - a) * g / 12) for a, b in zip(top, bottom))
            for c in range(16):
                pal[48 + g * 16 + c] = (*rgb, c * 17)
        result[name] = pal
    return result


def raster(font, char, style):
    stroke = 2 if style == 'title' else (1 if style == 'body' else 1.5)
    pad = 5 if style == 'title' else 3
    fallback = char == '\ufffd'
    left, top, right, bottom = font.getbbox('?' if fallback else char, anchor='ls')
    left, top = left // SCALE - pad, top // SCALE - pad
    right, bottom = (right + SCALE - 1) // SCALE + pad, (bottom + SCALE - 1) // SCALE + pad
    w, h = max(1, right - left), max(1, bottom - top)
    mask = Image.new('L', (w * SCALE, h * SCALE))
    painter = ImageDraw.Draw(mask)
    painter.text((-left * SCALE, -top * SCALE), '?' if fallback else char, font=font, anchor='ls', fill=255)
    if fallback:
        painter.rectangle((pad * SCALE, pad * SCALE, (w - pad) * SCALE - 1, (h - pad) * SCALE - 1),
                          outline=255, width=SCALE)
    expanded = mask.filter(ImageFilter.MaxFilter(int(stroke * SCALE) * 2 + 1))
    if style == 'body':
        # Flood from the padded exterior; enclosed counters are excluded from
        # the outline. The original fill mask is never eroded or overwritten.
        exterior = mask.point(lambda p: 255 if p else 0)
        ImageDraw.floodfill(exterior, (0, 0), 128)
        exterior = exterior.point(lambda p: 255 if p == 128 else 0)
        expanded = ImageChops.multiply(expanded, exterior)
    glow = expanded.filter(ImageFilter.GaussianBlur(SCALE)) if style == 'title' else Image.new('L', mask.size)
    mask, expanded, glow = [im.resize((w, h), Image.Resampling.LANCZOS) for im in (mask, expanded, glow)]
    plane = bytearray(w * h)
    for y in range(h):
        gradient = min(12, max(0, round((y - pad) * 12 / max(1, h - 2 * pad - 1))))
        for x in range(w):
            fill, outline, halo = (im.getpixel((x, y)) for im in (mask, expanded, glow))
            # One role per pixel; foreground dominates. Fixed role ranges keep
            # recolouring independent of outline/glow. 4-bit coverage quantized.
            if fill >= 9:
                coverage = max(1, round(fill / 17))
                plane[y * w + x] = 32 + coverage if style == 'title' and gradient == 0 else 48 + gradient * 16 + coverage
            elif outline >= 9:
                plane[y * w + x] = max(1, round(outline / 17))
            elif halo >= 9:
                plane[y * w + x] = 16 + max(1, round(halo / 17))
    return w, h, left, top, bytes(plane)


def build(output, style, size, path, stem=None):
    font = ImageFont.truetype(str(path), size * SCALE)
    supported = font_codepoints(path)
    charset = list(range(32, 127)) + list(range(160, 256)) + [0x2022, 0x2026]
    if style == 'numeric':
        charset = sorted(set(map(ord, '0123456789:.%+-x/ ?')))
    charset += [0xfffd]
    missing = [c for c in charset if c not in supported and c != 0xfffd]
    if missing:
        raise ValueError(f'{path.name}: missing {missing}')
    glyphs, planes = [], [bytearray(W * H)]
    x = y = rowheight = 0
    digit_advance = max(font.getlength(c) / SCALE for c in '0123456789')
    for c in charset:
        w, h, bx, by, pixels = raster(font, chr(c), style)
        if x + w > W:
            x, y, rowheight = 0, y + rowheight + 1, 0
        if y + h > H:
            planes.append(bytearray(W * H)); x = y = rowheight = 0
        if w > W or h > H:
            raise ValueError('Glyph exceeds page')
        page = len(planes) - 1
        for yy in range(h):
            planes[page][(y + yy) * W + x:(y + yy) * W + x + w] = pixels[yy * w:(yy + 1) * w]
        advance = digit_advance if style == 'numeric' and chr(c).isdigit() else font.getlength('?' if c == 0xfffd else chr(c)) / SCALE
        if style == 'body':
            advance += 1  # baked tracking also consumed by the native reader
        glyphs.append((c, page, x, y, w, h, bx, by, round(advance * 64)))
        x += w + 1; rowheight = max(rowheight, h)
    kern = []
    if style != 'numeric':
        for a, b in PAIRS:
            value = round((font.getlength(a + b) - font.getlength(a) - font.getlength(b)) / SCALE * 64)
            if value:
                kern.append((ord(a), ord(b), value))
    asc, desc = font.getmetrics()
    stem = stem or f'{style}-{size}'
    header = struct.pack('<4sHHHHiiII', b'GATL', 1, len(planes), W, H,
                         round((asc + desc) / SCALE * 64), round(asc / SCALE * 64), len(glyphs), len(kern))
    metrics = header + b''.join(struct.pack('<IHHHHHhhi', *g) for g in glyphs) + b''.join(struct.pack('<IIi', *k) for k in kern)
    (output / (stem + '.gatl')).write_bytes(metrics)
    variants = palettes(style)
    for name, pal in variants.items():
        (output / f'{stem}-{name}.rgba').write_bytes(bytes(v for colour in pal for v in colour))
    for page, plane in enumerate(planes):
        (output / f'{stem}-{page}.indices').write_bytes(plane)
        im = Image.new('RGBA', (W, H)); im.putdata([variants['gold' if style == 'title' else 'white'][i] for i in plane])
        im.save(output / f'{stem}-{page}.png')
    return {'style': style, 'size': size, 'pages': len(planes), 'glyphs': len(glyphs),
            'font': path.name, 'font_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'metrics_sha256': hashlib.sha256(metrics).hexdigest(),
            'tracking_px': 1 if style == 'body' else 0,
            'outline': 'external-only 1px; counters preserved' if style == 'body' else 'original'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'ui-assets/glyph-atlas-v2')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    fonts = HERE / 'font-candidates'
    result = []
    for style, sizes, font in [('title', (26, 18), 'ofl_kanit_Kanit-BlackItalic.ttf'),
                               ('body', (16, 12), 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf'),
                               ('numeric', (14, 11), 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf')]:
        for size in sizes:
            result.append(build(args.output, style, size, fonts / font))
    for licence in ('ofl_kanit_OFL.txt', 'ofl_barlowcondensed_OFL.txt'):
        shutil.copyfile(fonts / licence, args.output / licence)
    result.append(build(args.output,'body',12,fonts/'LiberationSans-Regular.ttf','body-upright-12'))
    shutil.copyfile(fonts/'liberation-OFL.txt',args.output/'liberation-OFL.txt')
    manifest = {'version': 1, 'art_revision': 2, 'palette_encoding': 'straight RGBA8, host alpha 0..255',
                'index_encoding': 'linear row-major; GS uploader must swizzle',
                'roles': {'transparent': [0, 0], 'outline': [1, 15], 'glow': [17, 31],
                          'highlight': [33, 47], 'fill': [48, 255]},
                'symbols_pending': 'direction arrows and controller button sprites are separate draw-layer assets',
                'styles': result}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
