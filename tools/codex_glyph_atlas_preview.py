"""Render using the generated indices/palettes/metrics, not font rasterization."""
import struct
import json
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
ROOT = HERE / 'ui-assets/glyph-atlas-v2'


def render(canvas, stem, variant, text, x, baseline):
    data = (ROOT / (stem + '.gatl')).read_bytes()
    _, _, pages, w, h, _, _, ng, nk = struct.unpack_from('<4sHHHHiiII', data)
    glyphs = {g[0]: g for g in [struct.unpack_from('<IHHHHHhhi', data, 28 + i * 22) for i in range(ng)]}
    kern = {(a, b): value for a, b, value in [struct.unpack_from('<IIi', data, 28 + ng * 22 + i * 12) for i in range(nk)]}
    pal = (ROOT / f'{stem}-{variant}.rgba').read_bytes()
    colours = [tuple(pal[i:i + 4]) for i in range(0, 1024, 4)]
    atlases = []
    for page in range(pages):
        image = Image.new('RGBA', (w, h))
        image.putdata([colours[i] for i in (ROOT / f'{stem}-{page}.indices').read_bytes()])
        atlases.append(image)
    pen = x * 64; previous = 0
    for char in text:
        c, page, u, v, gw, gh, bx, by, advance = glyphs.get(ord(char), glyphs[ord('?')])
        pen += kern.get((previous, c), 0)
        canvas.alpha_composite(atlases[page].crop((u, v, u + gw, v + gh)), (round(pen / 64) + bx, baseline + by))
        pen += advance; previous = c


catalog = json.loads((HERE / 'ui-assets/ui_strings.json').read_text(encoding='utf-8'))['strings']
def preview(locale):
    text = lambda key: catalog[key][locale]
    canvas = Image.new('RGBA', (640, 448), (18, 23, 32, 255))
    for y, stem, variant, label in [
        (42, 'title-26', 'gold', text('ModdedModes')),
        (78, 'title-18', 'gold', text('PreparingMatch')),
        (118, 'body-16', 'white', text('Resolution') + ' • ' + text('AspectRatio')),
        (147, 'body-12', 'white', text('RematchQuestion') + ' • ' + text('Yes') + ' • ' + text('Fullscreen')),
        (182, 'numeric-14', 'yellow', '0123456789 : 25.0%'),
        (211, 'numeric-11', 'cyan', '0123456789 : 25.0%'),
    ]:
        render(canvas, stem, variant, label, 25, y)
    for y, variant in enumerate(('gold', 'white', 'grey', 'cyan', 'yellow', 'red', 'green')):
        render(canvas, 'body-16', variant, text('Fusion') + ' • ' + text('TeamOne') + ' • ' + text('Ready'), 25, 249 + y * 28)
    path = ROOT / f'preview-{locale}.png'
    canvas.convert('RGB').save(path)
    return canvas
english, spanish = preview('en'), preview('es')
combined = Image.new('RGBA', (1280, 480), '#121720')
render(combined, 'body-12', 'white', 'English', 25, 20)
render(combined, 'body-12', 'white', 'Español', 665, 20)
combined.paste(english, (0, 32)); combined.paste(spanish, (640, 32))
combined.save(ROOT / 'preview-locales.png')
combined.resize((2560, 960), Image.Resampling.NEAREST).save(ROOT / 'preview-locales-2x.png')

def nine_slice(source, width, height, left=20, right=12, top=4, bottom=4):
    """Keep source caps at 1x; stretch only flat middle/edge strips."""
    result = Image.new('RGBA', (width, height))
    sx = (0, left, source.width-right, source.width)
    sy = (0, top, source.height-bottom, source.height)
    dx = (0, left, width-right, width)
    dy = (0, top, height-bottom, height)
    for row in range(3):
        for col in range(3):
            patch = source.crop((sx[col], sy[row], sx[col+1], sy[row+1]))
            patch = patch.resize((dx[col+1]-dx[col], dy[row+1]-dy[row]), Image.Resampling.NEAREST)
            result.alpha_composite(patch, (dx[col], dy[row]))
    return result

# Dark lobe from the actual HUD plate, excluding the raised/ribbed right half.
plate_path = HERE / 'power-scale-trial/hud-entry5-extracted/plate.png'
original_plate = Image.open(plate_path).convert('RGBA')
flat_lobe = original_plate.crop((0, 16, 78, 36))
row_plate = nine_slice(flat_lobe, 575, 48)
help_plate = nine_slice(flat_lobe, 575, 34)
def clean_right_cap(image):
    # Replace the contaminated source cap with a plain matching slant, and
    # give quiet rows one readable top edge. All work remains at logical1x.
    draw = ImageDraw.Draw(image)
    w, h = image.size
    draw.rectangle((w-20, 0, w-1, h-1), fill=(0, 0, 0, 0))
    draw.polygon([(w-21, 0), (w-1, 0), (w-13, h-1), (w-21, h-1)], fill=(9, 12, 17, 255))
    draw.line((20, 0, w-2, 0), fill=(95, 107, 123, 255), width=1)
    draw.line((w-2, 0, w-13, h-1), fill=(95, 107, 123, 255), width=1)
clean_right_cap(row_plate)
clean_right_cap(help_plate)
chip = Image.new('RGBA', (172, 36))
painter = ImageDraw.Draw(chip)
painter.polygon([(10, 0), (171, 0), (161, 35), (0, 35)], fill=(15, 20, 30, 255), outline=(183, 194, 208, 255), width=1)
for name, image in (('row-plate-9slice', row_plate), ('help-plate-9slice', help_plate), ('value-chip', chip)):
    image.save(ROOT / f'{name}.png')
for locale in ('en', 'es'):
    panel = Image.new('RGBA', (640, 448), '#121720')
    # Full decorated plate is reserved for the title. Text remains on its lobe.
    title_plate = original_plate.crop((0, 0, 256, 40)).resize((575, 76), Image.Resampling.NEAREST)
    panel.alpha_composite(title_plate, (25, 15))
    render(panel, 'title-26', 'gold', catalog['Settings'][locale], 58, 57)
    for row, (key, value) in enumerate((('Resolution', '1920 x 1080'), ('AspectRatio', '16:9'), ('Language', 'English' if locale == 'en' else 'Español'))):
        y = 110 + row * 84
        panel.alpha_composite(row_plate, (25, y))
        if row == 0:
            selected = Image.new('RGBA', row_plate.size)
            draw = ImageDraw.Draw(selected)
            draw.polygon([(18, 1), (573, 1), (561, 46), (2, 46)], fill=(44, 30, 64, 215), outline=(237, 173, 63, 255), width=1)
            panel.alpha_composite(selected, (25, y))
        panel.alpha_composite(chip, (409, y + 6))
        render(panel, 'body-16', 'white', catalog[key][locale], 62, y + 31)
        render(panel, 'body-16', 'cyan', value, 433, y + 30)
    panel.alpha_composite(help_plate, (25, 376))
    render(panel, 'body-12', 'grey', catalog['Back'][locale] + ' • ' + catalog['Apply'][locale], 62, 398)
    panel.convert('RGB').save(ROOT / f'settings-rows-{locale}.png')
    panel.resize((1280, 896), Image.Resampling.NEAREST).convert('RGB').save(ROOT / f'settings-rows-{locale}-2x.png')
print(ROOT / 'preview-locales.png')
