"""Claude: title cards for the release video (2560x1080, English and Spanish), drawn with our own icon and the project's OFL fonts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / 'video' / 'cards'
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2560, 1080
FONT_TITLE = HERE / 'font-candidates' / 'ofl_barlowcondensed_BarlowCondensed-ExtraBoldItalic.ttf'
FONT_BODY = HERE / 'font-candidates' / 'LiberationSans-Regular.ttf'
ICON = HERE / 'installer' / 'assets' / 'BT3TagTeam-icon-1024.png'


def bg():
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(12 + 14 * t), int(20 + 44 * t), int(44 + 40 * t)))
    # faint diagonal light streaks
    streaks = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(streaks)
    for i in range(-4, 14):
        x = i * 260
        sd.polygon([(x, 0), (x + 90, 0), (x - 380, H), (x - 470, H)], fill=(255, 255, 255, 10))
    im = Image.alpha_composite(im.convert('RGBA'), streaks)
    return im


def stroke_text(d, xy, text, font, fill, stroke=(24, 16, 44), width=8, anchor='la'):
    d.text(xy, text, font=font, fill=fill, stroke_width=width, stroke_fill=stroke, anchor=anchor)


def card(name, title, subtitle=None, lines=(), icon=True):
    im = bg()
    d = ImageDraw.Draw(im)
    if icon:
        ic = Image.open(ICON).convert('RGBA').resize((420, 420), Image.LANCZOS)
        im.alpha_composite(ic, (180, (H - 420) // 2))
        x0 = 700
    else:
        x0 = 220
    big = ImageFont.truetype(str(FONT_TITLE), 190)
    mid = ImageFont.truetype(str(FONT_TITLE), 82)
    body = ImageFont.truetype(str(FONT_BODY), 52)
    y = 300 if lines else 380
    stroke_text(d, (x0, y), title, big, (255, 205, 80))
    y += 210
    if subtitle:
        stroke_text(d, (x0, y), subtitle, mid, (236, 240, 255), width=5)
        y += 120
    for line in lines:
        d.text((x0, y), line, font=body, fill=(210, 222, 240))
        y += 70
    d.rectangle([x0, 292, x0 + 360, 298], fill=(240, 190, 70))
    im.convert('RGB').save(OUT / f'{name}.png')


CARDS = {
    'en': {
        'title': ('BT3 TAG TEAM', 'Standalone for Windows', ['Budokai Tenkaichi 3 + Power Scale BETA 1.5.1', 'Unofficial fan project. Bring your own disc image.']),
        'install': ('INSTALL', 'Three minutes, no admin rights', []),
        'hud': ('NEW HUD', 'Small markers over the fighters', []),
        'fusion': ('FUSION', 'Control modes, timers and form drain', []),
        'cpu': ('CPU TACTICS', 'Allies and enemies that transform', []),
        'revive': ('REVIVE', 'Bring your teammates back', []),
        'players': ('PLAYERS AND MODES', 'Team battle, free-for-all, co-op, training', []),
        'outro': ('CREDITS', 'Power Scale: LetsPlayBt3', ['Tag Team mod: The Mufti', 'Special thanks to RidJuampa for helping me understand the code.', 'Free download. Not affiliated with the owners of Dragon Ball.']),
    },
    'es': {
        'title': ('BT3 TAG TEAM', 'Versión independiente para Windows', ['Budokai Tenkaichi 3 + Power Scale BETA 1.5.1', 'Proyecto de fans no oficial. Trae tu propia imagen de disco.']),
        'install': ('INSTALAR', 'Tres minutos, sin permisos de administrador', []),
        'hud': ('NUEVO HUD', 'Pequeños marcadores sobre los luchadores', []),
        'fusion': ('FUSIÓN', 'Modos de control, temporizadores y desgaste por forma', []),
        'cpu': ('TÁCTICAS DE LA CPU', 'Aliados y enemigos que se transforman', []),
        'revive': ('REVIVIR', 'Recupera a tus compañeros', []),
        'players': ('JUGADORES Y MODOS', 'Equipos, todos contra todos, cooperativo, entrenamiento', []),
        'outro': ('CRÉDITOS', 'Power Scale: LetsPlayBt3', ['Mod Tag Team: The Mufti', 'Agradecimiento especial a RidJuampa por ayudarme a entender el código.', 'Descarga gratuita. Sin relación con los dueños de Dragon Ball.']),
    },
}

for lang, cards in CARDS.items():
    for key, (title, subtitle, lines) in cards.items():
        card(f'{key}-{lang}', title, subtitle, lines)
print('cards written to', OUT)
