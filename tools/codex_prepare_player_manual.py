"""Prepare current player-facing copies without editing Claude's draft manuals."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'installer/payload/manual'
OUT.mkdir(parents=True, exist_ok=True)
changes = {
    'EN': [
        ('press the menu switch button on the original main menu', 'press Select (the default menu switch button) on the original main menu'),
        ('Fusion between Goku Black (Rose) and Zamasu may not start yet, and Super Goku and Super Vegeta may not pair with each other yet.', 'Goku Black (Rosé) + Zamasu fusion still fails, including with two humans. Base Super Goku/Vegeta pairing has a guarded correction, but live acceptance and their transformed-form pairings remain pending.'),
        ('CPU fusion always picks the same result for a pair (for example Vegito); a choice between results is planned.', 'CPU fusion now rotates eligible native choices (for example Dance and Potara) when the original AI starts a fusion. It does not force a CPU to fuse; live acceptance remains pending.'),
        ('The loading cover between the mod menu and character select and the 2-player setup screen are being fixed.', 'The mode-to-character-select cover and multiplayer setup visibility still need live acceptance. If a setup screen is invisible, stop and report it rather than confirming selections blindly.'),
        ('Everything the game creates (imported data, saves, settings, logs) is inside', 'For new installations, everything the game creates (imported data, saves, settings, logs) is inside'),
        ('the logs do not contain personal paths.', 'review logs for personal paths before sharing them.'),
        ('5v5 currently runs around 20 to 30 updates per second on a Ryzen 5700G; small matches reach 60.', 'Performance depends on the machine, arena and fighter count; large simultaneous matches are more demanding.'),
    ],
    'ES': [
        ('pulsa el bot&oacute;n de cambio de men&uacute; del men&uacute; principal original', 'pulsa Select (el bot&oacute;n predeterminado para cambiar de men&uacute;) en el men&uacute; principal original'),
        ('El 5v5 funciona ahora a unas 20 a 30 actualizaciones por segundo en un Ryzen 5700G; las partidas peque&ntilde;as llegan a 60.', 'El rendimiento depende del equipo, el escenario y el n&uacute;mero de luchadores; las partidas simult&aacute;neas grandes exigen m&aacute;s recursos.'),
        ('La fusi&oacute;n entre Goku Black (Rose) y Zamasu puede no iniciarse a&uacute;n, y Super Goku y Super Vegeta pueden no emparejarse entre s&iacute; todav&iacute;a.', 'La fusi&oacute;n Black Ros&eacute; + Zamasu sigue fallando, incluso con dos jugadores humanos. La pareja base Goku/Vegeta de Super tiene una correcci&oacute;n protegida, pero siguen pendientes la prueba en juego y las parejas de sus formas transformadas.'),
        ('La fusi&oacute;n de la CPU elige siempre el mismo resultado para una pareja (por ejemplo Vegetto); est&aacute; prevista una elecci&oacute;n entre resultados.', 'La CPU alterna entre las opciones nativas disponibles cuando la IA original inicia una fusi&oacute;n. No obliga a la CPU a fusionarse; la prueba en juego sigue pendiente.'),
        ('La cubierta de carga entre el men&uacute; del mod y la selecci&oacute;n de personajes y la pantalla de preparaci&oacute;n de 2 jugadores se est&aacute;n corrigiendo.', 'La cubierta entre el men&uacute; del mod y la selecci&oacute;n de personajes y la visibilidad de la preparaci&oacute;n multijugador requieren una prueba en juego. Si la preparaci&oacute;n no es visible, detente y rep&oacute;rtalo en vez de confirmar a ciegas.'),
        ('los registros no contienen rutas personales.', 'revisa si los registros contienen rutas personales antes de compartirlos.'),
    ],
}
for lang in ('EN', 'ES'):
    text = (HERE / f'manual/BT3-TagTeam-Manual-{lang}.html').read_text(encoding='utf-8')
    for old, new in changes[lang]:
        assert old in text, f'Manual draft changed: {lang}: {old}'
        text = text.replace(old, new)
    # Avoid a section heading stranded at the bottom of a page.
    text = text.replace('break-after: avoid;', 'break-after: avoid; page-break-after: avoid;')
    (OUT / f'BT3-TagTeam-Manual-{lang}.html').write_text(text, encoding='utf-8')
node = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
subprocess.run([str(node), str(HERE / 'codex_render_player_manual.cjs')], check=True)
print('Prepared localized HTML/PDF player guides with current preview status')
